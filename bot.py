import os
from flask import Flask, request
from html import escape as html_escape

# PTB (python-telegram-bot) importlari
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)

# === TOKEN VA ADMIN ID ===
# DIQQAT: PTB kutubxonasini ishlatish uchun Tokeningiz to'g'ri ekanligiga ishonch hosil qiling.
BOT_TOKEN = "8549346336:AAFMvd3jU68-1-csiwOMRML0CflfkW114i4"
ADMIN_CHAT_ID = 7413228837 

# --- KONVERSATSIYA BOSQICHLARI ---
SELECT_CATEGORY, ENTER_COMPLAINT = range(2)


# --- GLOBAL FUNKSIYALAR ---

def create_main_menu_keyboard():
    # Faqat "Shikoyat qilish" tugmasi
    return ReplyKeyboardMarkup([["📨 Shikoyat qilish"]], resize_keyboard=True, one_time_keyboard=False)

def create_complaint_type_keyboard():
    # Shikoyat turlari
    options = [
        "🚫 Korrupsiya", "🏠 Yotoqxona muammolari", 
        "👩‍🏫 O‘qituvchi muammosi", "🧾 Imtihon adolatsizligi",
        "🧍‍♂️ Dekan/Fakultet muammosi", "🧑‍💼 Xodimlar bo‘yicha",
        "📑 Hujjatlar muammosi", "🧳 Yotoqxona kirish/chiqarish", 
        "💸 Pora/pul talab qilish", "📝 Boshqa shikoyat"
    ]
    keyboard = []
    # Ikki qatorli joylashtirish
    for i in range(0, len(options), 2):
        row = [options[i]]
        if i + 1 < len(options):
            row.append(options[i+1])
        keyboard.append(row)

    # Bekor qilish tugmasini qo'shish
    keyboard.append(["❌ Bekor qilish"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


# --- HANDLER FUNKSIYALARI ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/start buyrug'ini boshqaradi va asosiy menyuni chiqaradi."""
    markup = create_main_menu_keyboard()
    await update.message.reply_text(
        "Assalomu alaykum!\nQuyidagilardan birini tanlang:",
        reply_markup=markup
    )
    # Konversiya logikasini to'xtatadi
    return ConversationHandler.END

async def start_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shikoyat qilish tugmasi bosilganda ishga tushadi."""
    markup = create_complaint_type_keyboard()
    await update.message.reply_text(
        "📨 Shikoyat turini tanlang:",
        reply_markup=markup
    )
    # Keyingi bosqichga o'tish
    return SELECT_CATEGORY

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchi shikoyat turini tanlaganda ishga tushadi."""
    category = update.message.text
    context.user_data['category'] = category
    
    hide_markup = ReplyKeyboardRemove()
    
    await update.message.reply_text(
        "✍️ Shikoyatingizni yozing.\n\n"
        "📷 Rasm: 5 MB dan oshmasin\n"
        "🎥 Video: 1 daqiqadan oshmasin",
        reply_markup=hide_markup
    )
    
    # Shikoyat matnini kutish bosqichiga o'tish
    return ENTER_COMPLAINT

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shikoyat matnini qabul qiladi va adminga yuboradi."""
    category = context.user_data.get('category', 'Noma\'lum')
    user = update.effective_user
    
    user_id = user.id
    username = user.username
    full_name = f"{user.first_name} {user.last_name if user.last_name else ''}".strip()
    
    # Matn yoki media sarlavhasini olish
    message_text_raw = update.message.caption if update.message.caption else update.message.text
    message_text_raw = message_text_raw if message_text_raw else "Tekst mavjud emas (media)"
    
    cleaned_message_text = html_escape(message_text_raw)
    cleaned_category = html_escape(category) 

    # ADMINGA YUBORILADIGAN MATN
    text = (
        f"🚨 <b>YANGI SHIKOYAT KELDI</b> 🚨\n\n"
        f"<b>Kategoriya:</b> <u>{cleaned_category}</u>\n"
        f"<b>Shikoyat matni:</b>\n"
        f"{cleaned_message_text}\n\n"
        f"--- 👤 YUBORUVCHI MA'LUMOTI ---\n"
        f"<b>Foydalanuvchi:</b> <a href=\"tg://user?id={user_id}\">{html_escape(full_name)}</a>\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Username:</b> {html_escape('@' + username) if username else 'Mavjud emas'}"
    )

    try:
        # Mediani yuborish
        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(ADMIN_CHAT_ID, photo_file_id, caption=text, parse_mode="HTML")
        elif update.message.video:
            video_file_id = update.message.video.file_id
            await context.bot.send_video(ADMIN_CHAT_ID, video_file_id, caption=text, parse_mode="HTML")
        else:
            await context.bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML") 

        # Foydalanuvchiga tasdiqlash xabari
        markup = create_main_menu_keyboard()
        await update.message.reply_text(
            "✅ Shikoyatingiz yuborildi. Tez orada javob beramiz. Rahmat!", 
            reply_markup=markup
        )
        
    except Exception as e:
        print(f"--- KRITIK XATO (PTB): Adminga yuborishda xato: {e} ---")
        await update.message.reply_text(
            "❌ Uzr, shikoyatni Adminga yuborishda texnik xato yuz berdi. Iltimos, keyinroq urinib ko'ring."
        )

    # Konversiyani yakunlash
    return ConversationHandler.END

async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bekor qilish tugmasi bosilganda ishga tushadi."""
    markup = create_main_menu_keyboard()
    await update.message.reply_text(
        "❌ Amal bekor qilindi.",
        reply_markup=markup
    )
    return ConversationHandler.END

# --- ASOSIY ILK O'RNATISH (SETUP) ---
# Flask serverini ishga tushirish
app = Flask(__name__)
application = Application.builder().token("8549346336:AAFMvd3jU68-1-csiwOMRML0CflfkW114i4").build()

# Konversiya Handlerni sozlash
complaint_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^📨 Shikoyat qilish$"), start_complaint)
    ],
    states={
        SELECT_CATEGORY: [
            MessageHandler(filters.Regex("^(🚫|🏠|👩‍🏫|🧾|🧍‍♂️|🧑‍💼|📑|🧳|💸|📝)"), select_category),
        ],
        ENTER_COMPLAINT: [
            MessageHandler(filters.ALL & ~filters.COMMAND, forward_to_admin),
        ],
    },
    fallbacks=[
        MessageHandler(filters.Regex("^❌ Bekor qilish$"), cancel_action),
        CommandHandler("start", start_command)
    ],
)

