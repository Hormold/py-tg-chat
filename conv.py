"""Conversation history module"""
import os
import json
from transliterate import translit
import tiktoken
from decouple import config

ENABLE_TRANSLIT = config("ENABLE_TRANSLIT", default=False, cast=bool)
if ENABLE_TRANSLIT:
    print("[CONFIG] Transliteration is enabled (cyr -> latin)")
logDir = os.path.join(os.getcwd(), "logs")
conversation_history = {}
ENCODER = tiktoken.get_encoding("gpt2")
MODEL_MAX = 4000

def calc_array_tokens(messages):
    """Calculate tokens for array of messages"""
    tokens = 0
    for message in messages:
        tokens += len(ENCODER.encode(message['content']))
    return tokens

def strip_to_max(messages):
    """Strip messages array to max tokens, if needed"""
    tokens = calc_array_tokens(messages)
    print(f"Tokens: {tokens} (max: {MODEL_MAX})")
    if tokens > MODEL_MAX:
        # Remove second message, but stay first one!
        messages.pop(1)
        return strip_to_max(messages)
    else:
        return messages

def user_to_str(user, with_id=True):
    """Convert user object to string"""
    if user is None:
        return "None"
    first_name = trans(user['first_name'] if 'first_name' in user else "")
    last_name = trans(user['last_name'] if 'last_name' in user else "")
    username = user['username'] if 'username' in user else ""
    if with_id:
        return f'#{user["id"]} is {first_name} {last_name} (@{username})'
    else:
        return f'{first_name} {last_name} (aka @{username})'

def trans(text):
    """Translate text to english"""
    if ENABLE_TRANSLIT:
        return translit(text, 'ru', reversed=True)
    else:
        return text

def get_full_data(chat_id):
    """Get full conversation history"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        return {}
    data = json.dumps(conversation_history[str_id], indent=4, ensure_ascii=False)
    return data

def get_file_path(chat_id):
    """Get file path for chat history"""
    return os.path.join(logDir, f"new_{str(chat_id)}.json")

def get(chat_id):
    """Get conversation history for Prompt"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        return []
    # Generate prompt from history. Using title, type and member list
    prompt = f'You are ChatGPT bot, helping user inside Telegram chat. Do not send reply with you name in beginning. Not send me: "ChatGPT bot: ". Current chat title: "{conversation_history[str_id]["title"]}"\n'

    if conversation_history[str_id]['type'] == "private":
        member_obj = conversation_history[str_id]['members']
        # Get first member
        member = member_obj[list(member_obj.keys())[0]]
        member = user_to_str(member, False)
        prompt += f'Your companion in chat is {member}\n'
    else:
        members_count = len(conversation_history[str_id]["members"])
        prompt += f'You are in group chat with {members_count} members.\n'
        known_members = []
        for member_id in conversation_history[str_id]["members"]:
            member = conversation_history[str_id]["members"][member_id]
            known_members.append(user_to_str(member, True))
        prompt += f'Known members of chat: {", ".join(known_members)}\n'

    real_history = conversation_history[str_id]['history']
    # Add prompt to beginning of history
    # Remove messages where role is system
    real_history = [x for x in real_history if x['role'] != 'system']
    # Limit to LAST 25 messages
    real_history = [{"role": "system", "content": prompt}] + real_history
    real_history = strip_to_max(real_history)
    return real_history

def load(chat_id):
    """Load conversation history from file"""
    str_id = str(chat_id)
    path = get_file_path(str_id)
    if not os.path.exists(path):
        return print (f"[ERROR] Conversation history for chat {str_id} not found in {path}")
    with open(path, "r", encoding="utf-8") as content:
        conversation_history[str_id] = json.load(content)
        print(f"[CONV] Loaded conversation history for chat {str_id}")

def init(chat_id, title, chat_type, from_user):
    """Initialize conversation history"""
    str_id = str(chat_id)
    if str_id in conversation_history:
        return # Already initialized
    if title is None:
        title = 'Private chat'

    conversation_history[str_id] = {
        "id": str_id,
        "title": trans(title),
        "history": [],
        "members": {},
        "type": chat_type,
        "settings": {}
    }

    conversation_history[str_id]['members'][str(from_user.id)] = {
        "id": from_user.id,
        "first_name": trans(from_user.first_name if from_user.first_name is not None else ""),
        "last_name": trans(from_user.last_name if from_user.last_name is not None else ""),
        "username": from_user.username,
    }
    # Save conversation history to file after init
    save(str_id)

def save(chat_id):
    """Save conversation history to file"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        return
    path = get_file_path(str_id)
    with open(path, "w", encoding="utf-8") as content:
        # Remove duplicates from history where content is the same
        conversation_history[str_id]['history'] = [i for n, i in enumerate(conversation_history[str_id]['history']) if i not in conversation_history[str_id]['history'][n + 1:]]
        json.dump(conversation_history[str_id], content, indent=4, ensure_ascii=False)
        print(f"[CONV] Saved conversation history for chat {str_id}")


def save_question(chat_id, text, author):
    """Append question to history"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        print(f"[ERROR] chat {str_id} is not initialized")
        return

    # If member is not in members list, add him
    if not str(author.id) in conversation_history[str_id]['members']:
        print(f"[MEMBERS] Adding new member {author.id} to chat {str_id}")
        conversation_history[str_id]['members'][str(author.id)] = {
            "id": author.id,
            "first_name": trans(author.first_name if author.first_name is not None else ""),
            "last_name": trans(author.last_name if author.last_name is not None else ""),
            "username": author.username,
        }

    if conversation_history[str_id]['type'] == 'private':
        conversation_history[str_id]['history'].append({"role": 'user', "content": text})
    else:
        conversation_history[str_id]['history'].append({"role": 'user', "content": f'#{author.id}: {text}'});
    save(str_id)

def save_response(chat_id, text):
    """Append response to history"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        print(f"[ERROR] chat {str_id} is not initialized")
        return
    conversation_history[str_id]['history'].append({"role": 'assistant', "content": text})
    save(str_id)

def reset(chat_id):
    """Reset history"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        return
    conversation_history[str_id]['history'] = []
    save(str_id)

def rollback(chat_id, count):
    """Rollback history"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        return
    conversation_history[str_id]['history'] = conversation_history[str_id]['history'][:-count]
    save(str_id)

def save_chat_settings(chat_id, key, value): 
    """Save chat settings"""
    str_id = str(chat_id)
    if str_id not in conversation_history:
        return
    if not 'settings' in conversation_history[str_id]:
        conversation_history[str_id]['settings'] = {}
    conversation_history[str_id]['settings'][key] = value
    save(str_id)

def get_all_chat_settings(chat_id, default_settings):
    """Get all chat settings"""
    str_id = str(chat_id)
    # convert default_settings [{"k": "...", "default": "123"}] to {key: default_value}
    default_settings = {item['k']: item['default'] for item in default_settings}

    if str_id not in conversation_history:
        return default_settings
    if not 'settings' in conversation_history[str_id]:
        return default_settings
    mixed_settings = {**default_settings, **conversation_history[str_id]['settings']}
    return mixed_settings

