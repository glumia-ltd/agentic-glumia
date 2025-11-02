#!/usr/bin/env python3
import os, re, subprocess, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"

SECTIONS = {
    "Breaking": re.compile(r"BREAKING CHANGE|!:"),
    "Features": re.compile(r"^feat"),
    "Fixes": re.compile(r"^fix"),
    "Chore": re.compile(r"^(build|chore|ci|docs|refactor|perf|test)")
}

def last_tag():
    try:
        return subprocess.check_output(["git","describe","--tags","--abbrev=0"], text=True).strip()
    except subprocess.CalledProcessError:
        return None

def commits_since(tag):
    rng = f"{tag}..HEAD" if tag else "--since=1970-01-01"
    out = subprocess.check_output(["git","log","--pretty=%H%x09%s"], text=True, input=None, stderr=subprocess.STDOUT, args=None, env=None, )
    return subprocess.check_output(["git","log","--pretty=%s", rng], text=True).splitlines()

def group(commits):
    buckets = {k: [] for k in SECTIONS}
    other = []
    for c in commits:
        added = False
        for name, rx in SECTIONS.items():
            if rx.search(c):
                buckets[name].append(c)
                added = True
                break
        if not added and c.strip():
            other.append(c)
    return buckets, other

def write_changelog(version, grouped, other):
    today = datetime.date.today().isoformat()
    lines = []
    lines.append(f"## {version} - {today}\n")
    for name, items in grouped.items():
        if items:
            lines.append(f"### {name}\n")
            for it in items:
                lines.append(f"- {it}")
            lines.append("")
    if other:
        lines.append("### Other")
        for it in other:
            lines.append(f"- {it}")
        lines.append("")
    content = "\n".join(lines) + "\n"
    if CHANGELOG.exists():
        prev = CHANGELOG.read_text()
        CHANGELOG.write_text(content + "\n" + prev)
    else:
        CHANGELOG.write_text("# Changelog\n\n" + content)

if __name__ == "__main__":
    tag = last_tag()
    rng = f"{tag}..HEAD" if tag else "--since=1970-01-01"
    commits = subprocess.check_output(["git","log","--pretty=%s", rng], text=True).splitlines()
    if not any(c.strip() for c in commits):
        sys.exit(0)
    # Version provided via env (preferred), else fallback
    version = os.getenv("NEXT_VERSION", "0.0.0")
    grouped, other = group(commits)
    write_changelog(version, grouped, other)