# Handlerni qo'shish
application.add_handler(CommandHandler("start", start_command))
application.add_handler(complaint_handler)
application.add_handler(MessageHandler(filters.Regex("^❌ Bekor qilish$"), cancel_action)) # Bekor qilishni barcha bosqichlarda ushlaydi

# --- WEBHOOK QISMI (24/7 ishlash uchun) ---

@app.route(f"/{8549346336:AAFMvd3jU68-1-csiwOMRML0CflfkW114i4}", methods=["POST"])
async def webhook_handler():
    """Telegramdan kelgan xabarni qabul qiladi va PTB ga yuboradi."""
    if request.method == "POST":
        update = Update.de_json(await request.get_json(), application.bot)
        
        # PTB ni Webhook orqali ishga tushirish
        await application.process_update(update)
        
        return "ok", 200
    return "ok", 200

@app.route("/")
def index():
    """Bot serveri ishlayotganini bildirish uchun."""
    return "Bot serveri ishlayapti.", 200

# Webhookni bir marta o'rnatish uchun funksiya (Server ishga tushgandan so'ng Render Logs'da paydo bo'ladi)
async def set_webhook():
    # Render muhiti dinamik URL manzilini talab qiladi.
    # Bu yerda biz avtomatik Webhook o'rnatishni bekor qilamiz va u Render'da joylashganini taxmin qilamiz.
    # Agar bu Renderda ishlamasa, sizning Webhook URL'ingizni qo'lda o'rnatish kerak bo'ladi.
    pass

if __name__ == "__main__":
    # Server portini muhit o'zgaruvchisidan olamiz (Render talabi)
    PORT = int(os.environ.get('PORT', 5000))
    # Flask app ni ishga tushirish
    app.run(host="0.0.0.0", port=PORT)