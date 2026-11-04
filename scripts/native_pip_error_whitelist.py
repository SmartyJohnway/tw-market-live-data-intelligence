"""Closed-vocabulary classification of pip ERROR lines; never echo input text."""
from __future__ import annotations
import re

# Most specific conditions first. Return category labels only.
RULES = (
    ("PATH_TOO_LONG", r"winerror\s*206|errno\s*36|filename or extension is too long|file name too long|path too long"),
    ("FILE_IN_USE", r"winerror\s*32|sharing violation|being used by another process|file is in use"),
    ("ACCESS_DENIED", r"winerror\s*5|errno\s*13|access is denied|permission denied"),
    ("MISSING_PATH", r"winerror\s*[23]\b|errno\s*2\b|no such file or directory|cannot find the (?:file|path) specified"),
    ("SCRIPT_LAUNCHER", r"fatal error in launcher|unable to create process|script launcher|failed to create process"),
    ("UNICODE_CODEC", r"unicode(?:encode|decode)error|charmap.*can't encode|codec can't (?:encode|decode)"),
    ("HASH_MISMATCH", r"packages do not match the hashes|hashes do not match|hash mismatch"),
    ("WHEEL_MISSING", r"no matching distribution found|could not find a version that satisfies"),
    ("INSTALL_RECORD", r"record file|dist-info|installation record|entry.point"),
    ("RESOLUTION", r"resolutionimpossible|conflicting dependencies|requires a different python"),
    ("NETWORK", r"network is unreachable|certificate verify failed|connection (?:refused|timed out)"),
    ("PIP_INTERNAL", r"pip\._internal|pip\._vendor|exception within pip|pip encountered an error"),
)
MAX_LINES = 32
def classify(stderr: str) -> dict:
    if not isinstance(stderr, str):
        return {"count": 0, "categories": [], "winerror_codes": [], "unclassified": 0}
    # Match only actual emitted ERROR: lines; avoid traceback commands/fixtures.
    error_lines = re.findall(r"(?m)^\s*ERROR:\s*([^\r\n]*)", stderr[-131072:])
    categories = []
    unclassified = 0
    for line in error_lines[:MAX_LINES]:
        match = next((key for key, pattern in RULES if re.search(pattern, line, re.I)), None)
        if match is None:
            unclassified += 1
        elif match not in categories:
            categories.append(match)
    observed = set(re.findall(r"\[WinError\s*(\d{1,3})\]", stderr, re.I))
    allowed = {"2", "3", "5", "32", "80", "123", "183", "206", "267"}
    return {"count": min(len(error_lines), MAX_LINES),
            "categories": sorted(categories),
            "winerror_codes": sorted(observed & allowed, key=int),
            "unclassified": min(unclassified, MAX_LINES)}
def classify_stderr_context(stderr: str) -> dict:
    """Safe secondary flags for multi-line pip installation failure context."""
    if not isinstance(stderr, str):
        stderr = ""
    body = stderr[-131072:].lower()
    flags = {
        "oserror_seen": bool(re.search(r"(?:oserror|winerror|errno)", body)),
        "script_generation_seen": bool(re.search(r"(?:generating script|creating script|launchers?|entry.points?)", body)),
        "install_completed_seen": "successfully installed" in body,
        "install_started_seen": "installing collected packages" in body,
        "install_error_seen": bool(re.search(r"(?m)^\s*error:", body)),
        "pip_internal_traceback_seen": bool(re.search(r"(?:pip[./\\]_internal|pip[./\\]_vendor)", body)),
        "encoding_error_seen": bool(re.search(r"unicode(?:encode|decode)error|charmap|codec", body)),
    }
    return flags
