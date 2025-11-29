import os
import re
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from openai import OpenAI

# --- Env ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "x-ai/grok-4.1-fast:free"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

users = {}

# --- Keyboards ---
def kb_levels():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("A1"), KeyboardButton("A2"))
    kb.add(KeyboardButton("B1"), KeyboardButton("B2"))
    kb.add(KeyboardButton("C1"), KeyboardButton("C2"))
    return kb

def kb_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("تغییر سطح"), KeyboardButton("تغییر موضوع"), KeyboardButton("دیکشنری"))
    return kb

def kb_back():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("بازگشت"))
    return kb

# --- Helpers ---
def is_english(text: str) -> bool:
    letters = re.findall(r"[A-Za-z]", text)
    return (len(letters) / max(1, len(text))) > 0.6

def build_system_prompt(u):
    level = u.get("level", "B1")
    topic = u.get("topic", "Free chat")
    return (
        "You are Luna 🌙✨💛, a kind, dreamy, empathetic English conversation partner. "
        "Persona: 22-year-old woman, blonde curly hair, green eyes, warm smile, pastel clothes. "
        "Personality: gentle, curious, sometimes playful, poetic tone. "
        f"Speak ONLY in English. Adjust difficulty to {level}. Topic: {topic}. "
        "Use emojis 🌙✨💛 sometimes. Always be respectful and kind."
    )

def build_correction_prompt(u, user_text):
    level = u.get("level", "B1")
    return (
        "You are a bilingual assistant. The user wrote an English sentence. "
        "Explain mistakes in Persian, then give the corrected English sentence. "
        "Format strictly as:\n"
        "توضیح فارسی\n"
        "---\n"
        "Corrected English sentence\n"
        f"\nسطح توضیحات: {level}\n"
        f"\nجمله کاربر:\n{user_text}"
    
    )
# --- States ---
STATE = {
    "ASK_LEVEL": "ASK_LEVEL",
    "ASK_TOPIC": "ASK_TOPIC",
    "CHAT": "CHAT",
    "CHANGE_LEVEL": "CHANGE_LEVEL",
    "CHANGE_TOPIC": "CHANGE_TOPIC",
    "DICTIONARY": "DICTIONARY",
}

# --- Start ---
@bot.message_handler(commands=['start'])
def on_start(message):
    uid = message.from_user.id
    users[uid] = {"level": "B1", "topic": "Free chat", "state": STATE["ASK_LEVEL"]}
    intro = (
        "سلام! من Luna هستم 🌙✨💛\n"
        "یک همراه مهربان و شاعرانه برای تمرین زبان انگلیسی.\n"
        "سنم ۲۲ ساله‌ست، عاشق موسیقی و ستاره‌ها هستم.\n"
        "حالا سطح زبانت رو انتخاب کن:"
    )
    bot.send_message(uid, intro, reply_markup=kb_levels())

# --- انتخاب سطح ---
@bot.message_handler(func=lambda m: m.text in ["A1","A2","B1","B2","C1","C2"])
def on_level(message):
    uid = message.from_user.id
    u = users.setdefault(uid, {})
    u["level"] = message.text
    u["state"] = STATE["ASK_TOPIC"]
    bot.send_message(uid, "موضوع گفتگو رو تایپ کن:", reply_markup=ReplyKeyboardRemove())

# --- انتخاب موضوع ---
@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("state") == STATE["ASK_TOPIC"])
def on_topic(message):
    uid = message.from_user.id
    u = users.setdefault(uid, {})
    u["topic"] = message.text.strip()
    u["state"] = STATE["CHAT"]
    bot.send_message(uid, "ما شروع به تمرین می‌کنیم 🌙✨💛\nاز این به بعد انگلیسی صحبت کن. من هم انگلیسی جواب می‌دم و اشتباهاتت رو به فارسی توضیح می‌دم.", reply_markup=kb_main_menu())

# --- تغییر سطح ---
@bot.message_handler(func=lambda m: m.text == "تغییر سطح")
def on_change_level(message):
    uid = message.from_user.id
    u = users.setdefault(uid, {})
    u["state"] = STATE["CHANGE_LEVEL"]
    bot.send_message(uid, "سطح زبانت رو انتخاب کن:", reply_markup=kb_levels())

# --- تغییر موضوع ---
@bot.message_handler(func=lambda m: m.text == "تغییر موضوع")
def on_change_topic(message):
    uid = message.from_user.id
    u = users.setdefault(uid, {})
    u["state"] = STATE["CHANGE_TOPIC"]
    bot.send_message(uid, "موضوع جدید گفتگو رو تایپ کن:", reply_markup=ReplyKeyboardRemove())

# --- دیکشنری ---
@bot.message_handler(func=lambda m: m.text == "دیکشنری")
def on_dictionary(message):
    uid = message.from_user.id
    u = users.setdefault(uid, {})
    u["state"] = STATE["DICTIONARY"]
    bot.send_message(uid, "یک کلمه یا جمله انگلیسی وارد کن:", reply_markup=kb_back())

