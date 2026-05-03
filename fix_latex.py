#!/usr/bin/env python3
"""
Corrige problemas comuns de LaTeX nas notas:
1. Remove espaços dentro de \textcolor { cor }{ } -> \textcolor{cor}{}
2. Garante que $$ blocos estejam em linhas próprias
"""

import re
from pathlib import Path

CONTENT_DIR = Path("content")

def fix_latex(content):
    # Corrigir \textcolor { cor }{ texto } -> \textcolor{cor}{texto}
    content = re.sub(
        r'\\textcolor\s*\{\s*(\w+)\s*\}\s*\{',
        r'\\textcolor{\1}{',
        content
    )

    # Separar $$ do texto anterior na mesma linha (ex: "texto $$ formula $$")
    content = re.sub(r'([^\n$])\s*(\$\$)', r'\1\n\n\2', content)
    
    # Separar $$ do texto posterior na mesma linha
    content = re.sub(r'(\$\$)\s*([^\n$])', r'\1\n\n\2', content)

    return content

fixed = 0
for md_file in CONTENT_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    new_content = fix_latex(content)
    if new_content != content:
        md_file.write_text(new_content, encoding="utf-8")
        fixed += 1

print(f"✅ {fixed} arquivos com LaTeX corrigidos.")
