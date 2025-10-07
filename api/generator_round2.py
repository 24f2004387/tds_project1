import os
import tempfile, subprocess, pathlib, base64
from typing import Dict
from .models import TaskRequest, BuildResult
from .settings import settings
from .llm import generate_readme_via_llm, synthesize_app
from .notifier import notify_with_backoff
from .guardrails import (
    require_highlight_if_checked,
    require_title_if_checked,
    require_selector_if_mentioned,
)

def _run(cmd: list, cwd=None):
    print("RUN:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)

def update_existing_repo_with_llm(req: TaskRequest) -> BuildResult:
    assert req.round == 2, "This function only supports round 2"

    # Use same repo name as in round 1
    repo_name = req.task.replace(" ", "-")
    username = settings.GITHUB_USERNAME
    repo_url = f"https://github.com/{username}/{repo_name}.git"

    tmp = tempfile.mkdtemp()
    repo_path = pathlib.Path(tmp) / repo_name

    # Clone the repo
    _run(["git", "clone", repo_url, str(repo_path)])
    _run(["git", "checkout", settings.DEFAULT_BRANCH], cwd=repo_path)

    # Read current files
    index_path = repo_path / "index.html"
    app_path = repo_path / "app.js"

    if not index_path.exists() or not app_path.exists():
        raise RuntimeError("Existing repo does not contain index.html or app.js")

    old_files = {
        "index.html": index_path.read_text(encoding="utf-8"),
        "app.js": app_path.read_text(encoding="utf-8"),
    }

    seed = req.nonce[:8]
    attachments = {}  # Round 2 usually doesn't include new attachments
    extra_vars = {"seed": seed, "round": 2}

    # Ask LLM to modify the existing app
    updated_files = synthesize_app(
        brief=req.brief,
        checks=req.checks,
        seed=seed,
        attachments=attachments,
        extra_vars=extra_vars,
    )

    # Overwrite files
    for name, content in updated_files.items():
        fpath = repo_path / name
        fpath.write_text(content, encoding="utf-8")

    # Rebuild README
    readme = generate_readme_via_llm(req.brief, req.checks, repo_url=repo_url, pages_url=f"https://{username}.github.io/{repo_name}/")
    (repo_path / "README.md").write_text(readme, encoding="utf-8")

    # Guardrails
    require_highlight_if_checked(updated_files, req.checks)
    require_title_if_checked(updated_files, req.checks)
    require_selector_if_mentioned(updated_files, req.checks, seed)

    # Commit and push
    _run(["git", "add", "."], cwd=repo_path)
    _run(["git", "commit", "-m", "update: round 2 requirements"], cwd=repo_path)
    _run(["git", "push"], cwd=repo_path)

    # Notify
    if req.evaluation_url:
        notify_with_backoff(
            evaluation_url=req.evaluation_url,
            payload={
                "email": req.email,
                "task": req.task,
                "round": req.round,
                "nonce": req.nonce,
                "repo_url": f"https://github.com/{username}/{repo_name}",
                "commit_sha": os.popen(f"git -C {repo_path} rev-parse HEAD").read().strip(),
                "pages_url": f"https://{username}.github.io/{repo_name}/"
            }
        )

    return BuildResult(
        repo_url=f"https://github.com/{username}/{repo_name}",
        pages_url=f"https://{username}.github.io/{repo_name}/",
        commit_sha=os.popen(f"git -C {repo_path} rev-parse HEAD").read().strip()
    )