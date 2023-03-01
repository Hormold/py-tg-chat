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
        self.prompt = Prompt()
        self.conversations = {}

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

    def rollback(self, num: int) -> None:
        """
        Rollback chat history num times
        """
        for _ in range(num):
            self.prompt.chat_history.pop()

    def reset(self) -> None:
        """
        Reset chat history
        """
        self.prompt.chat_history = []

    def save_conversation(self, conversation_id: str) -> None:
        """
        Save conversation to conversations dict
        """
        self.conversations[conversation_id] = self.prompt

    def load_conversation(self, conversation_id: str) -> None:
        """
        Load conversation from conversations dict
        """
        self.prompt = self.conversations[conversation_id]

    def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete conversation from conversations dict
        """
        self.conversations.pop(conversation_id)

    def get_conversations(self) -> dict:
        """
        Get all conversations
        """
        return self.conversations

class Prompt:
    """
    Prompt class with methods to construct prompt
    """

    def __init__(self) -> None:
        """
        Initialize prompt with base prompt
        """
        self.base_prompt = (
            os.environ.get("CUSTOM_BASE_PROMPT")
            or "You are ChatGPT, a large language model trained by OpenAI.\n\n"
        )
        # Track chat history
        self.chat_history: list = []

    def add_to_chat_history(self, chat: str) -> None:
        """
        Add chat to chat history for next prompt
        """
        self.chat_history.append(chat)

    def history(self) -> str:
        """
        Return chat history
        """
        return "\n".join(self.chat_history)

    def construct_prompt(self, new_prompt: str) -> str:
        """
        Construct prompt based on chat history and request
        """
        prompt = (
            self.base_prompt + self.history() + "User: " + new_prompt + "\nChatGPT:"
        )
        # Check if prompt over 4000*4 characters
        max_tokens = 3200
        if len(ENCODER.encode(prompt)) > max_tokens:
            # Remove oldest chat
            self.chat_history.pop(0)
            # Construct prompt again
            prompt = self.construct_prompt(new_prompt)
        return prompt

