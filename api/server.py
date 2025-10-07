from fastapi import FastAPI, HTTPException
from threading import Thread
from .models import TaskRequest, TaskResponse
from .security import verify_secret
from .generator import generate_app_repo
from .notifier import notify_with_backoff
from .settings import settings
import os
import traceback

print("[BOOT] OPENAI_BASE_URL =", settings.OPENAI_BASE_URL)
print("[BOOT] OPENAI_API_KEY set? ->", bool(settings.OPENAI_API_KEY))

app = FastAPI(title="LLM Code Deployment API (Synthesizing)")

@app.post("/task", response_model=TaskResponse)
async def receive_task(req: TaskRequest):
    if not verify_secret(req.secret):
        raise HTTPException(status_code=401, detail="Invalid secret")

    try:
        if req.round == 1:
            result = generate_app_repo(req)
        elif req.round == 2:
            from .generator_round2 import update_existing_repo_with_llm
            result = update_existing_repo_with_llm(req)
        else:
            raise HTTPException(status_code=400, detail="Unsupported round")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Build failed: {e}")

    if req.evaluation_url:
        def _notify():
            try:
                notify_with_backoff(
                    evaluation_url=req.evaluation_url,
                    payload={
                        "email": req.email,
                        "task": req.task,
                        "round": req.round,
                        "nonce": req.nonce,
                        "repo_url": result.repo_url,
                        "commit_sha": result.commit_sha,
                        "pages_url": result.pages_url,
                    },
                )
            except Exception:
                pass
        Thread(target=_notify, daemon=True).start()

    return TaskResponse(status="ok", **result.dict())
