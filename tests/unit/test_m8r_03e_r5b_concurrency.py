import json
import pytest
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from scripts.m8r_filesystem_safety import atomic_create_text_exclusive, FilesystemSafetyError, validate_authorized_root

def test_exclusive_create_concurrency_race(tmp_path):
    root = tmp_path / "consumption_store"
    root.mkdir()
    
    # We will spin 10 threads all competing to exclusively create/write the same file.
    candidate = "exclusive_receipt.json"
    content_template = '{{"thread_id": {}, "status": "claimed"}}'
    
    success_records = []
    failure_records = []
    
    def worker(thread_idx):
        payload = content_template.format(thread_idx)
        try:
            atomic_create_text_exclusive(root, candidate, payload)
            success_records.append(thread_idx)
        except FilesystemSafetyError as exc:
            if exc.code == 'already_consumed_or_replayed':
                failure_records.append((thread_idx, exc))
            else:
                raise exc
        except Exception as exc:
            raise exc

    thread_count = 12
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        # Submit all tasks concurrently
        futures = [executor.submit(worker, i) for i in range(thread_count)]
        # Gather results
        for f in futures:
            f.result()
            
    # Assertions
    # 1. Exactly 1 thread must succeed
    assert len(success_records) == 1, f"Expected exactly 1 success, got {success_records}"
    
    # 2. Exactly N - 1 threads must fail with O_CREAT/O_EXCL check
    assert len(failure_records) == thread_count - 1, f"Expected {thread_count - 1} failures, got {len(failure_records)}"
    
    # 3. Verify final receipt matches successful thread ID payload
    dest_path = root / candidate
    assert dest_path.exists()
    
    final_data = json.loads(dest_path.read_text(encoding="utf-8"))
    successful_thread = success_records[0]
    assert final_data["thread_id"] == successful_thread
