## gpt-bot

Simple telegram bot for generating text using ChatGPT model.
Bot remember your conversation context and use it for generating next answer.
It requires token from [https://openai.com/](https://openai.com/) but you can use it for free. Requests are non limited and completed free of charge from the OpenAI API. All you need is an API key.

## Installation (Poetry)

1. Install [Poetry](https://python-poetry.org/docs/#installation)
2. Run ```poetry install```
3. Run ```poetry shell```
4. Edit ```.env``` file and set your tokens (see below)
5. And then ```python3 main.py```

## Environment variables
- OPENAI_TOKEN - your token from [https://openai.com/](https://openai.com/)
- BOT_TOKEN - your bot token from [https://telegram.me/BotFather](https://telegram.me/BotFather)
- OPENAI_ENGINE - engine for generating text. Default is text-davinci-003 (paid)