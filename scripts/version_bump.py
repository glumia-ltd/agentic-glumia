#!/usr/bin/env python3
import os, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
BREAKING_RE = re.compile(r"BREAKING CHANGE|!:")

def get_current_version():
    if VERSION_FILE.exists():
        v = VERSION_FILE.read_text().strip()
        if not SEMVER.match(v):
            print(f"Invalid VERSION: {v}", file=sys.stderr)
            sys.exit(1)
        return v
    return "0.1.0"

def get_last_tag():
    try:
        tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip()
        return tag
    except subprocess.CalledProcessError:
        return None

def get_commits_since(ref):
    if ref:
        rng = f"{ref}..HEAD"
    else:
        # no tags — use full history
        rng = "--since=1970-01-01"
    out = subprocess.check_output(["git", "log", "--pretty=%s%n%b", rng], text=True)
    return out.splitlines()

def detect_bump(commits):
    bump = "patch"  # default
    for line in commits:
        if BREAKING_RE.search(line):
            return "major"
    for line in commits:
        if line.startswith("feat"):
            bump = "minor"
    for line in commits:
        if line.startswith("fix"):
            bump = max(bump, "patch", key=["patch","minor","major"].index)
    return bump

def bump_version(v, bump):
    major, minor, patch = map(int, v.split("."))
    if bump == "major":
        return f"{major+1}.0.0"
    if bump == "minor":
        return f"{major}.{minor+1}.0"
    return f"{major}.{minor}.{patch+1}"

if __name__ == "__main__":
    cur = get_current_version()
    tag = get_last_tag()
    commits = get_commits_since(tag)
    if not any(c.strip() for c in commits):
        print(cur)  # nothing to bump
        sys.exit(0)
    bump = detect_bump(commits)
    nxt = bump_version(cur, bump)
    print(nxt)
