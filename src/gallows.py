from .bot import bot
from . import croco
from .database import database

from uuid import uuid4

stickman = [
"""
___________
|         |
|         
|        
|        
|
|
""",
"""
___________
|         |
|         0
|        
|        
|
|
""",
"""
___________
|         |
|         0
|         |
|        
|
|
""",
"""
___________
|         |
|         0
|        /|
|        
|
|
""",
r"""
___________
|         |
|         0
|        /|\
|        
|
|
""",
r"""
___________
|         |
|         0
|        /|\
|        / 
|
|
""",
r"""
___________
|         |
|         0
|        /|\
|        / \
|
|
"""
]


def gallows_suggestion(text, chat_id):
    game = database.gallows.find_one({'chat': chat_id})
    if game:
        splitted_word = list(game['word'])
        has_letter = False
        for i in range(len(splitted_word)):
            if splitted_word[i] == text:
                has_letter = True
        if has_letter:
            if text in game['word_in_underlines']:
                bot.send_message(chat_id, 'Эта буква уже угадана.')
                return
            for i in range(len(splitted_word)):
                if splitted_word[i] == text:
                    game['word_in_underlines'][i] = text
            if game['word_in_underlines'] == splitted_word:
                bot.send_message(
                    chat_id,
                    f'<code>{stickman[-(game["attempts"])]}</code>\n'
                    f'Победа.\nСлово: {" ".join(game["word_in_underlines"])}',
                    parse_mode='HTML'
                )
                database.gallows.delete_one({'_id': game['_id']})
                return
            database.gallows.update_one(
                {'chat': game['chat']},
                {'$set': {'word_in_underlines': game['word_in_underlines']}}
            )
            bot.send_message(
                chat_id,
                f'<code>{stickman[-(game["attempts"])]}</code>\n'
                f'Слово: {" ".join(game["word_in_underlines"])}',
                parse_mode='HTML'
            )
            return
        database.gallows.update_one(
            {'chat': game['chat']},
            {'$inc': {'attempts': -1}}
        )
        if game['attempts']-1 > 1:
            bot.send_message(
                chat_id, 
                f'<code>{stickman[-(game["attempts"]-1)]}</code>'
                f'\nСлово: {" ".join(game["word_in_underlines"])}',
                parse_mode='HTML'
            )
            return
        bot.send_message(
            chat_id,
            f'<code>{stickman[-(game["attempts"]-1)]}</code>\n'
            f'Вы проиграли. Загаданным словом было: {game["word"]}.'
        )
        database.gallows.delete_one({'_id': game['_id']})
