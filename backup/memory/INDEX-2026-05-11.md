# 📇 Memory Index

> **Jedna stránka pro rychlý přístup ke všemu důležitému**

---

## 🎯 Rychlé odkazy

| Co hledám | Kde je to |
|-----------|-----------|
| **Dnešní log** | [[2026-04-05]] — Anthropic budget, AK video analýza |
| **Dlouhodobá paměť** | [[MEMORY]] — rozhodnutí, know-how, projekty |
| **Kdo jsem** | [[SOUL]] — identita, pravidla |
| **Kdo je Petr** | [[USER]] — preference, kontakt |
| **Nezpracované** | `memory/inbox/` — clippings, rychlé poznámky |

---

## 📁 Struktura

```
memory/
├── INDEX.md              ← Tento soubor (vždy aktuální)
├── inbox/                ← Házej sem všechno nezpracované
│   └── (zpracovává cron job + ručně)
├── 2026-04-05.md         ← Denní logy (YYYY-MM-DD.md)
├── 2026-04-01.md
├── ...
└── MEMORY.md             ← Destilované znalosti (po důkladném zpracování)
```

---

## ✋ Jak to ovlivňuješ TY

### 1. **Rychlá poznámka** → do `inbox/`
Řekni: *"Zapiš do inboxu: [text]"*

Nebo manuálně:
```bash
write ~/.openclaw/workspace/memory/inbox/2026-04-05-poznamka.md "..."
```

### 2. **Důležitá věc** → do MEMORY.md
Řekni: *"Přidej do MEMORY.md do sekce Technologie: [obsah]"*

Případně pošli přímo na mě — já to zpracuju a aktualizuji MEMORY.md.

### 3. **Měsíční úklid**
Jednou za měsíc se zeptej: *"Zkontroluj inbox a aktualizuj MEMORY.md"*

---

## 🧠 Jak to vidím JÁ (OpenClaw)

Když hledám v paměti, používám prioritu:
1. **MEMORY.md** — nejdůvěryhodnější, kurátorované
2. **Posledních 7 dní** — daily logs
3. **Starší logs** — archive
4. **inbox/** — nezpracované, potřebují kontext

**Proč?** Chci mít jistotu, že používám ověřené informace, ne náhodné poznámky.

---

## 🔄 Automatizace (nastaveno)

| Co | Kdy | Co se stane |
|----|-----|-------------|
| **Index update** | 1. den v měsíci 9:00 | Projde poslední měsíc, aktualizuje INDEX.md |
| **Inbox alert** | Týdně neděle 20:00 | Připomene ti nezpracované soubory v inboxu |

---

## 📊 Stav systému

- **Poslední update INDEX.md:** 2026-04-05
- **Soubory v inboxu:** (doplním při kontrole)
- **Daily logs tento měsíc:** (doplním při kontrole)

---

*Pro úpravu tohoto souboru řekni: "Uprav INDEX.md, přidej [sekci]"*
