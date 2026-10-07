import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

def init_db():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price REAL,
            credentials TEXT,
            status TEXT DEFAULT 'available'
        )
    ''')
    c.execute("SELECT COUNT(*) FROM accounts")
    if c.fetchone()[0] == 0:
        # គណនីគំរូសាកល្បង
        c.execute("INSERT INTO accounts (title, price, credentials) VALUES (?, ?, ?)",
                  ("Roblox VC (New)", 1.50, "User: RobloxUser01 | Pass: Pass12345"))
        c.execute("INSERT INTO accounts (title, price, credentials) VALUES (?, ?, ?)",
                  ("Roblox VC (New)", 1.50, "User: RobloxUser02 | Pass: Pass67890"))
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 ទិញ Account Roblox VC ($1.50)", callback_data="buy_vc")],
        [InlineKeyboardButton("📦 ពិនិត្យចំនួនស្តុក", callback_data="check_stock")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "👋 **សួស្តី! សូមស្វាគមន៍មកកាន់ហាង Roblox VC**\n\n"
        "✨ គណនីថ្មី (13+) មាន Voice Chat ស្រាប់\n"
        "💵 តម្លៃ៖ $1.50 / 1 Account\n\n"
        "សូមជ្រើសរើសជម្រើសខាងក្រោម៖"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_stock":
        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'")
        stock = c.fetchone()[0]
        conn.close()

        back_kb = [[InlineKeyboardButton("🔙 ថយក្រោយ", callback_data="back_home")]]
        await query.edit_message_text(
            f"📦 **ចំនួនស្តុកបច្ចុប្បន្ន:**\n\n• នៅសល់ **{stock}** គណនី",
            reply_markup=InlineKeyboardMarkup(back_kb),
            parse_mode="Markdown"
        )

    elif query.data == "buy_vc":
        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("SELECT id, credentials FROM accounts WHERE status = 'available' LIMIT 1")
        acc = c.fetchone()

        if not acc:
            conn.close()
            back_kb = [[InlineKeyboardButton("🔙 ថយក្រោយ", callback_data="back_home")]]
            await query.edit_message_text("❌ សុំទោស ទំនិញដាច់ស្តុកហើយ!", reply_markup=InlineKeyboardMarkup(back_kb))
            return

        acc_id, creds = acc
        c.execute("UPDATE accounts SET status = 'sold' WHERE id = ?", (acc_id,))
        conn.commit()
        conn.close()

        back_kb = [[InlineKeyboardButton("🔙 ទិញបន្ថែម", callback_data="back_home")]]
        msg = (
            "🎉 **ការទិញបានជោគជ័យ!**\n\n"
            f"🔑 **ព័ត៌មានគណនីរបស់អ្នក:**\n`{creds}`\n\n"
            "⚠️ _សូមប្រញាប់ចូលប្តូរពាក្យសម្ងាត់ និងដាក់ Email ការពារ!_"
        )
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")

    elif query.data == "back_home":
        await start(update, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
