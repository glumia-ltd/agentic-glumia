import os, json, pathlib, datetime as dt
RUN_DIR = pathlib.Path("run_artifacts")
RUN_DIR.mkdir(exist_ok=True)

def write_artifact(name: str, content: str) -> str:
    ts = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    path = RUN_DIR / f"{ts}-{name}"
    path.write_text(content, encoding="utf-8")
    return str(path)

def log(msg: str):
    print(f"[agent] {msg}")
