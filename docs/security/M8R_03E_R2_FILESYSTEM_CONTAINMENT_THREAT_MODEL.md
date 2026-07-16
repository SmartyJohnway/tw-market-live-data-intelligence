# M8R-03E-R2 filesystem containment threat model

Baseline SHA: `1c2144498b524e52b2bf21fce8ed00683d9eb3a7`.

## Threats covered

The centralized primitive rejects lexical `..` traversal, absolute POSIX paths, Windows drive and drive-relative paths, UNC paths, mixed separators, prefix-collision escapes, parent symlink escapes, destination symlinks, nonexistent leaves below escaping symlink parents, and unsafe temporary-file placement.

## Platform notes

Root symlinks are resolved to the authorized root. Windows drive/UNC parsing is rejected portably; junction/reparse-point detection remains best-effort through `Path.resolve()` and requires Windows smoke follow-up for OS-specific structures. Case-insensitive behavior relies on resolved platform path semantics.

## Write semantics

Temporary files are created in the validated destination parent inside the authorized root and committed with `os.replace`. Failed containment occurs before writing. Cleanup is bounded to the authorized root.

## Limitations

The implementation is best-effort and portable. It does not claim complete race-proof sandboxing against a local adversary that can mutate directories between validation and replacement. True race-free `openat`/dirfd semantics are not implemented cross-platform.
