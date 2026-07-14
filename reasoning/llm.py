import subprocess
import tempfile
from pathlib import Path

CODEX_BIN = "/Applications/Codex.app/Contents/Resources/codex"


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        out_path = Path(f.name)

    try:
        result = subprocess.run(
            [
                CODEX_BIN, "exec",
                "--sandbox", "read-only",
                "--skip-git-repo-check",
                "--ephemeral",
                "-o", str(out_path),
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"codex exec failed: {result.stderr[:500]}")
        return out_path.read_text().strip()
    finally:
        out_path.unlink(missing_ok=True)
