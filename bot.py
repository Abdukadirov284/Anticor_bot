import requests
import telebot
import os # Server portini olish uchun kerak
from telebot import types
from html import escape as html_escape 
from flask import Flask, request # Webhook uchun kerak

# === TOKEN VA ADMIN ID ===
BOT_TOKEN = "8549346336:AAFMvd3jU68-1-csiwOMRML0CflfkW114i4"
ADMIN_CHAT_ID = 7413228837 

# --- Bot va Flaskni ishga tushirish ---
bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__) # Webhookni boshqaruvchi server

# --- GLOBAL FUNKSIYALAR ---

def create_main_menu_keyboard():
    # Faqat "Shikoyat qilish" tugmasi bo'lgan asosiy menu
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton("📨 Shikoyat qilish")) 
    return markup

def create_complaint_type_keyboard():
    # Shikoyat turlari bo'lgan menu (Reply Keyboard)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    
    options = [
        "🚫 Korrupsiya", "🏠 Yotoqxona muammolari", 
        "👩‍🏫 O‘qituvchi muammosi", "🧾 Imtihon adolatsizligi",
        "🧍‍♂️ Dekan/Fakultet muammosi", "🧑‍💼 Xodimlar bo‘yicha",
        "📑 Hujjatlar muammosi", "🧳 Yotoqxona kirish/chiqarish", 
        "💸 Pora/pul talab qilish", "📝 Boshqa shikoyat"
    ]
    
    # Ikki qatorli joylashtirish
    for i in range(0, len(options), 2):
        row = []
        row.append(types.KeyboardButton(options[i]))
        if i + 1 < len(options):
            row.append(types.KeyboardButton(options[i+1]))
        markup.row(*row)

    # Bekor qilish tugmasini alohida qo'shish
    markup.row(types.KeyboardButton("❌ Bekor qilish"))
    return markup

# --- 1. START FUNKSIYASI ---
@bot.message_handler(commands=["start"])
def start(message):
    markup = create_main_menu_keyboard()
    
    bot.send_message(message.chat.id,
                     "Assalomu alaykum!\nQuyidagilardan birini tanlang:",
                     reply_markup=markup)


# 2. --- ASOSIY MENYU TUGMALARI HANDLERI ---

# Shikoyat qilish tugmasi bosilganda
@bot.message_handler(func=lambda message: message.text == "📨 Shikoyat qilish")
def show_complaint_menu(message):
    markup = create_complaint_type_keyboard()
    
    bot.send_message(message.chat.id, 
                     "📨 Shikoyat turini tanlang:",
                     reply_markup=markup)

# Bekor qilish tugmasi bosilganda
@bot.message_handler(func=lambda message: message.text == "❌ Bekor qilish")
def cancel_action_reply(message):
    # Reply Keyboardni olib tashlab, asosiy menyuni chiqarish
    markup = create_main_menu_keyboard()
    
    bot.send_message(message.chat.id, 
                     "❌ Amal bekor qilindi.",
                     reply_markup=markup)

# 3. --- SHIKOYAT TURLARI HANDLERI ---

# Barcha shikoyat turlari uchun umumiy handler
@bot.message_handler(func=lambda message: message.text in [
    "🚫 Korrupsiya", "🏠 Yotoqxona muammolari", 
    "👩‍🏫 O‘qituvchi muammosi", "🧾 Imtihon adolatsizligi",
    "🧍‍♂️ Dekan/Fakultet muammosi", "🧑‍💼 Xodimlar bo‘yicha",
    "📑 Hujjatlar muammosi", "🧳 Yotoqxona kirish/chiqarish", 
    "💸 Pora/pul talab qilish", "📝 Boshqa shikoyat"
])
def ask_text_reply(message):
    # message.text bu yerda bizning kategoriyamiz bo'ladi (masalan, "🚫 Korrupsiya")
    category = message.text
    
    # Oldingi Reply Keyboardni olib tashlab, foydalanuvchiga yozishni so'rash
    hide_markup = types.ReplyKeyboardRemove(selective=False)
    
    msg = bot.send_message(
        message.chat.id,
        "✍️ Shikoyatingizni yozing.\n\n"
        "📷 Rasm: 5 MB dan oshmasin\n"
        "🎥 Video: 1 daqiqadan oshmasin",
        reply_markup=hide_markup # Klaviatura vaqtincha yo'qoladi
    )
    
    # Endi next_step_handlerga category matnini o'tkazamiz
    bot.register_next_step_handler(msg, forward_to_admin, category)


# --- SEND TO ADMIN FUNKSIYASI ---
def forward_to_admin(message, category):
    # Agar foydalanuvchi buyruq yuborsa, shikoyat jarayonini to'xtatish
    if message.text and message.text.startswith('/'):
        bot.reply_to(message, "Iltimos, avval shikoyatingizni yozib tugating yoki /start buyrug'ini qaytadan yuboring.")
        return

    # User ma'lumotlari
    user_id = message.from_user.id
    username = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name if message.from_user.last_name else ""
    full_name = f"{user_first_name} {user_last_name}".strip()

    message_text_raw = message.text if message.text else "Tekst mavjud emas (media)"
    
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


    # Mediani yuborish logikasi
    try:
        if message.photo:
            bot.send_photo(ADMIN_CHAT_ID, 
                           message.photo[-1].file_id, 
                           caption=text, 
                           parse_mode="HTML")
        elif message.video:
            bot.send_video(ADMIN_CHAT_ID, 
                           message.video.file_id, 
                           caption=text, 
                           parse_mode="HTML")
        else:
            bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML") 
    except Exception as e:
        # Admin xatosi haqida ma'lumot (masalan, chat topilmadi)
        print(f"Adminga xabar yuborishda xatolik: {e}")
        bot.reply_to(message, "❌ Uzr, shikoyatni Adminga yuborishda texnik xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")
        return

    # Foydalanuvchiga tasdiqlash xabari va asosiy menyuni qaytarish
    markup = create_main_menu_keyboard()
    bot.reply_to(message, "✅ Shikoyatingiz yuborildi. Tez orada javob beramiz Rahmat!", reply_markup=markup)


# --- WEBHOOK QISMI (24/7 ishlash uchun) ---

@server.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    """Telegramdan kelgan xabarni qabul qiladi va uni botga yuboradi."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403

@server.route("/")
def webhook_set():
    """Serverni ishga tushirishda Webhookni o'rnatish uchun funksiya."""
    # Webhook manzili (Bu joylashtirganingizdan keyin o'zgaradi, masalan Render/Heroku URL'i)
    # Siz uni qo'lda o'zgartirishingiz shart emas, chunki hosting muhiti o'zi o'rnatadi.
    # Agar test qilmoqchi bo'lsangiz, WEBHOOK_URL o'rniga Ngrok manzilingizni qo'yishingiz mumkin.
    
    # Biz shunchaki server ishlayotganini bildirish uchun 200 kodini qaytaramiz.
    return "Bot serveri ishlayapti.", 200


if __name__ == "__main__":
    # Server portini muhit o'zgaruvchisidan olamiz (Render/Heroku talabi)
    PORT = int(os.environ.get('PORT', 5000))
    # Bu joyda Webhook URL ni o'rnatish uchun alohida so'rov jo'natish kerak bo'ladi.
    # Bepul hostingda uni joylashtirgandan so'ng, brauzerda bir marta / so'rovini yuborishingiz kerak.
    # Masalan: https://your-app-name.onrender.com/
    
    print(f"Flask serveri {PORT} portida ishga tushdi...")
    server.run(host="0.0.0.0", port=PORT)