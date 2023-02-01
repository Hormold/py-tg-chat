# pylint: disable = no-name-in-module
"""Telegram bot for OpenAI GPT-3 chatbot"""
from datetime import datetime
from revChatGPT.Official import Chatbot
from revChatGPT.Official import Prompt
from decouple import config
from transliterate import translit
import telebot
from conv import load, get, init, reset, rollback, get_file_path
from conv import save_question, save_response

# Get API key from .env file
API_KEY = config("OPENAI_TOKEN")
BOT_TOKEN= config("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
chatbots = {}
BOT_NAME = bot.get_me().username
print(f"Loaded, bot name: @{BOT_NAME}")

def get_time():
    """Get current time"""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def initialize_chatbot(message):
    """Initialize chatbot"""
    if message.chat.id not in chatbots:
        chatbots[message.chat.id] = Chatbot(api_key=API_KEY)
        load(message.chat.id)
        init(message.chat.id, message.chat.title, message.chat.type, message.from_user)
        # Inject prompt to chatbot
        prompt = Prompt()
        prompt.chat_history = get(message.chat.id)
        chatbots[message.chat.id].prompt = prompt
        print(f"[BOT] Created chatbot for chat {message.chat.id}")
        return True
    return False

@bot.message_handler(commands=['reset'])
def reset_event(message):
    """Reset chat history"""
    initialize_chatbot(message)
    reset(message.chat.id)
    # Inject prompt to chatbot
    prompt = Prompt()
    prompt.chat_history = get(message.chat.id) # Reload history
    chatbots[message.chat.id].prompt = prompt
    bot.reply_to(message, "Chat history reset, try to send some messages first")

@bot.message_handler(commands=['rollback'])
def rollback_event(message):
    """Rollback one message"""
    initialize_chatbot(message)
    # Get count from command of fallback to 1
    count = int(message.text.split()[1]) if len(message.text.split()) > 1 else 1
    rollback(message.chat.id, count)
    # Inject prompt to chatbot
    prompt = Prompt()
    prompt.chat_history = get(message.chat.id) # Reload history
    chatbots[message.chat.id].prompt = prompt
    last_message = prompt.chat_history[-1]
    bot.reply_to(message, "Chat history rollback, last message now: " + last_message)

@bot.message_handler(commands=['help'])
def help_message(message):
    """Display help message"""
    bot.reply_to(message, """
/help - Display this message
/rollback <num> - Rollback current chat history by <num> messages
/reset - Reset current chat history
/backup - Download chat history (json file)
    """)

@bot.message_handler(commands=['backup'])
def backup_message(message):
    """Download chat history"""
    initialize_chatbot(message)
    # Get chat history as json string
    file_path = get_file_path(message.chat.id)
    # Send chat history as file - backup.json
    bot.send_document(
        message.chat.id,
        document=open(file_path, 'rb'),
        caption="Chat history backup"
    )

@bot.message_handler(func=lambda message: True)
def reply(message):
    """Handle all incoming messages"""
    initialize_chatbot(message)

    # Ignore zero length messages or it 1 symbol
    if len(message.text) < 2:
        return

    # If message not from private chat, it must start with bot name
    if message.chat.type != "private" and not message.text.startswith(f"@{BOT_NAME}"):
        return
    else:
        message.text = message.text.replace(f"@{BOT_NAME}", "").strip()

    # Allow only latin characters
    if not message.text.isascii():
        message.text = translit(message.text, "ru", reversed=True)
        # Non latin characters are very slow to process and badly tokenized
    # Save message to chat history
    save_question(message.chat.id, message.text, message.from_user)

    # Send typing status
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        print(f"[{get_time()}] [{message.from_user.id} in {message.chat.id}] > {message.text}")
        resp = chatbots[message.chat.id].ask(message.text)
        print(f"[{get_time()}] [BOT] < {resp['choices'][0]['text']}")
        bot.reply_to(message, resp["choices"][0]["text"])
        save_response(message.chat.id, resp["choices"][0]["text"])
    except Exception as ex:
        bot.reply_to(message, 'Oops, something went wrong. '+str(ex))
        print(f"Error: {ex}")

bot.infinity_polling()
