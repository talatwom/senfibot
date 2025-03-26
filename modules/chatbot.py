# modules/chatbot.py
from flask import request, jsonify, session
from langchain_openai import ChatOpenAI
import openai
from dotenv import load_dotenv
from datetime import datetime
import json
import re
import pytz
import shutil


# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات AvalAI API
AVALAI_API_KEY = "aa-OIK6fjtJytf8zV5lcsdge2OefR38jQF8INNtNbs120am3fm6"
AVALAI_API_BASE_URL = "https://api.avalai.ir/v1"

openai.api_key = AVALAI_API_KEY
openai.api_base = AVALAI_API_BASE_URL

# تنظیمات LangChain برای AvalAI
llm = ChatOpenAI(
    model_name="gpt-4o-mini-2024-07-18",  # نام مدل AvalAI
    openai_api_key=AVALAI_API_KEY,
    openai_api_base=AVALAI_API_BASE_URL
)

# کلاس برای مدیریت تاریخچه گفتگو
class ConversationManager:
    def __init__(self):
        self.conversations = {}

    def get_conversation(self, user_id):
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]

    def add_message(self, user_id, role, content):
        conversation = self.get_conversation(user_id)
        conversation.append({"role": role, "content": content})
        # نگهداری حداکثر 10 پیام آخر برای مدیریت حافظه
        if len(conversation) > 10:
            conversation.pop(0)

    def get_context(self, user_id):
        return self.get_conversation(user_id)

# ایجاد نمونه از مدیریت کننده گفتگو
conversation_manager = ConversationManager()

def get_shoray_senfi_response(text, user_id):
    # دریافت تاریخچه گفتگو
    conversation_history = conversation_manager.get_context(user_id)
    
    # ساخت زمینه‌ی گفتگو
    conversation_context = "\n".join([
        f"{'کاربر' if msg['role'] == 'user' else 'دستیار'}: {msg['content']}"
        for msg in conversation_history
    ])

    # خواندن محتوای آیین‌نامه شورای صنفی
    try:
        with open('data/shoray_senfi_data.txt', 'r', encoding='utf-8') as file:
            shoray_senfi_content = file.read()
    except FileNotFoundError:
        shoray_senfi_content = "متأسفانه فایل آیین‌نامه شورای صنفی یافت نشد."

    # پرامپت بهبود یافته
    prompt = f"""
    شما یک مشاور حقوقی متخصص در زمینه آیین‌نامه شورای صنفی دانشگاه اصفهان هستید و وظیفه شما پاسخ دقیق به سوالات است.


    [تاریخچه گفتگو]
    {conversation_context}

    [متن کامل آیین‌نامه شورای صنفی دانشگاه اصفهان]
    {shoray_senfi_content}

    سوال دانشجو: {text}

    پاسخ دقیق، مستند و کاربردی شما:
    """

    response = llm.predict(prompt)
    
    # ذخیره پیام‌های جدید
    conversation_manager.add_message(user_id, "user", text)
    conversation_manager.add_message(user_id, "assistant", response)

    return response


# پردازش درخواست‌های کاربر در چت‌بات
def ask_chatbot(user_input, user_id=None):
    if user_id is None:
        user_id = "default_user"  # در حالت واقعی باید از سیستم احراز هویت دریافت شود
    
    response = get_shoray_senfi_response(user_input, user_id)
    return response