import json
import requests
import random
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================
# إعدادات البوت
# ==========================
BOT_TOKEN = "8483309506:AAEe3bA4DTrLOXXPDNJS3W3Gnttau8LEXQg"
MASTER_USDT_ADDRESS = "TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
USDT_AMOUNT = 50
SUBSCRIBERS_FILE = "subscribers.json"
TRONSCAN_API = "https://apilist.tronscan.org/api/account/tokens?address="
# ==========================

# تحميل بيانات المشتركين
def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# حفظ بيانات المشتركين
def save_subscribers(subs):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subs, f, indent=4)

# توليد عنوان فرعي وهمي للمشترك
def generate_sub_address():
    return "T" + ''.join(random.choices(string.ascii_letters + string.digits, k=33))

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك! لاشتراك في البوت، استخدم الأمر /subscribe."
    )

# الاشتراك
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    subscribers = load_subscribers()

    if chat_id in subscribers and subscribers[chat_id]["active"]:
        await update.message.reply_text("أنت مشترك بالفعل ✅")
        return

    sub_address = generate_sub_address()
    subscribers[chat_id] = {"active": False, "usdt_address": sub_address}
    save_subscribers(subscribers)

    await update.message.reply_text(
        f"للاشتراك، يرجى تحويل {USDT_AMOUNT} USDT إلى عنوان المحفظة التالي:\n\n"
        f"{sub_address}\n\n"
        "بعد التحويل، استخدم الأمر /check لتأكيد الدفع."
    )

# التحقق من الدفع
async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    subscribers = load_subscribers()

    if chat_id not in subscribers:
        await update.message.reply_text("لم تقم بالاشتراك بعد، استخدم /subscribe أولاً.")
        return

    sub_address = subscribers[chat_id]["usdt_address"]
    response = requests.get(TRONSCAN_API + sub_address)
    if response.status_code != 200:
        await update.message.reply_text("حدث خطأ أثناء التحقق، حاول لاحقًا.")
        return

    data = response.json()
    usdt_balance = 0
    for token in data.get("data", []):
        if token["tokenName"] == "Tether USD" or token["tokenAbbr"] == "USDT":
            usdt_balance = float(token["balance"]) / 1_000_000
            break

    if usdt_balance >= USDT_AMOUNT:
        subscribers[chat_id]["active"] = True
        save_subscribers(subscribers)
        await update.message.reply_text("تم استلام الدفع ✅ تم تفعيل اشتراكك.")
    else:
        await update.message.reply_text(
            f"لم يتم استلام {USDT_AMOUNT} USDT بعد. الرصيد الحالي: {usdt_balance} USDT"
        )

# حالة الاشتراك
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    subscribers = load_subscribers()
    if chat_id in subscribers and subscribers[chat_id]["active"]:
        await update.message.reply_text("اشتراكك مفعل ✅")
    else:
        await update.message.reply_text("لم يتم تفعيل الاشتراك بعد ❌")

# إعداد البوت وتشغيله
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("subscribe", subscribe))
app.add_handler(CommandHandler("check", check_payment))
app.add_handler(CommandHandler("status", status))

app.run_polling()
