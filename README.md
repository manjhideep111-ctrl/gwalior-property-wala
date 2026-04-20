# 🏠 Gwalior Property Wala — Setup Guide

## Step 1 — Google Apps Script Setup (Leads Save Karne Ke Liye)

1. Google Sheets open karo
2. Top menu: **Extensions → Apps Script**
3. `apps_script.js` ka poora code paste karo
4. **Save** (Ctrl+S)
5. Pehle `setupPropertiesSheet` function run karo (Properties sheet banegi)
6. Phir **Deploy → New Deployment**
   - Type: **Web App**
   - Execute as: **Me**
   - Who has access: **Anyone**
7. **Deploy** click karo → URL copy karo
8. `bot.py` mein `APPS_SCRIPT_URL = ""` mein yeh URL paste karo

---

## Step 2 — Railway.app Pe Deploy (Free Hosting)

1. **railway.app** pe jaao → GitHub se login karo
2. **New Project → Deploy from GitHub**
3. Yeh folder GitHub pe upload karo
4. Railway automatically detect karega Python
5. **Done! Bot 24/7 live rahega**

### Ya Render.com Pe (Alternative Free Option)
1. **render.com** → New → Web Service
2. GitHub se connect karo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`

---

## Step 3 — Properties Add/Update Karna

Google Sheets → "Properties" sheet mein jaao
Columns:
| Location | Type | Price | Size | Features | Status |

- Nayi property add karni hai → new row add karo
- Property bik gayi → Status column mein "Sold" likh do
- AI automatically latest data use karega!

---

## Step 4 — Telegram Bot Commands

- `/start` → Nayi conversation shuru
- `/reset` → Conversation reset

---

## Files Overview

| File | Kaam |
|------|------|
| `bot.py` | Main Telegram bot code |
| `requirements.txt` | Python libraries |
| `apps_script.js` | Google Sheets script |

---

## Support
Koi issue aaye toh message karo! 🙏
