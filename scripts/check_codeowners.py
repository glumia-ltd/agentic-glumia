import os, sys
path = ".github/CODEOWNERS"
if not os.path.exists(path):
    print("Missing .github/CODEOWNERS", file=sys.stderr)
    sys.exit(1)
print("CODEOWNERS OK.")
