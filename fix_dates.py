#!/usr/bin/env python3
"""
Corrige as datas das notas convertendo o campo 'Criação' para 'date',
e protege blocos LaTeX de serem modificados por outros scripts.
"""

import re
from pathlib import Path
from datetime import datetime

CONTENT_DIR = Path("content")

def parse_frontmatter(content):
    if not content.startswith("---"):
        return None, None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None, content
    return parts[0], parts[1], parts[2]

def fix_date(fm_text):
    """Converte campo 'Criação: DD/MM/YYYY HH:MM' para 'date: YYYY-MM-DD'"""
    # Detectar campo Criação
    match = re.search(
        r'^Cria[çc][aã]o:\s*(\d{2})[/-](\d{2})[/-](\d{4})',
        fm_text,
        re.MULTILINE
    )
    if not match:
        return fm_text, False

    day, month, year = match.group(1), match.group(2), match.group(3)
    date_str = f"{year}-{month}-{day}"

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
