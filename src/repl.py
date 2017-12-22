# Copyright (C) 2017  alfred richardsn
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
    "Игра создана.\n"
    "Создатель игры: {owner}.\n"
    "{order}"
)

take_card = (
    "Игра начата!\n\n"
    "Порядок игроков следующий:\n"
    "{order}\n\n"
    "Игроки с номерами [{not_took}], разбираем карты!"
)

night_role = (
    "{past_role} засыпает, просыпается {new_role}.\n"
    "{new_role}, кого ты выбираешь?"
)

morning_message = (
    "{peaceful_night}"
    "Идёт день {day}.\n"
    "У вас есть время, чтобы решить, за кого вы проголосуете сегодняшним вечером.\n"
    "──────────────────\n"
    "Игроки:\n"
    "{order}"
)

vote = (
    "Город, настало время для голосования!\n"
    "{vote}"
)

conference_game = (
    "Номер игры: #mafia_{game_id}\n"
    "──────────────────\n"
    "Игроки:\n"
    "{order}\n"
    "──────────────────\n"
    "Игровая стадия:\n"
    "{game_stage}"
)
