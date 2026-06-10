from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth import get_credentials

def append_to_doc(doc_id: str, content: str):
    """
    Appends the specified content to the end of the Google Document.
    
    Args:
        doc_id (str): The Google Document ID.
        content (str): The string content to append.
    """
    try:
        creds = get_credentials()
        service = build('docs', 'v1', credentials=creds)
        
        # Retrieve the document structure to find the current body length / endIndex
        document = service.documents().get(documentId=doc_id).execute()
        
        # A document always ends with a newline character. 
        # To append, we insert text at body.content[-1].endIndex - 1.
        body_content = document.get('body', {}).get('content', [])
        if not body_content:
            insert_index = 1
        else:
            last_element = body_content[-1]
            end_index = last_element.get('endIndex', 1)
            insert_index = max(1, end_index - 1)
            
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': insert_index,
                    },
                    'text': content
                }
            }
        ]
        
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        return result
    except HttpError as err:
        print(f"Docs API Error: {err}")
        raise err
    except Exception as e:
        print(f"Unexpected error in docs_tool: {e}")
        raise e
