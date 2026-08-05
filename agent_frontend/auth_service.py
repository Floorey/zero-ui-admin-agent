import os
import uuid
import secrets
from typing import Dict, Optional, Any
from pydantic import BaseModel

class UserSession(BaseModel):
    user_id: str
    provider: str
    email: Optional[str] = None
    name: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: float

class OAuthConfig(BaseModel):
    provider: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    scope: str
    redirect_uri: str

class AuthService:
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.pending_states: Dict[str, str] = {}
        
        self.configs: Dict[str, OAuthConfig] = {
            "google": OAuthConfig(
                provider="google",
                client_id=os.getenv("GOOGLE_CLIENT_ID", "mock-google-client-id"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "mock-google-client-secret"),
                authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scope="openid email profile",
                redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/callback/google")
            ),
            "figma": OAuthConfig(
                provider="figma",
                client_id=os.getenv("FIGMA_CLIENT_ID", "mock-figma-client-id"),
                client_secret=os.getenv("FIGMA_CLIENT_SECRET", "mock-figma-client-secret"),
                authorize_url="https://www.figma.com/oauth",
                token_url="https://www.figma.com/api/oauth/token",
                scope="files:read",
                redirect_uri=os.getenv("FIGMA_REDIRECT_URI", "http://localhost:8000/api/auth/callback/figma")
            ),
            "canva": OAuthConfig(
                provider="canva",
                client_id=os.getenv("CANVA_CLIENT_ID", "mock-canva-client-id"),
                client_secret=os.getenv("CANVA_CLIENT_SECRET", "mock-canva-client-secret"),
                authorize_url="https://www.canva.com/api/oauth/authorize",
                token_url="https://api.canva.com/rest/v1/oauth/token",
                scope="asset:read design:meta:read",
                redirect_uri=os.getenv("CANVA_REDIRECT_URI", "http://localhost:8000/api/auth/callback/canva")
            )
        }

    def generate_auth_url(self, provider: str) -> Dict[str, str]:
        if provider not in self.configs:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        cfg = self.configs[provider]
        state = secrets.token_urlsafe(16)
        self.pending_states[state] = provider
        
        auth_url = (
            f"{cfg.authorize_url}?"
            f"client_id={cfg.client_id}&"
            f"redirect_uri={cfg.redirect_uri}&"
            f"response_type=code&"
            f"scope={cfg.scope}&"
            f"state={state}"
        )
        return {"provider": provider, "state": state, "auth_url": auth_url}

    def process_callback(self, provider: str, code: str, state: str) -> UserSession:
        if state not in self.pending_states or self.pending_states[state] != provider:
            raise ValueError("Invalid state parameter or CSRF mismatch")
        
        del self.pending_states[state]
        
        session_id = str(uuid.uuid4())
        session = UserSession(
            user_id=f"usr_{session_id[:8]}",
            provider=provider,
            email=f"user_{session_id[:4]}@{provider}-domain.org",
            name=f"Kubernetes Admin ({provider.capitalize()})",
            access_token=f"tok_{secrets.token_hex(24)}",
            expires_at=3600 * 24
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[UserSession]:
        return self.sessions.get(session_id)
