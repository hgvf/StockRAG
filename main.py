import requests
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from query_similar import query_sim


# Define command handlers
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and list available commands."""
    commands = (
        "Usage: <command>\n\n"
        "/help - 指令表\n"
        "/about - 機器人簡介\n"
        "/contact - 聯絡資訊\n"
        "/punish - 查詢今日處置股\n"
        "/warn - 查詢今日警示股\n"
        "/refreshStock - 更新資料庫的標的列表\n"
        "/similar_price <個股代碼> - 以給定標的近期的股價趨勢圖，找尋相關歷史事件\n"
        "/similar_vol <個股代碼> - 以給定標的近期的成交量趨勢圖，找尋相關歷史事件\n"
    )
    await update.message.reply_text(commands)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide bot details."""
    await update.message.reply_text("來幫你賺錢的!")


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide contact details."""
    await update.message.reply_text("聯絡 ->  gwtang@nlp.csie.ntust.edu.tw")


async def punish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查詢處置股"""

    out_str = ""

    resp = requests.post(url="https://openapi.twse.com.tw/v1/announcement/punish")
    for stock in resp.json():
        if stock["Code"] == "":
            break
        out_str += f"{stock['Code']} {stock['Name']} -> {stock['ReasonsOfDisposition']}, {stock['DispositionMeasures']}\n"

    out_str = "無" if out_str == "" else out_str
    await update.message.reply_text(out_str)


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查詢警示股"""

    out_str = ""

    resp = requests.post(url="https://openapi.twse.com.tw/v1/announcement/notice")
    for stock in resp.json():
        if stock["Code"] == "":
            break
        out_str += f"{stock['Code']} {stock['Name']} -> 第{stock['NumberOfAnnouncement']}次警示, PE: {stock['PE']}, {stock['TradingInfoForAttention']}\n"

    out_str = "無" if out_str == "" else out_str
    await update.message.reply_text(out_str)

async def similar_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """以給定標的近期的股價趨勢圖，找尋相關歷史事件"""
    stockID = str(update.message.text.split(" ")[-1])
    out_str = query_sim(stockID, 'price')
    await update.message.reply_text(out_str)

async def similar_vol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """以給定標的近期的成交量趨勢圖，找尋相關歷史事件"""
    stockID = str(update.message.text.split(" ")[-1])
    out_str = query_sim(stockID, 'vol')
    await update.message.reply_text(out_str)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text("公三小")


def main():
    """Run the bot."""
    TOKEN = "7380247567:AAFlYvJtQKQpgjNpAYFmEROijUW9z1bxFuQ"  # Replace with your actual bot token

    # Create application
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("punish", punish))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("similar_vol", similar_vol))
    app.add_handler(CommandHandler("similar_price", similar_price))

    # Handle unknown messages
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
