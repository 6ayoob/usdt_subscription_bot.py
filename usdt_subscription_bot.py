import json
import requests
import random
import string
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ==========================
# إعدادات البوت
# ==========================
BOT_TOKEN = "8483309506:AAEe3bA4DTrLOXXPDNJS3W3Gnttau8LEXQg"  # توكن البوت
MASTER_USDT_ADDRESS = "TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # محفظتك الرئيسية TRC20
USDT_AMOUNT = 50  # مبلغ الاشتراك
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

# توليد عنوان فرعي وهمي للمشترك (في الواقع تستخدم API محفظتك)
def generate_sub_address():
    # مثال وهمي: توليد عنوان عشوائي يبدأ بـ T
    return "T" + ''.join(random.choices(string.ascii_letters + string.digits, k=33))

# بدء البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "أهلاً بك! لاشتراك في البوت، استخدم الأمر /subscribe."
    )

# الاشتراك
def subscribe(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    subscribers = load_subscribers()

    if chat_id in subscribers and subscribers[chat_id]["active"]:
        update.message.reply_text("أنت مشترك بالفعل ✅")
        return

    # توليد عنوان فرعي فريد للمشترك
    sub_address = generate_sub_address()
    subscribers[chat_id] = {"active": False, "usdt_address": sub_address}
    save_subscribers(subscribers)

    update.message.reply_text(
        f"للاشتراك، يرجى تحويل {USDT_AMOUNT} USDT إلى عنوان المحفظة التالي:\n\n"
        f"{sub_address}\n\n"
        "بعد التحويل، استخدم الأمر /check لتأكيد الدفع."
    )

# التحقق من الدفع
def check_payment(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    subscribers = load_subscribers()

    if chat_id not in subscribers:
        update.message.reply_text("لم تقم بالاشتراك بعد، استخدم /subscribe أولاً.")
        return

    sub_address = subscribers[chat_id]["usdt_address"]

    # استدعاء TronScan API للتحقق من الرصيد
    response = requests.get(TRONSCAN_API + sub_address)
    if response.status_code != 200:
        update.message.reply_text("حدث خطأ أثناء التحقق، حاول لاحقًا.")
        return

    data = response.json()
    usdt_balance = 0
    for token in data.get("data", []):
        if token["tokenName"] == "Tether USD" or token["tokenAbbr"] == "USDT":
            usdt_balance = float(token["balance"]) / 1_000_000  # TRC20 بالديسيمال
            break

    if usdt_balance >= USDT_AMOUNT:
        subscribers[chat_id]["active"] = True
        save_subscribers(subscribers)
        update.message.reply_text("تم استلام الدفع ✅ تم تفعيل اشتراكك.")
    else:
        update.message.reply_text(
            f"لم يتم استلام {USDT_AMOUNT} USDT بعد. الرصيد الحالي: {usdt_balance} USDT"
        )

# حالة الاشتراك
def status(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    subscribers = load_subscribers()
    if chat_id in subscribers and subscribers[chat_id]["active"]:
        update.message.reply_text("اشتراكك مفعل ✅")
    else:
        update.message.reply_text("لم يتم تفعيل الاشتراك بعد ❌")

# إعداد البوت
updater = Updater(BOT_TOKEN)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("subscribe", subscribe))
updater.dispatcher.add_handler(CommandHandler("check", check_payment))
updater.dispatcher.add_handler(CommandHandler("status", status))

# تشغيل البوت
updater.start_polling()
updater.idle()
