# Deployment Plan: Google MCP Server on Railway

This document details the architectural changes and step-by-step procedures required to deploy the local Google MCP Server to the **Railway** cloud hosting platform.

---

## 1. Production Constraints & Solutions

Deploying a local, interactive script to a cloud container environment introduces three core constraints:

### Constraint A: Interactive Stdin Blocking (Console Approval Gate)
* **Problem**: The server calls `input("Approve? (y/n)")` to block and wait for human input. In Railway's headless, non-interactive container environment, standard input (`sys.stdin`) is closed. This causes immediate `EOFError` failures or indefinite hanging on incoming requests.
* **Solution**: 
  1. **Option 1 (Direct Bypass)**: Add an environment variable `BYPASS_APPROVAL=True` to skip the terminal prompt.
  2. **Option 2 (Slack / Telegram Webhook)**: Refactor the approval check to send a payload to Slack/Discord/Telegram with interactive approval buttons, and wait for a response callback webhook before executing.
  * *For this plan, we will implement **Option 1** as the baseline, allowing you to toggle approval requirements.*

### Constraint B: Ehemeral Filesystem (`credentials.json` & `token.json`)
* **Problem**: Railway containers are ephemeral. Any files written during execution (like `token.json` generated from a browser sign-in) are destroyed on restarts or redeploys. Additionally, you cannot commit these files to GitHub.
* **Solution**: 
  - Store the string contents of `credentials.json` and `token.json` in Railway **Environment Variables** (`GOOGLE_CREDENTIALS_JSON` and `GOOGLE_TOKEN_JSON`).
  - Modify `auth.py` to read from these environment variables first and fall back to local files if the variables aren't set.

### Constraint C: Host & Port Binding
* **Problem**: In local testing, the server binds to `127.0.0.1:8000`. Railway routes traffic from the public internet through a proxy to a dynamic port defined in the `PORT` environment variable, which requires binding the server to `0.0.0.0`.
* **Solution**: Update `server.py` to bind to `0.0.0.0` and read the port from the `PORT` environment variable when running in production.

---

## 2. Required Code Modifications

To support the above solutions, we need to adapt our server code.

### A. Modify `auth.py`
Add support for environment variables:
```python
import json
# ... inside get_credentials() ...
# 1. Try loading from environment variable first
env_token = os.getenv('GOOGLE_TOKEN_JSON')
if env_token:
    try:
        token_info = json.loads(env_token)
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    except Exception as e:
        print(f"Error loading GOOGLE_TOKEN_JSON env variable: {e}")
```

### B. Modify `server.py`
1. Read the bypass flag in the approval function:
```python
BYPASS_APPROVAL = os.getenv("BYPASS_APPROVAL", "false").lower() == "true"

def ask_approval(action_name: str, payload: dict) -> bool:
    if BYPASS_APPROVAL:
        print(f"Bypassing approval for {action_name} (BYPASS_APPROVAL is enabled)")
        return True
    # ... rest of the interactive prompt logic ...
```
2. Adjust `uvicorn` startup to bind to the correct environment port:
```python
if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 and PORT on Railway, fallback to 127.0.0.1:8000 locally
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host=host, port=port)
```

---

## 3. Step-by-Step Railway Deployment Guide

### Step 1: Push Project to GitHub
1. Initialize git in your project directory:
   ```bash
   cd "/Users/aarushigrover/Desktop/MCP Server/google-mcp-server"
   git init
   git add .
   git commit -m "Initial commit of Google MCP Server"
   ```
2. Create a private repository on GitHub and push your local repository to it. (Keep it **private** to protect the codebase).

### Step 2: Set Up Railway Project
1. Log in to [Railway.app](https://railway.app/).
2. Click **+ New Project** > **Deploy from GitHub repo**.
3. Select your private repository.

### Step 3: Add Variables
Click on your project service in Railway, go to the **Variables** tab, and add the following keys:

1. **`PORT`**: `8000` (Railway will overwrite or route this automatically).
2. **`HOST`**: `0.0.0.0`
3. **`BYPASS_APPROVAL`**: `true` (Disables the interactive command prompt).
4. **`GOOGLE_CREDENTIALS_JSON`**: Paste the entire content of your local `credentials.json` file.
5. **`GOOGLE_TOKEN_JSON`**: Paste the entire content of your local `token.json` file.

### Step 4: Configure Start Command
If Railway doesn't auto-detect the start command, you can set the custom Start Command in **Settings > Service > Start Command**:
```bash
python server.py
```

### Step 5: Verify Deployment
Railway will generate a public domain for your service (e.g., `https://google-mcp-server-production.up.railway.app`). You can test it from anywhere using:
```bash
curl -X POST https://your-railway-url.up.railway.app/create_email_draft \
     -H "Content-Type: application/json" \
     -d '{
       "to": "recipient@example.com",
       "subject": "Hello from Railway",
       "body": "This draft was generated from our Railway-hosted MCP server!"
     }'
```
Since `BYPASS_APPROVAL` is `true`, the draft will be created immediately without waiting for terminal input!
