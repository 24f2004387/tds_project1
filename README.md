# 🤖 LLM Code Deployment API (Synthesizing)

A fully automated **FastAPI-based system** that accepts a structured JSON prompt, uses an **LLM** (e.g. GPT-4o / GPT-5 via AI Pipe) to generate a minimal working web app, and then automatically:
- Creates a **public GitHub repository**
- Pushes all generated files (`index.html`, `app.js`, etc.)
- Adds a full `README.md` and MIT `LICENSE`
- Enables **GitHub Pages** for instant live hosting
- Reports results (repo URL, commit SHA, Pages URL) to an `evaluation_url`

This API forms the backend of a “self-deploying LLM” — capable of turning natural language app briefs into live, hosted sites in under a minute.

---

## 🚀 Features

✅ Accepts structured JSON requests (via `/task`)  
✅ Verifies secret key before any build  
✅ Uses LLMs to synthesize minimal apps from briefs + checks  
✅ Creates GitHub repos via `gh CLI` and deploys via GitHub Pages  
✅ Supports **Round 1** (new repo) and **Round 2** (update existing repo)  
✅ Automatically notifies the given `evaluation_url` with build details  
✅ Built-in retry & exponential backoff for robust webhook notifications  
✅ Log endpoint `/ _notify_log` for debugging delivery attempts  

---

## 🧠 How It Works

1. **POST a JSON request** to `/task` (round 1 or 2)  
   ```json
   {
     "email": "you@example.com",
     "secret": "enter",
     "task": "markdown-to-html-001",
     "round": 1,
     "nonce": "abc123",
     "brief": "Publish a static page that converts Markdown to HTML using marked.js",
     "checks": [
       "document.querySelector('#markdown-output')"
     ],
     "evaluation_url": "https://example.com/notify",
     "attachments": []
   }
2. The app:
Verifies the shared secret.
Calls synthesize_app() to generate HTML/JS.
Creates and pushes a new GitHub repo using the GitHub CLI (gh).
Enables GitHub Pages for live hosting.
Sends a POST back to evaluation_url with build details.

3. Response:

{
  "email": "you@example.com",
  "task": "markdown-to-html-001",
  "round": 1,
  "nonce": "abc123",
  "repo_url": "https://github.com/24f2004387/markdown-to-html-001",
  "commit_sha": "9f6808ba71025ba18294a40836b5b5da6e1645b9",
  "pages_url": "https://24f2004387.github.io/markdown-to-html-001/",
  "status": "ok"
}

