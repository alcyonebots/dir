import os
import zipfile
import requests
import base64
import shutil
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load tokens from environment variables
GITHUB_TOKEN = "GITHUB_TOKEN"
REPO_OWNER = "alcyonebots"
REPO_NAME = "shenhe"

TEMP_DIR = "temp_dir"

# Upload file to GitHub
def upload_to_github(file_path, repo_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{repo_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    with open(file_path, "rb") as f:
        content = f.read()
    content_base64 = base64.b64encode(content).decode("utf-8")

    data = {"message": f"Add {repo_path}", "content": content_base64}

    # Check if file exists to update instead of creating
    check_resp = requests.get(url, headers=headers)
    if check_resp.status_code == 200:
        sha = check_resp.json()["sha"]
        data["sha"] = sha

    response = requests.put(url, json=data, headers=headers)
    return response.status_code, response.json()

def handle_file(update: Update, context: CallbackContext):
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    file = update.message.document
    file_name = file.hai
    file_path = os.path.join(TEMP_DIR, file_name)

    telegram_file = context.bot.get_file(file.file_id)
    telegram_file.download(custom_path=file_path)

    update.message.reply_text(f"✅ File '{file_name}' received. Processing...")

    if not zipfile.is_zipfile(file_path):
        update.message.reply_text("❌ Please upload a valid .zip file containing the directory!")
        os.remove(file_path)
        return

    extract_dir = os.path.join(TEMP_DIR, file_name.replace(".zip", ""))
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    os.remove(file_path)

    for root, _, files in os.walk(extract_dir):
        for f in files:
            local_path = os.path.join(root, f)
            repo_path = os.path.relpath(local_path, extract_dir)
            status_code, response = upload_to_github(local_path, repo_path)
            if status_code in (200, 201):
                update.message.reply_text(f"✅ Uploaded: {repo_path}")
            else:
                update.message.reply_text(f"❌ Failed to upload {repo_path}: {response.get('message')}")

    shutil.rmtree(TEMP_DIR)
    update.message.reply_text("✅ Directory uploaded to GitHub successfully!")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Send me a .zip file containing your directory, and I'll upload it to GitHub!")

def main():
    TELEGRAM_TOKEN = "8318025596:AAHoRYdBcq2ZvvfNOA_moasrJhopLpph9t0"

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
