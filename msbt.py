"""msbt.py - read the game's message files (Msg/<lang>/*.msbt.zst).

An MSBT file has a label table (LBL1) and a text table (TXT2).  Each label is
stored as [u8 length][name][u32 index]; the index says which text in TXT2 it
names.  Labels are kept in hash-bucket order, not text order, so the index has
to be read rather than assumed from position.
"""
from __future__ import annotations

import struct


def _raw(path: str) -> bytes:
    data = open(path, "rb").read()
    if path.endswith(".zst"):
        import zstandard
        data = zstandard.ZstdDecompressor().decompressobj().decompress(data)
    return data


def read(path: str) -> dict[str, str]:
    """{label: text} for one message file.  Control codes (\\x0e…) are cut off."""
    raw = _raw(path)
    utf16 = raw[0x0C:0x0E] == b"\xff\xfe"
    lbl = raw.find(b"LBL1")
    txt = raw.find(b"TXT2")
    if lbl < 0 or txt < 0:
        return {}
    body = lbl + 16
    labels: dict[str, int] = {}
    for k in range(struct.unpack_from("<I", raw, body)[0]):
        cnt, off = struct.unpack_from("<II", raw, body + 4 + 8 * k)
        at = body + off
        for _ in range(cnt):
            ln = raw[at]
            name = raw[at + 1:at + 1 + ln].decode("ascii", "replace")
            labels[name] = struct.unpack_from("<I", raw, at + 1 + ln)[0]
            at += 1 + ln + 4
    tbody = txt + 16
    count = struct.unpack_from("<I", raw, tbody)[0]
    texts = []
    for k in range(count):
        at = tbody + struct.unpack_from("<I", raw, tbody + 4 + 4 * k)[0]
        if utf16:
            end = at
            while end + 1 < len(raw) and raw[end:end + 2] != b"\x00\x00":
                end += 2
            s = raw[at:end].decode("utf-16-le", "replace")
        else:
            end = raw.find(b"\x00", at)
            s = raw[at:end if end >= 0 else len(raw)].decode("utf-8", "replace")
        texts.append(s.split("\x0e")[0].strip())
    return {name: texts[i] for name, i in labels.items() if 0 <= i < len(texts)}


def jp_to_en(jp_path: str, en_path: str, skip=("_H_",)) -> dict[str, str]:
    """Japanese text -> English text, matched by label (help texts skipped)."""
    jp, en = read(jp_path), read(en_path)
    out: dict[str, str] = {}
    for label, jtext in jp.items():
        if any(s in label for s in skip):
            continue
        etext = en.get(label, "")
        if jtext and etext:
            out.setdefault(jtext, etext)
    return out


def english_dir(msg_dir: str) -> str:
    """The English message folder: EUen in some dumps, USen in others."""
    import os
    for name in ("EUen", "USen"):
        if os.path.isdir(os.path.join(msg_dir, name)):
            return os.path.join(msg_dir, name)
    return os.path.join(msg_dir, "EUen")
