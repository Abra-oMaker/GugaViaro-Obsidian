#!/usr/bin/env python3
"""
Gera wikilinks estáticos nas notas de índice do Quartz,
substituindo os blocos dataviewjs por listas de [[links]] reais.
"""

import os
import re
import yaml
from pathlib import Path
from collections import defaultdict

CONTENT_DIR = Path("content")

# Mapas: número do índice -> nome do arquivo de índice
# Ex: "4" -> "4 - BIOLOGIA"
indice_num_para_nome = {}

# Mapas: nome do arquivo de índice -> lista de notas que apontam para ele
# Separado por tipo de tag
referencias = defaultdict(list)    # tag: nota-referência
permanentes = defaultdict(list)    # tag: nota-permanente

def parse_frontmatter(content):
    """Extrai o frontmatter YAML de um arquivo markdown."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        fm = yaml.safe_load(parts[1]) or {}
        return fm, parts[2]
    except:
        return {}, content

def normalizar_indice(valor):
    """Extrai o número ou nome de um valor de índice."""
    if valor is None:
        return []
    if isinstance(valor, list):
        return [normalizar_indice(v)[0] for v in valor if normalizar_indice(v)]
    s = str(valor).strip()
    # Wikilink: [[4 - BIOLOGIA]] ou [[4 - BIOLOGIA|alias]]
    match = re.match(r'\[\[([^\]|]+)', s)
    if match:
        return [match.group(1).strip()]
    return [s]

def get_tags(fm):
    """Retorna lista de tags do frontmatter."""
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    return [t.lstrip("#").strip() for t in tags]

# --- Passo 1: Descobrir notas de índice e suas notas vinculadas ---

for md_file in CONTENT_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    tags = get_tags(fm)
    nome = md_file.stem  # ex: "4 - BIOLOGIA"

    # Registrar notas de índice pelo seu número
    if "nota-índice" in tags or "nota-indice" in tags:
        idx_val = fm.get("Índice") or fm.get("Indice")
        nums = normalizar_indice(idx_val)
        for num in nums:
            indice_num_para_nome[num] = nome

for md_file in CONTENT_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    tags = get_tags(fm)
    nome = md_file.stem

    # Pular as próprias notas de índice
    if "nota-índice" in tags or "nota-indice" in tags:
        continue

    idx_val = fm.get("Índice") or fm.get("Indice")
    indices_da_nota = normalizar_indice(idx_val)

    for idx in indices_da_nota:
        # Pode ser número ("4") ou nome completo ("4 - BIOLOGIA")
        # Tenta resolver pelo número primeiro
        nome_indice = indice_num_para_nome.get(idx, idx)

        if "nota-referência" in tags or "nota-referencia" in tags:
            referencias[nome_indice].append(nome)
        if "nota-permanente" in tags:
            permanentes[nome_indice].append(nome)

# --- Passo 2: Reescrever os arquivos de índice ---

DATAVIEW_PATTERN = re.compile(r'```dataviewjs.*?```', re.DOTALL)

substituicoes = 0

for md_file in CONTENT_DIR.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(content)
    tags = get_tags(fm)

    if "nota-índice" not in tags and "nota-indice" not in tags:
        continue

    nome_indice = md_file.stem
    refs = referencias.get(nome_indice, [])
    perms = permanentes.get(nome_indice, [])

    def substituir_dataview(match):
        bloco = match.group(0)

        # Detectar qual tipo de bloco é pelo conteúdo
        if "nota-referência" in bloco or "nota-referencia" in bloco:
            notas = refs
        elif "nota-permanente" in bloco:
            notas = perms
        else:
            return bloco  # Manter blocos desconhecidos

        if notas:
            links = "\n".join(f"- [[{n}]]" for n in sorted(notas))
        else:
            links = "_Nenhuma nota vinculada ainda._"
        return links

    novo_conteudo = DATAVIEW_PATTERN.sub(substituir_dataview, content)

    if novo_conteudo != content:
        md_file.write_text(novo_conteudo, encoding="utf-8")
        substituicoes += 1
        print(f"✅ {md_file.name}: {len(refs)} refs, {len(perms)} permanentes")

print(f"\n✨ {substituicoes} notas de índice atualizadas.")
