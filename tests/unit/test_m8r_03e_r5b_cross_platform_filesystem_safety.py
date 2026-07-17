import os
import pytest
import tempfile
import shutil
from pathlib import Path
from scripts.m8r_filesystem_safety import (
    classify_artifact_relative_path,
    validate_relative_artifact_path,
    validate_authorized_root,
    safe_destination,
    atomic_write_bytes,
    atomic_write_text,
    FilesystemSafetyError
)

def test_safe_portable_paths():
    safe_cases = [
        "result.json",
        "nested/result.json",
        "a/b/c.json",
        "a\\b\\c.json",
        "a/b\\c.json",
    ]
    for case in safe_cases:
        cls = classify_artifact_relative_path(case)
        assert cls.safe_relative is True
        assert cls.rejection_code is None
        assert len(cls.segments) > 0
        
        # Verify validate doesn't raise error
        segments = validate_relative_artifact_path(case)
        assert len(segments) > 0

def test_unsafe_classes():
    unsafe_cases = [
        # Traversal
        ("../x", "path_traversal_forbidden"),
        ("..\\x", "path_traversal_forbidden"),
        ("a/../../x", "path_traversal_forbidden"),
        ("a\\..\\..\\x", "path_traversal_forbidden"),
        ("a/..\\x", "path_traversal_forbidden"),
        ("a\\../x", "path_traversal_forbidden"),
        # POSIX/rooted
        ("/tmp/x", "rooted_output_path_forbidden"),
        ("/etc/passwd", "rooted_output_path_forbidden"),
        ("/rooted/path", "rooted_output_path_forbidden"),
        ("\\rooted\\path", "rooted_output_path_forbidden"),
        # Windows drive paths
        ("C:\\tmp\\x", "absolute_output_path_forbidden"),
        ("C:/tmp/x", "absolute_output_path_forbidden"),
        ("C:tmp\\x", "drive_relative_output_path_forbidden"),
        ("C:", "drive_relative_output_path_forbidden"),
        ("z:relative", "drive_relative_output_path_forbidden"),
        # UNC & Device namespace
        # UNC & Device namespace
        ("\\\\server\\share\\x", "unc_output_path_forbidden"),
        ("//server/share/x", "unc_output_path_forbidden"),
        ("\\\\?\\C:\\tmp\\x", "device_namespace_path_forbidden"),
        ("\\\\.\\C:\\tmp\\x", "device_namespace_path_forbidden"),
        ("\\\\?\\UNC\\server\\share\\x", "device_namespace_path_forbidden"),
        # URL/Scheme
        ("file:///tmp/x", "absolute_output_path_forbidden"),
        ("http://localhost", "absolute_output_path_forbidden"),
        ("https://google.com", "absolute_output_path_forbidden"),
        ("s3://bucket/key", "absolute_output_path_forbidden"),
        ("gs://bucket/key", "absolute_output_path_forbidden"),
        ("azure://bucket/key", "absolute_output_path_forbidden"),
        # Windows reserved names (per segment)
        ("CON", "reserved_path_segment_forbidden"),
        ("CON.txt", "reserved_path_segment_forbidden"),
        ("con.tar.gz", "reserved_path_segment_forbidden"),
        ("PRN", "reserved_path_segment_forbidden"),
        ("AUX", "reserved_path_segment_forbidden"),
        ("NUL", "reserved_path_segment_forbidden"),
        ("COM1", "reserved_path_segment_forbidden"),
        ("COM9", "reserved_path_segment_forbidden"),
        ("LPT1", "reserved_path_segment_forbidden"),
        ("LPT9", "reserved_path_segment_forbidden"),
        ("nested/CON/file.json", "reserved_path_segment_forbidden"),
        # Alternate Data Streams
        ("name:stream", "alternate_data_stream_forbidden"),
        ("file.txt:secret", "alternate_data_stream_forbidden"),
        # Control characters
        ("file\x00name.json", "control_character_forbidden"),
        ("file\x1fname.json", "control_character_forbidden"),
        ("file\x7fname.json", "control_character_forbidden"),
        # Trailing spaces/dots
        ("trailing.", "reserved_path_segment_forbidden"),
        ("trailing ", "reserved_path_segment_forbidden"),
        ("nested/trailing. /file", "reserved_path_segment_forbidden"),
        # Empty and Dot paths
        ("", "empty_relative_path_forbidden"),
        (".", "empty_relative_path_forbidden"),
        ("./", "empty_relative_path_forbidden"),
        (".\\", "empty_relative_path_forbidden"),
    ]
    for case, expected_code in unsafe_cases:
        cls = classify_artifact_relative_path(case)
        assert cls.safe_relative is False
        assert cls.rejection_code == expected_code
        
        with pytest.raises(FilesystemSafetyError) as excinfo:
            validate_relative_artifact_path(case)
        assert excinfo.value.code == expected_code

