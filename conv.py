from transliterate import translit
import os
import json
logDir = os.path.join(os.getcwd(), "logs")
conversation_history = {}

def userToStr(user, withId=True):
    if user == None:
        return "None";
    
    first_name = ruToEn(user['first_name'] if 'first_name' in user else "");
    last_name = ruToEn(user['last_name'] if 'last_name' in user else "");
    username = user['username'] if 'username' in user else "";
    if withId:
        return f'#{user["id"]} is {first_name} {last_name} (@{username})';
    else:
        return f'{first_name} {last_name} (aka @{username})';

def ruToEn(text):
    return translit(text, 'ru', reversed=True);

def get(chatId):
    strId = str(chatId);
    if not strId in conversation_history:
        return [];
    # Generate prompt from history. Using title, type and member list
    prompt = f'You are chat bot. Chat title: "{conversation_history[strId]["title"]}"\n';

    if conversation_history[strId]['type'] == "private":
        memberObj = conversation_history[strId]['members'];
        # Get first member
        member = memberObj[list(memberObj.keys())[0]];
        member = userToStr(member, False);
        prompt += f'Your companion is {member}\n';
    else:
        prompt += f'You are in group chat with {len(conversation_history[strId]["members"])} members.\n';

    realHistory = conversation_history[strId]['history'];
    # Concat prompt with history in array [prompt, ...history]
    # if one line is match one of prompt variants, it will be ignored
    ignoreLines = ['You are chat bot', 'Your companion', 'You are in group chat']
    # Filter history
    realHistory = [line for line in realHistory if not any(ignore in line for ignore in ignoreLines)]
    # Add prompt to beginning of history
    realHistory = [prompt] + realHistory;
    return realHistory;

def load(chatId):
    strId = str(chatId);
    if not os.path.exists(
        os.path.join(
            logDir,
            strId + ".json",
        )
    ):
        return print (f"Conversation history for chat {strId} not found")
    with open(
        os.path.join(logDir, strId + ".json",
        ),
        "r",
        encoding="utf-8",
    ) as f:
        conversation_history[strId] = json.load(f)
        print(f"Loaded conversation history for chat {strId}")

def init(chatId, title, type, fromUser):
    strId = str(chatId);
    if strId in conversation_history:
        return; # Already initialized

    if title == None:
        title = 'Private chat'

    conversation_history[strId] = {
        "id": strId,
        "title": ruToEn(title),
        "history": [],
        "members": {},
        "type": type,
    };

    conversation_history[strId]['members'][fromUser.id] = {
        "id": fromUser.id,
        "first_name": ruToEn(fromUser.first_name if fromUser.first_name != None else ""),
        "last_name": ruToEn(fromUser.last_name if fromUser.last_name != None else ""),
        "username": fromUser.username,
    };


    save(strId);

def save(chatId):
    strId = str(chatId);
    if not strId in conversation_history:
        return;
    with open(
        os.path.join(
            logDir,
            strId + ".json",
        ),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(conversation_history[strId], f, indent=4, ensure_ascii=False)
        print(f"Saved conversation history for chat {strId}")


def appendQuestion(chatId, question, author):
    strId = str(chatId);
    if not strId in conversation_history:
        print(f"Error: chat {strId} is not initialized");
        return;

    
    # If member is not in members list, add him
    if not str(author.id) in conversation_history[strId]['members']:
        print(f"Adding new member {author.id} to chat {strId}")
        conversation_history[strId]['members'][str(author.id)] = {
            "id": author.id,
            "first_name": ruToEn(author.first_name if author.first_name != None else ""),
            "last_name": ruToEn(author.last_name if author.last_name != None else ""),
            "username": author.username,
        }

    if(conversation_history[strId]['type'] == 'private'):
        conversation_history[strId]['history'].append(f'User: {question}');
    else:
        conversation_history[strId]['history'].append(f'#{author.id}: {question}');
    save(strId);

def appendResponse(chatId, response):
    strId = str(chatId);
    if not strId in conversation_history:
        print(f"Error: chat {strId} is not initialized");
        return;
    conversation_history[strId]['history'].append(f'Bot: {response}');
    save(strId);

def reset(chatId):
    strId = str(chatId);
    if not strId in conversation_history:
        return;
    conversation_history[strId]['history'] = [];
    save(strId);

def rollback(chatId, count):
    strId = str(chatId);
    if not strId in conversation_history:
        return;
    conversation_history[strId]['history'] = conversation_history[strId]['history'][:-count];
    save(strId);