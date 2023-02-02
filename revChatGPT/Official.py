"""
A custom wrapper for the official ChatGPT API
Removed unnecessary code
"""
import json
import os
import openai
import tiktoken
from decouple import config

ENCODER = tiktoken.get_encoding("gpt2")

ENGINE = config("OPENAI_ENGINE", default="text-davinci-003")


class Chatbot:
    """
    Official ChatGPT API
    """

    def get_max_tokens(self, prompt: str) -> int:
        """ Get the max tokens for a prompt """
        return 4000 - len(ENCODER.encode(prompt))

    def __init__(self, api_key: str, engine: str) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        openai.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.engine = engine or ENGINE or os.environ.get("OPENAI_ENGINE")
        self.prompt = Prompt()
        self.conversations = {}

    def ask(self, user_request: str) -> dict:
        """
        Send a request to ChatGPT and return the response
        """
        prompt = self.prompt.construct_prompt(user_request)
        completion = openai.Completion.create(
            engine=self.engine,
            prompt=prompt,
            temperature=0.5,
            max_tokens=self.get_max_tokens(prompt),
            stop=["\n\n\n"],
        )
        if completion.get("choices") is None:
            raise Exception("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception("ChatGPT API returned no choices")
        if completion["choices"][0].get("text") is None:
            raise Exception("ChatGPT API returned no text")
        completion["choices"][0]["text"] = completion["choices"][0]["text"].replace(
            "<|im_end|>",
            "",
        )
        # Add to chat history
        self.prompt.add_to_chat_history(
            "User: "
            + user_request
            + "\n\n\n"
            + "ChatGPT: "
            + completion["choices"][0]["text"]
            + "<|im_end|>\n",
        )
        return completion

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

    def dump_conversation_history(self) -> None:
        """
        Save all conversations history to a json file
        """
        for conversation_id, prompt in self.conversations.items():
            # ~/.config/revChatGPT/conversations/<conversation_id>.json
            with open(
                os.path.join(
                    os.path.expanduser("~"),
                    ".config",
                    "revChatGPT",
                    "conversations",
                    conversation_id + ".json",
                ),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(prompt.chat_history, f)

    def load_conversation_history(self) -> None:
        """
        Load conversation history from json files
        """
        # List all conversation files
        conversation_files = os.listdir(
            os.path.join(
                os.path.expanduser("~"),
                ".config",
                "revChatGPT",
                "conversations",
            ),
        )
        for conversation_file in conversation_files:
            conversation_id = conversation_file[:-5]
            with open(
                os.path.join(
                    os.path.expanduser("~"),
                    ".config",
                    "revChatGPT",
                    "conversations",
                    conversation_file,
                ),
                encoding="utf-8",
            ) as f:
                self.conversations[conversation_id] = Prompt()
                self.conversations[conversation_id].chat_history = json.load(f)


class AsyncChatbot(Chatbot):
    """
    Official ChatGPT API (async)
    """

    async def ask(self, user_request: str) -> dict:
        """
        Send a request to ChatGPT and return the response
        Response: {
            "id": "...",
            "object": "text_completion",
            "created": <time>,
            "model": "text-chat-davinci-002-20230126",
            "choices": [
                {
                "text": "<Response here>",
                "index": 0,
                "logprobs": null,
                "finish_details": { "type": "stop", "stop": "<|endoftext|>" }
                }
            ],
            "usage": { "prompt_tokens": x, "completion_tokens": y, "total_tokens": z }
        }
        """
        prompt = self.prompt.construct_prompt(user_request)
        completion = await openai.Completion.acreate(
            engine=ENGINE,
            prompt=prompt,
            temperature=0.5,
            max_tokens=4000 - int(len(prompt) / 3),
            stop=["\n\n\n"],
        )
        if completion.get("choices") is None:
            raise Exception("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception("ChatGPT API returned no choices")
        if completion["choices"][0].get("text") is None:
            raise Exception("ChatGPT API returned no text")
        completion["choices"][0]["text"] = completion["choices"][0]["text"].replace(
            "<|im_end|>",
            "",
        )
        # Add to chat history
        self.prompt.add_to_chat_history(
            "User: "
            + user_request
            + "\n\n\n"
            + "ChatGPT: "
            + completion["choices"][0]["text"]
            + "<|im_end|>\n",
        )
        return completion

    async def ask_stream(self, user_request: str) -> str:
        """
        Send a request to ChatGPT and yield the response
        """
        prompt = self.prompt.construct_prompt(user_request)
        completion = await openai.Completion.acreate(
            engine=ENGINE,
            prompt=prompt,
            temperature=0.5,
            max_tokens=4000 - int(len(prompt) / 3),
            stop=["\n\n\n"],
            stream=True,
        )
        full_response = ""
        for response in completion:
            if response.get("choices") is None:
                raise Exception("ChatGPT API returned no choices")
            if len(response["choices"]) == 0:
                raise Exception("ChatGPT API returned no choices")
            if response["choices"][0].get("finish_details") is not None:
                break
            if response["choices"][0].get("text") is None:
                raise Exception("ChatGPT API returned no text")
            if response["choices"][0]["text"] == "<|im_end|>":
                break
            yield response["choices"][0]["text"]
            full_response += response["choices"][0]["text"]

        # Add to chat history
        self.prompt.add_to_chat_history(
            "User: "
            + user_request
            + "\n\n\n"
            + "ChatGPT: "
            + full_response
            + "<|im_end|>\n",
        )


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

