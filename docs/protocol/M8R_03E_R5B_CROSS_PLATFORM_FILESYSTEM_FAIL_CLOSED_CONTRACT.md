# M8R-03E R5B Cross-Platform Filesystem Fail-Closed Contract

## Objective
Establish a single, authoritative, platform-neutral filesystem safety contract that prevents directory traversal, directory escapes, unauthorized writes, and Windows path anomalies, while enforcing a fail-before-side-effect ordering.

---

## Safety Contract & Invariant

### The Core Invariant
Any unsafe relative path input must fail lexically **before** any filesystem side effects are triggered. File operations must fail before:
- Network execution;
- Authorization token or nonce consumption;
- Parent or leaf directory creation;
- Temporary file creation;
- Target file write or replacement;
- State transitions.

---

## Validated Scope (Currently Enforced)

This contract and safety module (`m8r_filesystem_safety.py`) have been fully validated for the following local environment operations:
1. **Local Filesystem Backend**: Normal file reading, directory creation, atomic replacing.
2. **Windows Lexical Path Taxonomy**:
   - Rejects drive-relative paths (e.g., `C:file`, `z:relative`) and drive-absolute paths.
   - Rejects rooted paths starting with leading `/` or `\`.
   - Rejects UNC / Device Namespace paths (e.g., `\\server\share`, `\\?\C:\tmp`).
   - Rejects Alternate Data Streams (e.g., `name:stream`).
   - Rejects reserved names per path segment (e.g., `CON`, `PRN`, `AUX`, `NUL`, `COM1` through `COM9`, `LPT1` through `LPT9`), including variations with extensions (e.g., `CON.txt`).
   - Rejects trailing space or dot per segment.
   - Rejects NUL (`\x00`) and ASCII control characters.
3. **POSIX / Linux / Container Path Policy**:
   - Rejects traversal (`..`) in both forward-slash `/` and backslash `\` notations.
   - Standardizes delimiters (mixed delimiters like `a/b\c` are normalized).
4. **Deepest Existing Parent Verification**:
   - Resolves the authorized root target.
   - Iterates up to locate the deepest existing parent directory.
   - Resolves the existing parent and verifies it is contained within the root using case-safe `os.path.commonpath`.
   - Prevents symlink/junction escapes outside the root directory.
5. **Destination Symlink Protection**:
   - Rejects writes to a target that is a symlink pointing outside the root.
6. **Atomic Replacement (Local)**:
   - Uses `tempfile.mkstemp` inside the destination parent directory.
   - Forces `flush` and `os.fsync` before executing atomic `os.replace`.
   - Deterministically cleans up any temp files upon failure.

---

## Unvalidated Scope (Not Covered by this Task)

The safety contract **does not** validate or eliminate security risks under the following deployment conditions:
1. **NFS Atomic Rename Semantics**: NFS does not guarantee atomic rename on all platforms.
2. **SMB Concurrency Semantics**: Concurrent lock management and metadata synchronization on SMB share volumes are not validated.
3. **Kubernetes PVC Semantics**: Persistent Volume Claims and access modes (ReadWriteMany) are not verified for file operations.
4. **Container Host-Path Trust**: Security of mounting directory hierarchies into docker/container environments.
5. **Object-Store Persistence (S3 / GCS / Azure Blob)**: Key-value operations are not operating-system filesystems and do not respect POSIX permissions or file locking.
6. **Distributed Race Prevention**: No locking coordinator is implemented; concurrency conflicts between multiple hosts are not handled.
7. **Malicious Local Administrator**: Any administrator can access file descriptors or modify directory paths.
8. **Kernel-level TOCTOU Elimination**: Time-of-check to time-of-use races at the OS handle level are not mitigated.

---

## Future Cloud Deployment Policy

Future cloud or distributed microservices deployment must adhere to the following architecture rules:

1. **Local Volume backend**: Use the validated local-filesystem artifact backend inside a single, controlled container/VM volume (e.g., EBS/Local SSD with ReadWriteOnce); OR
2. **Dedicated Cloud Adapter**: Implement a separate object-storage artifact backend with its own key validation, versioning, publication, integrity, and concurrency contract.

> [!IMPORTANT]
> **Do not represent a cloud object storage key (e.g., S3 object key) as an operating-system path.** Do not pass URI schemes directly to local filesystem methods.
