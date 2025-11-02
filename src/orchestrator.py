import os, json, yaml, time
import openai
from typing import TypedDict, Literal, Dict, Any
from langgraph.graph import StateGraph, START, END
from openai import OpenAI
import os
from .runtime import io
from .tools import tool_stubs
from .tools.github_api import GitHub
from .tools import deploy
from .models import Blueprint, Phase

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_openai_client = None

def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client

class ProjectState(TypedDict, total=False):
    phase: str
    ctx: Dict[str, Any]
    artifacts: Dict[str, str]
    approvals: Dict[str, bool]
    last_event: str

def run_prompt(role_prompt: str, state: ProjectState) -> str:
    """Call OpenAI Responses API with plain text output."""
    sys = f"You are a helpful project {state.get('phase','agent')}."
    user = f"{role_prompt}\n\nSTATE:\n{json.dumps(state, indent=2)[:6000]}"
    io.log(f"LLM ({MODEL}) <- {state.get('phase')}")
    if os.getenv("OPENAI_OFFLINE", "").lower() in ("1", "true", "yes"):
        return f"[OFFLINE MOCK OUTPUT] phase={state.get('phase')}\n\n{role_prompt[:200]}..."
    client = _get_openai_client()
    last_err = None
    for attempt in range(3):
        try:
            res = client.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": user},
                ],
            )
            break
        except openai.RateLimitError as e:
            wait = 2 ** attempt
            io.log(f"Rate limited (429). Retry in {wait}s...")
            time.sleep(wait)
            last_err = e
        except Exception as e:
            raise
    else:
        raise last_err
    # Extract the first text output
    text = ""
    for item in res.output:
        if item.type == "message":
            for content in item.message.content:
                if content.type == "output_text":
                    text += content.text
    return text.strip()


def _parse_args(argstr: str):
    # format: "k1=v1|k2=v2|bare"
    out = {}
    if not argstr:
        return out
    parts = [p for p in (a.strip() for a in argstr.split("|")) if p]
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
        else:
            out[p] = True
    return out


def call_tool(spec: str, state: ProjectState | None = None):
    if ":" in spec:
        fn, arg = spec.split(":", 1)
    else:
        fn, arg = spec, None
    # --- Built-in stubs (still available)
    if fn == "doc.create":
        return tool_stubs.doc_create(arg or "note.md")
    if fn == "ci.run_tests":
        return tool_stubs.ci_run_tests()
    if fn == "lighthouse.audit":
        return tool_stubs.lighthouse_audit()
    # --- GitHub tools (require env: GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO)
    if fn.startswith("github."):
        gh = GitHub()
        a = _parse_args(arg or "")
        if fn == "github.create_issue":
            return gh.create_issue(title=a.get("title") or "Task", body=a.get("body",""))
        if fn == "github.create_branch":
            return gh.create_branch(new_branch=a.get("name","feature"), from_branch=a.get("from","main"))
        if fn == "github.commit_artifact":
            # commit the artifact produced by a phase into repo at path
            phase = a.get("phase")
            path  = a.get("path", f"{phase or 'artifact'}.md")
            branch = a.get("branch", "feature")
            msg = a.get("message", f"chore: add artifact {phase}")
            if not state or not phase or phase not in state.get("artifacts", {}):
                raise RuntimeError("github.commit_artifact needs phase=<id> and an existing artifact in state")
            artifact_path = state["artifacts"][phase]
            content = open(artifact_path, "r", encoding="utf-8").read()
            return gh.commit_file(path, content, msg, branch)
        if fn == "github.open_pr":
            title = a.get("title", "Automated PR")
            head  = a.get("head", "feature")
            base  = a.get("base", "main")
            body  = a.get("body","")
            return gh.create_pr(title=title, head=head, base=base, body=body)
    # --- Deploy tools
    if fn == "deploy.vercel":
        return deploy.vercel_deploy()
    # Fallback
    io.log(f"Unknown tool: {spec}")
    return None

def build_nodes(prompts: Dict[str, str]):
    def n_factory(phase: Phase):
        def node(state: ProjectState):
            state["phase"] = phase.id
            # 1) entry prompt
            role_prompt = prompts.get(phase.entry_prompt, "")
            if role_prompt:
                out = run_prompt(role_prompt, state)
                name = f"{phase.id}.md"
                path = io.write_artifact(name, out)
                state.setdefault("artifacts", {})[phase.id] = path
                io.log(f"artifact -> {path}")
            # 2) tasks tools
            for t in phase.tasks:
                for spec in t.tool_calls:
                    call_tool(spec)
            # 3) naive gating
            if phase.gate and phase.gate.type == "human_approval":
                approved = state.get("approvals", {}).get(phase.gate.approver or "PM", True)
                state["last_event"] = "approved" if approved else "rejected"
            elif phase.gate and phase.gate.type == "automated_checks":
                state["last_event"] = "pass"
            else:
                state["last_event"] = "complete"
            return state
        return node
    return n_factory

def compile_graph(bp: Blueprint, prompts: Dict[str,str]):
    builder = StateGraph(ProjectState)
    nodes = {}
    make = build_nodes(prompts)
    # add nodes
    for ph in bp.phases:
        fn = make(ph)
        nodes[ph.id] = fn
        builder.add_node(ph.id, fn)
    # add edges
    if bp.phases:
        builder.add_edge(START, bp.phases[0].id)
    # simple transitions based on 'transitions' map
    for ph in bp.phases:
        dest = ph.transitions or {}
        # normalize special terminal aliases to END
        def _norm_target(t):
            if isinstance(t, str) and t.lower() in ("done", "end", "finish"):
                return END
            return t
        dest2 = {k: _norm_target(v) for k, v in dest.items()}
        # map keys -> events
        targets = set(dest2.values())
        if not targets:
            continue
        # we’ll pick the first unique target as default
        default = list(targets)[0]
        def route(state: ProjectState, ph=ph, dest=dest2, default=default):
            ev = state.get("last_event","")
            # normalize keys
            key = None
            if ev in ("complete","approved","pass"):
                key = {"complete":"on_complete","approved":"on_approved","pass":"on_pass"}[ev]
            # fallback
            return dest.get(key, default)
        # build choices map
        choices = {v:v for v in targets}
        builder.add_conditional_edges(ph.id, route, choices)
    # end at last
    builder.add_edge(bp.phases[-1].id, END)
    return builder.compile()

def run_blueprint(blueprint_path: str, prompts_path: str, approvals: Dict[str,bool] | None = None):
    bp = Blueprint.model_validate(yaml.safe_load(open(blueprint_path)))
    prompts = yaml.safe_load(open(prompts_path))
    graph = compile_graph(bp, prompts)
    state: ProjectState = {"ctx":{"project_id": bp.project.id}, "artifacts":{}, "approvals": approvals or {"PM": True}}
    io.log(f"Starting run for {bp.project.id}")
    result = graph.invoke(state)
    io.log("Run complete.")
    return result
