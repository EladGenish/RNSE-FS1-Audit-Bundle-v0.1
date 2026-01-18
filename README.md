# RNSE-FS1-Audit-Bundle-v0.1
Audit-grade, black-box verification bundle for RNSE boundary legibility under FS.1 (v0.1).

**Architects:**
- **Elad Genish**: RNSE Core Engine
- **Meir Goldman**: Verification Contract Schema, FS.1 Rule

## Package Contents
- `MANIFEST.json`: Signed assertion with integrity hash.
- `trace.bin`: Raw float64 array of the **Divergence (D)** metric.
- `verify.py`: Independent auditor script.

## Technical Specifications
- **Metric**: $D[t]$ (Divergence / Description Length Proxy)
- **Trace Format**: IEEE-754 Float64, Little Endian
- **Boundary Rule**: `BDR_ROBUST_STEP_V0` (FS.1)

## Verification
```bash
python3 verify.py MANIFEST.json trace.bin
```

RNSE Boundary Legibility — v0.1

This repository contains a self-contained verification bundle demonstrating boundary legibility for RNSE under a strict FS.1-style audit contract.

It is intentionally black-box and IP-safe: the bundle exposes only a designated audit observable and a deterministic verification surface. RNSE internals are not included and cannot be inferred from this artifact.

What this repo is

A reproducible verification artifact

A sanity-check bundle for third-party auditing

A PASS / FAIL surface, not an implementation

This repository is designed so that an independent reviewer can verify results without requiring access to RNSE internals.

Contents

This repo contains a single primary artifact:

rnse_v0.1_bundle.txt
A text-only bundle containing:

canonicalized manifest.json

the audit trace embedded as base64 (trace.f64le, Float64 little-endian)

verify.py

SHA-256 hashes for each component and the full bundle

All payloads are textual to avoid ambiguity from binary attachments, hidden extensions, or platform-specific handling.

Verification overview

The verification process checks whether a statistically legible regime boundary exists in the provided audit trace using a fixed FS.1-style windowed analysis.

High-level steps:

Decode the base64 trace to recover the exact Float64 byte sequence

Apply the verification script

Observe a deterministic PASS or FAIL

Indexing, slice semantics, and missing-value handling are defined explicitly in the manifest.

Reproducibility notes

Indexing is 0-based

Window slices use Python semantics:

pre-window: [b - w_pre, b)

post-window: [b, b + w_post)

NaNs are ignored for statistical computation; verification fails if windows cannot be computed

All hashes must match exactly for verification to be valid

IP boundary

This bundle exposes only:

a designated audit observable (D_audit[t])

a verification procedure

metadata required for reproducibility

It does not expose:

RNSE internal state

update rules

acceptance criteria

weight dynamics

reversible mappings to engine internals

The artifact is intentionally insufficient to reconstruct the RNSE engine.

Versioning

v0.1 — initial public audit bundle

Future revisions may adjust windowing parameters or verification strictness without altering the audit philosophy.
