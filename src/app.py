import os, argparse, yaml, sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from pydantic import ValidationError
from .models import Blueprint
from .orchestrator import run_blueprint

def cmd_validate(args):
    try:
        Blueprint.model_validate(yaml.safe_load(open(args.blueprint)))
        print("Blueprint is valid ✅")
    except ValidationError as e:
        print("Blueprint validation failed ❌")
        print(e)
        sys.exit(1)

def cmd_run(args):
    if not os.getenv("OPENAI_API_KEY"):
        hint = f" (looked in: {LOADED_DOTENV})" if 'LOADED_DOTENV' in globals() and LOADED_DOTENV else ""
        print(f"OPENAI_API_KEY is not set. Add it to your .env or export it.{hint}")
        sys.exit(1)
    run_blueprint(args.blueprint, args.prompts, approvals=None)

def main():
    # Load env from .env (search upward from CWD), with fallback to repo root
    dotenv_path = find_dotenv(usecwd=True)
    if not dotenv_path:
        repo_root = Path(__file__).resolve().parents[1]
        candidate = repo_root / ".env"
        dotenv_path = str(candidate) if candidate.exists() else ""
    load_dotenv(dotenv_path or None, override=True)
    global LOADED_DOTENV
    LOADED_DOTENV = dotenv_path
    parser = argparse.ArgumentParser(description="AI Project Agent")
    sub = parser.add_subparsers(dest="cmd")

    p1 = sub.add_parser("validate")
    p1.add_argument("--blueprint", required=True)
    p1.set_defaults(func=cmd_validate)

    p2 = sub.add_parser("run")
    p2.add_argument("--blueprint", required=True)
    p2.add_argument("--prompts", default="prompts/role_prompts.yaml")
    p2.set_defaults(func=cmd_run)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(0)
    args.func(args)

if __name__ == "__main__":
    main()
