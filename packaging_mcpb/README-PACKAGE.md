# Windows MCPB packaging authority

The first-party packer reuses `packaging_native/resource-policy.json` app members
and the exact accepted Windows wheels. It installs using offline hashed pip into
`server/lib`; script launchers and bytecode are excluded. The MCPB entry point
uses Python 3.13 and the existing exact six stdio tools. No new executor exists.

Use `python -B -m scripts.build_mcpb_distribution --wheelhouse <accepted-copy>
--output <fresh-external-directory>`. No automatic acquisition occurs.
Archives use lexical paths, ZIP_DEFLATED level 9, 1980-01-01 timestamps and
regular 0644 Unix attributes. The sidecar contains lowercase SHA-256, two spaces,
the canonical filename and one terminal newline.

R1 builds are TEST artifacts. R2 rebuilds from the actual merged R1 source.
Registry metadata and current v1.0.0 documentation remain unchanged until A7.
Integrity is SHA-256 plus release provenance; signing authority is not established.

The vendored official v0.3 schema and license are from `anthropics/mcpb` commit
`70fe3b34cd6dff1b3bba046638edc72a6467a4fb`; see upstream/provenance.json.
