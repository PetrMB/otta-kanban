# Analýza: Karpathy LLM Knowledge Base → OpenClaw Paměť

## Zdroj
- **Video:** I Built Self-Evolving Claude Code Memory w/ Karpathy's LLM Knowledge Bases
- **URL:** https://www.youtube.com/watch?v=7huCP6RkcY4
- **Autor:** Dynamis (YouTube)
- **Inspirace:** Andrej Karpathy (@karpathy) tweet o LLM knowledge bases

---

## 1. Původní Karpathyho Architektura (Externí Data)

### Kompilátorová analogie:
```
Source Code (raw) → Compiler (LLM) → Executable (wiki) → Runtime (queries)
                      ↓                    ↓
                Processing          Test Suite (linting)
```

### Komponenty:

| Fáze | Soubor/Folder | Účel |
|------|---------------|------|
| **Input** | `raw/` | Nezpracované články, papery, transkripty (dump) |
| **Compiler** | Skripty | LLM zpracovává raw → wiki (sumarizace, linkování) |
| **Output** | `wiki/` | Zpracované články s backlinks, koncepty, spojení |
| **Index** | `index.md` | Hlavní navigační soubor pro agenta |
| **Pravidla** | `agents.md` | Globální pravidla popisující celý systém |
| **Testy** | Linting | Kontrola: chybějící data, broken links, stale info |
| **Runtime** | Queries | Agent prohledává wiki pomocí indexu |

### Klíčové principy:
1. **Žádný RAG/vector DB** - Agent naviguje přes index a backlinks
2. **Graph view** - Vizualizace propojení znalostí v Obsidianu
3. **Self-maintaining** - LLM si sám udržuje index soubory
4. **Data ingestion** - Obsidian Web Clipper pro články z webu

---

## 2. Dynamis Implementace (Interní Data)

### Rozdíl: Místo externích dat → SESSION LOGY z Claude Code

### Architektura:
```
Session Logs (raw) → Claude Agent SDK → Knowledge Wiki → Queries
       ↓                      ↓                ↓
   Daily (.md)         Extraction       Concepts + Connections
   (konverzace)       (koncepty)        (cross-reference)
```

### Claude Code Hooks:

| Hook | Kdy se spouští | Co dělá |
|------|----------------|---------|
| `session_start` | Start session | Načte `agents.md` + `knowledge/index.md` |
| `pre-compact` | Před memory compaction | Extrahuje takeaways z konverzace |
| `session_end` | Konec session | Uloží summary do daily logu |

### Flush Process (denní):
1. vezme daily logy
2. extrahuje koncepty a spojení
3. aktualizuje wiki (knowledge/)
4. aktualizuje index.md

---

## 3. Aplikace na OpenClaw

### Co už máme (aktuální stav):
```
AGENTS.md        → Pravidla pro agenty
SOUL.md          → Identita
USER.md          → O uživateli
IDENTITY.md      → Kdo jsem (prázdné)
MEMORY.md        → Dlouhodobá paměť (hlavní session only)
memory/YYYY-MM-DD.md → Denní logy
HEARTBEAT.md     → Periodické úkoly
TOOLS.md         → Lokální poznámky
```

### Problémy současného stavu:
1. ❌ Žádný explicitní **index** - agent neví, co má k dispozici
2. ❌ **Backlinks** nejsou systematické
3. ❌ Daily logy jsou surové, nezpracované
4. ❌ Chybí **koncept extraction** - nedochází k promoci do wiki
5. ❌ Žádná **kontrola integrity** (linting)
6. ❌ MEMORY.md není strukturované jako knowledge base

---

## 4. Návrh Vylepšení

### Nová struktura paměti:

