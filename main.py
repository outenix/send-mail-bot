from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import rotator

API_ID = 3731359
API_HASH = "036ee2d35316873cb402ac61ea3f5618"
BOT_TOKEN = "8208608845:AAFcTuETk5Tm7jlBzJ3GEXgw1oBg0rRBFWw"

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ======================
# STATE MANAGEMENT
# ======================
user_state = {}  # contoh: { chat_id: "waiting_for_email" }


# ======================
# MENU
# ======================
async def show_menu(message):
    available, usedup = rotator.get_accounts()
    targets = rotator.get_targets()

    text = "📊 Status Akun\n\n"
    text += f"Email Tersedia: {len(available)}\n"
    text += f"Email Digunakan (>=2x): {len(usedup)}\n\n"

    if targets:
        text += "🎯 Email Tujuan:\n"
        for t in targets:
            text += f"- {t}\n"
    else:
        text += "⚠️ Email tujuan belum ada.\n"

    buttons = [
        [InlineKeyboardButton("➕ Tambah Email", callback_data="add_email")],
        [InlineKeyboardButton("🗑️ Hapus Email", callback_data="del_menu")],
        [InlineKeyboardButton("🎯 Tambah Email Tujuan", callback_data="add_target")],
        [InlineKeyboardButton("📩 Kirim Email", callback_data="send_email")],
    ]

    # Bisa dipanggil dari /start atau callback
    if hasattr(message, "reply"):
        await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await show_menu(message)


# ======================
# BUTTON HANDLERS
# ======================
@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id

    # Hentikan state lama jika user klik tombol lain
    if chat_id in user_state:
        user_state.pop(chat_id, None)

    if data == "add_email":
        await callback_query.message.edit_text(
            "✉️ Kirim email & app password dengan format:\n`email|apppassword`",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]]
            )
        )
        user_state[chat_id] = "waiting_for_email"

    elif data == "del_menu":
        buttons = [
            [InlineKeyboardButton("🗑️ Hapus Email Terpakai", callback_data="del_used")],
            [InlineKeyboardButton("🗑️ Hapus Semua Email", callback_data="del_all")],
            [InlineKeyboardButton("🗑️ Hapus Email Tujuan", callback_data="del_target")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")],
        ]
        await callback_query.message.edit_text(
            "Pilih opsi hapus:", reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "del_used":
        rotator.delete_used()
        await callback_query.message.edit_text("🗑️ Semua email yang sudah dipakai 2x dihapus.")
        await show_menu(callback_query.message)

    elif data == "del_all":
        rotator.clear_accounts()
        await callback_query.message.edit_text("🗑️ Semua email pengirim berhasil dihapus.")
        await show_menu(callback_query.message)

    elif data == "del_target":
        rotator.clear_targets()
        await callback_query.message.edit_text("🗑️ Semua email tujuan berhasil dihapus.")
        await show_menu(callback_query.message)

    elif data == "back_menu":
        await show_menu(callback_query.message)

    elif data == "add_target":
        await callback_query.message.edit_text(
            "🎯 Kirim email tujuan yang ingin ditambahkan.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]]
            )
        )
        user_state[chat_id] = "waiting_for_target"

    elif data == "send_email":
        await callback_query.message.edit_text(
            "📱 Masukkan nomor WhatsApp dengan format internasional (contoh: +6281234567890)",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Kembali", callback_data="back_menu")]]
            )
        )
        user_state[chat_id] = "waiting_for_number"

    await callback_query.answer()


# ======================
# MESSAGE HANDLER
# ======================
@app.on_message(filters.text & ~filters.command("start"))
async def input_handler(client, message):
    chat_id = message.chat.id
    text = message.text.strip()
    state = user_state.get(chat_id)

    # Jika sedang menunggu email baru
    if state == "waiting_for_email":
        if "|" not in text:
            await message.reply("❌ Format salah. Gunakan: `email|apppassword`")
            return
        email, app_pass = text.split("|", 1)
        accounts = rotator.load_accounts()
        accounts.append({"email": email.strip(), "app_password": app_pass.strip(), "used": 0})
        rotator.save_accounts(accounts)
        await message.reply(f"✅ Email {email} berhasil ditambahkan.")
        user_state.pop(chat_id, None)
        await show_menu(message)
        return

    # Jika sedang menunggu email tujuan
    if state == "waiting_for_target":
        rotator.add_target(text)
        await message.reply(f"✅ Email tujuan {text} berhasil ditambahkan.")
        user_state.pop(chat_id, None)
        await show_menu(message)
        return

    # Jika sedang menunggu nomor WhatsApp
    if state == "waiting_for_number":
        number = text
        sender = rotator.rotate_account()
        targets = rotator.get_targets()

        if not targets:
            await message.reply("⚠️ Email tujuan tidak tersedia.")
            user_state.pop(chat_id, None)
            await show_menu(message)
            return
        if not sender:
            await message.reply("⚠️ Email pengirim tidak tersedia.")
            user_state.pop(chat_id, None)
            await show_menu(message)
            return

        target = targets[0]  # sementara ambil tujuan pertama
        body = f"""Halo Tim Dukungan WhatsApp! Perkenalkan, nama saya [Repzsx] dan nomor WhatsApp saya ({number}), Saya mengalami masalah karena setiap kali mencoba masuk atau mendaftar, saya selalu mendapat pesan "Login Tidak Tersedia." Meskipun saya menggunakan aplikasi WhatsApp resmi, saya tetap tidak bisa masuk. Saya meminta agar WhatsApp meninjau dan segera menyelesaikan masalah ini agar nomor saya dapat diaktifkan kembali tanpa masalah. Mohon hubungi kami sesegera mungkin. Terima kasih.
"""

        success, info = rotator.send_mail(
            sender["email"], sender["app_password"], target, "Dukungan WhatsApp", body
        )

        if success:
            rotator.mark_account_used(sender["email"])
            await message.reply(
                f"📤 Email berhasil dikirim!\n\n"
                f"Pengirim: {sender['email']}\n"
                f"Tujuan: {target}\n"
                f"Nomor: {number}"
            )
        else:
            await message.reply(f"❌ Gagal kirim email: {info}")

        user_state.pop(chat_id, None)
        await show_menu(message)


print("✅ Bot jalan...")
app.run()
