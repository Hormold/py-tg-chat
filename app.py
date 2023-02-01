# pylint: disable = no-name-in-module
"""Telegram bot for OpenAI GPT-3 chatbot"""
from datetime import datetime
from revChatGPT.Official import Chatbot
from revChatGPT.Official import Prompt
from decouple import config
from transliterate import translit
import telebot
from conv import load, get, init, reset, rollback
from conv import save_question, save_response

# Get API key from .env file
API_KEY = config("OPENAI_TOKEN")
BOT_TOKEN= config("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
chatbots = {}
BOT_NAME = bot.get_me().username
print(f"Loaded, bot name: @{BOT_NAME}")

@bot.message_handler(commands=['reset'])
def reset_event(message):
    """Reset chat history"""
    if message.chat.id not in chatbots:
        bot.reply_to(message, "Chat history is empty")
        return
    reset(message.chat.id)
    # Inject prompt to chatbot
    prompt = Prompt()
    prompt.chat_history = get(message.chat.id) # Reload history
    chatbots[message.chat.id].prompt = prompt
    bot.reply_to(message, "Chat history reset")

@bot.message_handler(commands=['rollback'])
def rollback_event(message):
    """Rollback one message"""
    if message.chat.id not in chatbots:
        bot.reply_to(message, "Chat history is empty")
        return
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
/rollback <num> - Rollback chat history by <num> messages
/reset - Reset chat history
/info - Display chat info
    """)

@bot.message_handler(commands=['info'])
def info_message(message):
    """Display chat info"""
    bot.reply_to(message, f"""
Chat ID: {message.chat.id}
Chat title: {message.chat.title}
Chat type: {message.chat.type}
    """)


@bot.message_handler(func=lambda message: True)
def reply(message):
    """Handle all messages"""
    if message.chat.id not in chatbots:
        chatbots[message.chat.id] = Chatbot(api_key=API_KEY)
        load(message.chat.id)
        init(message.chat.id, message.chat.title, message.chat.type, message.from_user)
        # Inject prompt to chatbot
        prompt = Prompt()
        prompt.chat_history = get(message.chat.id)
        chatbots[message.chat.id].prompt = prompt
        print(f"[BOT] Created chatbot for chat {message.chat.id}")

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
        resp = chatbots[message.chat.id].ask(message.text)
        time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        print(f"[{time}] ({message.from_user.id} in {message.chat.id}) {message.text}")
        bot.reply_to(message, resp["choices"][0]["text"])
        save_response(message.chat.id, resp["choices"][0]["text"])
    except Exception as ex:
        print(f"Error: {ex}")

bot.infinity_polling()
