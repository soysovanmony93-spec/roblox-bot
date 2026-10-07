import os
import sqlite3
import threading
import random
import time
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
# ២. ការកំណត់ Token និង Admin
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
    # តារាងកត់ត្រាការបញ្ជាទិញ (Orders)
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_code TEXT PRIMARY KEY,
            user_id INTEGER,
            user_name TEXT,
            status TEXT DEFAULT 'pending',
            created_at REAL
        )
    ''')
    
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price', '1.50')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('detail', 'គណនីថ្មី (13+) មាន Voice Chat ស្រាប់ • Clean 100% មិនទាន់ភ្ជាប់ Email/Phone')")
    
    default_banner = "https://images.unsplash.com/photo-1612287232230-07e3240fbfdb?w=900&auto=format&fit=crop&q=80"
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('banner', ?)", (default_banner,))
    
    # QR Code លំនាំដើម
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('qr_code', '')")
    
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
        c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'")
        stock = c.fetchone()[0]

        if stock <= 0:
            conn.close()
            err_msg = "❌ **សុំទោស ទំនិញដាច់ស្តុកហើយ!**\n\nសូមរង់ចាំ Admin បន្ថែមស្តុកថ្មី ឬទាក់ទងមក Admin។"
            if query.message.caption:
                await query.edit_message_caption(caption=err_msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")
            else:
                await query.edit_message_text(text=err_msg, reply_markup=InlineKeyboardMarkup(back_kb), parse_mode="Markdown")
            return

        # បង្កើតលេខកូដ Order Code ការពារការបន្លំ Receipt ចាស់
        order_code = f"MN-{random.randint(1000, 9999)}"
        c.execute("INSERT INTO orders (order_code, user_id, user_name, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
                  (order_code, query.from_user.id, query.from_user.full_name, time.time()))
        conn.commit()
        conn.close()

        price = get_setting("price", "1.50")
        qr_code = get_setting("qr_code")

        pay_msg = (
            f"🛒 **ការបញ្ជាទិញលេខកូដ៖** `{order_code}`\n\n"
            f"💵 **ចំនួនទឹកប្រាក់ដែលត្រូវបង់៖** `${price}`\n\n"
            "⚠️ **លក្ខខណ្ឌសំខាន់ដើម្បីការពារការខាតបង់៖**\n"
            f"1. ពេលស្កេនបង់លុយ សូមបញ្ចូលពាក្យក្នុង **Remark:** `{order_code}`\n"
            "2. បន្ទាប់ពីបង់រួច សូមផ្ញើរូបភាពវិក្កយបត្រ (Receipt) ចូលមកទីនេះភ្លាម!\n"
            "3. លេខកូដនេះមានសុពលភាពត្រឹមតែ **១០ នាទី** ប៉ុណ្ណោះ។"
        )

        cancel_kb = [[InlineKeyboardButton("❌ បោះបង់ការទិញ", callback_data="back_home")]]
        
        try:
            await query.message.delete()
        except Exception:
            pass

        if qr_code:
            await query.message.reply_photo(photo=qr_code, caption=pay_msg, reply_markup=InlineKeyboardMarkup(cancel_kb), parse_mode="Markdown")
        else:
            await query.message.reply_text(pay_msg + "\n\n*(Admin មិនទាន់បានដាក់រូប QR Code ទេ)*", reply_markup=InlineKeyboardMarkup(cancel_kb), parse_mode="Markdown")

    elif query.data.startswith("approve_"):
        if not is_admin(query.from_user.id):
            return

        order_code = query.data.split("_")[1]
        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("SELECT user_id, status FROM orders WHERE order_code = ?", (order_code,))
        order = c.fetchone()

        if not order or order[1] != 'pending':
            conn.close()
            await query.edit_message_caption(caption=f"⚠️ ការបញ្ជាទិញ `{order_code}` ត្រូវបានដោះស្រាយរួចរាល់ហើយ!", parse_mode="Markdown")
            return

        buyer_id = order[0]

        # ចាប់យក Account ដែលទំនេរ
        c.execute("SELECT id, credentials FROM accounts WHERE status = 'available' LIMIT 1")
        acc = c.fetchone()

        if not acc:
            conn.close()
            await query.message.reply_text("❌ អស់ស្តុកហើយ មិនអាចបញ្ចេញគណនីបានទេ!")
            return

        acc_id, creds = acc
        c.execute("UPDATE accounts SET status = 'sold' WHERE id = ?", (acc_id,))
        c.execute("UPDATE orders SET status = 'approved' WHERE order_code = ?", (order_code,))
        conn.commit()
        conn.close()

        # ផ្ញើគណនីទៅកាន់ភ្ញៀវ
        buyer_msg = (
            "🎉 **ការទូទាត់ប្រាក់ទទួលបានជោគជ័យ!**\n\n"
            f"🔑 **ព័ត៌មានគណនី Roblox របស់អ្នក:**\n`{creds}`\n\n"
            "⚠️ _សូមប្រញាប់ចូលប្តូរពាក្យសម្ងាត់ និងភ្ជាប់ Email ការពារភ្លាមៗ!_\n"
            "អរគុណច្រើនសម្រាប់ការគាំទ្រហាង MN STORE! ❤️"
        )
        try:
            await context.bot.send_message(chat_id=buyer_id, text=buyer_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending to buyer: {e}")

        await query.edit_message_caption(
            caption=f"✅ បាន **APPROVE** ការបញ្ជាទិញ `{order_code}` ជោគជ័យ!\nAccount ត្រូវបានផ្ញើជូនភ្ញៀវរួចរាល់។",
            parse_mode="Markdown"
        )

    elif query.data.startswith("reject_"):
        if not is_admin(query.from_user.id):
            return

        order_code = query.data.split("_")[1]
        conn = sqlite3.connect("shop.db")
        c = conn.cursor()
        c.execute("SELECT user_id FROM orders WHERE order_code = ?", (order_code,))
        order = c.fetchone()

        if order:
            buyer_id = order[0]
            c.execute("UPDATE orders SET status = 'rejected' WHERE order_code = ?", (order_code,))
            conn.commit()
            conn.close()

            reject_buyer_msg = (
                f"❌ **ការបញ្ជាទិញលេខកូដ `{order_code}` ត្រូវបានបដិសេធ!**\n\n"
                "មូលហេតុ៖ វិក្កយបត្រមិនត្រឹមត្រូវ គ្មាន Remark កូដសម្គាល់ ឬមិនទាន់បានបង់ប្រាក់។\n"
                "បើមានចម្ងល់ សូមទាក់ទងមក Admin ដោយផ្ទាល់។"
            )
            try:
                await context.bot.send_message(chat_id=buyer_id, text=reject_buyer_msg, parse_mode="Markdown")
            except Exception:
                pass

        await query.edit_message_caption(
            caption=f"❌ បាន **REJECT** ការបញ្ជាទិញ `{order_code}` រួចរាល់។",
            parse_mode="Markdown"
        )

    elif query.data == "back_home":
        await start(update, context)

# ==========================================
# ៥. ទទួលវិក្កយបត្រពីភ្ញៀវ
# ==========================================
async def handle_buyer_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # បើ Admin ផ្ញើរូប មិនមែនជាការបង់ប្រាក់ទេ
    if is_admin(update.effective_user.id):
        return

    user_id = update.effective_user.id
    conn = sqlite3.connect("shop.db")
    c = conn.cursor()
    # ស្វែងរកការបញ្ជាទិញដែលនៅ pending ក្នុងរយៈពេល ១០ នាទី
    ten_mins_ago = time.time() - 600
    c.execute("SELECT order_code FROM orders WHERE user_id = ? AND status = 'pending' AND created_at >= ? ORDER BY created_at DESC LIMIT 1", (user_id, ten_mins_ago))
    row = c.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("⚠️ មិនមានការបញ្ជាទិញដែលកំពុងរង់ចាំឡើយ ឬការបញ្ជាទិញរបស់អ្នកបានផុតកំណត់ (លើសពី ១០ នាទី)។ សូមចុច /start ដើម្បីទិញឡើងវិញ។")
        return

    order_code = row[0]
    receipt_photo = update.message.photo[-1].file_id

    # ផ្ញើដំណឹងប្រាប់ភ្ញៀវ
    await update.message.reply_text("⏳ ទទួលបានវិក្កយបត្រហើយ! ប្រព័ន្ធកំពុងជូនដំណឹងទៅ Admin ដើម្បីត្រួតពិនិត្យ និងបញ្ចេញគណនីជូនអ្នកក្នុងរយៈពេលខ្លី...")

    # បញ្ជូនវិក្កយបត្រទៅកាន់ Admin
    admin_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order_code}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_code}")
        ]
    ])

    admin_caption = (
        "🔔 **មានភ្ញៀវផ្ញើវិក្កយបត្របង់ប្រាក់!**\n\n"
        f"👤 ឈ្មោះភ្ញៀវ៖ {update.effective_user.mention_markdown()}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"🏷 **លេខកូដបញ្ជាទិញ (Remark):** `{order_code}`\n\n"
        "👉 _សូមពិនិត្យ Remark លើវិក្កយបត្រឱ្យឃើញត្រូវគ្នា មុននឹងចុច Approve!_"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=receipt_photo,
        caption=admin_caption,
        reply_markup=admin_kb,
        parse_mode="Markdown"
    )

# ==========================================
# ៦. មុខងារ ADMIN
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
        "• **ប្តូររូប Banner:** Reply លើរូប រួចវាយ `/setbanner`\n"
        "• **ប្តូររូប QR Code:** Reply លើរូប QR រួចវាយ `/setqr`\n"
        "• `/stocklist` ➡️ ឆែករបាយការណ៍ស្តុក\n"
        "• `/clearstock` ➡️ លុបស្តុកចោលទាំងអស់"
    )
    await update.message.reply_text(admin_text, parse_mode="Markdown")

async def set_qr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
        return

    file_id = None
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        file_id = update.message.reply_to_message.photo[-1].file_id
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id

    if file_id:
        set_setting("qr_code", file_id)
        await update.message.reply_text("✅ បានកំណត់រូបភាព QR Code បង់ប្រាក់ជោគជ័យ!")
        return

    await update.message.reply_text("💡 **របៀបដាក់ QR Code:**\nសូម **Reply** លើរូបភាព QR Code ABA/Bakong របស់អ្នក រួចវាយពាក្យ `/setqr` ផ្ញើមកវិញ!", parse_mode="Markdown")

async def set_banner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ អ្នកមិនមែនជា Admin ទេ!")
        return

    file_id = None
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        file_id = update.message.reply_to_message.photo[-1].file_id
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id

    if file_id:
        set_setting("banner", file_id)
        await update.message.reply_text("✅ បានកំណត់រូបភាព Banner ជោគជ័យ!")
        return

    await update.message.reply_text("💡 **របៀបប្តូរ Banner:**\nសូម **Reply** លើរូបភាព Banner រួចវាយពាក្យ `/setbanner` ផ្ញើមកវិញ!", parse_mode="Markdown")

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
# ៧. ចាប់ផ្ដើមដំណើរការ Bot
# ==========================================
if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # ទទួលវិក្កយបត្រពីភ្ញៀវ
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.CaptionRegex(r"^/set"), handle_buyer_receipt))
    
    # Admin handlers
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("setbanner", set_banner_cmd))
    app.add_handler(CommandHandler("setqr", set_qr_cmd))
    app.add_handler(CommandHandler("add", add_account))
    app.add_handler(CommandHandler("stocklist", stock_list))
    app.add_handler(CommandHandler("clearstock", clear_stock_cmd))
    app.add_handler(CommandHandler("setprice", set_price_cmd))
    app.add_handler(CommandHandler("setdetail", set_detail_cmd))
    
    app.run_polling()
