import os
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
import ai_config
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "86551786"))

logger.info(f"Bot starting with TOKEN: {TOKEN[:5]}...{TOKEN[-5:] if TOKEN else None}")
logger.info(f"Admin user ID: {ADMIN_USER_ID}")

# File paths
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
REPORTS_FILE = "reports.json"

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# User states
WAITING_FOR_PASSKEY = "waiting_for_passkey"
WAITING_FOR_REPORT = "waiting_for_report"
WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
NORMAL_MODE = "normal_mode"

# Menu buttons
MENU_KEYBOARD = [
    ["ارسال گزارش/نامه", "راهنما"],
    ["آرشیو", "ارتباط با مدیر"]
]

# Default passkeys (should be changed in production)
DEFAULT_PASSKEYS = {
    "admin": "admin123",
    "user1": "user123"
}

# Load users from file
def load_users():
    try:
        if not os.path.exists(USERS_FILE):
            logger.warning(f"Users file not found: {USERS_FILE}")
            users = {
                str(ADMIN_USER_ID): {
                    "role": "admin",
                    "passkey": DEFAULT_PASSKEYS["admin"],
                    "failed_attempts": 0,
                    "is_authenticated": False
                }
            }
            save_users(users)
            return users
            
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading users: {e}")
        # Create initial file with admin user
        users = {
            str(ADMIN_USER_ID): {
                "role": "admin",
                "passkey": DEFAULT_PASSKEYS["admin"],
                "failed_attempts": 0,
                "is_authenticated": False
            }
        }
        save_users(users)
        return users

# Save users to file
def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

# Log event
def log_event(user_id, event_type, details=None):
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logger.warning(f"Logs file not found: {LOGS_FILE}")
            logs = []
        
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "event_type": event_type,
            "details": details
        })
        
        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error logging event: {e}")

# Save report
def save_report(user_id, original_text, ai_response):
    try:
        if os.path.exists(REPORTS_FILE):
            with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                reports = json.load(f)
        else:
            logger.warning(f"Reports file not found: {REPORTS_FILE}")
            reports = []
        
        report_id = len(reports) + 1
        reports.append({
            "id": report_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "original_text": original_text,
            "ai_response": ai_response
        })
        
        with open(REPORTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=4)
        
        return report_id
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        return 0

# Create Word document with report content
def create_docx(report_content, report_id):
    try:
        doc = docx.Document()
        
        # Add header
        header = doc.add_paragraph()
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_run = header.add_run("شورای صنفی دانشگاه اصفهان")
        header_run.bold = True
        header_run.font.size = Pt(16)
        
        # Add date
        date_paragraph = doc.add_paragraph()
        date_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        date_paragraph.add_run(f"تاریخ: {datetime.now().strftime('%Y/%m/%d')}")
        
        # Add report number
        id_paragraph = doc.add_paragraph()
        id_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        id_paragraph.add_run(f"شماره گزارش: {report_id}")
        
        # Add separator
        doc.add_paragraph("_" * 50)
        
        # Add report content
        content_paragraph = doc.add_paragraph()
        content_paragraph.add_run(report_content)
        
        # Add signature
        signature = doc.add_paragraph()
        signature.alignment = WD_ALIGN_PARAGRAPH.LEFT
        signature.add_run("\n\nبا احترام\nشورای صنفی دانشگاه اصفهان")
        
        # Save to BytesIO
        f = BytesIO()
        doc.save(f)
        f.seek(0)
        return f
    except Exception as e:
        logger.error(f"Error creating DOCX: {e}")
        return None

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    
    logger.info(f"User {user_id} started the bot")
    
    # Check user authentication
    if user_id in users and users[user_id].get("is_authenticated", False):
        # User is already authenticated
        await show_menu(update, context)
    else:
        # User needs authentication
        context.user_data["state"] = WAITING_FOR_PASSKEY
        await update.message.reply_text(
            "به ربات شورای صنفی دانشگاه اصفهان خوش آمدید.\n"
            "لطفاً پس‌کی خود را وارد کنید:"
        )
    
    # Log bot start
    log_event(user_id, "start_bot")

