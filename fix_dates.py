#!/usr/bin/env python3
"""
Corrige as datas das notas convertendo o campo 'Criação' para 'date',
compatível com o Quartz.
Formato esperado: Criação: YYYY-MM-DD, HH:MM
"""

import re
from pathlib import Path

CONTENT_DIR = Path("content")

def parse_frontmatter(content):
    if not content.startswith("---"):
        return None, None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None, content
    return parts[0], parts[1], parts[2]

def fix_date(fm_text):
    # Formato: Criação: YYYY-MM-DD, HH:MM
    match = re.search(
        r'^Cria[çc][aã]o:\s*(\d{4}-\d{2}-\d{2})',
        fm_text,
        re.MULTILINE
    )
    if not match:
        return fm_text, False

    date_str = match.group(1)  # já está no formato YYYY-MM-DD

    # Verificar se já tem campo 'date'
    if re.search(r'^date:', fm_text, re.MULTILINE):
        return fm_text, False

    # Adicionar campo date logo após o campo Criação
    new_fm = re.sub(
        r'(Cria[çc][aã]o:.*)',
        rf'\1\ndate: {date_str}',
        fm_text,
        count=1
    )
    return new_fm, True

fixed = 0
for md_file in CONTENT_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    _, fm_text, body = parse_frontmatter(content)

    if fm_text is None:
        continue

    new_fm, changed = fix_date(fm_text)
    if changed:
        new_content = f"---{new_fm}---{body}"
        md_file.write_text(new_content, encoding="utf-8")
        fixed += 1

print(f"✅ {fixed} notas com datas corrigidas.")