def test_prefix_collision(tmp_path):
    root = tmp_path / "output"
    root.mkdir()
    sibling = tmp_path / "output-evil"
    
    # lexical collision test
    # root resolved joinpath candidate must remain within root.
    # relative_path resolving to output-evil
    with pytest.raises(FilesystemSafetyError) as excinfo:
        # candidate is traversal that reaches sibling, but since validate_relative_artifact_path blocks '..',
        # we can't easily traverse via validate_relative_artifact_path.
        # But if somehow it bypasses, or if candidate is "../output-evil", it fails at relative validation.
        validate_relative_artifact_path("../output-evil")
    assert excinfo.value.code == "path_traversal_forbidden"

def test_no_side_effect_lexical_checks(tmp_path):
    root = tmp_path / "sandbox"
    
    unsafe_candidates = [
        "../evil.json",
        "/absolute/path.json",
        "CON",
        "bad:stream",
        "trailing. ",
        "",
        ".",
        "\\root\\escape",
        "C:drive_relative"
    ]
    
    for cand in unsafe_candidates:
        if root.exists():
            shutil.rmtree(root)
            
        with pytest.raises(FilesystemSafetyError):
            safe_destination(root, cand, create_parent=True)
            
        # Root must never be created if validation fails
        assert not root.exists()

