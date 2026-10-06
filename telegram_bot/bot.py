import logging
import os
import random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states for /check
AGE, SYMPTOMS, CONFIRM = range(3)

# Health tips list (derived from project logic)
HEALTH_TIPS = [
    "Maintain a healthy weight. Extra weight puts extra strain on your heart.",
    "Exercise for at least 150 minutes per week. Walking, swimming, or cycling are great options.",
    "Follow a balanced diet. Focus on fruits, vegetables, whole grains, and lean proteins.",
    "Avoid tobacco in all forms. Smoking is a major risk factor for heart disease.",
    "Monitor your blood pressure and cholesterol levels regularly.",
    "Reduce sodium intake to help maintain healthy blood pressure.",
    "Manage stress through techniques like meditation, yoga, or deep breathing exercises.",
    "Get enough quality sleep. 7-9 hours is recommended for most adults.",
    "Stay hydrated. Drink plenty of water throughout the day.",
    "Limit alcohol consumption to moderate levels."
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the user and provides an overview of commands."""
    user = update.effective_user
    welcome_msg = (
        f"Hello {user.first_name}! 👋\n\n"
        "I am your Heart Health Assistant. I can help you with:\n"
        "• /tips - Get daily heart health tips\n"
        "• /check - Basic heart health assessment\n"
        "• /help - See all available commands\n\n"
        "How can I assist you today?"
    )
    await update.message.reply_text(welcome_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all available commands."""
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/tips - Get a random heart health tip\n"
        "/check - Start an interactive health assessment\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

async def tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provides a random heart health tip."""
    tip = random.choice(HEALTH_TIPS)
    await update.message.reply_text(f"💡 *Heart Health Tip:*\n{tip}", parse_mode='Markdown')

# --- Interactive Check Logic ---

async def start_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the basic heart health check conversation."""
    await update.message.reply_text(
        "Let's do a quick heart health assessment. 📝\n"
        "First, what is your age?"
    )
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores age and asks about symptoms."""
    age = update.message.text
    context.user_data['age'] = age
    
    reply_keyboard = [['Yes', 'No']]
    await update.message.reply_text(
        f"Got it. Are you experiencing any symptoms like chest pain, shortness of breath, or palpitations?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SYMPTOMS

async def get_symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores symptoms and provides summary advice."""
    symptoms = update.message.text
    context.user_data['symptoms'] = symptoms
    
    age = context.user_data.get('age', 'Unknown')
    
    if symptoms.lower() == 'yes':
        advice = (
            "⚠️ *Precautionary Advice:*\n"
            "Since you are experiencing symptoms, we strongly recommend consulting a cardiologist for a proper evaluation.\n\n"
            "General advice: Avoid strenuous activity until you speak with a doctor. If you experience severe chest pain, seek emergency medical attention immediately."
        )
    else:
        advice = (
            "✅ *General Advice:*\n"
            "It's good that you aren't experiencing acute symptoms. To maintain heart health at your age:\n"
            "• Keep an active lifestyle.\n"
            "• Monitor your blood pressure regularly.\n"
            "• Maintain a heart-healthy diet."
        )
    
    await update.message.reply_text(
        f"Summary for Age {age}:\n\n{advice}",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Check cancelled. Stay healthy! ❤️",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# --- Main Entry Point ---

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in .env file.")
        return

    application = ApplicationBuilder().token(token).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tips", tips))

    # Conversation handler for /check
    check_handler = ConversationHandler(
        entry_points=[CommandHandler("check", start_check)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            SYMPTOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_symptoms)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(check_handler)

    # General message handler (optional)
    async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("I'm here to help! Try /help to see what I can do.")
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()
