from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import jwt
import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = os.getenv("MODEL", "llama3.2:3b")
JWT_SECRET = os.getenv("JWT_SECRET", "ourjwtsecret")

app = FastAPI()


class Message(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    messages: list[Message]


def verify_jwt(auth: str | None):
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth.split(" ", 1)[1]
    try:
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/chat")
def chat(body: ChatBody, authorization: str = Header(None)):
    verify_jwt(authorization)
    system = {
        "role": "system",
        "content": (
            "You are a friendly German tutor. Be natural, encouraging, and concise. "
            "Ask a short follow-up question each turn."
        ),
    }

    payload = {
        "model": MODEL,
        "messages": [system] + [m.model_dump() for m in body.messages],
        "stream": False,
    }

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return {"reply": data["message"]["content"]}
