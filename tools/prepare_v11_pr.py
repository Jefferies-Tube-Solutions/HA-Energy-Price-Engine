"""Create/reuse the one ordinary beta review PR; never approve, merge or bypass."""

import json
import re
import subprocess
import tempfile
from pathlib import Path

from publish_v11 import BRANCH, REPO, api, stable_integrity
from verify_v11_source import verify


def prepare():
    verify(native=True)
    stable_integrity()
    prs = api("pulls?state=open&base=main&head=NicolaiTandrup%3Afeat%2Fv1.1-beta1-dashboard")
    assert len(prs) <= 1
    if prs:
        url = prs[0]["html_url"]
    else:
        notes = Path("docs/RELEASE_V11_BETA1.md").read_text()
        base = f"https://github.com/{REPO}/blob/{BRANCH}/docs/"
        notes = re.sub(r"\]\((?!https?://)([^)]+)\)", lambda m: "](" + base + m[1] + ")", notes)
        body = Path(tempfile.gettempdir()) / "pe-v11-pr.md"
        body.write_text(notes)
        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                REPO,
                "--base",
                "main",
                "--head",
                BRANCH,
                "--draft",
                "--title",
                "v1.1 beta.1: automatic Lovelace card and independent display units",
                "--body-file",
                str(body),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        url = result.stdout.strip()
    print(json.dumps({"pr_url": url, "branch": BRANCH, "main_unmerged": True}))


if __name__ == "__main__":
    try:
        prepare()
    except Exception as err:
        message = str(err).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::error title=Ordinary v1.1 beta PR gate::" + message, flush=True)
        raise
