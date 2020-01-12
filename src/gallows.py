from .bot import bot
from .database import database
from . import lang

stickman = [
    ('', '', ''),
    (' 0', '', ''),
    (' 0', ' |', ''),
    (' 0', '/|', ''),
    (' 0', '/|\\', ''),
    (' 0', '/|\\', '/'),
    (' 0', '/|\\', '/ \\')
]


def gallows_suggestion(letter, chat_id):
    game = database.gallows.find_one({'chat': chat_id})
    if not game:
        return
    if letter in game['wrong'] or letter in game['right']:
        bot.send_message(chat_id, 'Эта буква уже выбиралась.')
        return

    word = list(game['word'])
    word_in_underlines = []
    has_letter = False
    for ch in word:
        if ch == letter:
            word_in_underlines.append(ch)
            has_letter = True
        elif ch in game['right']:
            word_in_underlines.append(ch)
        else:
            word_in_underlines.append('_')

    if has_letter:
        attempts = len(game['wrong'])
        if word_in_underlines == word:
            bot.send_message(
                chat_id,
                lang.gallows.format(result='Вы победили.\n', word=' '.join(word)) % stickman[attempts],
                parse_mode='HTML'
            )
            database.gallows.delete_one({'_id': game['_id']})
            return
        database.gallows.update_one({'chat': game['chat']}, {'$addToSet': {'right': letter}})
    else:
        attempts = len(game['wrong']) + 1
        if len(game['wrong']) >= len(stickman) - 2:
            bot.send_message(
                chat_id,
                lang.gallows.format(result='Вы проиграли.\n', word=' '.join(word)) % stickman[-1],
                parse_mode='HTML'
            )
            database.gallows.delete_one({'_id': game['_id']})
            return
        database.gallows.update_one({'chat': game['chat']}, {'$addToSet': {'wrong': letter}})

    bot.send_message(
        chat_id,
        lang.gallows.format(result='', word=' '.join(word_in_underlines)) % stickman[attempts],
        parse_mode='HTML'
    )
