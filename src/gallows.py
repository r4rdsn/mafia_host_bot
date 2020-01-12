import re

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


def win_game(game):
    bot.send_message(
        game['chat'],
        lang.gallows.format(
            result='Вы победили.\n', word=' '.join(list(game['word']))
        ) % stickman[len(game['wrong'])],
        parse_mode='HTML'
    )
    database.games.delete_one({'_id': game['_id']})


def gallows_suggestion(suggestion, game):
    if not game:
        return

    if len(suggestion) > 1:
        if re.search(r'\b{}\b'.format(suggestion), game['word']):
            win_game(game)
        return

    if suggestion in game['wrong'] or suggestion in game['right']:
        bot.send_message(game['chat'], 'Эта буква уже выбиралась.')
        return

    word = list(game['word'])
    word_in_underlines = []
    has_letter = False
    for ch in word:
        if ch == suggestion:
            word_in_underlines.append(ch)
            has_letter = True
        elif ch in game['right']:
            word_in_underlines.append(ch)
        else:
            word_in_underlines.append('_')

    if has_letter:
        if word_in_underlines == word:
            win_game(game)
            return
        attempts = len(game['wrong'])
        database.games.update_one({'_id': game['_id']}, {'$addToSet': {'right': suggestion}})
    else:
        if len(game['wrong']) >= len(stickman) - 2:
            bot.send_message(
                game['chat'],
                lang.gallows.format(result='Вы проиграли.\n', word=' '.join(word)) % stickman[-1],
                parse_mode='HTML'
            )
            database.games.delete_one({'_id': game['_id']})
            return
        attempts = len(game['wrong']) + 1
        database.games.update_one({'_id': game['_id']}, {'$addToSet': {'wrong': suggestion}})

    bot.send_message(
        game['chat'],
        lang.gallows.format(result='', word=' '.join(word_in_underlines)) % stickman[attempts],
        parse_mode='HTML'
    )
