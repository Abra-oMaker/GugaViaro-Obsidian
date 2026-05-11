#!/usr/bin/env python3
"""
Gera um dashboard de analytics do vault do Obsidian.
Analisa todas as notas e produz um arquivo analytics.md com dados JSON embutidos.
"""

import re
import json
import yaml
from pathlib import Path
from collections import defaultdict
from datetime import datetime

CONTENT_DIR = Path("content")

def parse_frontmatter(content):
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

def get_tags(fm):
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    return [t.lstrip("#").strip() for t in (tags or [])]

def extract_wikilinks(body):
    return re.findall(r'\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]', body)

def count_words(body):
    clean = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
    clean = re.sub(r'\$\$.*?\$\$', '', clean, flags=re.DOTALL)
    clean = re.sub(r'[#*_\[\]|>-]', ' ', clean)
    return len(clean.split())

# Coletar dados de todas as notas
notes = []
all_existing_slugs = set()

for md_file in CONTENT_DIR.rglob("*.md"):
    if md_file.name == "index.md":
        continue
    all_existing_slugs.add(md_file.stem)

for md_file in CONTENT_DIR.rglob("*.md"):
    if md_file.name == "index.md":
        continue
    
    content = md_file.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    tags = get_tags(fm)
    wikilinks = extract_wikilinks(body)
    words = count_words(body)
    
    # Data de criação
    date_str = str(fm.get("date") or fm.get("Criação") or "")
    date_obj = None
    for fmt in ["%Y-%m-%d", "%Y-%m-%d, %H:%M", "%d/%m/%Y"]:
        try:
            date_obj = datetime.strptime(date_str[:10], fmt[:10])
            break
        except:
            continue
    
    # Índice(s)
    idx_val = fm.get("Índice") or fm.get("Indice") or []
    if not isinstance(idx_val, list):
        idx_val = [idx_val]
    indices = []
    for v in idx_val:
        m = re.match(r'\[\[([^\]|]+)', str(v))
        if m:
            indices.append(m.group(1).strip())
        else:
            indices.append(str(v).strip())

    # Links existentes vs inexistentes
    existing_links = [l for l in wikilinks if l.strip() in all_existing_slugs]
    broken_links = [l for l in wikilinks if l.strip() not in all_existing_slugs]

    is_index = "nota-índice" in tags or "nota-indice" in tags

    notes.append({
        "name": md_file.stem,
        "path": str(md_file.relative_to(CONTENT_DIR)),
        "tags": tags,
        "wikilinks": wikilinks,
        "existing_links": existing_links,
        "broken_links": broken_links,
        "words": words,
        "status": str(fm.get("Status") or ""),
        "indices": indices,
        "date": date_obj.strftime("%Y-%m-%d") if date_obj else "",
        "date_obj": date_obj,
        "is_index": is_index,
        "folder": str(md_file.parent.relative_to(CONTENT_DIR)),
    })

# ── Métricas ──────────────────────────────────────────────────────────────

total_notes = len(notes)
total_words = sum(n["words"] for n in notes)
avg_words = total_words // total_notes if total_notes else 0
total_links = sum(len(n["wikilinks"]) for n in notes)
total_broken = sum(len(n["broken_links"]) for n in notes)
total_existing_links = sum(len(n["existing_links"]) for n in notes)

# Notas por status
status_counts = defaultdict(int)
for n in notes:
    s = n["status"] or "Sem status"
    status_counts[s] += 1

# Notas por tag
tag_counts = defaultdict(int)
for n in notes:
    for t in n["tags"]:
        tag_counts[t] += 1

# Notas por pasta
folder_counts = defaultdict(int)
for n in notes:
    folder_counts[n["folder"]] += 1

# Notas por índice
index_counts = defaultdict(int)
for n in notes:
    for idx in n["indices"]:
        index_counts[idx] += 1

# Top notas por número de wikilinks (incluindo e excluindo índices)
top_linked_all = sorted(notes, key=lambda x: len(x["wikilinks"]), reverse=True)[:10]
top_linked_no_index = sorted([n for n in notes if not n["is_index"]], key=lambda x: len(x["wikilinks"]), reverse=True)[:10]

# Notas órfãs (sem wikilinks de entrada e sem wikilinks de saída)
all_link_targets = set()
for n in notes:
    for l in n["wikilinks"]:
        all_link_targets.add(l.strip())

orphan_notes = [n for n in notes if len(n["wikilinks"]) == 0 and n["name"] not in all_link_targets and not n["is_index"]]

# Notas mais longas
top_words = sorted(notes, key=lambda x: x["words"], reverse=True)[:10]

# Crescimento por mês
monthly_growth = defaultdict(int)
for n in notes:
    if n["date"]:
        month = n["date"][:7]  # YYYY-MM
        monthly_growth[month] += 1

monthly_growth_sorted = sorted(monthly_growth.items())

# Notas com mais links quebrados
top_broken = sorted(notes, key=lambda x: len(x["broken_links"]), reverse=True)[:10]
top_broken = [n for n in top_broken if len(n["broken_links"]) > 0]

# Taxa de completude dos links
link_health = round((total_existing_links / total_links * 100) if total_links else 0, 1)

# Média de links por nota
avg_links = round(total_links / total_notes, 1) if total_notes else 0

# Notas sem data
no_date = len([n for n in notes if not n["date"]])

# Distribuição de palavras
word_ranges = {"0-100": 0, "101-300": 0, "301-500": 0, "501-1000": 0, "1000+": 0}
for n in notes:
    w = n["words"]
    if w <= 100: word_ranges["0-100"] += 1
    elif w <= 300: word_ranges["101-300"] += 1
    elif w <= 500: word_ranges["301-500"] += 1
    elif w <= 1000: word_ranges["501-1000"] += 1
    else: word_ranges["1000+"] += 1

# Compilar dados para o dashboard
analytics_data = {
    "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
    "summary": {
        "total_notes": total_notes,
        "total_words": total_words,
        "avg_words": avg_words,
        "total_links": total_links,
        "total_broken": total_broken,
        "link_health": link_health,
        "avg_links": avg_links,
        "orphan_count": len(orphan_notes),
        "no_date_count": no_date,
    },
    "status_counts": dict(sorted(status_counts.items(), key=lambda x: x[1], reverse=True)),
    "tag_counts": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
    "folder_counts": dict(sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)),
    "index_counts": dict(sorted(index_counts.items(), key=lambda x: x[1], reverse=True)),
    "top_linked_all": [{"name": n["name"], "count": len(n["wikilinks"])} for n in top_linked_all],
    "top_linked_no_index": [{"name": n["name"], "count": len(n["wikilinks"])} for n in top_linked_no_index],
    "top_words": [{"name": n["name"], "count": n["words"]} for n in top_words],
    "orphan_notes": [n["name"] for n in orphan_notes[:20]],
    "top_broken": [{"name": n["name"], "count": len(n["broken_links"]), "links": n["broken_links"][:5]} for n in top_broken[:10]],
    "monthly_growth": [{"month": m, "count": c} for m, c in monthly_growth_sorted],
    "word_ranges": word_ranges,
}

# Salvar JSON
json_path = Path("analytics-data.json")
json_path.write_text(json.dumps(analytics_data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✅ Analytics gerado: {total_notes} notas, {total_words} palavras, {total_links} links.")
