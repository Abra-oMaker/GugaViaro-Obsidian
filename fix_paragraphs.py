#!/usr/bin/env python3
"""
Corrige espaçamento entre parágrafos nas notas do Quartz.
Adiciona linha em branco entre linhas de texto que não têm separação,
preservando frontmatter, blocos de código, tabelas e listas.
"""

import re
from pathlib import Path

CONTENT_DIR = Path("content")

def fix_paragraphs(content):
    # Separar frontmatter do corpo
    frontmatter = ""
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = "---" + parts[1] + "---"
            body = parts[2]

    lines = body.split("\n")
    result = []
    in_code_block = False
    in_table = False

    for i, line in enumerate(lines):
        # Detectar blocos de código
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        result.append(line)

        # Dentro de bloco de código, não mexer
        if in_code_block:
            continue

        # Detectar tabelas
        if "|" in line and "---" in line:
            in_table = True
        elif in_table and "|" not in line:
            in_table = False

        if in_table:
            continue

        # Verificar se precisa adicionar linha em branco
        current = line.strip()
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

        # Condições para NÃO adicionar linha em branco:
        skip = (
            not current                          # linha atual vazia
            or not next_line                     # próxima linha vazia
            or next_line.startswith("#")         # próxima é cabeçalho
            or current.startswith("#")           # atual é cabeçalho
            or next_line.startswith("-")         # próxima é lista
            or next_line.startswith("*")         # próxima é lista
            or next_line.startswith(">")         # próxima é blockquote
            or next_line.startswith("|")         # próxima é tabela
            or current.startswith("-")           # atual é lista
            or current.startswith("*")           # atual é lista
            or current.startswith(">")           # atual é blockquote
            or current.startswith("|")           # atual é tabela
            or current.startswith("!")           # atual é imagem/embed
            or next_line.startswith("!")         # próxima é imagem/embed
            or current.endswith("\\")            # quebra de linha forçada
        )

        if not skip:
            # Adicionar linha em branco entre parágrafos
            result.append("")

    fixed_body = "\n".join(result)
    return frontmatter + fixed_body

fixed = 0
for md_file in CONTENT_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    new_content = fix_paragraphs(content)
    if new_content != content:
        md_file.write_text(new_content, encoding="utf-8")
        fixed += 1

print(f"✅ {fixed} arquivos corrigidos.")
