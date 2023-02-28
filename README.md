## Self hosted telegram bot to talk with GPT-3 using OpenAI Model with converstion manager

Simple telegram bot for generating text using ChatGPT model.
Bot remember your conversation context and use it for generating next answer.
It requires token from [https://openai.com/](https://openai.com/) but you can use it for free. Requests are non limited and completed free of charge from the OpenAI API. All you need is an API key.

## Installation (Poetry)

1. Install [Poetry](https://python-poetry.org/docs/#installation)
2. Navigate to project folder. If you want to save env in project folder use: ```poetry config virtualenvs.create false --local```
3. Run ```poetry install```
4. Run ```poetry shell```
5. Edit ```.env``` file and set your tokens (see below)
6. And then ```python3 main.py```

## Environment variables
- OPENAI_TOKEN - your token from [https://openai.com/](https://openai.com/)
- BOT_TOKEN - your bot token from [https://telegram.me/BotFather](https://telegram.me/BotFather)
- OPENAI_ENGINE - engine for generating text. Default is text-davinci-003 (paid)
