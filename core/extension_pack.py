"""Pack the Chrome/Edge floating-orb extension into a downloadable zip."""

from __future__ import annotations

import io
import zipfile
from functools import lru_cache
from pathlib import Path

EXTENSION_DIR = Path(__file__).resolve().parent.parent / "extension"

# Skip junk / secrets if any linger in the folder
_SKIP_NAMES = {
    ".DS_Store",
    "signing_private_key.pem",
    "manifest_key.txt",
    "extension_id.txt",
}


@lru_cache(maxsize=1)
def extension_zip_bytes() -> bytes:
    """Build once per process — zip work on every rerun was stalling Cloud CPU."""
    if not EXTENSION_DIR.is_dir():
        raise FileNotFoundError(f"Missing extension dir: {EXTENSION_DIR}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(EXTENSION_DIR.rglob("*")):
            if not path.is_file():
                continue
            if path.name in _SKIP_NAMES or path.name.startswith("."):
                continue
            arc = Path("bubu-fab-extension") / path.relative_to(EXTENSION_DIR)
            zf.write(path, arcname=str(arc).replace("\\", "/"))
    return buf.getvalue()
