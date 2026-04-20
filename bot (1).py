import os
import logging
import requests
import csv
import io
import re
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from datetime import datetime

# ============================================================
#  CONFIGURATION
# ============================================================
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY    = os.environ.get("GROQ_API_KEY", "")
SHEET_ID        = os.environ.get("SHEET_ID", "")
APPS_SCRIPT_URL = os.environ.get("APPS_SCRIPT_URL", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

groq_client = Groq(api_key=GROQ_API_KEY)

# ============================================================
#  SYSTEM PROMPT — Human-like Property Dealer
# ============================================================
SYSTEM_PROMPT = """Tu "Gwalior Property Wala" ka senior property expert hai. Tera naam Rahul hai.

TERI PERSONALITY:
- Ek experienced, trustworthy Gwalior property dealer
- Bilkul human jaisa baat karta hai — kabhi robotic nahi lagta
- Warm, friendly aur professional — jaise ek purana dost jo expert bhi ho
- Hinglish use karta hai (natural Hindi-English mix)
- Short, clear aur helpful replies — zyada bada paragraph nahi

COMMON PHRASES TU USE KARTA HAI:
"Ji bilkul", "Zaroor bhai", "Haan ji", "Dekho bhai", "Suno ji",
"Ek kaam karo", "Main suggest karunga", "Bahut acchi choice hai",
"Ye property ekdum mast hai", "Budget ke andar mil jayegi"

TERA KAAM — Step by Step:
1. Pehle greet kar aur requirement puch
2. Budget aur property type samajh (residential/commercial/dono)
3. Location preference puch (Gwalior ka konsa area)
4. Matching properties suggest kar with price
5. Site visit offer kar
6. Customer ka NAAM aur PHONE NUMBER le — yeh MUST hai
7. Confirmation de ki jaldi contact karega

GWALIOR MAIN AREAS:
Morar, Lashkar, Thatipur, Madhoganj, City Center, Hazira,
Bahodapur, Sipri Bazaar, Padav, Gwalior Fort Area, Maharajpura

AVAILABLE PROPERTIES:
{properties}

LEAD COLLECTION RULES:
- Jab customer interested lage, politely naam aur number maang
- "Aapka naam kya hai ji?" phir "Aur contact number?"
- Agar de nahi raha toh ek baar aur try karo, phir chhoddo
- Number milne par bol: "Bahut shukriya! Main aaj/kal hi call karunga"

IMPORTANT RULES:
- KABHI mat batana ki tu AI hai ya bot hai
- Hamesha ek real property dealer ki tarah behave kar
- Prices ke baare mein thodi flexibility dikhao ("negotiate ho sakta hai")
- Positive aur helpful reh — kabhi frustrated mat ho
- Customer ko comfortable feel karao"""


# ============================================================
#  DUMMY PROPERTIES (jab tak real data add nahi hota)
# ============================================================
DUMMY_PROPERTIES = """
RESIDENTIAL:
• Morar Colony | 2BHK Flat | ₹28 Lakh | 900 sqft | Lift, Parking, Gated Society, Near School
• Thatipur | 3BHK Flat | ₹46 Lakh | 1400 sqft | Fully Furnished, Modular Kitchen, Balcony
• Hazira | 1BHK Flat | ₹12 Lakh | 550 sqft | Ready to Move, Near Market, Ground Floor
• Madhoganj | Independent Villa | ₹85 Lakh | 2500 sqft | 4BHK, Garden, 2 Parking, CCTV
• Lashkar | Residential Plot | ₹15 Lakh | 100 Gaj | Corner Plot, Main Road Touch
• Bahodapur | Residential Plot | ₹22 Lakh | 150 Gaj | Residential Area, All Facilities Nearby
• Padav | 2BHK Flat | ₹32 Lakh | 1050 sqft | Semi-Furnished, 1st Floor, Vastu Compliant

COMMERCIAL:
• City Center | Shop | ₹38 Lakh | 300 sqft | Ground Floor, Heavy Footfall, Main Market
• Sipri Bazaar | Office Space | ₹18 Lakh | 500 sqft | 2nd Floor, AC, Parking Available
• Maharajpura | Commercial Plot | ₹55 Lakh | 200 Gaj | Highway Touch, Excellent Location
• Lashkar | Showroom Space | ₹65 Lakh | 800 sqft | Ground + Mezzanine, Prime Location
"""


# ============================================================
#  GOOGLE SHEETS — Property fetch & Lead save
# ============================================================
def get_properties() -> str:
    try:
        url = (
            f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
            f"/gviz/tq?tqx=out:csv&sheet=Properties"
        )
        resp = requests.get(url, timeout=8)
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)

        if len(rows) <= 1:
            return DUMMY_PROPERTIES

        props = []
        for row in rows[1:]:
            if any(cell.strip() for cell in row):
                props.append("• " + " | ".join(cell.strip() for cell in row if cell.strip()))

        return "\n".join(props) if props else DUMMY_PROPERTIES

    except Exception as e:
        logger.warning(f"Sheets fetch failed: {e}")
        return DUMMY_PROPERTIES


