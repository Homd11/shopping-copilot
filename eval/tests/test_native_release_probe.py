"""Cross-platform proof-tool input identity, without Docker or subprocesses."""

import hashlib
import json

from eval.native_release_probe import directory_digest


def test_tool_directory_digest_uses_case_sensitive_relative_path_order(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"lowercase path")
    (tmp_path / "Z.txt").write_bytes(b"uppercase path")
    entries = [
        {
            "path": name,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for name, content in (("Z.txt", b"uppercase path"), ("a.txt", b"lowercase path"))
    ]
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    assert directory_digest(tmp_path) == (hashlib.sha256(canonical).hexdigest(), 2)
