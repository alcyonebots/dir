import os
import zipfile
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# GitHub Configuration
GITHUB_TOKEN = "."
REPO_OWNER = "alcyonebots"
REPO_NAME = "shenhe"

# Temporary storage for downloaded files
TEMP_DIR = "temp_dir"

# Function to upload a file to GitHub
def upload_to_github(file_path, repo_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{repo_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    with open(file_path, "rb") as f:
        content = f.read().encode("base64").decode()  # Base64 encode the file content
    data = {
        "message": f"Add {repo_path}",
        "content": content,
    }
    response = requests.put(url, json=data, headers=headers)
    return response.status_code, response.json()

# Telegram Bot: Handle File Upload
def handle_file(update: Update, context: CallbackContext):
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    file = update.message.document  # Get the document object
    file_name = file.file_name
    file_path = os.path.join(TEMP_DIR, file_name)

    # Get the File object and download the file
    telegram_file = context.bot.get_file(file.file_id)
    telegram_file.download(custom_path=file_path)
    update.message.reply_text(f"✅ File '{file_name}' received. Processing...")

    # Check if the file is a ZIP
    if not zipfile.is_zipfile(file_path):
        update.message.reply_text("❌ Please upload a valid .zip file containing the directory!")
        os.remove(file_path)
        return

    # Extract the ZIP file
    extract_dir = os.path.join(TEMP_DIR, file_name.split(".zip")[0])
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    os.remove(file_path)  # Remove the ZIP after extraction

    # Upload the directory contents to GitHub
    for root, _, files in os.walk(extract_dir):
        for file in files:
            local_path = os.path.join(root, file)
            repo_path = os.path.relpath(local_path, extract_dir)  # Relative path for GitHub
            status_code, response = upload_to_github(local_path, repo_path)

            if status_code == 201:
                update.message.reply_text(f"✅ Uploaded: {repo_path}")
            else:
                update.message.reply_text(f"❌ Failed to upload {repo_path}: {response.get('message')}")

    # Cleanup
    for root, _, files in os.walk(extract_dir):
        for file in files:
            os.remove(os.path.join(root, file))
        os.rmdir(root)
    os.rmdir(TEMP_DIR)

    update.message.reply_text("✅ Directory uploaded to GitHub successfully!")

# Start Command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Send me a .zip file containing your directory, and I'll upload it to GitHub!")

# Main Function
def main():
    TELEGRAM_TOKEN = "7918162797:AAGRfFzQzJiMYdO-3OUZMtR2-D_JSV00IZ4"

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Command Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
