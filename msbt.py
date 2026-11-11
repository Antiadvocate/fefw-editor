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


def strip_tags(s: str) -> str:
    """UTF-16 message text with its control tags removed, text around them kept.

    A tag is \\x0e, group, type, parameter size in bytes, then the parameters;
    a closing tag is \\x0f, group, type.  Furigana is a tag (group 0, type 0)
    placed in front of the kanji it reads.
    """
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\x0e" and i + 3 < len(s):
            i += 4 + ord(s[i + 3]) // 2
            continue
        if c == "\x0f":
            i += 3
            continue
        out.append(c)
        i += 1
    return "".join(out)


def read(path: str) -> dict[str, str]:
    """{label: text} for one message file, control tags stripped."""
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
    offs = [struct.unpack_from("<I", raw, tbody + 4 + 4 * k)[0] for k in range(count)]
    # A text runs to where the next one starts.  Scanning for 00 00 instead
    # stops inside the first tag (its group/type are often 0), so a name that
    # opens with furigana came back empty and never matched.
    ends = offs[1:] + [struct.unpack_from("<I", raw, txt + 4)[0]]
    texts = []
    for k in range(count):
        at = tbody + offs[k]
        if utf16:
            s = raw[at:tbody + ends[k]].decode("utf-16-le", "replace")
            s = strip_tags(s).split("\x00")[0]
        else:
            end = raw.find(b"\x00", at)
            s = raw[at:end if end >= 0 else len(raw)].decode("utf-8", "replace")
            s = s.split("\x0e")[0]
        texts.append(s.strip())
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
