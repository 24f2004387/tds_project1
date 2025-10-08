from fastapi import FastAPI, HTTPException
from threading import Thread
from .models import TaskRequest, TaskResponse
from .security import verify_secret
from .generator import generate_app_repo
from .notifier import notify_with_backoff
from .settings import settings
import os
import traceback
from fastapi.responses import PlainTextResponse
import pathlib


from fastapi.responses import RedirectResponse, JSONResponse
import traceback, sys

print("[BOOT] GITHUB_USERNAME =", os.getenv("GITHUB_USERNAME"))
print("[BOOT] GH_TOKEN set?", bool(os.getenv("GH_TOKEN")))
print("[BOOT] GITHUB_TOKEN set?", bool(os.getenv("GITHUB_TOKEN")))


app = FastAPI(title="LLM Code Deployment API (Synthesizing)")


# show a tiny landing page and a debug JSON at /_routes for HF to probe
@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")

@app.get("/_routes", include_in_schema=False)
async def debug_routes():
    try:
        r = [{"path": rt.path, "name": getattr(rt, "name", "")} for rt in app.routes]
        return JSONResponse(r)
    except Exception:
        return JSONResponse({"error": "listing routes failed", "trace": traceback.format_exc()})


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

    return {
        "email": req.email,
        "task": req.task,
        "round": req.round,
        "nonce": req.nonce,
        **result.dict(),
        "status": "ok"
    }


@app.get("/_notify_log", include_in_schema=False)
async def _notify_log():
    path = pathlib.Path("/tmp/notify.log")
    if not path.exists():
        return PlainTextResponse("NO LOG: /tmp/notify.log not found\n")
    try:
        text = path.read_text(encoding="utf-8")
        return PlainTextResponse(text)
    except Exception as e:
        return PlainTextResponse(f"ERROR reading log: {e}\n")

