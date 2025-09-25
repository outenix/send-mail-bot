from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from rotator import (
    add_account, delete_used_accounts, get_accounts,
    add_target, get_first_target, get_next_account, increment_used
)
import smtplib
from email.message import EmailMessage

API_ID = 123456            # ganti dengan API ID kamu
API_HASH = "abc123..."     # ganti dengan API HASH kamu
BOT_TOKEN = "1234:abcd"    # ganti dengan BOT TOKEN kamu

app = Client("mailbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Simpan state user
user_state = {}

# Menu utama
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("➕ Tambah Email Pengirim")],
            [KeyboardButton("➕ Tambah Email Tujuan")],
            [KeyboardButton("🗑 Hapus Email Pengirim")],
            [KeyboardButton("📧 Kirim Email")]
        ],
        resize_keyboard=True
    )

@app.on_message(filters.command("start"))
async def start(client, message):
    available, usedup = get_accounts()
    target = get_first_target()

    text = "📌 **Email Pengirim Tersedia:**\n"
    if available:
        for a in available:
            text += f" - {a['email']} (used {a['used']})\n"
    else:
        text += " - (tidak ada)\n"

    text += "\n📌 **Email Pengirim Digunakan (>=2):**\n"
    if usedup:
        for a in usedup:
            text += f" - {a['email']} (used {a['used']})\n"
    else:
        text += " - (tidak ada)\n"

    text += f"\n📌 **Email Tujuan:** {target if target else '(tidak ada)'}"

    await message.reply(text, reply_markup=main_menu())

# Tambah email pengirim
@app.on_message(filters.regex("^➕ Tambah Email Pengirim$"))
async def tambah_email(client, message):
    await message.reply("Kirim email & app password dalam format:\n`email|password`", quote=True)
    user_state[message.chat.id] = "adding_account"

# Tambah email tujuan
@app.on_message(filters.regex("^➕ Tambah Email Tujuan$"))
async def tambah_email_tujuan(client, message):
    await message.reply("Kirim alamat email tujuan, contoh:\n`support@support.whatsapp.com`", quote=True)
    user_state[message.chat.id] = "adding_target"

# Hapus email pengirim
@app.on_message(filters.regex("^🗑 Hapus Email Pengirim$"))
async def hapus_email(client, message):
    delete_used_accounts()
    await message.reply("✅ Semua email dengan `used >= 2` sudah dihapus.")

# Kirim email
@app.on_message(filters.regex("^📧 Kirim Email$"))
async def kirim_email(client, message):
    available, _ = get_accounts()
    if not available:
        await message.reply("❌ Email pengirim tidak tersedia.")
        return
    if not get_first_target():
        await message.reply("❌ Email tujuan tidak tersedia.")
        return

    await message.reply("Kirim nomor WhatsApp dalam format internasional (contoh: +62xxxx):")
    user_state[message.chat.id] = "sending_email"

# Handle input text
@app.on_message(filters.text & ~filters.command("start"))
async def handle_text(client, message):
    state = user_state.get(message.chat.id)

    if state == "adding_account":
        if "|" in message.text:
            try:
                email, password = message.text.split("|", 1)
                add_account(email.strip(), password.strip())
                await message.reply(f"✅ Email pengirim `{email}` berhasil ditambahkan!")
            except Exception as e:
                await message.reply(f"❌ Gagal menambahkan: {e}")
        else:
            await message.reply("❌ Format salah. Gunakan `email|password`")
        user_state.pop(message.chat.id, None)

    elif state == "adding_target":
        try:
            add_target(message.text.strip())
            await message.reply(f"✅ Email tujuan `{message.text.strip()}` berhasil ditambahkan!")
        except Exception as e:
            await message.reply(f"❌ Gagal menambahkan email tujuan: {e}")
        user_state.pop(message.chat.id, None)

    elif state == "sending_email":
        nomor = message.text.strip()
        if not nomor.startswith("+"):
            await message.reply("❌ Nomor harus dalam format internasional, contoh: +62xxxx")
            return

        acc, idx, accounts = get_next_account()
        if acc is None:
            await message.reply("❌ Email pengirim tidak tersedia.")
            return

        target = get_first_target()
        if not target:
            await message.reply("❌ Email tujuan tidak tersedia.")
            return

        # Template email
        body = f"""
Halo Tim Dukungan WhatsApp!

Perkenalkan, nama saya [Repzsx] dan nomor WhatsApp saya {nomor}, 
Saya mengalami masalah karena setiap kali mencoba masuk atau mendaftar, saya selalu mendapat pesan "Login Tidak Tersedia."

Meskipun saya menggunakan aplikasi WhatsApp resmi, saya tetap tidak bisa masuk.

Saya meminta agar WhatsApp meninjau dan segera menyelesaikan masalah ini agar nomor saya dapat diaktifkan kembali tanpa masalah.

Mohon hubungi kami sesegera mungkin. Terima kasih.
"""

        try:
            msg = EmailMessage()
            msg["From"] = acc["email"]
            msg["To"] = target
            msg["Subject"] = "Permintaan Dukungan WhatsApp"
            msg.set_content(body)

            with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                smtp.starttls()
                smtp.login(acc["email"], acc["app_password"])
                smtp.send_message(msg)

            increment_used(accounts, idx)
            await message.reply(f"✅ Email berhasil dikirim dari `{acc['email']}` ke `{target}`\nNomor: {nomor}")
        except Exception as e:
            await message.reply(f"❌ Gagal mengirim email: {e}")

        user_state.pop(message.chat.id, None)

app.run()
