import os, subprocess, shutil
from . import io

def vercel_deploy(cwd: str = ".", prod: bool = True):
    token = os.getenv("VERCEL_TOKEN")
    if not token:
        raise RuntimeError("VERCEL_TOKEN is required for deploy.vercel")
    if not shutil.which("vercel"):
        raise RuntimeError("vercel CLI not found. Install: npm i -g vercel")
    cmd = ["vercel", "--token", token, "-y"]
    if prod:
        cmd.append("--prod")
    io.log(f"Running: {' '.join(cmd)} in {cwd}")
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    io.log(res.stdout.strip())
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    return {"ok": True}
