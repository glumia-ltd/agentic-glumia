import os, base64, json, typing as t
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO  = os.getenv("GITHUB_REPO")

API = "https://api.github.com"

class GitHub:
    def __init__(self, token: str | None = None, owner: str | None = None, repo: str | None = None):
        self.token = token or GITHUB_TOKEN
        self.owner = owner or GITHUB_OWNER
        self.repo  = repo or GITHUB_REPO
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN is required")
        if not self.owner or not self.repo:
            raise RuntimeError("GITHUB_OWNER and GITHUB_REPO are required")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })

    # --- helpers
    def _url(self, path: str) -> str:
        return f"{API}/repos/{self.owner}/{self.repo}{path}"

    def get_default_branch(self) -> str:
        r = self.session.get(self._url(""))
        r.raise_for_status()
        return r.json().get("default_branch", "main")

    # --- branches
    def get_branch_sha(self, branch: str) -> str:
        r = self.session.get(self._url(f"/git/ref/heads/{branch}"))
        r.raise_for_status()
        return r.json()["object"]["sha"]

    def create_branch(self, new_branch: str, from_branch: str | None = None) -> dict:
        from_branch = from_branch or self.get_default_branch()
        sha = self.get_branch_sha(from_branch)
        r = self.session.post(self._url("/git/refs"), json={"ref": f"refs/heads/{new_branch}", "sha": sha})
        if r.status_code == 422 and "Reference already exists" in r.text:
            return {"message": "exists", "ref": new_branch}
        r.raise_for_status()
        return r.json()

    # --- contents
    def commit_file(self, path: str, content: str, message: str, branch: str) -> dict:
        b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        # Get sha if exists
        get = self.session.get(self._url(f"/contents/{path}"), params={"ref": branch})
        sha = get.json().get("sha") if get.status_code == 200 else None
        payload = {"message": message, "content": b64, "branch": branch}
        if sha:
            payload["sha"] = sha
        r = self.session.put(self._url(f"/contents/{path}"), json=payload)
        r.raise_for_status()
        return r.json()

    # --- issues & PRs
    def create_issue(self, title: str, body: str = "") -> dict:
        r = self.session.post(self._url("/issues"), json={"title": title, "body": body})
        r.raise_for_status()
        return r.json()

    def create_pr(self, title: str, head: str, base: str, body: str = "") -> dict:
        r = self.session.post(self._url("/pulls"), json={"title": title, "head": head, "base": base, "body": body})
        r.raise_for_status()
        return r.json()

    # --- protection (optional helper)
    def protect_main(self, branch: str = "main") -> dict:
        url = self._url(f"/branches/{branch}/protection")
        r = self.session.put(url, json={
            "required_status_checks": {"strict": False, "contexts": []},
            "enforce_admins": True,
            "required_pull_request_reviews": {"required_approving_review_count": 1, "dismiss_stale_reviews": True},
            "restrictions": None
        })
        r.raise_for_status()
        return r.json()
