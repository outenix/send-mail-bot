from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import rotator

API_ID = 3731359
API_HASH = "036ee2d35316873cb402ac61ea3f5618"
BOT_TOKEN = "8208608845:AAFcTuETk5Tm7jlBzJ3GEXgw1oBg0rRBFWw"

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start_handler(client, message):
    available, usedup = rotator.get_accounts()
    targets = rotator.get_targets()

    text = "📊 Status Akun\n\n"
    text += f"Email Tersedia: {len(available)}\n"
    text += f"Email Digunakan (sudah 2x): {len(usedup)}\n\n"

    if targets:
        text += "🎯 Email Tujuan:\n"
        for t in targets:
            text += f"- {t}\n"
    else:
        text += "⚠️ Email tujuan belum ada.\n"

    buttons = [
        [InlineKeyboardButton("➕ Tambah Email", callback_data="add_email")],
        [InlineKeyboardButton("🗑️ Hapus Email (used>=2)", callback_data="del_email")],
        [InlineKeyboardButton("🎯 Tambah Email Tujuan", callback_data="add_target")],
        [InlineKeyboardButton("📩 Kirim Email", callback_data="send_email")],
    ]

    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


print("✅ Bot jalan...")
app.run()
