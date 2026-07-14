import json
import urllib.request

API_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)

    return data["response"]
