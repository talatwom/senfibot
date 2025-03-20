import openai
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# بارگذاری متغیرهای محیطی از فایل .env (در صورت وجود)
load_dotenv()

# تنظیمات API AvalAI
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "your-default-api-key")
AVALAI_API_BASE_URL = os.getenv("AVALAI_API_BASE_URL", "https://api.avalai.ir/v1")

# تنظیمات OpenAI با استفاده از AvalAI API
openai.api_key = AVALAI_API_KEY
openai.api_base = AVALAI_API_BASE_URL

# ایجاد نمونه‌ای از مدل زبانی با استفاده از LangChain
llm = ChatOpenAI(
    model_name="gpt-4o-mini-2024-07-18",  # نام مدل مورد استفاده
    openai_api_key=AVALAI_API_KEY,
    openai_api_base=AVALAI_API_BASE_URL
)

def ask_ai(prompt: str) -> str:
    """
    تابعی جهت ارسال پرسش به هوش مصنوعی و دریافت پاسخ
    """
    return llm.predict(prompt)

if __name__ == "__main__":
    user_prompt = input("لطفاً پرسش خود را وارد کنید: ")
    ai_response = ask_ai(user_prompt)
    print("پاسخ هوش مصنوعی:")
    print(ai_response)