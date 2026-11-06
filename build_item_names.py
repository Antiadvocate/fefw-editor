"""build_item_names.py - official English item names for item_ids.json.

item_ids.json was made from the game's Japanese item ids, and its English
names were translated from those ("Augus' teff"), not taken from the game's
own English text ("Orgus Coffee").  The game's message files hold both
languages under the same label (MIID_AugusTeff), so the Japanese text there
matches an item's Japanese name exactly and the English text next to it is the
official name.  This rewrites the "en" field of every item it can match; items
it can't match keep their current name.

    python build_item_names.py <path to your dumped romfs folder>

(or set FEFW_ROM).  Forged copies (＋1 … ＋5) take the base item's name.
"""
import glob
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import msbt                                   # noqa: E402

ROM = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FEFW_ROM", "")


def jp_to_en_all(rom: str) -> dict[str, str]:
    """Japanese -> English from every message file; Item* files win on clashes."""
    jp_dir = os.path.join(rom, "Msg", "JPja")
    en_dir = msbt.english_dir(os.path.join(rom, "Msg"))
    out: dict[str, str] = {}
    files = sorted(glob.glob(os.path.join(jp_dir, "*.msbt*")),
                   key=lambda p: not os.path.basename(p).lower().startswith("item"))
    for jp_path in files:
        en_path = os.path.join(en_dir, os.path.basename(jp_path))
        if not os.path.isfile(en_path):
            continue
        try:
            pairs = msbt.jp_to_en(jp_path, en_path)
        except Exception as exc:              # noqa: BLE001 - skip a file we can't read
            print("  skipped %s: %s" % (os.path.basename(jp_path), exc))
            continue
        for jp, en in pairs.items():
            out.setdefault(jp, en)
    return out


# Items the game's text doesn't name at all (cut or unused content).  These are
# hand translations, following the game's own wording elsewhere (宝珠 = Gem,
# 聖杖 = Wand, 秘薬 = Panacea, demon lances go by their name alone), so they
# read consistently instead of half-Japanese.  They are not official names.
HAND_NAMES = {
    "グラディウスの大剣": "Gladius's Greatsword",
    "魔槍グランシーダ": "Grancida",
    "カーラの聖弓": "Kara's Holy Bow",
    "隠れ里の秘薬": "Hidden Village Panacea",
    "宝石": "Gem",
    "ジュラの氷盾": "Jura's Ice Shield",
    "闇弦・黒曜[コーエン]": "Obsidian Dark String [Cohen]",
    "マーズの熱石": "Mars's Heat Stone",
    "フォルタナーの聖杖": "Fortana's Wand",
    "可憐の宝珠": "Graceful Gem",
    "魅了の宝珠": "Charming Gem",
    "酔狂の宝珠": "Whimsy Gem",
    "波乱の宝珠": "Turbulent Gem",
    "闇血の文様": "Dark Blood Crest",
    "魔砲台": "Magic Cannon",
    "魔砲台白": "Magic Cannon (White)",
    "魔羽の友宝": "Demon-Feather Keepsake",
    "馬毛の友宝": "Horse-Hair Keepsake",
    "赤毛の友宝": "Red-Hair Keepsake",
    "黒毛の友宝": "Black-Hair Keepsake",
    "白毛の友宝": "White-Fur Keepsake",
    "灰羽の友宝": "Gray-Feather Keepsake",
    "白羽の友宝": "White-Feather Keepsake",
    "大羽の友宝": "Great-Feather Keepsake",
    # cutscene props (デモ_…)
    "紋章石": "Crest Stone",
    "フォトナ鳥": "Fortuna Bird",
    "フォトナ鳥_無銘の槍": "Fortuna Bird with The Nameless",
    "イシュマールの槍": "Eshmel's Lance",
    "王権の斧": "Axe of Sovereignty",
    "女神像": "Goddess Statue",
    "黒曜": "Obsidian",
    "月白": "Moonwhite",
    "バロールの心臓": "Heart of Balor",
    "羅針盤": "Compass",
    "羅針盤_左手": "Compass (left hand)",
    "ナイフ": "Knife",
    "ナイフ_ジャグリング": "Juggling Knives",
    "探索機": "Searcher",
    "ウルヴァシの冠": "Urvashi's Crown",
    "ビウエラ": "Vihuela",
    "干し首袋": "Bag of Shrunken Heads",
    "巨大な盃": "Giant Sake Cup",
    "手毬": "Temari Ball",
    "手毬_両手": "Temari Ball (both hands)",
    "鍬": "Hoe",
    "木箱": "Wooden Crate",
    "本": "Book",
    "ペン": "Pen",
    "片手で持てる横笛": "Flute",
    "松明": "Torch",
    "画家セット": "Painter's Set",
    "筆": "Brush",
    "折りたたんだ雑巾": "Folded Rag",
    "紙": "Paper",
    "ペンと紙": "Pen and Paper",
    "鍛冶": "Smithing Tools",
    "釣り竿": "Fishing Rod",
    "つるはし": "Pickaxe",
    "銀の斧と盾": "Silver Axe and Shield",
    "鍋料理": "Hot Pot",
    "袋": "Bag",
    "イシュマールの左腕": "Eshmel's Left Arm",
    "大熊の鉤爪": "Great Bear Claw",
}


