import os
import tempfile
from pathlib import Path
from notebooklm import NotebookLMClient
from notebooklm.auth import AuthTokens

class NotebookLmService:
    @classmethod
    async def query_notebook(cls, notebook_id: str, auth_json: str, query: str) -> str:
        """
        Thread-safe method to query a NotebookLM notebook using custom auth JSON.
        Writes auth_json to a temporary file to prevent environment variable pollution
        across concurrent requests.
        """
        if not notebook_id or not auth_json:
            raise ValueError("Notebook ID and Auth JSON are required.")

        # Create a temporary file to store the credentials safely
        import uuid
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"notebooklm_auth_{os.getpid()}_{uuid.uuid4()}.json")
        
        try:
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(auth_json)
                
            # Initialize AuthTokens from the temporary file
            auth = await AuthTokens.from_storage(path=Path(temp_file_path))
            
            # Query NotebookLM
            async with NotebookLMClient(auth) as client:
                result = await client.chat.ask(notebook_id, query)
                return result.answer
        except Exception as e:
            print(f"Error querying NotebookLM: {e}")
            raise e
        finally:
            # Always clean up the temp file
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass
