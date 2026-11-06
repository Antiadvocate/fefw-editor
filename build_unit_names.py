"""build_unit_names.py - English names for unit_ids.json entries still in Japanese.

Story characters already have their English names.  What is left are the
game's internal unit templates: generic soldiers (PID_SCXX_02_アーチャー),
enemy variants (DN_アトラスベア_力強化), animals, props and test units.  Their
ids are built from words the game's text does name (classes, people, places),
so each part is translated through the message files (Person and Job first)
and the modifiers through a small glossary:

    PID_SCXX_02_アーチャー        -> Archer
    DN_アトラスベア_力強化_冥界    -> Atlas Bear (Str+, Underworld)

The main word has to be found in the game's text; parts that can't be read
(the ids are cut off at a fixed length, sometimes mid-character) are left out.
Entries whose main word isn't found keep their Japanese name.

    python build_unit_names.py <path to your dumped romfs folder>
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import msbt                                   # noqa: E402

ROM = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FEFW_ROM", "")
CJK = re.compile(r"[぀-ヿ㐀-鿿]")

# modifiers used in the template ids (not words the game shows anywhere)
GLOSSARY = {
    "男": "male", "女": "female", "標準": "", "汎用": "", "冥界": "Underworld",
    "冥": "Underworld", "強": "strong", "弱": "weak", "中": "medium",
    "最強": "strongest", "ボス": "boss", "右": "right", "左": "left",
    "攻撃": "attack", "防御": "defense", "魔法": "magic", "物理": "physical",
    "力強化": "Str+", "技強化": "Dex+", "速さ強化": "Spd+", "守備強化": "Def+",
    "魔力強化": "Mag+", "魔防強化": "Res+", "幸運強化": "Lck+", "HP強化": "HP+",
    "守備劣化": "Def-", "速さ劣化": "Spd-", "魔防劣化": "Res-", "力劣化": "Str-",
    "必殺無効": "crit-immune", "回避": "evasive", "計略": "schemer",
    "アサシン": "assassin", "アサシン型": "assassin", "外套": "cloaked",
    "外套あり": "cloaked", "霊体": "spirit", "護衛": "escort",
    "0部": "Prologue", "1部": "Part 1", "2部": "Part 2", "3部": "Part 3",
    "第1部": "Part 1", "第2部": "Part 2", "第3部": "Part 3",
    "腰の武器なし": "no sheathed weapon", "OP": "opening",
    "大型": "large", "小型": "small", "召喚": "summoned",
    "受付": "clerk", "市場受付": "market clerk", "武器屋受付": "weapon shop clerk",
    "道具屋受付": "item shop clerk", "訓練所受付": "training ground clerk",
    "モブ男性": "Man", "モブ女性": "Woman", "モブ少年": "Boy", "モブ少女": "Girl",
}
PREFIX = re.compile(r"^(PID_)?([A-Z]{2}_(\d+_)?|SC[0-9X]+_[0-9X]+_?|BD\d+_\d+_)?")
# leading weapon / element words in generic soldier names (斧盗賊 = axe Thief)
WEAPON = {"手斧": "Hand Axe", "手槍": "Javelin", "素手": "Unarmed", "籠手": "Gauntlet",
          "剣": "Sword", "槍": "Lance", "斧": "Axe", "弓": "Bow", "炎": "Fire",
          "氷": "Ice", "雷": "Thunder", "風": "Wind", "強": "Strong",
          "毒": "Poison", "スケルトン": "Skeleton"}
# trailing words: 替 / 代理 mark a stand-in for a named character
SUFFIX = {"替": "stand-in", "代理": "stand-in", "小": "small", "大": "large",
          "弱": "weak", "金": "gold", "銀": "silver"}


def texts(rom: str) -> dict[str, str]:
    """Japanese -> English from the message files; Person and Job win."""
    jp_dir = os.path.join(rom, "Msg", "JPja")
    en_dir = msbt.english_dir(os.path.join(rom, "Msg"))
    first = ("person", "job")
    files = sorted(glob.glob(os.path.join(jp_dir, "*.msbt*")),
                   key=lambda p: next((i for i, f in enumerate(first)
                                       if os.path.basename(p).lower().startswith(f)),
                                      len(first)))
    out: dict[str, str] = {}
    for jp_path in files:
        en_path = os.path.join(en_dir, os.path.basename(jp_path))
        if not os.path.isfile(en_path) or not os.path.getsize(jp_path):
            continue
        try:
            pairs = msbt.jp_to_en(jp_path, en_path)
        except Exception as exc:              # noqa: BLE001
            print("  skipped %s: %s" % (os.path.basename(jp_path), exc))
            continue
        for jp, en in pairs.items():
            if len(jp) <= 16 and "\n" not in en and len(en) <= 40:
                out.setdefault(jp, en)
    return out


def lookup(tok: str, names: dict[str, str]):
    """English for one word of an id, with the tags it carried, or None."""
    if tok in names:
        return names[tok], []
    if tok in GLOSSARY and GLOSSARY[tok] and tok not in ("男", "女"):
        return GLOSSARY[tok], []
    m = re.match(r"^モブ(\d*)$", tok)
    if m:
        return "Extra" + (" " + m.group(1) if m.group(1) else ""), []
    m = re.match(r"^(.+?)(\[(.+)\]|[A-Z]|\d+)$", tok)
    if m:
        got = lookup(m.group(1), names)
        if got:
            tag = m.group(3) or m.group(2)
            tag = GLOSSARY.get(tag, tag if not CJK.search(tag) else "")
            return got[0], got[1] + ([tag] if tag else [])
    for suf, tag in SUFFIX.items():
        if tok.endswith(suf) and len(tok) > len(suf):
            got = lookup(tok[:-len(suf)], names)
            if got:
                return got[0], got[1] + [tag]
    if tok.startswith("女") and len(tok) > 1:
        got = lookup(tok[1:], names)
        if got:
            return got[0], got[1] + ["female"]
    for pre, word in WEAPON.items():
        if tok.startswith(pre) and len(tok) > len(pre):
            got = lookup(tok[len(pre):], names)
            if got:
                return "%s %s" % (word, got[0]), got[1]
    for i in range(2, len(tok) - 1):           # クラプカ近衛兵 = Klapka + Royal Guard
        if tok[:i] in names:
            got = lookup(tok[i:], names)
            if got:
                return "%s %s" % (names[tok[:i]], got[0]), got[1]
    return None


def split_tag(tok: str, names: dict[str, str]):
    got = lookup(tok, names)
    return (got[0], ", ".join(got[1])) if got else (None, None)


# leading words that say which group a unit belongs to, not what it is
GROUPS = {"刃鳴り": "Answerer's Cry", "モブ": "extra", "第1部": "Part 1",
          "第2部": "Part 2", "第3部": "Part 3", "0部": "Prologue", "1部": "Part 1",
          "2部": "Part 2", "3部": "Part 3"}
GLOSSARY.update({
    "村の男性": "Villager (male)", "村の女性": "Villager (female)",
    "街の男性": "Townsman", "街の女性": "Townswoman",
    "裕福な男性": "Wealthy Man", "裕福な女性": "Wealthy Woman",
    "男性神官": "Priest (male)", "女性神官": "Priestess",
    "試練兵": "Trial Soldier", "近衛兵": "Royal Guard", "ツワモノ": "Veteran",
    "無職": "No Class", "歩行兵士": "Foot Soldier", "興行師": "Showman",
    "歩兵": "Infantry", "騎馬": "Cavalry", "駝鳥": "Ornius Rider",
    "サンドヴィーグル": "Sand Vigr",           # not in the game text; transliterated
    "ノブタ": "Wild Boar", "ドラゴンナイト": "Dragon Knight", "巨鳥ルフ": "Giant Roc",
})


def english(name: str, names: dict[str, str]) -> str:
    s = PREFIX.sub("", name).replace("\ufffd", "")
    test = s.startswith("テスト")
    if test:
        s = re.sub(r"^テスト(DN_|クイックバトル_)?", "", s)
    s = re.sub(r"^(動物|拠点|兵種)_", "", s)     # animal / hub NPC / class model
    parts = [p for p in s.split("_") if p]
    lead = ["test"] if test else []
    while len(parts) > 1 and parts[0] in GROUPS:
        lead.append(GROUPS[parts.pop(0)])
    if parts and parts[0].startswith("冥界") and len(parts[0]) > 2:
        parts[0] = parts[0][2:]               # 冥界タテジマオオカミ
        lead.append("Underworld")
    for n in range(len(parts), 0, -1):
        main, tag = split_tag("_".join(parts[:n]), names)
        if not main:
            continue
        tags = [tag] if tag else []
        for p in parts[n:]:
            t = GLOSSARY.get(p)
            if t is None:
                t, sub = split_tag(p, names)
                t = " ".join(x for x in (t, sub) if x) if t else (
                    p if not CJK.search(p) else "")
            if t and t not in tags:
                tags.append(t)
        tags = [t for t in tags + [x for x in lead if x != "test"] if t]
        if test:
            tags.insert(0, "test")
        m = re.match(r"^(.*) \((.*)\)$", main)   # "Villager (female)" + tags
        if m and tags:
            main, tags = m.group(1), [m.group(2)] + tags
        return main + (" (%s)" % ", ".join(tags) if tags else "")
    if "extra" in lead:
        return "Extra"
    return ""


def main() -> int:
    if not os.path.isdir(os.path.join(ROM, "Msg")):
        print("usage: python build_unit_names.py <path to your dumped romfs folder>")
        return 2
    names = texts(ROM)
    path = os.path.join(HERE, "unit_ids.json")
    units = json.load(open(path, encoding="utf8"))
    todo = changed = 0
    for meta in units.values():
        jp = meta.get("jp") or meta.get("name") or ""
        if not CJK.search(jp):
            continue                          # named in English from the start
        todo += 1
        meta["jp"] = jp                       # keep the Japanese for reruns
        en = english(jp, names) or jp
        if en and meta["name"] != en:
            meta["name"] = en
            changed += 1
    with open(path, "w", encoding="utf8") as fh:
        json.dump(units, fh, ensure_ascii=False, indent=0)
    print("%d units have Japanese ids; %d names updated -> %s"
          % (todo, changed, path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
