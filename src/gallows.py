from .bot import bot
from . import croco
from .database import database

from uuid import uuid4


def gallows_suggestion(text, chat_id):
    game = database.gallows.find_one({'chat': chat_id})
    if game:
        splitted_word = list(game['word'])
        has_letter = False
        for i in range(len(splitted_word)):
            if splitted_word[i] == text:
                has_letter = True
                game['word_in_underlines'][i] = text
        if has_letter:
            if game['word_in_underlines'] == splitted_word:
                database.gallows.delete_one({'_id': game['_id']})
                bot.send_message(
                    chat_id,
                    f'{"".join(game["word_in_underlines"])}\nВы победили'
                )
                return
            database.gallows.update_one(
                {'chat': game['chat']},
                {'$set': {'word_in_underlines': game['word_in_underlines']}}
            )
            bot.send_message(
                chat_id,
                f'{"".join(game["word_in_underlines"])}'
            )
            return
        database.gallows.update_one(
            {'chat': game['chat']},
            {'$inc': {'attempts': -1}}
        )
        bot.send_message(
            chat_id, 
            f'{game["word_in_underlines"]}\nОсталось попыток: {game["attempts"] - 1}'
        )
