import sys, yaml, os, io
CFG = "codeowners.config.yaml"
OUT = ".github/CODEOWNERS"
def main():
    if not os.path.exists(CFG):
        print(f"{CFG} not found", file=sys.stderr)
        sys.exit(1)
    data = yaml.safe_load(open(CFG, "r", encoding="utf-8"))
    mappings = data.get("mappings", {})
    buf = io.StringIO()
    buf.write("# CODEOWNERS (generated)\n")
    for path, owners in mappings.items():
        owners_str = " ".join(owners)
        buf.write(f"{path} {owners_str}\n")
    os.makedirs(".github", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    print(f"Wrote {OUT}")
if __name__ == "__main__":
    main()
