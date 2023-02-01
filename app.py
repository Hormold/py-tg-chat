from revChatGPT.Official import Chatbot
from revChatGPT.Official import Prompt
from decouple import config
from datetime import datetime
import telebot
from conv import load, appendQuestion, appendResponse, get, init, reset, rollback
from transliterate import translit

# Get API key from .env file
API_KEY = config("OPENAI_TOKEN")
BOT_TOKEN= config("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
chatbots = {}
conversation_history = {}
BOT_NAME = bot.get_me().username
print(f"Loaded, bot name: @{BOT_NAME}")

@bot.message_handler(commands=['reset'])
def reset(message):
    if message.chat.id not in chatbots:
        bot.reply_to(message, "Chat history is empty")
        return
    reset(message.chat.id);
    bot.reply_to(message, "Chat history reset")

@bot.message_handler(commands=['rollback'])
def rollback(message):
    if message.chat.id not in chatbots:
        bot.reply_to(message, "Chat history is empty")
        return
    rollback(message.chat.id);
    bot.reply_to(message, "Chat history rollback")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, """
    /help - Display this message
    /rollback - Rollback chat history
    /reset - Reset chat history
    """)
    
@bot.message_handler(func=lambda message: True)
def reply(message):
    if(message.chat.id not in chatbots):
      chatbots[message.chat.id] = Chatbot(api_key=API_KEY)
      load(message.chat.id);
      init(message.chat.id, message.chat.title, message.chat.type, message.from_user);
      # Inject prompt
      prompt = Prompt()
      prompt.chat_history = get(message.chat.id)
      for i in range(len(prompt.chat_history)):
          print(f"Prompt {i}: {prompt.chat_history[i]}")
      chatbots[message.chat.id].prompt = prompt
      print(f"Created chatbot for chat {message.chat.id}")

    # If message not from private chat, it must start with bot name
    if message.chat.type != "private" and not message.text.startswith(f"@{BOT_NAME}"):
       return;
    else:
       message.text = message.text.replace(f"@{BOT_NAME}", "").strip()

    # Allow only latin characters
    if not message.text.isascii():
        message.text = translit(message.text, "ru", reversed=True)
        # Non latin characters are very slow to process and badly tokenized

    appendQuestion(message.chat.id, message.text, message.from_user);

    chatbot = chatbots[message.chat.id]
    response = chatbot.ask(message.text)
    currentDateTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    currentContext = message.chat.id;
    print(f"[{currentDateTime}] ({message.from_user.first_name} in {currentContext}) {message.text} ~{message.chat.type}")
    bot.reply_to(message, response["choices"][0]["text"])
    appendResponse(message.chat.id, response["choices"][0]["text"]);

bot.infinity_polling()

