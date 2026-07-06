import os
from typing import Optional
import json
import uuid
from datetime import datetime
SESSION_FOLDER = "sessions"

class SessionRepository:
    def __init__(self):
        self.session_folder = SESSION_FOLDER 
        os.makedirs(SESSION_FOLDER, exist_ok=True)
        self.metadata_path = os.path.join(
            SESSION_FOLDER, 
            "metadata.json",
        )

        if not os.path.exists(self.metadata_path):
            with open(self.metadata_path, "w") as f:
                json.dump([], f)

    def create_session(self, document_name: Optional[str]):
        session_id = str(uuid.uuid4())
        metadata = self.get_all_sessions()

        session = {
            "id": session_id, 
            "document_name": document_name, 
            "created_at": datetime.now().isoformat(), 
            "updated_at": datetime.now().isoformat(),
        }

        metadata.append(session)

        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f, indent=2) 

        session_file = {
            "id": session_id, 
            "document_name": document_name, 
            "messages": [],
        }

        with open(
            os.path.join(self.session_folder, f"{session_id}.json"),
            "w", 
        ) as f:
            json.dump(session_file, f, indent=2)

        return session

    def get_latest_session(self, document_name):
        sessions = self.get_all_sessions()
        for session in reversed(sessions):
            if session.get("document_name") == document_name:
                return session
        return None

    def add_message(self, session_id, role, content):
        path = os.path.join(self.session_folder, f"{session_id}.json")
        if not os.path.exists(path):
            return 
        with open(path, "r") as f:
            session = json.load(f)
        session["messages"].append({
            "role": role, 
            "content": content,
        })
        with open(path, "w") as f:
            json.dump(
                session, 
                f,
                indent=2,
            )
    
    def get_messages(self, session_id):
        path = os.path.join(
            self.session_folder, 
            f"{session_id}.json",
        )

        if not os.path.exists(path):
            return []

        with open(path, "r") as f:
            session = json.load(f)
        
        return session.get(
            "messages", 
            [],
        )

    def get_all_sessions(self):
        with open(self.metadata_path, "r") as f:
            return json.load(f)