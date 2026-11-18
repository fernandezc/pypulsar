"""Verify the preserved source tree without executing historical code."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile


def verify(root):
    manifest = json.loads((root / "provenance/sourceforge-r385.json").read_text())
    archive = root / "provenance" / manifest["archive"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["archive_sha256"]:
        raise ValueError("Original archive checksum mismatch")
    entries = {entry["path"]: entry for entry in manifest["files"]}
    if len(entries) != manifest["source_file_count"]:
        raise ValueError("Manifest file count mismatch")
    found = set()
    with zipfile.ZipFile(archive) as source:
        for item in source.infolist():
            if item.is_dir():
                continue
            path = PurePosixPath(item.filename)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "pypulsar-code-r385-trunk":
                raise ValueError("Unexpected archive path")
            relative = PurePosixPath(*path.parts[1:]).as_posix()
            if relative in found:
                raise ValueError("Duplicate archive path")
            entry = entries[relative]
            data = source.read(item)
            if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError("Manifest mismatch: " + relative)
            if (root / relative).read_bytes() != data:
                raise ValueError("Working tree source mismatch: " + relative)
            found.add(relative)
    if found != entries.keys():
        raise ValueError("Archive and manifest paths differ")
    print(f"Verified {len(found)} original files and archive SHA-256.")


if __name__ == "__main__":
    try:
        verify(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
