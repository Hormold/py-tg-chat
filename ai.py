"""
A custom wrapper for the official ChatGPT API
Removed unnecessary code
"""
import os
import openai
import tiktoken
from decouple import config

ENCODER = tiktoken.get_encoding("gpt2")
ENGINE = config("OPENAI_ENGINE", default="gpt-3.5-turbo")


class Chatbot:
    """
    Official ChatGPT API
    """

    def get_max_tokens(self, prompt: str) -> int:
        """ Get the max tokens for a prompt """
        return 4000 - len(ENCODER.encode(prompt))

    def __init__(self, api_key: str) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        openai.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.engine = ENGINE
        print(f"[BOT] Initialized Chatbot with engine {self.engine}");

    def ask_gpt(self, prompt, temperature: "0.5") -> dict:
        """
        Send a request to ChatGPT and return the response
        """
        completion = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            temperature=float(temperature or 0.5),
            max_tokens=self.get_max_tokens(prompt),
        )
        if completion.get("choices") is None:
            raise Exception("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception("ChatGPT API returned no choices")
        
        text = completion.choices[0].text;
        return text


    def ask(self, messages, temperature: "0.5") -> dict:
        """
        Send a request to ChatGPT and return the response
        """
        completion = openai.ChatCompletion.create(
            model=self.engine,
            temperature=float(temperature),
            messages=messages,
            #max_tokens=4000,
        )
        if completion.get("choices") is None:
            raise Exception("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception("ChatGPT API returned no choices")
        
        text = completion.choices[0].message.content;
        return text