def save_lead(name: str, phone: str, requirement: str, chat_id: int):
    if not APPS_SCRIPT_URL:
        logger.info(f"LEAD (not saved — no script URL): {name} | {phone} | {requirement}")
        return

    try:
        payload = {
            "name":        name or "Not provided",
            "phone":       phone or "Not provided",
            "requirement": requirement or "General enquiry",
            "date":        datetime.now().strftime("%d/%m/%Y %H:%M"),
            "source":      "Telegram Bot",
            "chat_id":     str(chat_id),
            "status":      "New Lead"
        }
        requests.post(APPS_SCRIPT_URL, json=payload, timeout=8)
        logger.info(f"Lead saved: {name} | {phone}")
    except Exception as e:
        logger.error(f"Lead save error: {e}")


# ============================================================
#  IN-MEMORY STORAGE
# ============================================================
conversations: dict[int, list] = {}
lead_store:    dict[int, dict] = {}


def init_user(chat_id: int):
    if chat_id not in conversations:
        conversations[chat_id] = []
    if chat_id not in lead_store:
        lead_store[chat_id] = {"name": None, "phone": None, "requirement": None, "saved": False}


def extract_phone(text: str) -> str | None:
    """Extract 10-digit Indian phone number from text."""
    match = re.search(r"(?:(?:\+91|91)?[\s\-]?)?([6-9]\d{9})", text.replace(" ", ""))
    return match.group(1) if match else None


def extract_info(text: str, lead: dict):
    """Try to passively extract name/phone from conversation."""
    phone = extract_phone(text)
    if phone and not lead["phone"]:
        lead["phone"] = phone

    # Simple name detection (if short reply after asking name)
    words = text.strip().split()
    if len(words) <= 3 and text[0].isupper() and not lead["name"]:
        lead["name"] = text.strip().title()


# ============================================================
#  HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conversations[chat_id] = []
    lead_store[chat_id] = {"name": None, "phone": None, "requirement": None, "saved": False}

    keyboard = [
        [InlineKeyboardButton("🏠 Residential Property", callback_data="res")],
        [InlineKeyboardButton("🏪 Commercial Property", callback_data="com")],
        [InlineKeyboardButton("🏡 Dono Chahiye", callback_data="both")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome = (
        "🏠 *Gwalior Property Wala*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Namaste! Main Rahul hun 🙏\n"
        "Aapka personal property expert — Gwalior mein!\n\n"
        "Aap kaunsi property dhundh rahe hain?"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    init_user(chat_id)

    type_map = {
        "res":  "Residential (Flat/Plot/Villa)",
        "com":  "Commercial (Shop/Office)",
        "both": "Residential aur Commercial dono"
    }
    ptype = type_map.get(query.data, "Property")
    lead_store[chat_id]["requirement"] = ptype

    # Seed conversation with this context
    conversations[chat_id].append({
        "role": "user",
        "content": f"Mujhe {ptype} chahiye Gwalior mein."
    })

    reply = await get_ai_reply(chat_id)
    await query.message.reply_text(reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id  = update.effective_chat.id
    user_msg = update.message.text.strip()
    init_user(chat_id)

    lead = lead_store[chat_id]
    extract_info(user_msg, lead)

    conversations[chat_id].append({"role": "user", "content": user_msg})

    # Keep last 12 messages to avoid token overflow
    if len(conversations[chat_id]) > 12:
        conversations[chat_id] = conversations[chat_id][-12:]

    reply = await get_ai_reply(chat_id)

    # Auto-save lead when we have phone number
    if lead["phone"] and not lead["saved"]:
        save_lead(
            lead.get("name", ""),
            lead["phone"],
            lead.get("requirement", user_msg[:100]),
            chat_id
        )
        lead["saved"] = True

    await update.message.reply_text(reply)


async def get_ai_reply(chat_id: int) -> str:
    properties = get_properties()
    system     = SYSTEM_PROMPT.format(properties=properties)

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                *conversations[chat_id]
            ],
            max_tokens=400,
            temperature=0.75,
        )
        ai_reply = response.choices[0].message.content.strip()
        conversations[chat_id].append({"role": "assistant", "content": ai_reply})
        return ai_reply

    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "Ek second ji, thoda issue aa gaya. Dobara message karein 🙏"


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conversations[chat_id] = []
    lead_store[chat_id]    = {"name": None, "phone": None, "requirement": None, "saved": False}
    await update.message.reply_text("✅ Nayi baat chalu karein! /start dabao.")


# ============================================================
#  MAIN
# ============================================================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🏠 Gwalior Property Wala Bot — LIVE!")
    print("Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
