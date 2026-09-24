"""Замена блоков в BSL (BOM, CRLF). Использование: python3 tools/bslpatch.py <файл> <патч>
Патч: блоки
@@@ OLD
...
@@@ NEW
...
@@@ END
OLD пуст + NEW с маркером APPEND_BEFORE:<строка> — вставка перед строкой."""
import sys, re
path, patch = sys.argv[1], open(sys.argv[2], encoding="utf-8").read()
text = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
blocks = re.findall(r"@@@ OLD\n(.*?)@@@ NEW\n(.*?)@@@ END\n", patch, re.S)
for old, new in blocks:
    n = text.count(old)
    if n != 1:
        sys.exit(f"OLD найден {n} раз:\n{old[:300]}")
    text = text.replace(old, new)
open(path, "w", encoding="utf-8-sig", newline="").write(text.replace("\n", "\r\n"))
print("ok", len(blocks))
