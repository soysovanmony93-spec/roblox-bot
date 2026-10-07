import os
import sqlite3
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Web Server សម្រាប់ Render Web Service
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

TOKEN = os.getenv("BOT_TOKEN")

# Telegram Admin ID
ADMIN_ID = 873482655

def init_db():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            credentials TEXT,
            status TEXT DEFAULT 'available'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # តម្លៃលំនាំដើម និងព័ត៌មាន Detail
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price', '1.50')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('detail', 'គណនីថ្មី (13+) មាន Voice Chat ស្រាប់')")
    
    # លុប Account Demo ចាស់ៗចោលស្វ័យប្រវត្តិ
    c.execute("DELETE FROM accounts WHERE credentials LIKE '%RobloxUser%'")
    conn.commit()
    conn.close()

init_db()

def get_setting(key, default=""):
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_setting("price", "1.50")
    detail = get_setting("detail", "គណនីថ្មី (13+) មាន Voice Chat ស្រាប់")

    keyboard = [
        [InlineKeyboardButton(f"🛒 ទិញ Account Roblox VC (${price})", callback_data="buy_vc")],
        [InlineKeyboardButton("📦 ពិនិត្យចំនួនស្តុក", callback_data="check_stock")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "👋 **សួស្តី! សូមស្វាគមន៍មកកាន់ហាង Roblox VC**\n\n"
        f"✨ {detail}\n"
        f"💵 តម្លៃ៖ ${price} / 1 Account\n\n"
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

# --- មុខងារ ADMIN សម្រាប់អ្នកគ្រប់គ្រង ---
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    creds = " ".join(context.args)
    if not creds:
        await update.message.reply_text("⚠️ របៀបប្រើ៖ `/add User:xxx | Pass:xxx`", parse_mode="Markdown")
        return

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("INSERT INTO accounts (title, credentials) VALUES (?, ?)", ("Roblox VC", creds))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ បានបញ្ចូល Account ចូលស្តុកជោគជ័យ:\n`{creds}`", parse_mode="Markdown")

async def clear_stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("DELETE FROM accounts")
    conn.commit()
    conn.close()

    await update.message.reply_text("🗑️ បានលុប Stock ទាំងអស់ចោលស្អាតហើយ! (ស្តុកបច្ចុប្បន្ន = 0)")

async def set_price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("⚠️ របៀបប្រើ៖ `/setprice 2.00`", parse_mode="Markdown")
        return

    new_price = context.args[0]
    set_setting("price", new_price)
    await update.message.reply_text(f"✅ តម្លៃត្រូវបានប្តូរទៅជា៖ **${new_price}**", parse_mode="Markdown")

async def set_detail_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    new_detail = " ".join(context.args)
    if not new_detail:
        await update.message.reply_text("⚠️ របៀបប្រើ៖ `/setdetail ព័ត៌មានលម្អិតថ្មី...`", parse_mode="Markdown")
        return

    set_setting("detail", new_detail)
    await update.message.reply_text(f"✅ Detail ត្រូវបានកែប្រែទៅជា៖\n{new_detail}")

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_account))
    app.add_handler(CommandHandler("clearstock", clear_stock_cmd))
    app.add_handler(CommandHandler("setprice", set_price_cmd))
    app.add_handler(CommandHandler("setdetail", set_detail_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