```
workspace/
├── AGENTS.md                    # Existuje - pravidla
├── SOUL.md                      # Existuje - identita  
├── USER.md                      # Existuje - o uživateli
├── IDENTITY.md                  # Existuje - kdo jsem
├── TOOLS.md                     # Existuje - lokální poznámky
├── HEARTBEAT.md                 # Existuje - periodické úkoly
│
├── memory/
│   ├── INDEX.md                 # NOVÉ: Hlavní index paměti
│   ├── MEMORY.md                # Přesunuto: Dlouhodobá paměť
│   │
│   ├── raw/                     # NOVÉ: Surové logy
│   │   └── 2026-05-03.md        # Přesunuto: Denní konverzace
│   │
│   ├── wiki/                    # NOVÉ: Zpracovaná znalost
│   │   ├── concepts/            # Koncepty (extrahované)
│   │   ├── connections/         # Spojení mezi koncepty
│   │   ├── decisions/           # Důležitá rozhodnutí
│   │   └── lessons/             # Naučené lekce
│   │
│   └── research/                # NOVÉ: Výzkum a analýzy
│       └── karpathy-llm-kb-analysis.md  # Tento soubor
│
└── scripts/                     # NOVÉ: Skripty pro paměť
    ├── memory-extract.sh        # Extrakce z raw do wiki
    ├── memory-lint.sh           # Kontrola integrity
    └── memory-index.sh          # Aktualizace indexu
```

### Klíčové nové soubory:

#### 1. `memory/INDEX.md` (Hlavní index)
```markdown
# Paměťový Index

## Rychlá navigace

### Identita
- [SOUL.md](/SOUL.md) - Kdo jsem
- [IDENTITY.md](/IDENTITY.md) - Mé jméno a avatar
- [USER.md](/USER.md) - O mém člověku

### Aktivní projekty
- [OpenClav vývoj](/memory/wiki/concepts/openclaw-development.md)
- [Paměťový systém](/memory/wiki/concepts/memory-system.md)

### Důležitá rozhodnutí
- [2026-05: Přechod na Karpathy architekturu](/memory/wiki/decisions/2026-05-memory-refactor.md)

### Naučené lekce
- [LLM Knowledge Bases](/memory/wiki/lessons/llm-knowledge-bases.md)

### Poslední konverzace (raw)
- [2026-05-03](/memory/raw/2026-05-03.md)
- [2026-05-02](/memory/raw/2026-05-02.md)

### Periodické úkoly
- [HEARTBEAT.md](/HEARTBEAT.md) - Co kontrolovat
```

#### 2. `memory/wiki/concepts/` (Koncepty)
Extrahované koncepty z konverzací, např.:
- `openclaw-development.md`
- `memory-system.md`
- `claude-code.md`
- `mcp-servers.md`

Formát:
```markdown
# OpenClaw Vývoj

## Definice
OpenClaw je agentní systém...

## Související koncepty
- [[claude-code]] - Claude Code integrace
- [[mcp-servers]] - MCP servery

## Zdroje
- [Rozhovor 2026-05-03](/memory/raw/2026-05-03.md)

## Aktualizováno
2026-05-03
```

#### 3. `memory/wiki/connections/` (Spojení)
Vztahy mezi koncepty:
```markdown
# Jak souvisí OpenClaw s Claude Code

## Relace
- OpenClaw **používá** Claude Code jako backend
- Claude Code **poskytuje** nástroje pro OpenClaw

## Kontext
V rozhovoru [2026-05-03](/memory/raw/2026-05-03.md) jsme...
```

---

## 5. Automatizační Skripty

### 1. Extrakce konceptů (`scripts/memory-extract.sh`)
```bash
#!/bin/bash
# Spustí se na konci dne nebo před HEARTBEAT
# - Prochází raw logy
# - Extrahuje koncepty pomocí LLM
# - Uloží do wiki/concepts/
# - Aktualizuje connections/
```

### 2. Linting (`scripts/memory-lint.sh`)
```bash
#!/bin/bash
# Kontroluje:
# - Broken links (odkazy na neexistující soubory)
# - Orphaned concepts (koncepty bez odkazů)
# - Stale data (starší > 90 dní bez aktualizace)
# - Duplicity v konceptech
```

### 3. Index update (`scripts/memory-index.sh`)
```bash
#!/bin/bash
# Aktualizuje memory/INDEX.md:
# - Seznam posledních raw logů
# - Seznam konceptů
# - Seznam rozhodnutí a lekcí
```

