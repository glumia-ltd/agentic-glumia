import os, requests, sys, json
OWNER = os.getenv("GITHUB_OWNER")
REPO  = os.getenv("GITHUB_REPO")
TOKEN = os.getenv("GITHUB_TOKEN")
if not (OWNER and REPO and TOKEN):
    print("Set GITHUB_OWNER, GITHUB_REPO, and GITHUB_TOKEN env vars.", file=sys.stderr)
    sys.exit(1)
API = f"https://api.github.com/repos/{OWNER}/{REPO}/labels"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
labels_path = "labels.json"
if os.path.exists(labels_path):
    LABELS = json.load(open(labels_path))
else:
    LABELS = {"area/agent":{"color":"1f77b4","description":"Agent orchestration & prompts"}}
def upsert_label(name, meta):
    payload = {"name": name, "color": meta.get("color","ededed"), "description": meta.get("description","")}
    r = requests.patch(f"{API}/{name}", headers=HEADERS, json=payload)
    if r.status_code == 404:
        r = requests.post(API, headers=HEADERS, json=payload)
    r.raise_for_status()
    print(f"✔ {name}")
def main():
    for name, meta in LABELS.items():
        upsert_label(name, meta)
    print("Done.")
if __name__ == "__main__":
    main()
