import os
import sys
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from docs_tool import append_to_doc
from gmail_tool import create_email_draft

app = FastAPI(
    title="Google Docs & Gmail MCP Server",
    description="A FastAPI-based MCP-style server to append to Google Docs and create Gmail drafts, with manual console approval.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Google Docs & Gmail MCP Server is running successfully.",
        "documentation": "/docs"
    }

# Pydantic schemas for endpoint validation
class AppendDocRequest(BaseModel):
    doc_id: str
    content: str

class CreateEmailDraftRequest(BaseModel):
    to: str
    subject: str
    body: str

# Configurable approval bypass for headless/production deployments
BYPASS_APPROVAL = os.getenv("BYPASS_APPROVAL", "false").lower() == "true"

def ask_approval(action_name: str, payload: dict) -> bool:
    """
    Displays the action details in the terminal and waits for user confirmation (y/n).
    If BYPASS_APPROVAL environment variable is true, automatically approves without prompting.
    
    Args:
        action_name (str): The name of the endpoint action.
        payload (dict): The payload containing user input parameters.
        
    Returns:
        bool: True if approved or bypassed, False otherwise.
    """
    if BYPASS_APPROVAL:
        print(f"\n[APPROVAL BYPASS] Action '{action_name}' automatically approved.")
        return True

    print(f"\n========================================")
    print(f"ACTION REQUESTED: {action_name}")
    print(f"Payload: {payload}")
    print(f"========================================")
    
    # Prompt user in terminal console
    try:
        response = input("Approve? (y/n): ").strip().lower()
        return response == 'y'
    except EOFError:
        print("Error: Stdin not available. Disallowing action.")
        return False
    except Exception as e:
        print(f"Error reading approval input: {e}")
        return False

@app.post("/append_to_doc", status_code=status.HTTP_200_OK)
def handle_append_to_doc(request: AppendDocRequest):
    payload = {
        "doc_id": request.doc_id,
        "content": request.content
    }
    
    # Check operator approval
    if not ask_approval("append_to_doc", payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action approval denied by server operator."
        )
        
    try:
        result = append_to_doc(request.doc_id, request.content)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to append to document: {str(e)}"
        )

@app.post("/create_email_draft", status_code=status.HTTP_201_CREATED)
def handle_create_email_draft(request: CreateEmailDraftRequest):
    payload = {
        "to": request.to,
        "subject": request.subject,
        "body": request.body
    }
    
    # Check operator approval
    if not ask_approval("create_email_draft", payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action approval denied by server operator."
        )
        
    try:
        result = create_email_draft(request.to, request.subject, request.body)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create email draft: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    # Bind to HOST (default: 127.0.0.1) and PORT (default: 8000) from env variables
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    
    # Note: We do NOT use reload=True or multiple worker processes here when running locally, 
    # as uvicorn's reloading mechanism forks worker processes, which redirects 
    # sys.stdin and causes EOFError when calling python's input() function.
    uvicorn.run("server:app", host=host, port=port)