---

## 6. OpenClaw-Specifická Úprava

### Problém: OpenClaw nemá "Claude Code hooks" jako takové

### Řešení - použijeme existující mechanismy:

| Karpathy Hook | OpenClaw Ekvivalent |
|---------------|---------------------|
| session_start | AGENTS.md se načítá automaticky |
| session_end | `cron` job na konci dne |
| pre-compact | `HEARTBEAT.md` kontrola |
| flush | Denní cron job |

### Implementace pomocí cron:

```bash
# Denní extrakce (23:00)
0 23 * * * cd ~/.openclaw/workspace && scripts/memory-extract.sh

# Týdenní linting (neděle 00:00)
0 0 * * 0 cd ~/.openclaw/workspace && scripts/memory-lint.sh

# Aktualizace indexu (po každé extrakci)
# Součást memory-extract.sh
```

---

## 7. Konkrétní Kroky Implementace

### Fáze 1: Struktura (nyní)
1. [x] Vytvořit `memory/wiki/` adresáře
2. [x] Vytvořit `memory/research/` adresář
3. [ ] Vytvořit `memory/INDEX.md`
4. [ ] Přesunout existující daily logy do `memory/raw/`

### Fáze 2: Skripty (tento týden)
1. [ ] Vytvořit `scripts/memory-extract.sh`
2. [ ] Vytvořit `scripts/memory-lint.sh`
3. [ ] Vytvořit `scripts/memory-index.sh`

### Fáze 3: Automatizace (příští týden)
1. [ ] Nastavit cron joby pro denní extrakci
2. [ ] Testovat propojení konceptů
3. [ ] Doladit formát wiki článků

### Fáze 4: Vylepšení (budoucnost)
1. [ ] Graph vizualizace v Obsidianu
2. [ ] Search pomocí Obsidian API
3. [ ] Integrace s OpenClaw HEARTBEAT.md

---

## 8. Klíčové Výhody

1. **Self-documenting** - Index říká agentovi, co má k dispozici
2. **Compounding** - Každá konverzace obohacuje knowledge base
3. **Backlinks** - Agent může procházet související koncepty
4. **No RAG** - Jednodušší, žádný vektorový embedding
5. **Linting** - Zajištění integrity dat
6. **Customizable** - Můžeme měnit extrakční logiku

---

## 9. Ukázka Workflow

### Scénář: Pracuji na OpenClaw projektu

**Bez nového systému:**
- Musím procházet celé git history
- Hledat v raw daily logech
- Ztrácím kontext mezi soubory

**S novým systémem:**
1. Agent načte `memory/INDEX.md` - ví, že existuje koncept "OpenClaw"
2. Jde do `memory/wiki/concepts/openclaw-development.md`
3. Vidí rozhodnutí a lekce
4. Prochází backlinks na související koncepty
5. Odpovídá za 10s místo 2 minut prohledávání

---

## 10. Poznámky k Implementaci

### Technické detaily:
- **Backlinks** v Obsidian: `[[nazev-souboru]]` syntax
- **Index** je MANUÁLNĚ udržovaný - LLM ho čte, člověk ho aktualizuje
- **Extrakce** je AUTOMATICKÁ - cron job provádí LLM call
- **Linting** je AUTOMATICKÝ - cron job kontroluje

### Rozdíl od Karpathyho:
- On má externí data (články z webu)
- My máme interní data (naše konverzace)
- Ale architektura je STEJNÁ

### Využití v existujícím AGENTS.md:
```markdown
## Paměťový Systém

Na začátku každé session:
1. Načti `memory/INDEX.md` pro navigaci
2. Pokud dotaz souvisí s existujícím konceptem, načti `memory/wiki/concepts/`
3. Raw daily logy jsou v `memory/raw/` pro detailní kontext
```

---

*Analyzu vytvořil: Otto Honeger*
*Datum: 2026-05-03*
*Zdroj: Karpathy LLM Knowledge Base video*
