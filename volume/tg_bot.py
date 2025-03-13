from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and list available commands."""
    commands = (
        "Hello! I'm your bot. Here are some commands you can use:\n"
        "/help - Show help menu\n"
        "/about - Learn more about this bot\n"
        "/contact - Get contact information\n"
    )
    await update.message.reply_text(commands)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    await update.message.reply_text("This bot helps you get information. Use /about to learn more!")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide bot details."""
    await update.message.reply_text("來幫你賺錢的")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide contact details."""
    await update.message.reply_text("聯絡 ->  gwtang@nlp.csie.ntust.edu.tw")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text("???喔喔喔")

def main():
    """Run the bot."""
    TOKEN = "7380247567:AAFlYvJtQKQpgjNpAYFmEROijUW9z1bxFuQ"  # Replace with your actual bot token

    # Create application
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("contact", contact))

    # Handle unknown messages
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