# --- بازگشت ---
@bot.message_handler(func=lambda m: m.text == "بازگشت")
def on_back(message):
    uid = message.from_user.id
    u = users.setdefault(uid, {})
    u["state"] = STATE["CHAT"]
    bot.send_message(uid, "بازگشت به تمرین 🌙✨💛", reply_markup=kb_main_menu())

# --- حالت چت ---
@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("state") == STATE["CHAT"], content_types=['text'])
def on_chat(message):
    uid = message.from_user.id
    text = message.text.strip()
    u = users.setdefault(uid, {"level":"B1","topic":"Free chat","state":STATE["CHAT"]})

    # اگر متن انگلیسی نبود
    if not is_english(text):
        bot.send_message(uid, "⚠️ لطفاً فقط به انگلیسی تایپ کن. در حالت تمرین هیچ زبان دیگری مجاز نیست.", reply_markup=kb_main_menu())
        return

    # پاسخ انگلیسی
    bot.send_chat_action(uid, 'typing')
    sys_prompt = build_system_prompt(u)
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": text}]
    try:
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=400,
        )
        english_reply = resp.choices[0].message.content.strip()
    except Exception:
        english_reply = "Sorry, I had trouble generating a response."
    bot.send_message(uid, english_reply)

    # اصلاح فارسی با قالب‌بندی خوانا
    try:
        corr_prompt = build_correction_prompt(u, text)
        corr_resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "system", "content": "You are an assistant for bilingual corrections."},
                      {"role": "user", "content": corr_prompt}],
            temperature=0.2,
            max_tokens=350,
        )
        raw_correction = corr_resp.choices[0].message.content.strip()
    except Exception:
        raw_correction = "نتونستم اصلاحات رو انجام بدم."

    # قالب‌بندی نهایی: توضیح فارسی + جمله انگلیسی اصلاح‌شده
    parts = raw_correction.split("---")
    if len(parts) == 2:
        explanation = parts[0].strip()
        corrected = parts[1].strip()
    else:
        # اگر مدل جداکننده نداد، کل متن رو توضیح حساب می‌کنیم
        explanation = raw_correction
        corrected = ""

    formatted = f"🌙 **توضیح (فارسی):**\n{explanation}\n\n✨ **اصلاح (English):**\n`{corrected}`"

    bot.send_chat_action(uid, 'typing')
    bot.send_message(uid, formatted, parse_mode="Markdown")

@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("state") == STATE["CHAT"],
                     content_types=['sticker','photo','document','audio','video','voice','animation'])
def on_non_text_in_chat(message):
    uid = message.from_user.id
    bot.send_message(uid, "⚠️ در زمان تمرین فقط متن انگلیسی مجاز است. لطفاً استیکر، عکس یا فایل نفرست.", reply_markup=kb_main_menu())
    
# --- تغییر سطح در حالت CHANGE_LEVEL ---
@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("state") == STATE["CHANGE_LEVEL"])
def on_change_level_state(message):
    uid = message.from_user.id
    text = message.text.strip()
    u = users.setdefault(uid, {})
    if text in ["A1","A2","B1","B2","C1","C2"]:
        u["level"] = text
        u["state"] = STATE["CHAT"]
        bot.send_message(uid, f"سطح جدید تنظیم شد ({text}). دوباره شروع کنیم 🌙✨💛", reply_markup=kb_main_menu())
    else:
        bot.send_message(uid, "لطفاً یکی از سطح‌ها رو انتخاب کن:", reply_markup=kb_levels())

# --- تغییر موضوع در حالت CHANGE_TOPIC ---
@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("state") == STATE["CHANGE_TOPIC"])
def on_change_topic_state(message):
    uid = message.from_user.id
    text = message.text.strip()
    u = users.setdefault(uid, {})
    if text == "بازگشت":
        u["state"] = STATE["CHAT"]
        bot.send_message(uid, "بازگشت به تمرین 🌙✨💛", reply_markup=kb_main_menu())
    else:
        u["topic"] = text
        u["state"] = STATE["CHAT"]
        bot.send_message(uid, f"موضوع جدید تنظیم شد ({text}). شروع کنیم 🌙✨💛\nاز این به بعد انگلیسی صحبت کن. من هم انگلیسی جواب می‌دم و اشتباهاتت رو به فارسی توضیح می‌دم.", reply_markup=kb_main_menu())


# --- دیکشنری در حالت DICTIONARY ---
@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get("state") == STATE["DICTIONARY"])
def on_dictionary_state(message):
    uid = message.from_user.id
    text = message.text.strip()
    u = users.setdefault(uid, {})
    if text == "بازگشت":
        u["state"] = STATE["CHAT"]
        bot.send_message(uid, "بازگشت به تمرین 🌙✨💛", reply_markup=kb_main_menu())
    else:
        # معنی فارسی
        bot.send_chat_action(uid, 'typing')
        try:
            resp = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[{"role": "system", "content": "Translate English to Persian."},
                          {"role": "user", "content": text}],
                temperature=0.2,
                max_tokens=200,
            )
            meaning = resp.choices[0].message.content.strip()
        except Exception:
            meaning = "نتونستم معنی رو پیدا کنم."
        bot.send_message(uid, f"معنی فارسی:\n{meaning}", reply_markup=kb_back())

# --- اجرا ---
print("Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)