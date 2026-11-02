import os
import json
import html
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# ---------------- SOZLAMALAR ----------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  # BotFather'dan olingan token
ORDERS_GROUP_ID = int(os.getenv("ORDERS_GROUP_ID"))  # Guruh ID raqami (-1004481951922)

# BotFather'dagi "KATALOG" Mini App'ga bergan HTTPS manzil
WEBAPP_URL = "https://barchinoy-boutique-tmacom.netlify.app/"

# Butik koordinatalari
BOUTIQUE_LAT = 40.76131161416723
BOUTIQUE_LON = 72.35441157515811

if not TOKEN:
    raise SystemExit("BOT_TOKEN o'rnatilmagan!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# ---------------- YORDAMCHI FUNKSIYALAR ----------------
def money(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍️ Mahsulotlar katalogi", callback_data="catalog")
    builder.button(text="📍 Butik manzili", callback_data="boutique_location")
    builder.button(text="🛒 Savatcham", callback_data="cart")
    builder.button(text="📞 Aloqa / Murojaat", callback_data="contact")
    builder.button(text="ℹ️ Butik haqida", callback_data="about")
    builder.adjust(1, 2, 1, 1)
    return builder.as_markup()


def back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data="back_to_main")
    return builder.as_markup()


def catalog_keyboard():
    """Reply-keyboard tugma: sendData() faqat shu yo'l bilan ishlaydi."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛍 Do'konga kirish", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )


async def safe_edit(callback: types.CallbackQuery, text: str, markup=None):
    """Xabarni tahrirlaydi; bo'lmasa o'chirib, yangisini yuboradi."""
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=markup)


# ---------------- KOMANDALAR ----------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "✨ <b>Assalomu alaykum!</b> Premium atirlar va brend kiyimlar butigimizga xush kelibsiz.\n\n"
        "Marhamat, quyidagi tugmalar yordamida o'zingizga kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(),
    )


@dp.message(Command("id"))
async def cmd_id(message: types.Message):
    """Guruh ID sini bilish uchun: botni guruhga qo'shib, /id yozing."""
    await message.answer(f"Chat ID: <code>{message.chat.id}</code>")


# ---------------- MENYU BO'LIMLARI ----------------
@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery):
    await callback.message.answer(
        "📦 <b>Mahsulotlar katalogi</b>\n\n"
        "Do'konni ochish uchun pastdagi <b>«🛍 Do'konga kirish»</b> tugmasini bosing 👇",
        reply_markup=catalog_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "about")
async def show_about(callback: types.CallbackQuery):
    await safe_edit(
        callback,
        "💎 <b>Bizning Butik haqida:</b>\n\n"
        "💎 BARCHINOY BOUTIQUE - bu sizning shaxsiy uslubingizni va jozibangizni oshirishga yordam beradigan joy. "
        "Biz faqatgina eng sara, eksklyuziv va jahon brendiga ega bo'lgan atir-upalar hamda kiyimlarni taqdim etamiz. "
        "Sizning jozibangiz va qulayligingiz biz uchun birinchi o'rinda!",
        back_button(),
    )
    await callback.answer()


@dp.callback_query(F.data == "boutique_location")
async def show_boutique_location(callback: types.CallbackQuery):
    await callback.message.answer(
        "📍 <b>Bizning butik manzili:</b>\n\n"
        "Andijon shahri, MILLIY TIKLANISH ko'chasi 16b uy!\n"
        "Mo'ljal: MAZZA SOMSA yaqinida\n\n"
        "Marhamat, xaritadan ko'rib kelishingiz mumkin:"
    )
    await callback.message.answer_location(
        latitude=BOUTIQUE_LAT,
        longitude=BOUTIQUE_LON,
        reply_markup=back_button(),
    )
    await callback.answer()


@dp.callback_query(F.data == "cart")
async def show_cart(callback: types.CallbackQuery):
    await safe_edit(
        callback,
        "🛒 <b>Savatchangiz:</b>\n\n"
        "Savat do'kon (Mini App) ichida ishlaydi. Mahsulotlarni tanlash va buyurtma berish uchun "
        "«🛍️ Mahsulotlar katalogi» bo'limiga kiring.",
        back_button(),
    )
    await callback.answer()


@dp.callback_query(F.data == "contact")
async def show_contact(callback: types.CallbackQuery):
    await safe_edit(
        callback,
        "📞 <b>Biz bilan bog'lanish:</b>\n\n"
        "Savollar bo'yicha menejerga murojaat qiling:\n"
        "Telefon: +998 97 996 89 01",
        back_button(),
    )
    await callback.answer()


@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await safe_edit(callback, "✨ Asosiy menyudasiz:", get_main_menu())
    await callback.answer()


# ---------------- MINI APP'DAN KELGAN BUYURTMA ----------------
@dp.message(F.web_app_data)
async def handle_tma_order(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
    except json.JSONDecodeError:
        await message.answer("❌ Buyurtma ma'lumoti noto'g'ri. Iltimos, qaytadan urinib ko'ring.")
        return

    customer = data.get("customer", {})
    items = data.get("items", [])
    delivery = data.get("delivery", {})

    # Mahsulotlar ro'yxati va o'lchamlari
    lines = "\n".join(
        f"• {html.escape(str(i.get('name', '')))} [{html.escape(str(i.get('size', '—')))}] — "
        f"{i.get('quantity', 0)} ta × {money(i.get('price', 0))} = {money(i.get('subtotal', 0))} UZS"
        for i in items
    )

    # Qabul qilish usuli (Yetkazib berish yoki Olib ketish)
    deliv_type = delivery.get("type")
    if deliv_type == "pickup":
        raw_date = delivery.get("pickup_date", "")
        try:
            pickup_date_formatted = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d.%m.%Y")
        except Exception:
            pickup_date_formatted = raw_date
            
        delivery_line = f"📍 <b>Olib ketish (Do'kondan):</b> {pickup_date_formatted} soat {delivery.get('pickup_time', '')}"
        address_line = "🏪 Manzil: Do'kondan o'zi olib ketadi"
    else:
        delivery_line = "🚚 <b>Yetkazib berish</b>"
        address_line = f"📍 Manzil: {html.escape(delivery.get('address', ''))}"

    username = f"@{message.from_user.username}" if message.from_user.username else "—"

    text = (
        "🛒 <b>Yangi zakaz</b>\n\n"
        f"👤 {html.escape(customer.get('name', ''))} ({html.escape(username)})\n"
        f"📞 {html.escape(customer.get('phone', ''))}\n"
        f"{address_line}\n"
        f"💬 {html.escape(customer.get('comment') or '—')}\n\n"
        f"{lines}\n\n"
        f"🧾 Mahsulotlar: {money(data.get('subtotal', 0))} UZS\n"
        f"{delivery_line}\n"
        f"💰 <b>Jami: {money(data.get('total_price', 0))} UZS</b>"
    )

    if not ORDERS_GROUP_ID:
        print("ORDERS_GROUP_ID o'rnatilmagan! Buyurtma:\n", text)
        await message.answer("⚠️ Buyurtma qabul qilindi, lekin tizimda xatolik bor. Iltimos, menejerga qo'ng'iroq qiling.")
        return

    try:
        await bot.send_message(ORDERS_GROUP_ID, text)
    except Exception as e:
        print("Guruhga yuborishda xato:", e)
        await message.answer("⚠️ Buyurtmani yuborishda xatolik. Iltimos, menejerga qo'ng'iroq qiling.")
        return

    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada telefon qilamiz!")


# ---------------- ISHGA TUSHIRISH ----------------
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
