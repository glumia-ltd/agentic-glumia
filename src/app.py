import os, argparse, yaml, sys
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
    run_blueprint(args.blueprint, args.prompts, approvals=None)

def main():
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
