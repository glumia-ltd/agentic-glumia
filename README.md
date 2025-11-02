# AI Project Agent — Starter Kit

This starter shows how to build a *stateful agent* that:
- curates inputs,
- designs a project blueprint,
- implements tasks,
- and fires prompts/tools at specific **states** and **deliverables**.

It uses **LangGraph** for orchestration and the **OpenAI Python SDK (Responses API)** for LLM calls. MCP/Connectors can be added later.

## Quickstart

```bash
# 1) Python 3.10+ recommended
python -V

# 2) Create a virtualenv
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)

# 3) Install
pip install -r requirements.txt

# 4) Configure your API key
export OPENAI_API_KEY="sk-..."
# Optional: choose a model
export OPENAI_MODEL="gpt-4o-mini"

# 5) Dry run with the example blueprint
python src/app.py run --blueprint examples/website_redesign.yaml

# (Optional) Validate structure
python src/app.py validate --blueprint examples/website_redesign.yaml
```

### What this does
- Loads a **Project Blueprint** (YAML).
- Compiles a **state graph** with phases: `intake → design → implement → review → ship → done`.
- On each state entry, runs a role prompt with the current **state** and stores artifacts in `./run_artifacts`.
- Emits clear logs so you can plug in real tools (GitHub, CI, Vercel) later via MCP/connectors.

## Structure

```
ai-project-agent-starter/
  src/
    app.py            # CLI (run / validate)
    orchestrator.py   # Graph + nodes + hooks
    models.py         # Pydantic models for the blueprint
    tools/
      tool_stubs.py   # local function-tool examples (doc.create, ci.run_tests, etc.)
    runtime/
      io.py           # simple logging / artifact writing
  prompts/
    role_prompts.yaml # Curator/Designer/Implementer/QA/Release Manager
  examples/
    website_redesign.yaml  # Sample blueprint
  tests/
    test_blueprint.py
  requirements.txt
  .env.example
  README.md
```

## Next steps
- Swap `tool_stubs.py` with real MCP connectors (GitHub/Jira/Docs/Slack).
- Add automated gates (CI, Lighthouse) and human approvals.
- Persist graph state to a DB checkpointer (Postgres/Redis).
- Add tracing (OpenAI tracing, LangSmith) and regression evals.


## GitHub repo + CI (one-time setup)

1) Authenticate the GitHub CLI:
```bash
gh auth login
```

2) Create the repo and push the code (private by default):
```bash
./scripts/bootstrap_repo.sh <your-username-or-org> ai-project-agent-starter private
```

3) Enable branch protection & PR gating (requires appropriate token scopes):
```bash
./scripts/protect_main.sh <your-username-or-org> ai-project-agent-starter
```

4) Open a test PR. GitHub Actions will run **CI** (unit tests). With branch protection enabled, merges will be **blocked until CI passes**.


## Real GitHub automation

Set these env vars (or add to `.env`):
```bash
export GITHUB_TOKEN=ghp_your_PAT_with_repo_scope
export GITHUB_OWNER=<your-username-or-org>
export GITHUB_REPO=<existing-repo-name>  # create/push with scripts/bootstrap_repo.sh first
```

Run the GitHub automation example:
```bash
python src/app.py run --blueprint examples/gh_automation.yaml
```

What it does:
1. Creates a branch `feat/blueprint` from `main`.
2. Files an issue titled "Draft spec".
3. Commits the **design** artifact to `docs/spec.md` on that branch.
4. Opens a PR from the branch to `main`.
5. (Optional) Runs a deploy step using `deploy.vercel` (requires `VERCEL_TOKEN` and `vercel` CLI).

## Deploys (optional)

For Vercel deployments from the agent:
```bash
npm i -g vercel
export VERCEL_TOKEN=your_token
python src/app.py run --blueprint examples/gh_automation.yaml
```

**CI gating:** With `.github/workflows/ci.yml` in place and branch protection on `main`, PRs will be blocked until tests pass.


## Labels, Code Owners, and Templates

- **Auto-labeling**: `.github/labeler.yml` + `auto-label.yml` add `area/*` labels based on changed paths.
- **CODEOWNERS**: `.github/CODEOWNERS` routes reviews to your teams. Update the `@YOUR_*` placeholders.
- **Issue templates**: Bug & Feature request YAML forms in `.github/ISSUE_TEMPLATE/`.
- **PR template**: `.github/pull_request_template.md` with a checklist for CI, docs, and labels.

## Container Image (GHCR)

The workflow `.github/workflows/release-image.yml` publishes to `ghcr.io/<owner>/ai-project-agent` on:
- pushes to `main` (branch tag and SHA tag),
- semantic tags `vX.Y.Z`.

**Local run:**
```bash
docker build -t agent .
docker run --rm -it \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e GITHUB_OWNER=$GITHUB_OWNER \
  -e GITHUB_REPO=$GITHUB_REPO \
  -v $PWD/examples:/app/examples \
  agent run --blueprint examples/gh_automation.yaml
```