def hand_name(jp: str) -> str:
    """Hand translation for an unnamed item, its forged copies and its
    per-chapter variants (…_SC15_08)."""
    base = re.sub(r"_SC\d+_\d+$", "", jp)
    return HAND_NAMES.get(base, "")


def renamed(jp: str) -> list[str]:
    """Other spellings the game's text may use for an id's Japanese name.
    Only used when the result matches a message exactly."""
    out = []
    if jp.endswith("書") and not jp.endswith("指南書"):
        stem = jp[:-1]
        if stem.startswith("秘蔵の"):
            out.append("上級" + stem[len("秘蔵の"):] + "指南書")
        out.append(stem + "指南書")
    return out


def main() -> int:
    if not os.path.isdir(os.path.join(ROM, "Msg")):
        print("usage: python build_item_names.py <path to your dumped romfs folder>\n"
              "       (or set FEFW_ROM to it)")
        return 2
    names = jp_to_en_all(ROM)
    path = os.path.join(HERE, "item_ids.json")
    items = json.load(open(path, encoding="utf8"))
    changed = matched = 0
    for meta in items.values():
        jp = unicodedata.normalize("NFKC", meta.get("jp") or "").strip()
        m = re.search(r"\+(\d+)$", jp)
        base = jp[:m.start()] if m else jp
        en = names.get(jp) or names.get(base)
        if not en:
            # per-chapter copies (…_SC18_13), cutscene props (デモ_…) and the
            # art-less copy of a weapon (…_戦技なし) take the real item's name
            stem = re.sub(r"_SC\d+_\d+$", "", base)
            note = ""
            if stem.startswith("デモ_"):
                stem, note = stem[len("デモ_"):], " (cutscene)"
            if stem.endswith("_戦技なし"):
                stem, note = stem[:-len("_戦技なし")], " (no art)"
            if note == " (cutscene)":
                found = hand_name(stem) or names.get(stem)
            else:
                found = names.get(stem) or hand_name(stem)
            en = found + note if found else ""
        if not en:
            # ids that kept an older working name: skill books are 戦術書 /
            # 秘蔵の戦術書 in the ids but 戦術指南書 / 上級戦術指南書 in the game
            for alt in renamed(base):
                en = names.get(alt)
                if en:
                    break
        if en:
            matched += 1
        else:
            en = hand_name(base)
            if not en:
                continue
        if m and not re.search(r"\+\s*\d+$", en):
            en = "%s +%s" % (en, m.group(1))
        if meta.get("en") != en:
            meta["en"] = en
            changed += 1
    with open(path, "w", encoding="utf8") as fh:
        json.dump(items, fh, ensure_ascii=False, separators=(",", ":"))
    print("%d items: %d matched the game's English text, %d names updated -> %s"
          % (len(items), matched, changed, path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
