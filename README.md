# Tinfoil Hardware Measurements (legacy republisher)

This repository is on a deprecation path. The source of truth for platform
measurements and machine endorsements is
[`tinfoilsh/platform-endorsements`](https://github.com/tinfoilsh/platform-endorsements).

For verifiers that predate that repository, each canonical release is
republished here as the legacy artifact:

- `hardware-measurements.json` — the `measurements` section of the canonical
  `platform-endorsements.json`, attested under this repository's signing
  identity (predicate `https://tinfoil.sh/predicate/hardware-measurements/v1`)
- `tinfoil.hash` — its digest

The republish workflow verifies the canonical artifact's Sigstore attestation
before re-signing. Releases here mirror the canonical release tags.

Do not edit measurements in this repository: change
`tinfoilsh/platform-endorsements` and let the republish workflow pick it up
(triggered automatically on canonical releases, or manually via
workflow dispatch with the canonical tag).

This repository will be archived when legacy client support ends. Its name
must never be reused afterwards.
