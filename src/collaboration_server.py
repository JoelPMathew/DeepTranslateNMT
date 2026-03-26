"""
Real-Time WebSocket Collaboration Server
Enables multi-user translation with live updates and shared translation history.
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    TRANSLATE = "translate"
    TRANSLATE_RESULT = "translate_result"
    ANNOTATION = "annotation"
    FEEDBACK = "feedback"
    HISTORY = "history"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    CURSOR_UPDATE = "cursor_update"
    ERROR = "error"


@dataclass
class User:
    """Represents a connected user"""
    user_id: str
    username: str
    color: str  # For UI identification
    connected_at: datetime = field(default_factory=datetime.now)
    language_pair: str = "ta-en"
    cursor_position: int = 0


@dataclass
class Translation:
    """Represents a translation result"""
    original_id: str
    original_text: str
    translated_text: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    flags: List[str] = field(default_factory=list)


@dataclass
class Annotation:
    """Represents an annotation/comment on a translation"""
    annotation_id: str
    translation_id: str
    user_id: str
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


class CollaborationSession:
    """Manages a collaboration session with multiple users"""

    def __init__(self, session_id: str, name: str = "Untitled Session"):
        self.session_id = session_id
        self.name = name
        self.created_at = datetime.now()
        self.users: Dict[str, User] = {}
        self.translations: List[Translation] = []
        self.annotations: List[Annotation] = []
        self.feedback: List[Dict] = []
        self.active = True

    def add_user(self, user: User) -> bool:
        """Add user to session"""
        if user.user_id in self.users:
            return False
        self.users[user.user_id] = user
        logger.info(f"User {user.username} ({user.user_id}) joined session {self.session_id}")
        return True

    def remove_user(self, user_id: str) -> Optional[User]:
        """Remove user from session"""
        user = self.users.pop(user_id, None)
        if user:
            logger.info(f"User {user.username} ({user_id}) left session {self.session_id}")
        return user

    def add_translation(self, translation: Translation):
        """Add translation to session history"""
        self.translations.append(translation)
        logger.info(f"Translation added: {translation.original_text[:50]}...")

    def get_translations(self, limit: int = 100) -> List[Dict]:
        """Get recent translations"""
        return [asdict(t) for t in self.translations[-limit:]]

    def add_annotation(self, annotation: Annotation):
        """Add annotation to a translation"""
        self.annotations.append(annotation)

    def get_annotations(self, translation_id: str) -> List[Dict]:
        """Get annotations for a translation"""
        return [
            asdict(a) for a in self.annotations
            if a.translation_id == translation_id
        ]

    def add_feedback(self, feedback: Dict):
        """Add user feedback"""
        feedback['timestamp'] = datetime.now().isoformat()
        self.feedback.append(feedback)

    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "active_users": len(self.users),
            "total_translations": len(self.translations),
            "total_annotations": len(self.annotations),
            "users": [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "connected_at": u.connected_at.isoformat()
                }
                for u in self.users.values()
            ]
        }


class CollaborationServer:
    """WebSocket collaboration server"""

    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.connections: Dict[str, Set] = {}  # user_id -> set of websocket connections
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id

    def create_session(self, name: str = "Untitled Session") -> str:
        """Create a new collaboration session"""
        session_id = str(uuid.uuid4())[:8]
        session = CollaborationSession(session_id, name)
        self.sessions[session_id] = session
        logger.info(f"Session created: {session_id} - {name}")
        return session_id

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def join_session(self, session_id: str, user: User) -> bool:
        """Join a user to a session"""
        session = self.get_session(session_id)
        if not session:
            return False

        if session.add_user(user):
            self.user_sessions[user.user_id] = session_id
            if user.user_id not in self.connections:
                self.connections[user.user_id] = set()
            return True
        return False

    def leave_session(self, user_id: str) -> Optional[str]:
        """Remove user from session"""
        session_id = self.user_sessions.pop(user_id, None)
        if session_id and session_id in self.sessions:
            self.sessions[session_id].remove_user(user_id)
            
            # Close empty sessions after 30 minutes
            if not self.sessions[session_id].users:
                self.sessions[session_id].active = False
                logger.info(f"Session {session_id} marked inactive")
        
        return session_id

    def broadcast_to_session(self, session_id: str, message: Dict, exclude_user: Optional[str] = None):
        """Broadcast message to all users in a session"""
        session = self.get_session(session_id)
        if not session:
            return

        for user in session.users.values():
            if exclude_user and user.user_id == exclude_user:
                continue
            
            if user.user_id in self.connections:
                for connection in self.connections[user.user_id]:
                    asyncio.create_task(connection.send_json(message))

    def process_translate_message(self, session_id: str, user_id: str, payload: Dict) -> Dict:
        """Process translation request from user"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        user = session.users.get(user_id)
        if not user:
            return {"error": "User not in session"}

        original_text = payload.get("text", "")
        src_lang, tgt_lang = user.language_pair.split("-")

        # Note: Actual translation happens in the API layer
        return {
            "type": "translate_request",
            "original_id": str(uuid.uuid4()),
            "text": original_text,
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "user_id": user_id,
        }

    def add_translation_result(self, session_id: str, translation: Translation):
        """Record translation result in session"""
        session = self.get_session(session_id)
        if session:
            session.add_translation(translation)

    def add_user_annotation(self, session_id: str, annotation: Annotation):
        """Add annotation from user"""
        session = self.get_session(session_id)
        if session:
            session.add_annotation(annotation)

    def get_session_history(self, session_id: str) -> Dict:
        """Get complete session history"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "name": session.name,
            "created_at": session.created_at.isoformat(),
            "translations": session.get_translations(),
            "annotations": session.annotations,
            "feedback": session.feedback,
            "stats": session.get_session_stats(),
        }

    def list_active_sessions(self) -> List[Dict]:
        """List all active sessions"""
        return [
            session.get_session_stats()
            for session in self.sessions.values()
            if session.active
        ]

    def list_user_sessions(self, username: str) -> List[str]:
        """List all sessions a user participated in"""
        # This would need additional tracking
        return []


# Singleton instance
_server_instance = None


def get_collaboration_server() -> CollaborationServer:
    """Get or create the collaboration server"""
    global _server_instance
    if _server_instance is None:
        _server_instance = CollaborationServer()
    return _server_instance


if __name__ == "__main__":
    # Example usage
    server = get_collaboration_server()
    
    # Create a session
    session_id = server.create_session("Project Translation")
    print(f"Created session: {session_id}")
    
    # Add users
    user1 = User("user1", "Alice", "#FF6B6B", language_pair="ta-en")
    user2 = User("user2", "Bob", "#4ECDC4", language_pair="te-en")
    
    server.join_session(session_id, user1)
    server.join_session(session_id, user2)
    
    # Add a translation
    translation = Translation(
        original_id="trans1",
        original_text="வணக்கம்",
        translated_text="Hello",
        user_id="user1"
    )
    server.add_translation_result(session_id, translation)
    
    # Get session stats
    stats = server.get_session_history(session_id)
    print(json.dumps(stats, indent=2, default=str))
