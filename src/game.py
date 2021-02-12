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


role_titles = {
    'don': 'дон мафии',
    'mafia': 'мафия',
    'sheriff': 'шериф',
    'peace': 'мирный житель'
}


def stop_game(game, reason):
    bot.try_to_send_message(
        game['chat'],
        f'Игра окончена! {reason}\n\nРоли были распределены следующим образом:\n' +
        '\n'.join([f'{i+1}. {p["name"]} - {role_titles[p.get("role", "?")]}' for i, p in enumerate(game['players'])])
    )
    database.games.delete_one({'_id': game['_id']})