def test_parent_symlink_escape(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    
    # Create symlink inside root pointing to outside
    link = root / "link"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not supported on this platform/privilege level")
        
    # target candidate is link/file.json
    # link exists, resolve(link) goes to outside.
    # safe_destination of "link/file.json" must fail because existing parent "link" resolves outside root.
    with pytest.raises(FilesystemSafetyError) as excinfo:
        safe_destination(root, "link/file.json", create_parent=False)
    assert excinfo.value.code == "output_parent_symlink_escape"

def test_destination_symlink(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    
    target_file = outside / "leak.json"
    target_file.write_text("secret")
    
    # Create symlink inside root pointing to outside/leak.json
    link = root / "link.json"
    try:
        os.symlink(target_file, link)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not supported on this platform/privilege level")
        
    # safe_destination on link.json with allow_destination_symlink=False (default) must fail
    with pytest.raises(FilesystemSafetyError) as excinfo:
        safe_destination(root, "link.json", allow_destination_symlink=False)
    assert excinfo.value.code == "output_destination_symlink_forbidden"
    
    # If we allow destination symlink, it must still fail because it resolves outside root
    with pytest.raises(FilesystemSafetyError) as excinfo:
        safe_destination(root, "link.json", allow_destination_symlink=True)
    assert excinfo.value.code == "output_path_outside_authorized_root"

def test_root_symlink(tmp_path):
    real_root = tmp_path / "real_root"
    real_root.mkdir()
    
    sym_root = tmp_path / "sym_root"
    try:
        os.symlink(real_root, sym_root, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not supported on this platform/privilege level")
        
    # validate_authorized_root should resolve sym_root to real_root
    resolved = validate_authorized_root(sym_root)
    assert resolved.resolve() == real_root.resolve()
    
    # safe_destination relative to sym_root should be resolved canonical target
    dest = safe_destination(sym_root, "test.json")
    assert dest.root == real_root.resolve()

def test_atomic_write_operations(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    
    candidate = "sub/output.json"
    content_text = "hello world"
    content_bytes = b"hello bytes"
    
    # 1. Test write text
    p = atomic_write_text(root, candidate, content_text)
    assert p.exists()
    assert p.read_text(encoding="utf-8") == content_text
    
    # 2. Test overwrite forbidden
    with pytest.raises(FilesystemSafetyError) as excinfo:
        atomic_write_text(root, candidate, "new content", allow_overwrite=False)
    assert excinfo.value.code == "atomic_replace_failed"
    
    # 3. Test overwrite allowed
    atomic_write_text(root, candidate, "new content", allow_overwrite=True)
    assert p.read_text(encoding="utf-8") == "new content"
    
    # 4. Test write bytes
    cand_bytes = "sub/bytes.bin"
    p2 = atomic_write_bytes(root, cand_bytes, content_bytes)
    assert p2.exists()
    assert p2.read_bytes() == content_bytes
    
    # 5. Temporary cleanup on successful write
    # The temp file must not exist inside root
    files = list(root.rglob("*.tmp"))
    assert len(files) == 0

def test_atomic_write_cleanup_on_failure(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    
    # Inject a permission error during atomic write by making parent read-only if possible,
    # or we can mock os.replace to raise OSError.
    # Let's mock os.replace to raise OSError to test cleanup.
    import unittest.mock as mock
    
    candidate = "fail.json"
    with mock.patch("os.replace", side_effect=OSError("Mock replacement error")):
        with pytest.raises(FilesystemSafetyError) as excinfo:
            atomic_write_text(root, candidate, "some text")
        assert excinfo.value.code == "atomic_replace_failed"
        
    # Ensure temporary file is cleaned up
    files = list(root.rglob("*.tmp"))
    assert len(files) == 0


def test_uri_like_root_rejection_portable():
    uri_schemes = [
        "s3://bucket/key",
        "gs://bucket",
        "azure://container",
        "file:///tmp",
        "http://localhost",
        "https://google.com",
        "myscheme://path",
    ]
    for uri in uri_schemes:
        with pytest.raises(FilesystemSafetyError) as excinfo:
            validate_authorized_root(uri)
        assert excinfo.value.code == "absolute_output_path_forbidden"


def test_atomic_exclusive_write_failure_cleanup(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    candidate = "exclusive_failure.json"
    dest_path = root / candidate
    
    import unittest.mock as mock
    from scripts.m8r_filesystem_safety import atomic_create_text_exclusive
    
    # 1. Mock write() failure
    class FailWriteFile:
        def __init__(self, fd, *args, **kwargs):
            self.fd = fd
        def write(self, content): raise OSError("Mock write failure")
        def flush(self): pass
        def close(self):
            try: os.close(self.fd)
            except OSError: pass
        
    with mock.patch("os.fdopen", side_effect=lambda fd, *args, **kwargs: FailWriteFile(fd)):
        with pytest.raises(OSError) as excinfo:
            atomic_create_text_exclusive(root, candidate, "content")
        assert "Mock write failure" in str(excinfo.value)
    assert not dest_path.exists()
    
    # Verify subsequent writes succeed
    atomic_create_text_exclusive(root, candidate, "good content")
    assert dest_path.exists()
    assert dest_path.read_text(encoding="utf-8") == "good content"
    dest_path.unlink()
    
    # 2. Mock flush() failure
    class FailFlushFile:
        def __init__(self, fd, *args, **kwargs):
            self.fd = fd
        def write(self, content): pass
        def flush(self): raise OSError("Mock flush failure")
        def close(self):
            try: os.close(self.fd)
            except OSError: pass
        
    with mock.patch("os.fdopen", side_effect=lambda fd, *args, **kwargs: FailFlushFile(fd)):
        with pytest.raises(OSError) as excinfo:
            atomic_create_text_exclusive(root, candidate, "content")
        assert "Mock flush failure" in str(excinfo.value)
    assert not dest_path.exists()
    
    # 3. Mock os.fsync() failure
    with mock.patch("os.fsync", side_effect=OSError("Mock fsync failure")):
        with pytest.raises(OSError) as excinfo:
            atomic_create_text_exclusive(root, candidate, "content")
        assert "Mock fsync failure" in str(excinfo.value)
    assert not dest_path.exists()
