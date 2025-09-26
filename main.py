from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import rotator

# ===== KONFIGURASI =====
API_ID = 3731359
API_HASH = "036ee2d35316873cb402ac61ea3f5618"
BOT_TOKEN = "8208608845:AAFcTuETk5Tm7jlBzJ3GEXgw1oBg0rRBFWw"

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start_handler(client, message):
    available, usedup = rotator.get_accounts()
    target = rotator.get_first_target()

    teks = (
        f"📊 **Status Email**\n\n"
        f"✅ Tersedia: {len(available)}\n"
        f"❌ Terpakai: {len(usedup)}\n\n"
        f"🎯 Email Tujuan: {target if target else 'Belum ada'}"
    )

    buttons = [
        [InlineKeyboardButton("➕ Tambah Email Pengirim", callback_data="add_sender")],
        [InlineKeyboardButton("➕ Tambah Email Tujuan", callback_data="add_target")],
        [InlineKeyboardButton("🗑 Hapus Email Terpakai", callback_data="del_sender")],
        [InlineKeyboardButton("📧 Kirim Email", callback_data="send_email")],
    ]

    await message.reply_text(teks, reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id

    if data == "add_sender":
        await client.send_message(chat_id, "Kirim data dengan format:\n`email|app_password`")
    elif data == "add_target":
        await client.send_message(chat_id, "Kirim email tujuan:\n`contoh@email.com`")
    elif data == "del_sender":
        rotator.delete_used_accounts()
        await client.send_message(chat_id, "✅ Semua email terpakai (>=2) sudah dihapus.")
    elif data == "send_email":
        await client.send_message(chat_id, "Masukkan nomor WhatsApp dengan format internasional, contoh:\n`+6281234567890`")


@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(client, message):
    text = message.text.strip()

    # Input tambah email pengirim
    if "|" in text:
        try:
            email, app_password = text.split("|", 1)
            rotator.add_account(email.strip(), app_password.strip())
            await message.reply("✅ Email pengirim berhasil ditambahkan.")
        except Exception as e:
            await message.reply(f"❌ Gagal tambah email: {e}")
        return

    # Input tambah email tujuan
    if "@" in text and "|" not in text and not text.startswith("+"):
        rotator.add_target(text.strip())
        await message.reply("✅ Email tujuan berhasil ditambahkan.")
        return

    # Input nomor telepon
    if text.startswith("+"):
        available, _ = rotator.get_accounts()
        target = rotator.get_first_target()

        if not available:
            await message.reply("❌ Email pengirim tidak tersedia.")
            return
        if not target:
            await message.reply("❌ Email tujuan tidak tersedia.")
            return

        sender = available[0]
        # Update penggunaan
        sender["used"] += 1
        accounts = rotator.load_accounts()
        for acc in accounts:
            if acc["email"] == sender["email"]:
                acc["used"] = sender["used"]
        rotator.save_accounts(accounts)

        # Isi pesan
        body = (
            f"Halo Tim Dukungan WhatsApp! Perkenalkan, nama saya [Repzsx] dan nomor WhatsApp saya ({text}), "
            "Saya mengalami masalah karena setiap kali mencoba masuk atau mendaftar, saya selalu mendapat pesan "
            "\"Login Tidak Tersedia.\" Meskipun saya menggunakan aplikasi WhatsApp resmi, saya tetap tidak bisa masuk. "
            "Saya meminta agar WhatsApp meninjau dan segera menyelesaikan masalah ini agar nomor saya dapat diaktifkan kembali "
            "tanpa masalah. Mohon hubungi kami sesegera mungkin. Terima kasih."
        )

        # Kirim email lewat Gmail
        success, info = rotator.send_mail(
            sender["email"],
            sender["app_password"],
            target,
            "Dukungan WhatsApp",
            body
        )

        if success:
            await message.reply(
                f"📤 Email berhasil dikirim!\n\n"
                f"Pengirim: {sender['email']}\n"
                f"Tujuan: {target}\n"
                f"Nomor: {text}"
            )
        else:
            await message.reply(f"❌ Gagal kirim email: {info}")


print("✅ Bot jalan...")
app.run()
