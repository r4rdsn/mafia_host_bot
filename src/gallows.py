from .bot import bot
from .database import database
from . import lang

stickman = [
    ('', '', ''),
    (' 0 ', '', ''),
    (' 0 ', ' | ', ''),
    (' 0 ', '/|', ''),
    (' 0 ', '/|\\', '/'),
    (' 0 ', '/|\\', '/ \\')
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
                    lang.gallows.format(
                        result='Вы победили.\n',
                        word=' '.join(game['word_in_underlines'])
                    ) % stickman[-game['attempts']],
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
                lang.gallows.format(
                    result='',
                    word=' '.join(game['word_in_underlines'])
                ) % stickman[-game['attempts']],
                parse_mode='HTML'
            )
            return
        database.gallows.update_one(
            {'chat': game['chat']},
            {'$inc': {'attempts': -1}}
        )
        if game['attempts'] - 1 > 1:
            bot.send_message(
                chat_id,
                lang.gallows.format(
                    result='',
                    word=' '.join(game["word_in_underlines"])
                ) % stickman[-game['attempts'] + 1],
                parse_mode='HTML'
            )
            return
        bot.send_message(
            chat_id,
            lang.gallows.format(
                result='Вы проиграли.\n',
                word=' '.join(list(game["word"]))
            ) % stickman[-1],
            parse_mode='HTML'
        )
        database.gallows.delete_one({'_id': game['_id']})
