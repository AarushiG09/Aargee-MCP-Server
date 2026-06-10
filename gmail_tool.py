import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth import get_credentials

def create_email_draft(to: str, subject: str, body: str):
    """
    Creates a Gmail draft.
    
    Args:
        to (str): The email recipient.
        subject (str): The email subject.
        body (str): The email body.
    """
    try:
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)
        
        # Create a standard MIME email message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        # Encode the MIME message into URL-safe base64
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        draft_body = {
            'message': {
                'raw': raw
            }
        }
        
        # Call the Gmail API user drafts create endpoint
        draft = service.users().drafts().create(userId='me', body=draft_body).execute()
        return draft
    except HttpError as err:
        print(f"Gmail API Error: {err}")
        raise err
    except Exception as e:
        print(f"Unexpected error in gmail_tool: {e}")
        raise e
