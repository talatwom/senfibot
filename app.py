import os
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Initialize Flask app
app = Flask(__name__)

# Initialize bot with your token
BOT_TOKEN = '7595888832:AAGHkNqZcQZ4RDn5ww7vtYMPpNdiXmOpg7c'
bot = telebot.TeleBot(BOT_TOKEN)

# Welcome message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    welcome_text = f"سلام {user_first_name}، به بات سنفی خوش آمدید!"
    
    # Create inline keyboard for menu
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("منوی اصلی", callback_data="main_menu"),
        InlineKeyboardButton("درباره ما", callback_data="about")
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# Help command
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
دستورات قابل استفاده:
/start - شروع مجدد بات
/help - نمایش این راهنما
/menu - نمایش منوی اصلی
    """
    bot.send_message(message.chat.id, help_text)

# Menu command
@bot.message_handler(commands=['menu'])
def show_menu(message):
    menu_text = "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    
    # Create reply keyboard with buttons
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("خدمات"), KeyboardButton("محصولات"))
    markup.add(KeyboardButton("تماس با ما"), KeyboardButton("سوالات متداول"))
    
    bot.send_message(message.chat.id, menu_text, reply_markup=markup)

# Handle inline button callbacks
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "main_menu":
        menu_text = "منوی اصلی:"
        
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("خدمات", callback_data="services"),
            InlineKeyboardButton("محصولات", callback_data="products"),
            InlineKeyboardButton("تماس با ما", callback_data="contact"),
            InlineKeyboardButton("سوالات متداول", callback_data="faq")
        )
        
        bot.edit_message_text(chat_id=call.message.chat.id, 
                             message_id=call.message.message_id,
                             text=menu_text, 
                             reply_markup=markup)
        
    elif call.data == "about":
        about_text = "بات سنفی برای ارائه خدمات و پشتیبانی به کاربران طراحی شده است."
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("بازگشت به منو", callback_data="main_menu"))
        
        bot.edit_message_text(chat_id=call.message.chat.id, 
                             message_id=call.message.message_id,
                             text=about_text, 
                             reply_markup=markup)
    
    elif call.data == "services":
        services_text = "خدمات ما شامل موارد زیر است:\n- مشاوره\n- طراحی\n- پشتیبانی\n- آموزش"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("بازگشت به منو", callback_data="main_menu"))
        
        bot.edit_message_text(chat_id=call.message.chat.id, 
                             message_id=call.message.message_id,
                             text=services_text, 
                             reply_markup=markup)
                             
    elif call.data == "products":
        products_text = "محصولات ما:\n- محصول ۱\n- محصول ۲\n- محصول ۳"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("بازگشت به منو", callback_data="main_menu"))
        
        bot.edit_message_text(chat_id=call.message.chat.id, 
                             message_id=call.message.message_id,
                             text=products_text, 
                             reply_markup=markup)
                             
    elif call.data == "contact":
        contact_text = "برای تماس با ما:\nایمیل: info@senfi.com\nتلفن: 021-12345678"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("بازگشت به منو", callback_data="main_menu"))
        
        bot.edit_message_text(chat_id=call.message.chat.id, 
                             message_id=call.message.message_id,
                             text=contact_text, 
                             reply_markup=markup)
                             
    elif call.data == "faq":
        faq_text = "سوالات متداول:\n\nس: چگونه سفارش دهم؟\nج: از طریق منوی محصولات\n\nس: زمان پاسخگویی چقدر است؟\nج: حداکثر 24 ساعت"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("بازگشت به منو", callback_data="main_menu"))
        
        bot.edit_message_text(chat_id=call.message.chat.id, 
                             message_id=call.message.message_id,
                             text=faq_text, 
                             reply_markup=markup)

# Handle text messages
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    
    if text == "خدمات":
        services_text = "خدمات ما شامل موارد زیر است:\n- مشاوره\n- طراحی\n- پشتیبانی\n- آموزش"
        bot.send_message(message.chat.id, services_text)
        
    elif text == "محصولات":
        products_text = "محصولات ما:\n- محصول ۱\n- محصول ۲\n- محصول ۳"
        bot.send_message(message.chat.id, products_text)
        
    elif text == "تماس با ما":
        contact_text = "برای تماس با ما:\nایمیل: info@senfi.com\nتلفن: 021-12345678"
        bot.send_message(message.chat.id, contact_text)
        
    elif text == "سوالات متداول":
        faq_text = "سوالات متداول:\n\nس: چگونه سفارش دهم؟\nج: از طریق منوی محصولات\n\nس: زمان پاسخگویی چقدر است؟\nج: حداکثر 24 ساعت"
        bot.send_message(message.chat.id, faq_text)
        
    else:
        bot.send_message(message.chat.id, f"پیام شما: {text}\n\nبرای دیدن منوی اصلی، دستور /menu را وارد کنید.")

# Set up webhook for Flask
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/')
def home():
    return 'Bot is running!'

# Set webhook route for deployment
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    url = request.args.get('url', '')
    if url:
        bot.remove_webhook()
        bot.set_webhook(url + '/' + BOT_TOKEN)
        return f'Webhook set to {url}'
    return 'Please provide a URL parameter'

# Poll mode for local testing
def polling_mode():
    bot.remove_webhook()
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # For local testing, use polling_mode()
    # For deployment on hosting services, use the webhook setup
    
    if os.environ.get('WEBHOOK_URL'):
        # Webhook mode for production
        webhook_url = os.environ.get('WEBHOOK_URL')
        bot.remove_webhook()
        bot.set_webhook(webhook_url + '/' + BOT_TOKEN)
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Polling mode for local development
        import threading
        threading.Thread(target=polling_mode).start()
        app.run(debug=True, host='0.0.0.0', port=5000)