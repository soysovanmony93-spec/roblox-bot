import os
import sqlite3
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# ១. បង្កើត Web Server សម្រាប់ Render Web Service
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    # ទំព័រនេះសម្រាប់ឱ្យ Render ដឹងថា Server នៅរស់រានមានជីវិត ២៤/៧
    return "Roblox Shop Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# ២. កំណត់ Token និង Admin ID
# ==========================================
TOKEN = os.getenv("BOT_TOKEN")

# Telegram User ID របស់អ្នក (មានសិទ្ធិតែ 1 គត់ជា Admin)
ADMIN_ID = 873482655

# ==========================================
# ៣. ប្រព័ន្ធ Database (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    
    # តារាងផ្ទុកគណនី Roblox
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            credentials TEXT,
            status TEXT DEFAULT 'available'
        )
    ''')
    
    # តារាងផ្ទុកតម្លៃ និងព័ត៌មាន Detail
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # តម្លៃដើម និង Detail ដើម
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price', '1.50')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('detail', 'គណនីថ្មី (13+) មាន Voice Chat ស្រាប់')")
    
    # លុប Account Demo ចោលដោយស្វ័យប្រវត្តិ
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

# មុខងារជំនួយ៖ ពិនិត្យមើលថាតើអ្នកផ្ញើសារជា Admin ឬអត់
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ==========================================
# ៤. មុខងារសម្រាប់ USER ទូទៅ
# ==========================================

# បញ្ជា /start
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

# គ្រប់គ្រងប៊ូតុងចុច (Callback Query)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # ប៊ូតុងឆែកស្តុក
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

    # ប៊ូតុងទិញគណនី
    elif query.data == "buy_vc":
        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        # រក Account ដែលនៅទំនេរ
        c.execute("SELECT id, credentials FROM accounts WHERE status = 'available' LIMIT 1")
        acc = c.fetchone()

        if not acc:
            conn.close()
            back_kb = [[InlineKeyboardButton("🔙 ថយក្រោយ", callback_data="back_home")]]
            await query.edit_message_text("❌ សុំទោស ទំនិញដាច់ស្តុកហើយ!", reply_markup=InlineKeyboardMarkup(back_kb))
            return

        acc_id, creds = acc
        # ដកស្តុក auto ដោយប្តូរទៅជា sold
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

# ==========================================
# ៥. មុខងារ ADMIN (USER ធម្មតាមិនអាចប្រើបានដាច់ខាត)
# ==========================================

# ម៉ឺនុយជំនួយសម្រាប់ Admin (/admin)
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ មិនមានសិទ្ធិប្រើប្រាស់ Command នេះឡើយ!")
        return

    admin_text = (
        "🛠 **ផ្ទាំងគ្រប់គ្រង ADMIN (Admin Control Panel)**\n\n"
        "បញ្ជា (Commands) ដែលអ្នកអាចប្រើបាន៖\n"
        "• `/add User:xxx | Pass:xxx` ➡️ បញ្ចូលគណនីថ្មីចូលស្តុក\n"
        "• `/setprice 2.00` ➡️ កែប្រែតម្លៃលក់\n"
        "• `/setdetail ព័ត៌មានថ្មី...` ➡️ កែប្រែការពិពណ៌នា Detail\n"
        "• `/stocklist` ➡️ មើលចំនួនស្តុកទាំងលក់រួច និងនៅសល់\n"
        "• `/clearstock` ➡️ លុបស្តុកចោលទាំងអស់ (Reset មក 0)"
    )
    await update.message.reply_text(admin_text, parse_mode="Markdown")

# បញ្ចូល Account ចូលស្តុក (/add)
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ មិនមានសិទ្ធិប្រើប្រាស់ Command នេះឡើយ!")
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

# មើលរបាយការណ៍ស្តុកលម្អិតសម្រាប់ Admin (/stocklist)
async def stock_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ មិនមានសិទ្ធិប្រើប្រាស់ Command នេះឡើយ!")
        return

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'")
    available = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'sold'")
    sold = c.fetchone()[0]
    conn.close()

    await update.message.reply_text(
        f"📊 **របាយការណ៍ស្តុកបច្ចុប្បន្ន:**\n\n"
        f"• គណនីនៅសល់ក្នុងស្តុក៖ **{available}**\n"
        f"• គណនីដែលបានលក់ចេញរួច៖ **{sold}**\n"
        f"• សរុបទាំងអស់៖ **{available + sold}**",
        parse_mode="Markdown"
    )

# លុបស្តុកទាំងអស់ចោល (/clearstock)
async def clear_stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ មិនមានសិទ្ធិប្រើប្រាស់ Command នេះឡើយ!")
        return

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("DELETE FROM accounts")
    conn.commit()
    conn.close()

    await update.message.reply_text("🗑️ បានលុប Stock ទាំងអស់ចោលស្អាតហើយ! (ស្តុកបច្ចុប្បន្ន = 0)")

# កំណត់តម្លៃ (/setprice)
async def set_price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ មិនមានសិទ្ធិប្រើប្រាស់ Command នេះឡើយ!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ របៀបប្រើ៖ `/setprice 2.00`", parse_mode="Markdown")
        return

    new_price = context.args[0]
    set_setting("price", new_price)
    await update.message.reply_text(f"✅ តម្លៃត្រូវបានប្តូរទៅជា៖ **${new_price}**", parse_mode="Markdown")

# កំណត់ Detail (/setdetail)
async def set_detail_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ មិនមានសិទ្ធិប្រើប្រាស់ Command នេះឡើយ!")
        return

    new_detail = " ".join(context.args)
    if not new_detail:
        await update.message.reply_text("⚠️ របៀបប្រើ៖ `/setdetail ព័ត៌មានលម្អិតថ្មី...`", parse_mode="Markdown")
        return

    set_setting("detail", new_detail)
    await update.message.reply_text(f"✅ Detail ត្រូវបានកែប្រែទៅជា៖\n{new_detail}")

# ==========================================
# ៦. ចាប់ផ្ដើមដំណើរការ Bot
# ==========================================
if __name__ == '__main__':
    # បើកដំណើរការ Web Server លើ thread ដាច់ដោយឡែក
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers សម្រាប់ User
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Handlers សម្រាប់ Admin
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add", add_account))
    app.add_handler(CommandHandler("stocklist", stock_list))
    app.add_handler(CommandHandler("clearstock", clear_stock_cmd))
    app.add_handler(CommandHandler("setprice", set_price_cmd))
    app.add_handler(CommandHandler("setdetail", set_detail_cmd))
    
    print("Bot is successfully running...")
    app.run_polling()
