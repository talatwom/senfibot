import openai
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# AvalAI API Configuration
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "your-default-api-key")
AVALAI_API_BASE_URL = os.getenv("AVALAI_API_BASE_URL", "https://api.avalai.ir/v1")

# Configure OpenAI with AvalAI API
openai.api_key = AVALAI_API_KEY
openai.api_base = AVALAI_API_BASE_URL

# Create fallback function in case of API errors
def ask_ai_direct(prompt: str) -> str:
    """
    Direct API call to AvalAI/OpenAI as a fallback method
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Direct API call failed: {e}")
        return f"خطا در ارتباط با سرویس هوش مصنوعی. لطفاً بعداً دوباره تلاش کنید."

# Create LangChain model instance
try:
    llm = ChatOpenAI(
        model_name="gpt-4o-mini-2024-07-18",
        openai_api_key=AVALAI_API_KEY,
        openai_api_base=AVALAI_API_BASE_URL
    )
    logger.info("Successfully initialized LangChain with AvalAI")
except Exception as e:
    logger.error(f"Error initializing LangChain: {e}")
    llm = None

def ask_ai(prompt: str) -> str:
    """
    Send a prompt to the AI and get a response with error handling
    """
    if not prompt or len(prompt.strip()) == 0:
        return "پرسش نامعتبر است. لطفاً متن خود را وارد کنید."
        
    try:
        # Try LangChain first
        if llm:
            logger.info("Using LangChain for AI response")
            return llm.predict(prompt)
        else:
            # Fallback to direct API call
            logger.info("Using direct API call for AI response")
            return ask_ai_direct(prompt)
    except Exception as e:
        logger.error(f"Error in ask_ai: {e}")
        # Try fallback method
        try:
            return ask_ai_direct(prompt)
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")
            return "خطا در ارتباط با سرویس هوش مصنوعی. لطفاً بعداً دوباره تلاش کنید."

if __name__ == "__main__":
    # Simple test for the module
    print("Testing AI service...")
    user_prompt = input("لطفاً پرسش خود را وارد کنید: ")
    ai_response = ask_ai(user_prompt)
    print("پاسخ هوش مصنوعی:")
    print(ai_response)