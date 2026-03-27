#!/usr/bin/env python3
"""
Pack / unpack K7 cartridge PNGs (PICO-8–style: visible label + tEXt chunk k7cart).

Payload matches the web editor URL share format:
  z + base64url(raw_deflate(utf8(json)))
  j + base64url(utf8(json))   if smaller uncompressed

The editor inserts the same payload into PNG keyword "k7cart" (tEXt).

Requires Python 3.9+ (stdlib only).
"""

from __future__ import annotations

import argparse
import base64
import json
import struct
import sys
import zlib
from pathlib import Path


def _crc32_png(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def _read_u32_be(b: bytes, off: int) -> int:
    return struct.unpack(">I", b[off : off + 4])[0]


def _chunks(png: bytes):
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    i = 8
    while i < len(png):
        length = _read_u32_be(png, i)
        ctype = png[i + 4 : i + 8]
        data = png[i + 8 : i + 8 + length]
        crc = _read_u32_be(png, i + 8 + length)
        yield ctype, data, i, length, crc
        i += 12 + length


def extract_k7cart_payload(png: bytes) -> str | None:
    for ctype, data, _i, _l, _c in _chunks(png):
        if ctype != b"tEXt":
            continue
        z = data.find(b"\x00")
        if z <= 0:
            continue
        kw = data[:z].decode("latin1", errors="replace")
        if kw == "k7cart":
            return data[z + 1 :].decode("utf-8")
    return None


def insert_text_chunk_before_iend(png: bytes, keyword: str, text: str) -> bytes:
    if len(keyword) < 1 or len(keyword) > 79:
        raise ValueError("tEXt keyword length must be 1..79")
    kw = keyword.encode("latin1")
    val = text.encode("utf-8")
    chunk_data = kw + b"\x00" + val
    ctype = b"tEXt"
    crc = _crc32_png(ctype + chunk_data)
    new_chunk = struct.pack(">I", len(chunk_data)) + ctype + chunk_data + struct.pack(">I", crc)
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    i = 8
    while i < len(png):
        length = _read_u32_be(png, i)
        ctype_b = png[i + 4 : i + 8]
        total = 12 + length
        if ctype_b == b"IEND":
            return png[:i] + new_chunk + png[i:]
        i += total
    raise ValueError("IEND not found")


def _b64url_encode(raw: bytes) -> str:
    s = base64.urlsafe_b64encode(raw).decode("ascii")
    return s.rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def encode_payload(obj: dict) -> str:
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    cobj = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    z = cobj.compress(raw) + cobj.flush()
    if len(z) < len(raw):
        return "z" + _b64url_encode(z)
    return "j" + _b64url_encode(raw)


def decode_payload(s: str) -> dict:
    s = s.strip()
    if not s:
        raise ValueError("empty payload")
    if s[0] == "z":
        raw = _b64url_decode(s[1:])
        dobj = zlib.decompressobj(-15)
        out = dobj.decompress(raw) + dobj.flush()
        return json.loads(out.decode("utf-8"))
    if s[0] == "j":
        out = _b64url_decode(s[1:])
        return json.loads(out.decode("utf-8"))
    # legacy URL base64
    out = base64.b64decode(s)
    return json.loads(out.decode("utf-8"))


def cmd_pack(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    if not state_path.is_file():
        print("state JSON not found:", state_path, file=sys.stderr)
        return 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    payload = encode_payload(state)
    label = Path(args.base).read_bytes() if args.base else None
    if label is None:
        label = _minimal_rgba_png(256, 256, (40, 40, 48, 255))
    out = insert_text_chunk_before_iend(label, "k7cart", payload)
    outp = Path(args.output)
    outp.write_bytes(out)
    print("wrote", outp, "(%d bytes)" % len(out))
    return 0


def cmd_unpack(args: argparse.Namespace) -> int:
    png = Path(args.png).read_bytes()
    payload = extract_k7cart_payload(png)
    if not payload:
        print("no k7cart chunk", file=sys.stderr)
        return 1
    state = decode_payload(payload)
    if args.json:
        Path(args.json).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote", args.json)
    if args.code is not None:
        code = state.get("code", "")
        Path(args.code).write_text(code if isinstance(code, str) else "", encoding="utf-8")
        print("wrote", args.code)
    if not args.json and args.code is None:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


def _minimal_rgba_png(w: int, h: int, rgba: tuple[int, int, int, int]) -> bytes:
    r, g, b, a = rgba
    row = bytes([0, r, g, b, a] * w)
    raw = row * h
    zobj = zlib.compressobj(9, zlib.DEFLATED, 15)
    z = zobj.compress(raw) + zobj.flush()

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", _crc32_png(t + d))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", z) + chunk(b"IEND", b"")


def main() -> int:
    ap = argparse.ArgumentParser(description="K7 cart PNG pack/unpack (tEXt k7cart)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pack = sub.add_parser("pack", help="Embed state JSON into a PNG (optional base label image)")
    p_pack.add_argument("--state", required=True, help="Game state JSON (same keys as editor share)")
    p_pack.add_argument("--base", help="Existing PNG to embed into (default: blank 256×256 label)")
    p_pack.add_argument("-o", "--output", required=True, help="Output .png path")
    p_pack.set_defaults(func=cmd_pack)

    p_un = sub.add_parser("unpack", help="Extract k7cart from PNG")
    p_un.add_argument("png", help="Input .png")
    p_un.add_argument("--json", help="Write full state JSON to this path")
    p_un.add_argument("--code", help="Write Python code field to this path")
    p_un.set_defaults(func=cmd_unpack)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
