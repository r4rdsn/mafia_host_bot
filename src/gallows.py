from .bot import bot
from .database import database
from . import lang

import re

stickman = [
    ('', '', ''),
    (' 0', '', ''),
    (' 0', ' |', ''),
    (' 0', '/|', ''),
    (' 0', '/|\\', ''),
    (' 0', '/|\\', '/'),
    (' 0', '/|\\', '/ \\')
]


def set_gallows(game, result, word, stickman):
    bot.edit_message_text(
        lang.gallows.format(result=result + '\n', word=word) % stickman,
        chat_id=game['chat'],
        message_id=game['message_id'],
        parse_mode='HTML'
    )


def win_game(game):
    set_gallows(game, 'Вы победили!', ' '.join(list(game['word'])), stickman[len(game['wrong'])])
    database.games.delete_one({'_id': game['_id']})


def gallows_suggestion(suggestion, game, message_id):
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

    bot.safely_delete_message(chat_id=game['chat'], message_id=message_id)

    if has_letter:
        if word_in_underlines == word:
            win_game(game)
            return
        attempts = len(game['wrong'])
        database.games.update_one({'_id': game['_id']}, {'$addToSet': {'right': suggestion}})
    else:
        if len(game['wrong']) >= len(stickman) - 2:
            set_gallows(game, 'Вы проиграли.', ' '.join(word), stickman[-1])
            database.games.delete_one({'_id': game['_id']})
            return
        attempts = len(game['wrong']) + 1
        database.games.update_one({'_id': game['_id']}, {'$addToSet': {'wrong': suggestion}})

    set_gallows(game, '', ' '.join(word_in_underlines), stickman[attempts])
