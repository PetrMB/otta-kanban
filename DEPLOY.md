# 🚀 Jak nasadit Kanban na otto.honeger.com

## 1️⃣ Přihlášení do Cloudflare

```bash
cd ~/.openclaw/workspace/otta-kanban
wrangler login
```

Toto otevře browser s Cloudflare OAuth — přihlaš se svým účtem.

---

## 2️⃣ Vytvoření Pages projektu

```bash
wrangler pages project create otta-kanban
```

---

## 3️⃣ Deploy

```bash
wrangler pages deploy . --project-name=otta-kanban
```

---

## 4️⃣ Vlastní doména (otto.honeger.com)

1. Jdi na [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Zvol **Pages** → **otta-kanban**
3. V **Custom Domains** přidej `otto.honeger.com`
4. Cloudflare automaticky nastaví DNS (CNAME)

---

## 5️⃣ Overení

Po 1-2 minutách bude kanban dostupný na:  
👉 https://otto.honeger.com

---

## 🛠 Zdrojový kód

 Lokální projekt: `~/.openclaw/workspace/otta-kanban/`
