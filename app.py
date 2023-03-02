# pylint: disable = no-name-in-module
"""Telegram bot for OpenAI GPT-3 chatbot"""
from datetime import datetime
import traceback
from decouple import config
import telebot

# Local imports
from ai import Chatbot
from conv import load, get, init, reset, rollback, get_file_path, trans
from conv import save_question, save_response, save_chat_settings, get_all_chat_settings
from utils.serp import get_serp

# Get API key from .env file
API_KEY = config("OPENAI_TOKEN")
BOT_TOKEN = config("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
chatbots = {}
try:
    BOT_NAME = bot.get_me().username
    print(f"[TELEGRAM] Token is ok, bot username: @{BOT_NAME}")
except AttributeError as error:
    print(f"Looks like telegram token is invalid, error: {error}")
    exit(1)

BOT_USERNAME = bot.get_me().username

print("[BOT] Initialized Chatbot @"+BOT_USERNAME)

AVAILBLE_SETTINGS = [
    {
        "k": "region",
        "default": "us-en",
        "description": "Region of DuckDuckGo search engine: wt-wt, us-en, uk-en, ru-ru, etc.",
    },
    {
        "k": "num",
        "default": "3",
        "description": "Max results to show from DuckDuckGo search engine",
        "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    },
    {
        "k": "time",
        "default": "all",
        "description": "Time range of DuckDuckGo search engine: all, d, w, m, y",
        "options": ["all", "d", "w", "m", "y"],
    },
    {
        "k": "temperature",
        "default": "0.5",
        "description": "Temperature of OpenAI GPT-3 chatbot",
        "options": ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"],
    }
]

def get_time():
    """Get current time"""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def initialize_chatbot(message):
    """Initialize chatbot"""
    if message.chat.id not in chatbots:
        chatbots[message.chat.id] = Chatbot(api_key=API_KEY)
        load(message.chat.id)
        init(message.chat.id, message.chat.title, message.chat.type, message.from_user)
        print(f"[BOT] Created chatbot for chat {message.chat.id}")
        return True
    return False

@bot.message_handler(commands=['reset'])
def reset_event(message):
    """Reset chat history"""
    initialize_chatbot(message)
    reset(message.chat.id)
    bot.reply_to(message, "Chat history has been reset to empty!")

@bot.message_handler(commands=['rollback'])
def rollback_event(message):
    """Rollback one message"""
    initialize_chatbot(message)
    # Get count from command of fallback to 1
    count = int(message.text.split()[1]) if len(message.text.split()) > 1 else 1
    history = get(message.chat.id)
     # Check if can rollback (not more than history size)
    if len(history) < count:
        bot.reply_to(message, "Can't rollback more than chat history size!")
        return
    rollback(message.chat.id, count)
    history = get(message.chat.id)
    last_message = history[-count]
    bot.reply_to(message, "Chat history rollback successful. Last message now: " + last_message["text"])


@bot.message_handler(commands=['help', 'start'])
def help_message(message):
    """Display help message"""
    bot.reply_to(message, """Hi, I'm a chatbot powered by OpenAI GPT-3. 
Open source code on GitHub: https://github.com/Hormold/py-tg-chat by @define
Current chat history size: """ + str(len(get(message.chat.id))) + """. Bot uses ChatGPT API.

Available commands:
/help - Display this message
/rollback <num> - Rollback current chat history by <num> messages
/reset - Remove all current chat history
/backup - Download chat history (json file)
/s <query> - Search on DuckDuckGo and compile a one-line response
/settings key:value - Change chat settings (see /settings) + set temperature
""")

@bot.message_handler(commands=['settings'])
def settings_message(message):
    """Display chat settings"""
    initialize_chatbot(message)
    settings = get_all_chat_settings(message.chat.id, AVAILBLE_SETTINGS)
    if len(message.text.split()) == 1:
        # Display current settings
        text = "Available settings:\n\n"
        for sett in AVAILBLE_SETTINGS:
            current_value = settings[sett["k"]]
            text += f"{sett['k']}: {current_value} ({sett['description']})\n"
        text+="\n\nSend message in format /settings key:value to change setting. Example: /settings temperature:0.5"
        bot.reply_to(message, text)
    else:
        # Change settings
        key, value = message.text.split()[1].split(":")
        if key not in settings:
            bot.reply_to(message, f"Invalid setting key: {key}")
            return
      
        # if has settings[key]["options"] and value not in settings[key]["options"]
        if "options" in settings[key] and value not in settings[key]["options"]:
            #map_to_str = lambda x: str(x)
            options = settings[key]["options"]#map(map_to_str, settings[key]["options"])
            bot.reply_to(message, f"Invalid setting value: {value}, available options: {options.join(', ')}")
            return
        if (value == "default" or len(value) == 0 or value == " " or len(value) > 100):
            value = settings[key]["default"]
        if key == "num":
            value = int(value)
        #if key == "temperature":
        #    value = float(value)
        save_chat_settings(message.chat.id, key, value)
        bot.reply_to(message, f"Setting {key} has been changed to {value}")

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

@bot.message_handler(commands=['s'])
def search_message(message):
    """Search on DuckDuckGo"""
    initialize_chatbot(message)
    # Get search query from command /s <query>
    query = message.text.split(maxsplit=1)[1]
    # Get search results
    settings = get_all_chat_settings(message.chat.id, AVAILBLE_SETTINGS)
    bot.send_chat_action(message.chat.id, 'typing')

    try: 
        final_prompt = get_serp(query, num_results=int(settings["num"]), time_period=settings["time"], region=settings["region"])
        save_question(message.chat.id, 'Search in DuckDuckGo for: '+query, message.from_user)
        resp = chatbots[message.chat.id].ask_gpt(final_prompt, temperature=float(settings["temperature"]))
        save_response(message.chat.id, resp)
        
    except Exception as err:
        print('[ERROR] Search error: ', err)
        return bot.reply_to(message, "Search error: " + str(err))
    try: 
        # Try to response in markdown
        bot.reply_to(message, resp, parse_mode="Markdown")
    except Exception as err:
        print('[ERROR] Markdown error: ', err)
        bot.reply_to(message, resp)

@bot.message_handler(func=lambda message: True)
def reply(message):
    """Handle all incoming messages"""
    initialize_chatbot(message)

    # Ignore zero length messages or it 1 symbol
    if len(message.text) < 2:
        return
    is_reply = False
    if message.reply_to_message is not None:
        is_reply = message.reply_to_message.from_user.username == BOT_NAME
    # If message not from private chat, it must start with bot name
    if message.chat.type != "private" and not message.text.startswith(f"@{BOT_NAME}") and not is_reply:
        return
    else:
        message.text = message.text.replace(f"@{BOT_NAME}", "").strip()

    # Allow only latin characters
    if not message.text.isascii():
        message.text = trans(message.text)
        # Non latin characters are very slow to process and badly tokenized
    # Save message to chat history
    save_question(message.chat.id, message.text, message.from_user)

    chat_history = get(message.chat.id)

    settings = get_all_chat_settings(message.chat.id, AVAILBLE_SETTINGS)

    # Send typing status
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        print(f"[{get_time()}] [{message.from_user.id} in {message.chat.id}] > {message.text} ({settings['temperature']})")
        resp = chatbots[message.chat.id].ask(chat_history, temperature=settings["temperature"])
        print(f"[{get_time()}] [BOT] < {resp}")
        bot.reply_to(message, resp)
        save_response(message.chat.id, resp)
    except Exception as ex:
        bot.reply_to(message, 'Oops, something went wrong. '+str(ex))
        print(f"[ERROR] On reply > {ex}")
        traceback.print_exc()

bot.infinity_polling()
