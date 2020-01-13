# Copyright (C) 2017, 2018, 2019, 2020  alfred richardsn
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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


def set_gallows(game, result, word):
    bot.edit_message_text(
        lang.gallows.format(
            result=result + '\n',
            word=word,
            attempts='\nПопытки: ' + ', '.join(game['wrong']) if game['wrong'] else ''
        ) % stickman[len(game['wrong'])],
        chat_id=game['chat'],
        message_id=game['message_id'],
        parse_mode='HTML'
    )


def win_game(game):
    set_gallows(game, 'Вы победили!', ' '.join(list(game['word'])))
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
        database.games.update_one({'_id': game['_id']}, {'$addToSet': {'right': suggestion}})
    else:
        game['wrong'].append(suggestion)
        if len(game['wrong']) >= len(stickman) - 1:
            set_gallows(game, 'Вы проиграли.', ' '.join(word))
            database.games.delete_one({'_id': game['_id']})
            return
        database.games.update_one({'_id': game['_id']}, {'$addToSet': {'wrong': suggestion}})

    set_gallows(game, '', ' '.join(word_in_underlines))
