#!/usr/bin/env python3
"""
Corrige espaçamento entre parágrafos nas notas do Quartz.
Preserva frontmatter, blocos de código, tabelas, listas e blocos LaTeX.
Separa blocos $$ que estejam colados ao texto.
"""

from pathlib import Path
import re

CONTENT_DIR = Path("content")

def separate_latex_blocks(body):
    """
    Garante que $$ blocos estejam em linhas próprias.
    Ex: 'texto: $$formula$$' -> 'texto:\n\n$$formula$$'
    """
    # Separar $$ do texto anterior na mesma linha
    body = re.sub(r'(.+?)(\$\$[^$]+\$\$)', r'\1\n\n\2', body)
    # Separar $$ do texto posterior na mesma linha  
    body = re.sub(r'(\$\$[^$]+\$\$)(.+)', r'\1\n\n\2', body)
    return body

def fix_paragraphs(content):
    frontmatter = ""
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = "---" + parts[1] + "---"
            body = parts[2]

    # Primeiro separar LaTeX inline que está colado ao texto
    body = separate_latex_blocks(body)

    lines = body.split("\n")
    result = []
    in_code_block = False
    in_latex_block = False
    in_table = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "$$":
            in_latex_block = not in_latex_block
            result.append(line)
            continue

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            continue

        result.append(line)

        if in_code_block or in_latex_block:
            continue

        if re.match(r'^\|.*\|', stripped) and "---" in stripped:
            in_table = True
        elif in_table and not re.match(r'^\|', stripped):
            in_table = False

        if in_table:
            continue

        current = stripped
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

        skip = (
            not current
            or not next_line
            or next_line.startswith("#")
            or current.startswith("#")
            or next_line.startswith("-")
            or next_line.startswith("*")
            or next_line.startswith(">")
            or re.match(r'^\|', next_line)
            or next_line.startswith("$$")
            or current.startswith("-")
            or current.startswith("*")
            or current.startswith(">")
            or re.match(r'^\|', current)
            or current.startswith("!")
            or current.startswith("$$")
            or next_line.startswith("!")
            or current.endswith("\\")
        )

        if not skip:
            result.append("")

    return frontmatter + "\n".join(result)

fixed = 0
for md_file in CONTENT_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    new_content = fix_paragraphs(content)
    if new_content != content:
        md_file.write_text(new_content, encoding="utf-8")
        fixed += 1

print(f"✅ {fixed} arquivos corrigidos.")
