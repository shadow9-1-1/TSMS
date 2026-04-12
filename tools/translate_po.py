import re
import sys
from pathlib import Path

import polib
from deep_translator import MyMemoryTranslator

PLACEHOLDER_RE = re.compile(r"%(?:\([^)]+\))?[sd]")
NON_ALPHA_RE = re.compile(r"^[\W\d_]+$")


def protect_placeholders(text: str):
    placeholders = []

    def repl(match):
        idx = len(placeholders)
        placeholders.append(match.group(0))
        return f"__PH_{idx}__"

    return PLACEHOLDER_RE.sub(repl, text), placeholders


def restore_placeholders(text: str, placeholders):
    for idx, ph in enumerate(placeholders):
        text = text.replace(f"__PH_{idx}__", ph)
    return text


def should_translate(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if NON_ALPHA_RE.match(stripped):
        return False
    return True


def translate_text(translator: MyMemoryTranslator, cache: dict, text: str) -> str:
    if not should_translate(text):
        return text
    if text in cache:
        return cache[text]

    protected, placeholders = protect_placeholders(text)
    try:
        translated = translator.translate(protected)
    except Exception:
        translated = protected
    translated = restore_placeholders(translated, placeholders)
    cache[text] = translated
    return translated


def main():
    if len(sys.argv) < 2:
        print("Usage: translate_po.py <path-to-po>")
        return 1

    po_path = Path(sys.argv[1])
    if not po_path.exists():
        print(f"PO file not found: {po_path}")
        return 1

    po = polib.pofile(str(po_path))
    translator = MyMemoryTranslator(source="english", target="arabic")
    cache = {}

    updated = 0
    failed = 0

    for entry in po:
        if entry.obsolete:
            continue

        try:
            if entry.msgid_plural:
                singular_ar = translate_text(translator, cache, entry.msgid)
                plural_ar = translate_text(translator, cache, entry.msgid_plural)

                for i in range(6):
                    current = entry.msgstr_plural.get(i, "")
                    if current:
                        continue
                    entry.msgstr_plural[i] = singular_ar if i == 0 else plural_ar
                    updated += 1
            else:
                if entry.msgstr:
                    continue
                entry.msgstr = translate_text(translator, cache, entry.msgid)
                updated += 1
        except Exception:
            failed += 1

    po.save(str(po_path))
    print(f"Updated entries: {updated}")
    print(f"Failed entries: {failed}")
    print(f"Total entries: {len(po)}")
    print(f"Saved: {po_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
