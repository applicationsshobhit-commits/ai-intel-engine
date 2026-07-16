import os
import signal
import subprocess
import tempfile
from pathlib import Path

CODEX_BIN = "/Applications/Codex.app/Contents/Resources/codex"
TIMEOUT_SECONDS = 120


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        out_path = Path(f.name)

    proc = subprocess.Popen(
        [
            CODEX_BIN, "exec",
            "--sandbox", "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "-o", str(out_path),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,  # own process group, so we can kill any children it spawns
    )
    try:
        _, stderr = proc.communicate(input=prompt, timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait()
        out_path.unlink(missing_ok=True)
        raise RuntimeError(f"codex exec timed out after {TIMEOUT_SECONDS}s")

    try:
        if proc.returncode != 0:
            raise RuntimeError(f"codex exec failed: {stderr[:500]}")
        return out_path.read_text().strip()
    finally:
        out_path.unlink(missing_ok=True)
