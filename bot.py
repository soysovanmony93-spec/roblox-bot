import os
import sqlite3
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==========================================
# ១. Web Server សម្រាប់ Render Web Service
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Roblox Shop Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# ២. កំណត់ Token, Admin ID, Admin Username និង Channel
# ==========================================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 873482655

ADMIN_USERNAME = "sovanmony_55"
CHANNEL_LINK = "https://t.me/MN_SELLER90"

# ==========================================
# ៣. ប្រព័ន្ធ Database (SQLite)
# ==========================================
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
    
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price', '1.50')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('detail', 'គណនីថ្មី (13+) មាន Voice Chat ស្រាប់ • Clean 100% មិនទាន់ភ្ជាប់ Email/Phone')")
    default_banner = "https://images.unsplash.com/photo-1612287232230-07e3240fbfdb?w=900&auto=format&fit=crop&q=80"
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('banner', ?)", (default_banner,))
    
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

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ==========================================
# ៤. មុខងារសម្រាប់ USER
# ==========================================
def get_main_keyboard(price):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🛒 ទិញ Account Roblox VC (${price})", callback_data="buy_vc")],
        [
            InlineKeyboardButton("📦 ពិនិត្យស្តុក", callback_data="check_stock"),
            InlineKeyboardButton("ℹ️ ការណែនាំ / FAQ", callback_data="faq")
        ],
        [
            InlineKeyboardButton("💬 ទាក់ទង Admin", url=f"https://t.me/{ADMIN_USERNAME}"),
            InlineKeyboardButton("📢 ចូល Channel", url=CHANNEL_LINK)
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_setting("price", "1.50")
    detail = get_setting("detail")
    banner = get_setting("banner")

    caption_text = (
        "👋 **សួស្តី! សូមស្វាគមន៍មកកាន់ហាង ROBLOX VC STORE**\n\n"
        f"✨ {detail}\n"
        f"💵 **តម្លៃ:** `${price}` / 1 Account\n"
        "⚡ **ដំណើរការ:** ស្វ័យប្រវត្តិ ២៤/៧ ទិញភ្លាមបាន Account ភ្លាម!\n\n"
        "👇 _សូមជ្រើសរើសជម្រើសខាងក្រោម៖_"
    )
    
    reply_markup = get_main_keyboard(price)

    if update.message:
        try:
            await update.message.reply_photo(photo=banner, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(caption_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass
        try:
            await update.callback_query.message.reply_photo(photo=banner, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await update.callback_query.message.reply_text(caption_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    back_kb = [[InlineKeyboardButton("🔙 ត្រឡប់ទៅម៉ឺនុយដើម", callback_data="back_home")]]

    if query.data == "check_stock":
        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'")
        stock = c.fetchone()[0]
        conn.close()

        status_icon = "🟢 នៅសល់ស្តុក" if stock > 0 else "🔴 អស់ស្តុក"
        msg = (
            "📦 **ព័ត៌មានស្តុកបច្ចុប្បន្ន**\n\n"
            f"• ស្ថានភាព៖ {status_icon}\n"
            f"• ចំនួននៅសល់៖ **{stock}** គណនី\n\n"
            "⚡ ទិញភ្លាម ទទួលបាន Account ប្រើភ្លាមៗ!"
        )
        if query.message.caption:
            await query.edit_message_caption(caption=msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")

    elif query.data == "faq":
        faq_text = (
            "ℹ️ **ការណែនាំ និងលក្ខខណ្ឌប្រើប្រាស់ (FAQ)**\n\n"
            "1️⃣ **Voice Chat (VC):** គណនីទាំងអស់ត្រូវបានផ្ទៀងផ្ទាត់អាយុ 13+ រួចរាល់ អាចបើក VC ក្នុងហ្គេមបានភ្លាមៗ។\n"
            "2️⃣ **សុវត្ថិភាព:** គណនីថ្មីស្អាត មិនទាន់ភ្ជាប់ Email ឬលេខទូរស័ព្ទឡើយ។\n"
            "3️⃣ **បន្ទាប់ពីទិញ:** សូមចូលទៅកាន់ Settings ដើម្បីភ្ជាប់ Email ផ្ទាល់ខ្លួន និងប្តូរ Password ភ្លាមៗ!\n\n"
            "⚠️ បើមានចម្ងល់បន្ថែម សូមចុចប៊ូតុង **ទាក់ទង Admin** ខាងក្រោម។"
        )
        if query.message.caption:
            await query.edit_message_caption(caption=faq_text, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=faq_text, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")

    elif query.data == "buy_vc":
        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("SELECT id, credentials FROM accounts WHERE status = 'available' LIMIT 1")
        acc = c.fetchone()

        if not acc:
            conn.close()
            err_msg = "❌ **សុំទោស ទំនិញដាច់ស្តុកហើយ!**\n\nសូមរង់ចាំ Admin បន្ថែមស្តុកថ្មី ឬទាក់ទងមក Admin។"
            if query.message.caption:
                await query.edit_message_caption(caption=err_msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")
            else:
                await query.edit_message_text(text=err_msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")
            return

        acc_id, creds = acc
        c.execute("UPDATE accounts SET status = 'sold' WHERE id = ?", (acc_id,))
        conn.commit()
        conn.close()

        success_msg = (
            "🎉 **ការបញ្ជាទិញជោគជ័យ!**\n\n"
            f"🔑 **ព័ត៌មានគណនីរបស់អ្នក:**\n`{creds}`\n\n"
            "⚠️ _សូមប្រញាប់ចូលប្តូរពាក្យសម្ងាត់ និងភ្ជាប់ Email ការពារភ្លាមៗ!_"
        )
        if query.message.caption:
            await query.edit_message_caption(caption=success_msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=success_msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")

    elif query.data == "back_home":
        await start(update, context)

# ==========================================
# ៥. មុខងារ ADMIN
# ==========================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
        return

    admin_text = (
        "🛠 **ផ្ទាំងគ្រប់គ្រង ADMIN (Admin Panel)**\n\n"
        "• `/add User:xxx | Pass:xxx` ➡️ បញ្ចូលគណនីថ្មី\n"
        "• `/setprice 2.00` ➡️ កែប្រែតម្លៃ\n"
        "• `/setdetail អត្ថបទ...` ➡️ កែប្រែព័ត៌មាន Detail\n"
        "• **ប្តូរ Banner:** Reply លើរូប រួចវាយ `/setbanner`\n"
        "• `/stocklist` ➡️ ឆែករបាយការណ៍ស្តុក\n"
        "• `/clearstock` ➡️ លុបស្តុកចោលទាំងអស់"
    )
    await update.message.reply_text(admin_text, parse_mode="Markdown")

async def set_banner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
        return

    file_id = None
    # ករណី Reply លើរូប
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        file_id = update.message.reply_to_message.photo[-1].file_id
    # ករណីផ្ញើរូបផ្ទាល់ជាមួយ Caption /setbanner
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id

    if file_id:
        set_setting("banner", file_id)
        await update.message.reply_text("✅ បានកំណត់រូបភាព Banner ជោគជ័យ!")
        return

    # ករណីដាក់ Link URL តាមក្រោយ /setbanner <url>
    if context.args:
        set_setting("banner", context.args[0])
        await update.message.reply_text("✅ បានកំណត់ Link រូបភាពធ្វើជា Banner ជោគជ័យ!")
        return

    await update.message.reply_text("💡 **របៀបប្តូរ Banner:**\nសូម **Reply** លើរូប Logo MN STORE រួចវាយពាក្យ `/setbanner` ផ្ញើមកវិញ!", parse_mode="Markdown")

async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
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

async def stock_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
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
        f"• នៅសល់ក្នុងស្តុក៖ **{available}**\n"
        f"• លក់ចេញរួច៖ **{sold}**\n"
        f"• សរុបទាំងអស់៖ **{available + sold}**",
        parse_mode="Markdown"
    )

async def clear_stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
        return

    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    c.execute("DELETE FROM accounts")
    conn.commit()
    conn.close()

    await update.message.reply_text("🗑️ បានលុប Stock ទាំងអស់ចោលស្អាតហើយ!")

async def set_price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ របៀបប្រើ៖ `/setprice 2.00`", parse_mode="Markdown")
        return

    new_price = context.args[0]
    set_setting("price", new_price)
    await update.message.reply_text(f"✅ តម្លៃត្រូវបានប្តូរទៅជា៖ **${new_price}**", parse_mode="Markdown")

async def set_detail_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
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
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("setbanner", set_banner_cmd))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"^/setbanner"), set_banner_cmd))
    app.add_handler(CommandHandler("add", add_account))
    app.add_handler(CommandHandler("stocklist", stock_list))
    app.add_handler(CommandHandler("clearstock", clear_stock_cmd))
    app.add_handler(CommandHandler("setprice", set_price_cmd))
    app.add_handler(CommandHandler("setdetail", set_detail_cmd))
    
    app.run_polling()
