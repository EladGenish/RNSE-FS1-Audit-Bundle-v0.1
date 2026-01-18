#!/usr/bin/env python3
"""RNSE v0.1 bundle verifier

- Verifies sha256(trace.f64le) matches manifest
- Verifies manifest canonical sha256 (computed over the manifest with the hash field removed)
- Prints PASS/FAIL plus sha256 digests and FS.1 summary stats

Indexing conventions:
- 0-based indexing
- pre window slice  = [b-w_pre, b)
- post window slice = [b, b+w_post)

Missing-value handling:
- NaNs are ignored for stats and window computations
- FAIL if a required window becomes empty after NaN filtering
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def read_f64le(path: Path, expected_len: int | None = None):
    data = path.read_bytes()
    if len(data) % 8 != 0:
        raise ValueError(f"trace length not multiple of 8 bytes: {len(data)}")
    n = len(data) // 8
    if expected_len is not None and n != expected_len:
        raise ValueError(f"trace length mismatch: expected {expected_len}, got {n}")
    # unpack little-endian float64
    return list(struct.unpack("<" + "d" * n, data))


def nan_filter(xs):
    out = []
    for x in xs:
        if x is None:
            continue
        if isinstance(x, float) and math.isnan(x):
            continue
        out.append(float(x))
    return out


def stats(xs):
    xs = nan_filter(xs)
    if not xs:
        return {"n": 0}
    xs_sorted = sorted(xs)
    n = len(xs)
    mid = n // 2
    median = xs_sorted[mid] if n % 2 == 1 else 0.5 * (xs_sorted[mid - 1] + xs_sorted[mid])
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / n
    return {
        "n": n,
        "min": min(xs),
        "max": max(xs),
        "mean": mean,
        "std": math.sqrt(var),
        "median": median,
    }


def main() -> int:
    here = Path(__file__).resolve().parent
    manifest_path = here / "manifest.json"
    trace_path = here / "trace.f64le"

    ok = True

    manifest_raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 1) Verify canonical manifest hash (excluding the hash field)
    expected_manifest_hash = manifest_raw.get("manifest_canonical_sha256")
    manifest_nohash = dict(manifest_raw)
    manifest_nohash.pop("manifest_canonical_sha256", None)
    computed_manifest_hash = sha256_bytes(canonical_json_bytes(manifest_nohash))

    if expected_manifest_hash != computed_manifest_hash:
        ok = False
        print("FAIL: manifest canonical sha256 mismatch")

    # 2) Verify trace hash
    expected_trace_hash = manifest_raw["trace"]["sha256"]
    computed_trace_hash = sha256_bytes(trace_path.read_bytes())
    if expected_trace_hash != computed_trace_hash:
        ok = False
        print("FAIL: trace sha256 mismatch")

    # 3) FS.1 window stats
    b = int(manifest_raw["fs1"]["boundary_b"])
    w_pre = int(manifest_raw["fs1"]["w_pre"])
    w_post = int(manifest_raw["fs1"]["w_post"])

    xs = read_f64le(trace_path, expected_len=int(manifest_raw["trace"]["length"]))

    # explicit slices (0-based)
    pre_slice = xs[max(0, b - w_pre) : b]
    post_slice = xs[b : min(len(xs), b + w_post)]

    pre_f = nan_filter(pre_slice)
    post_f = nan_filter(post_slice)

    if manifest_raw["missing_values"].get("fail_if_window_empty_after_nan_filter", True):
        if len(pre_f) == 0 or len(post_f) == 0:
            ok = False
            print("FAIL: FS.1 windows empty after NaN filtering")

    full_s = stats(xs)
    pre_s = stats(pre_slice)
    post_s = stats(post_slice)

    delta_mean = None
    delta_median = None
    if pre_s.get("n", 0) and post_s.get("n", 0):
        delta_mean = post_s["mean"] - pre_s["mean"]
        delta_median = post_s["median"] - pre_s["median"]

    # Output
    print("PASS" if ok else "FAIL")
    print(f"sha256(trace)              = {computed_trace_hash}")
    print(f"sha256(canonical manifest) = {computed_manifest_hash}")
    print("FS.1 stats:")
    print(f"  b={b}, w_pre={w_pre}, w_post={w_post}")
    print(f"  full:  {json.dumps(full_s, sort_keys=True)}")
    print(f"  pre:   {json.dumps(pre_s, sort_keys=True)}")
    print(f"  post:  {json.dumps(post_s, sort_keys=True)}")
    print(f"  delta_mean_post_minus_pre   = {delta_mean}")
    print(f"  delta_median_post_minus_pre = {delta_median}")

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
