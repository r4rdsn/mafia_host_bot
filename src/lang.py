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


new_request = (
    'Игра создана.\n'
    'Создатель игры: {owner}.\n'
    'Время удаления игры: {time} UTC.\n'
    '{order}'
)

take_card = (
    'Игра начата!\n\n'
    'Порядок игроков следующий:\n'
    '{order}\n\n'
    'Игроки с номерами [{not_took}], разбираем карты!'
)

morning_message = (
    '{peaceful_night}'
    'Идёт день {day}.\n'
    'У вас есть время, чтобы решить, за кого вы проголосуете сегодняшним вечером.\n'
    '──────────────────\n'
    'Игроки:\n'
    '{order}'
)

vote = (
    'Город, настало время для голосования!\n'
    '{vote}'
)

gallows = (
    '<code>'
    '___________\n'
    '|         |\n'
    '|        %s\n'
    '|        %s\n'
    '|        %s\n'
    '|\n'
    '|'
    '</code>\n'
    '{result}\nСлово: {word}{attempts}{players}'
)