# Show main menu
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = NORMAL_MODE
    await update.message.reply_text(
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    )

# Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        text = update.message.text
        state = context.user_data.get("state", WAITING_FOR_PASSKEY)
        users = load_users()
        
        logger.info(f"Received message from user {user_id} in state {state}")
        
        # Process based on user state
        if state == WAITING_FOR_PASSKEY:
            # Check passkey validity
            is_valid = False
            for role, passkey in DEFAULT_PASSKEYS.items():
                if text == passkey:
                    is_valid = True
                    user_role = role
                    break
            
            if is_valid:
                # Valid passkey
                if user_id not in users:
                    users[user_id] = {
                        "role": "user" if user_role != "admin" else "admin",
                        "passkey": text,
                        "failed_attempts": 0,
                        "is_authenticated": True
                    }
                else:
                    users[user_id]["is_authenticated"] = True
                    users[user_id]["failed_attempts"] = 0
                
                save_users(users)
                log_event(user_id, "login_success")
                
                await update.message.reply_text("ورود موفقیت‌آمیز!")
                await show_menu(update, context)
            else:
                # Invalid passkey
                if user_id in users:
                    users[user_id]["failed_attempts"] = users[user_id].get("failed_attempts", 0) + 1
                    save_users(users)
                
                log_event(user_id, "login_failed")
                
                await update.message.reply_text(
                    "پس‌کی نامعتبر است. لطفاً دوباره تلاش کنید:"
                )
        
        elif state == WAITING_FOR_REPORT:
            # Receive report from user
            try:
                # Add guidance message to user's text for ChatGPT
                prompt = f"""
                لطفاً متن زیر را به یک گزارش یا نامه رسمی برای شورای صنفی دانشگاه اصفهان تبدیل کنید. 
                متن را کامل، مرتب و با رعایت اصول نگارش رسمی بازنویسی کنید.
                
                متن کاربر:
                {text}
                """
                
                logger.info(f"Sending prompt to AI service for user {user_id}")
                await update.message.reply_text("در حال پردازش پیش‌نویس... لطفاً صبر کنید.")
                
                # Send to ChatGPT
                ai_response = ai_config.ask_ai(prompt)
                
                if not ai_response or ai_response.strip() == "":
                    raise Exception("AI returned empty response")
                
                # Save report
                report_id = save_report(user_id, text, ai_response)
                
                # Save report in context for later use
                context.user_data["current_report"] = ai_response
                context.user_data["report_id"] = report_id
                
                # Create confirmation buttons
                keyboard = [
                    [InlineKeyboardButton("تایید پیش‌نویس", callback_data="confirm")],
                    [InlineKeyboardButton("ویرایش متن", callback_data="edit")]
                ]
                
                # Show draft to user
                await update.message.reply_text(
                    f"پیش‌نویس شما آماده شد:\n\n{ai_response}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # Change user state
                context.user_data["state"] = WAITING_FOR_CONFIRMATION
                log_event(user_id, "draft_generated")
                
            except Exception as e:
                # Error in AI communication
                logger.error(f"Error generating AI response: {e}")
                log_event(user_id, "ai_error", str(e))
                await update.message.reply_text(
                    "متأسفانه در پردازش درخواست شما خطایی رخ داده است. لطفاً دوباره تلاش کنید."
                )
                await show_menu(update, context)
        
        elif state == NORMAL_MODE:
            # Process menu options
            if text == "ارسال گزارش/نامه":
                context.user_data["state"] = WAITING_FOR_REPORT
                await update.message.reply_text(
                    "لطفاً متن اولیه گزارش یا نامه خود را وارد کنید:"
                )
            elif text == "راهنما":
                await show_help(update, context)
            elif text == "آرشیو":
                await show_archive(update, context)
            elif text == "ارتباط با مدیر":
                await contact_admin(update, context)
            else:
                await update.message.reply_text(
                    "دستور نامعتبر. لطفاً از منوی موجود استفاده کنید."
                )
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
        await show_menu(update, context)

# Handle inline button callbacks
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Callback from user {user_id}: {query.data}")
        
        if query.data == "confirm":
            # Confirm draft
            report_content = context.user_data.get("current_report", "")
            report_id = context.user_data.get("report_id", 0)
            
            # Create Word document
            docx_file = create_docx(report_content, report_id)
            
            if docx_file:
                # Send file to user
                await query.message.reply_document(
                    document=docx_file,
                    filename=f"report_{report_id}.docx",
                    caption="فایل گزارش شما آماده شد."
                )
                
                log_event(user_id, "report_confirmed", {"report_id": report_id})
            else:
                await query.message.reply_text("خطا در ایجاد فایل گزارش. لطفاً دوباره تلاش کنید.")
            
            await show_menu(update, context)
        
        elif query.data == "edit":
            # Edit text
            context.user_data["state"] = WAITING_FOR_REPORT
            await query.message.reply_text(
                "لطفاً متن جدید خود را وارد کنید:"
            )
        elif query.data.startswith("get_report_"):
            # Get report by ID
            report_id = int(query.data.split("_")[-1])
            await get_report(update, context, report_id)
    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        await query.message.reply_text("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
        await show_menu(update, context)

# Get report by ID
async def get_report(update: Update, context: ContextTypes.DEFAULT_TYPE, report_id):
    user_id = str(update.effective_user.id)
    
    try:
        # Read reports
        with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
            reports = json.load(f)
        
        # Find report
        report = next((r for r in reports if r["id"] == report_id and r["user_id"] == user_id), None)
        
        if report:
            # Create Word document
            docx_file = create_docx(report["ai_response"], report_id)
            
            if docx_file:
                # Send file to user
                await update.callback_query.message.reply_document(
                    document=docx_file,
                    filename=f"report_{report_id}.docx",
                    caption=f"گزارش شماره {report_id}"
                )
            else:
                await update.callback_query.message.reply_text("خطا در ایجاد فایل گزارش. لطفاً دوباره تلاش کنید.")
        else:
            await update.callback_query.message.reply_text("گزارش مورد نظر یافت نشد.")
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        await update.callback_query.message.reply_text("خطا در بازیابی گزارش. لطفاً دوباره تلاش کنید.")

# Show help
async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🔰 راهنمای استفاده از ربات شورای صنفی 🔰

- برای ارسال گزارش یا نامه، گزینه "ارسال گزارش/نامه" را انتخاب کنید.
- پس از وارد کردن متن اولیه، پیش‌نویس توسط هوش مصنوعی تکمیل می‌شود.
- در صورت تایید پیش‌نویس، فایل Word نهایی برای شما ارسال می‌شود.
- برای مشاهده گزارش‌های قبلی، گزینه "آرشیو" را انتخاب کنید.
- برای ارتباط با مدیر، گزینه "ارتباط با مدیر" را انتخاب کنید.

🔑 توجه: لطفاً پس‌کی خود را در اختیار دیگران قرار ندهید.
"""
    await update.message.reply_text(help_text)

# Show archive
async def show_archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    try:
        if os.path.exists(REPORTS_FILE):
            with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                reports = json.load(f)
        else:
            reports = []
            logger.warning(f"Reports file not found: {REPORTS_FILE}")
        
        # Filter reports for current user
        user_reports = [r for r in reports if r["user_id"] == user_id]
        
        if not user_reports:
            await update.message.reply_text("شما هنوز گزارشی ثبت نکرده‌اید.")
            return
        
        # Show 5 most recent reports
        recent_reports = sorted(user_reports, key=lambda x: x["id"], reverse=True)[:5]
        response = "گزارش‌های اخیر شما:\n\n"
        
        for report in recent_reports:
            try:
                date = datetime.fromisoformat(report["timestamp"]).strftime("%Y/%m/%d")
            except (ValueError, KeyError):
                date = "نامشخص"
                
            report_brief = report.get("ai_response", "")[:50] + "..." if len(report.get("ai_response", "")) > 50 else report.get("ai_response", "")
            response += f"📄 شناسه گزارش: {report['id']}\n"
            response += f"📅 تاریخ: {date}\n"
            response += f"📝 خلاصه: {report_brief}\n\n"
        
        # Create archive buttons
        buttons = []
        for report in recent_reports:
            buttons.append([InlineKeyboardButton(f"دریافت گزارش {report['id']}", callback_data=f"get_report_{report['id']}")])
        
        await update.message.reply_text(
            response,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    except Exception as e:
        logger.error(f"Error showing archive: {e}")
        await update.message.reply_text("خطا در نمایش آرشیو. لطفاً دوباره تلاش کنید.")

# Contact admin
async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "برای ارتباط با مدیر، لطفاً پیام خود را با /admin شروع کنید. مثال:\n"
        "/admin سلام، یک سوال داشتم..."
    )

# Send message to admin
async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Remove /admin from the beginning of message
    if len(update.message.text) <= 7:
        await update.message.reply_text("لطفاً پیام خود را پس از دستور /admin وارد کنید.")
        return
        
    message = update.message.text[7:]
    
    # Send message to admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"پیام جدید از کاربر {user_name} (ID: {user_id}):\n\n{message}"
        )
        await update.message.reply_text("پیام شما با موفقیت به مدیر ارسال شد.")
    except Exception as e:
        logger.error(f"Error sending message to admin: {e}")
        await update.message.reply_text("خطا در ارسال پیام به مدیر. لطفاً دوباره تلاش کنید.")

# Admin reply to user
# Admin reply to user
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check if sender is admin
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("شما دسترسی به این دستور را ندارید.")
        return
    
    # Format: /reply ID MESSAGE
    try:
        command_parts = update.message.text.split(" ", 2)
        if len(command_parts) < 3:
            await update.message.reply_text("فرمت صحیح: /reply شناسه_کاربر پیام")
            return
            
        target_user_id = command_parts[1]
        message = command_parts[2]
        
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"پاسخ از مدیر:\n\n{message}"
        )
        await update.message.reply_text(f"پاسخ شما به کاربر {target_user_id} ارسال شد.")
    except Exception as e:
        logger.error(f"Error in admin reply: {e}")
        await update.message.reply_text("خطا در ارسال پاسخ. لطفاً دستور را به شکل صحیح وارد کنید:\n/reply ID MESSAGE")

# Statistics command (admin only)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check if sender is admin
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("شما دسترسی به این دستور را ندارید.")
        return
    
    try:
        # User statistics
        users = load_users()
        active_users = sum(1 for u in users.values() if u.get("is_authenticated", False))
        
        # Report statistics
        try:
            if os.path.exists(REPORTS_FILE):
                with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                    reports = json.load(f)
                total_reports = len(reports)
            else:
                total_reports = 0
        except (FileNotFoundError, json.JSONDecodeError):
            total_reports = 0
        
        # Log statistics
        try:
            if os.path.exists(LOGS_FILE):
                with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                total_logs = len(logs)
                login_failures = sum(1 for log in logs if log.get("event_type") == "login_failed")
                ai_errors = sum(1 for log in logs if log.get("event_type") == "ai_error")
            else:
                total_logs = 0
                login_failures = 0
                ai_errors = 0
        except (FileNotFoundError, json.JSONDecodeError):
            total_logs = 0
            login_failures = 0
            ai_errors = 0
        
        stats_text = f"""📊 آمار سیستم:

👥 تعداد کل کاربران: {len(users)}
✅ کاربران فعال: {active_users}

📝 گزارش‌های ثبت شده: {total_reports}

🔑 تلاش‌های ناموفق ورود: {login_failures}
⚠️ خطاهای هوش مصنوعی: {ai_errors}
📜 کل رویدادهای ثبت شده: {total_logs}
"""
        await update.message.reply_text(stats_text)
    
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        await update.message.reply_text("خطا در تولید آمار. لطفاً دوباره تلاش کنید.")

def main():
    try:
        # Create and configure application
        logger.info("Creating application...")
        application = Application.builder().token(TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", show_help))
        application.add_handler(CommandHandler("admin", send_to_admin))
        application.add_handler(CommandHandler("reply", admin_reply))
        application.add_handler(CommandHandler("stats", stats))
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start bot
        logger.info("Starting bot...")
        application.run_polling()
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")

if __name__ == "__main__":
    main()