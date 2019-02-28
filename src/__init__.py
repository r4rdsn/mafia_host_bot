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


import config
from .logger import logger, log_update
from .db import database
from . import repl
from . import croco
from .game_config import role_titles
from .stages import stages, go_to_next_stage, format_roles, get_votes
from .bot import bot

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telebot.apihelper import ApiException

import re
import flask
import random
from time import time
from uuid import uuid4
from threading import Thread
from datetime import datetime
from pymongo.collection import ReturnDocument
from bson.objectid import ObjectId


def get_name(user):
    return '@' + user.username if user.username else user.first_name


def user_object(user):
    return {"id": user.id,
            "name": get_name(user)}


def try_to_send_message(*args, **kwargs):
    try:
        bot.send_message(*args, **kwargs)
    except ApiException:
        logger.error('Ошибка API при отправке сообщения', exc_info=True)


def repin_message(chat_id, pinned_message, last_pinned):
    try:
        chat = bot.get_chat(chat_id)
        if chat.pinned_message.id == pinned_message:
            if last_pinned:
                bot.pin_chat_message(chat_id, last_pinned, disable_notification=True)
            else:
                bot.unpin_chat_message(chat_id)
    except ApiException:
        logger.error('Ошибка API при закреплении сообщения', exc_info=True)


@bot.message_handler(
    func=lambda message: message.chat.type == "private",
    commands=["start", "help"]
)
@bot.message_handler(
    regexp=f"/help@{bot.get_me().username}"
)
def start_command(message):
    answer = f"""Привет, я {bot.get_me().first_name}!
Я умею создавать игры в мафию в группах и супергруппах.
Инструкция и исходный код: https://gitlab.com/r4rdsn/mafia_host_bot
По всем вопросам пишите на https://t.me/r4rdsn"""
    bot.send_message(message.chat.id, answer)


@bot.message_handler(
    commands=["croco"]
)
def play_croco(message):
    if database.croco.find_one({"chat": message.chat.id}):
        bot.send_message(message.chat.id, "Игра в этом чате уже идёт.")
        return
    word = croco.get_word()[:-2]
    id = str(uuid4())[:8]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="Получить слово",
            callback_data=f"get_word {id}"
        )
    )
    name = get_name(message.from_user)
    database.croco.insert_one({
        "id": id,
        "player": message.from_user.id,
        "name": name,
        "word": word,
        "chat": message.chat.id,
        "time": time() + 60,
        "stage": 0
    })
    bot.send_message(message.chat.id, f"Игра началась! {name.capitalize()}, у тебя есть две минуты, чтобы объяснить слово.", reply_markup=keyboard)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("get_word")
)
def get_word(call):
    game = database.croco.find_one({"id": call.data.split()[1], "player": call.from_user.id})
    if game:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=True,
            text=f"Твоё слово: {game['word']}."
        )
    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь получить слово для этой игры."
        )


@bot.callback_query_handler(
    func=lambda call: call.data == "take card",
)
def take_card(call):
    player_game = database.games.find_one({
        "stage": -4,
        "players.id": call.from_user.id,
        "chat": call.message.chat.id,
    })

    if player_game:
        player_index = next(i for i, p in enumerate(player_game["players"]) if p["id"] == call.from_user.id)
        player_object = player_game["players"][player_index]

        if player_object.get("role") is None:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    text="🃏 Вытянуть карту",
                    callback_data="take card"
                )
            )

            player_role = player_game["cards"][player_index]

            player_game = database.games.find_one_and_update(
                {"_id": player_game["_id"]},
                {"$set": {f"players.{player_index}.role": player_role,
                          f"players.{player_index}.alive": True}},
                return_document=ReturnDocument.AFTER)

            bot.answer_callback_query(
                callback_query_id=call.id,
                show_alert=True,
                text=f"Твоя роль - {role_titles[player_role]}."
            )

            players_without_roles = [i + 1 for i, p in enumerate(player_game["players"]) if p.get("role") is None]

            if len(players_without_roles) > 0:
                bot.edit_message_text(
                    repl.take_card.format(
                        order=format_roles(player_game),
                        not_took=", ".join(map(str, players_without_roles))),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=keyboard
                )

            else:
                database.games.update_one(
                    {"_id": player_game["_id"]},
                    {"$set": {"order": []}}
                )

                bot.edit_message_text(
                    "Порядок игроков для игры следующий:\n\n" + format_roles(player_game),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                )

                go_to_next_stage(player_game, inc=2)

        else:
            bot.answer_callback_query(
                callback_query_id=call.id,
                show_alert=False,
                text="У тебя уже есть роль."
            )

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты сейчас не играешь в игру в этой конфе."
        )


@bot.callback_query_handler(
    func=lambda call: call.data == "mafia team"
)
def mafia_team(call):
    player_game = database.games.find_one({
        "players": {"$elemMatch": {
            "id": call.from_user.id,
            "role": {"$in": ["don", "mafia"]},
        }},
        "chat": call.message.chat.id
    })

    if player_game:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=True,
            text='Ты играешь в следующей команде:\n' + format_roles(player_game, True, lambda p: p["role"] in ("don", "mafia"))
        )

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь знакомиться с командой мафии."
        )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("check don"),
)
def check_don(call):
    player_game = database.games.find_one({
        "stage": 5,
        "players": {"$elemMatch": {
            "alive": True,
            "role": "don",
            "id": call.from_user.id
        }},
        "chat": call.message.chat.id
    })

    if player_game and call.from_user.id not in player_game['played']:
        check_player = int(re.match(r"check don (\d+)", call.data).group(1)) - 1

        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=True,
            text=f"Да, игрок под номером {check_player+1} - {role_titles['sheriff']}"
                 if player_game['players'][check_player]['role'] == 'sheriff' else
                 f"Нет, игрок под номером {check_player+1} - не {role_titles['sheriff']}"
        )

        database.games.update_one({'_id': player_game['_id']}, {'$addToSet': {'played': call.from_user.id}})

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь совершать проверку дона."
        )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("check sheriff"),
)
def check_sheriff(call):
    player_game = database.games.find_one({
        "stage": 6,
        "players": {"$elemMatch": {
            "alive": True,
            "role": "sheriff",
            "id": call.from_user.id
        }},
        "chat": call.message.chat.id
    })

    if player_game and call.from_user.id not in player_game['played']:
        check_player = int(re.match(r"check sheriff (\d+)", call.data).group(1)) - 1

        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=True,
            text=f"Да, игрок под номером {check_player+1} - {role_titles['don']}"
                 if player_game['players'][check_player]['role'] == 'don' else
                 f"Да, игрок под номером {check_player+1} - {role_titles['mafia']}"
                 if player_game['players'][check_player]['role'] == 'mafia' else
                 f"Нет, игрок под номером {check_player+1} - не {role_titles['mafia']}"
        )

        database.games.update_one({'_id': player_game['_id']}, {'$addToSet': {'played': call.from_user.id}})

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь совершать проверку шерифа."
        )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("append to order"),
)
def append_order(call):
    player_game = database.games.find_one({
        "stage": -2,
        "players": {"$elemMatch": {
            "role": "don",
            "id": call.from_user.id
        }},
        "chat": call.message.chat.id
    })

    if player_game:
        call_player = re.match(r"append to order (\d+)", call.data).group(1)

        database.games.update_one(
            {"_id": player_game["_id"]},
            {"$addToSet": {"order": call_player}}
        )

        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text=f"Игрок под номером {call_player} добавлен в приказ."
        )

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь отдавать приказ дона."
        )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("vote"),
)
def vote(call):
    player_game = database.games.find_one({
        "stage": 1,
        "players": {"$elemMatch": {
            "alive": True,
            "id": call.from_user.id
        }},
        "chat": call.message.chat.id
    })

    if player_game and call.from_user.id not in player_game['played']:
        vote_player = int(re.match(r"vote (\d+)", call.data).group(1)) - 1
        player_index = next(i for i, p in enumerate(player_game["players"]) if p["id"] == call.from_user.id)

        game = database.games.find_one_and_update(
            {"_id": player_game["_id"]},
            {"$addToSet": {"played": call.from_user.id,
                           "vote.%d" % vote_player: player_index}},
            return_document=ReturnDocument.AFTER
        )

        keyboard = InlineKeyboardMarkup(row_width=8)
        keyboard.add(
            *[InlineKeyboardButton(
                text=f"{i+1}",
                callback_data=f"vote {i+1}"
            ) for i, player in enumerate(game["players"]) if player['alive']]
        )
        keyboard.add(
            InlineKeyboardButton(
                text="Не голосовать",
                callback_data="vote 0"
            )
        )
        bot.edit_message_text(
            repl.vote.format(vote=get_votes(game)),
            chat_id=game['chat'],
            message_id=game['message_id'],
            reply_markup=keyboard
        )

        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text=f"Голос отдан против игрока {vote_player+1}." if vote_player >= 0 else "Голос отдан."
        )

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь голосовать."
        )


@bot.callback_query_handler(
    func=lambda call: call.data == "end order",
)
def end_order(call):
    player_game = database.games.find_one({
        "stage": -2,
        "players": {"$elemMatch": {
            "role": "don",
            "id": call.from_user.id
        }},
        "chat": call.message.chat.id
    })

    if player_game:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Приказ записан и будет передан команде мафии."
        )

        go_to_next_stage(player_game)

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь отдавать приказ дона."
        )


@bot.callback_query_handler(
    func=lambda call: call.data == "get order",
)
def get_order(call):
    player_game = database.games.find_one({
        "$or": [
            {"players": {"$elemMatch": {
                "role": "don",
                "id": call.from_user.id
            }}},
            {"players": {"$elemMatch": {
                "role": "mafia",
                "id": call.from_user.id
            }}}
        ],
        "chat": call.message.chat.id
    })

    if player_game:
        if player_game.get("order"):
            order_text = f'Я отдал тебе следующий приказ: {", ".join(player_game["order"])}. Стреляем именно в таком порядке, в противном случае промахнёмся. ~ {role_titles["don"]}'
        else:
            order_text = f'Я не отдал приказа, импровизируем по ходу игры. Главное - стрелять в одних и тех же людей в одну ночь, в противном случае промахнёмся. ~ {role_titles["don"]}'

        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=True,
            text=order_text
        )

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь получать приказ дона."
        )


@bot.callback_query_handler(
    func=lambda call: call.data == "request interact"
)
def request_interact(call):
    message_id = call.message.message_id
    required_request = database.requests.find_one({"message_id": message_id})

    if required_request:
        update_dict = {}
        player_object = None
        for player in required_request["players"]:
            if player["id"] == call.from_user.id:
                player_object = player
                increment_value = -1
                request_action = "$pull"
                alert_message = 'Ты больше не в игре.'

                break

        if player_object is None:
            if len(required_request["players"]) >= config.PLAYERS_COUNT_LIMIT:
                bot.answer_callback_query(
                    callback_query_id=call.id,
                    show_alert=False,
                    text='В игре состоит максимальное количество игроков.'
                )
                return

            player_object = user_object(call.from_user)
            increment_value = 1
            request_action = "$push"
            alert_message = 'Ты теперь в игре.'
            update_dict["$set"] = {"time": time() + config.REQUEST_OVERDUE_TIME}

        update_dict.update(
            {request_action: {"players": player_object},
             "$inc": {"players_count": increment_value}}
        )

        updated_document = database.requests.find_one_and_update(
            {"_id": required_request["_id"]},
            update_dict,
            return_document=ReturnDocument.AFTER
        )

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                text="Вступить в игру или выйти из игры",
                callback_data="request interact"
            )
        )

        bot.edit_message_text(
            repl.new_request.format(
                owner=updated_document["owner"]["name"],
                time=datetime.fromtimestamp(updated_document['time']).strftime('%H:%M'),
                order='Игроков нет.' if not updated_document['players_count'] else
                      'Игроки:\n' + '\n'.join([f'{i+1}. {p["name"]}' for i, p in enumerate(updated_document["players"])])
            ),
            chat_id=call.message.chat.id,
            message_id=message_id,
            reply_markup=keyboard
        )

        bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text=alert_message)
    else:
        bot.edit_message_text("Заявка больше не существует.", chat_id=call.message.chat.id, message_id=message_id)


@bot.message_handler(
    func=lambda message: message.chat.type in ("group", "supergroup"),
    regexp=f"^/create@{bot.get_me().username}$"
)
def create(message):
    existing_request = database.requests.find_one({"chat": message.chat.id})
    if existing_request:
        bot.send_message(message.chat.id, 'В этом чате уже есть игра!', reply_to_message_id=existing_request['message_id'])
        return

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="Вступить в игру или выйти из игры",
            callback_data="request interact"
        )
    )

    player_object = user_object(message.from_user)
    request_overdue_time = time() + config.REQUEST_OVERDUE_TIME

    answer = repl.new_request.format(
        owner=get_name(message.from_user),
        time=datetime.fromtimestamp(request_overdue_time).strftime('%H:%M'),
        order=f"Игроки:\n1. {player_object['name']}"
    )
    sent_message = bot.send_message(message.chat.id, answer, reply_markup=keyboard)

    pinned_message = bot.get_chat(message.chat.id).pinned_message

    database.requests.insert_one({
        "id": str(uuid4())[:8],
        "owner": player_object,
        "players": [player_object],
        "time": request_overdue_time,
        "chat": message.chat.id,
        "message_id": sent_message.message_id,
        "pinned_message": pinned_message.message_id if pinned_message else None,
        "players_count": 1
    })

    bot.pin_chat_message(message.chat.id, sent_message.message_id)


@bot.message_handler(
    func=lambda message: message.chat.type in ("group", "supergroup"),
    regexp=f"^/start@{bot.get_me().username}$"
)
def start_game(message):
    req = database.requests.find_and_modify(
        {"owner.id": message.from_user.id,
         "chat": message.chat.id,
         "players_count": {"$gte": config.PLAYERS_COUNT_TO_START}},
        new=False,
        remove=True
    )
    if req is not None:
        players_count = req["players_count"]

        cards = ["mafia"] * (players_count // 3 - 1) + ["don", "sheriff"]
        cards += ["peace"] * (players_count - len(cards))
        random.shuffle(cards)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                text="🃏 Вытянуть карту",
                callback_data="take card"
            )
        )

        stage_number = min(stages.keys())

        repin_message(message.chat.id, req["message_id"], req['pinned_message'])

        message_id = bot.send_message(
            message.chat.id,
            repl.take_card.format(
                order="\n".join([f"{i+1}. {p['name']}" for i, p in enumerate(req["players"])]),
                not_took=", ".join(map(str, range(1, len(req["players"]) + 1))),
            ),
            reply_markup=keyboard
        ).message_id

        database.games.insert_one(
            {"chat": req["chat"],
             "id": req["id"],
             "stage": stage_number,
             "day_count": 0,
             "players": req["players"],
             "cards": cards,
             "next_stage_time": time() + stages[stage_number]['time'],
             "message_id": message_id,
             "don": [],
             "vote": {},
             "shots": [],
             "played": []}
        )

    else:
        bot.send_message(message.chat.id, "У тебя нет заявки на игру, которую возможно начать.")


@bot.message_handler(
    func=lambda message: message.chat.type in ("group", "supergroup"),
    regexp=f"^/cancel@{bot.get_me().username}$"
)
def cancel(message):
    req = database.requests.find_one_and_delete(
        {"owner.id": message.from_user.id,
         "chat": message.chat.id}
    )
    if req:
        repin_message(message.chat.id, req["message_id"], req["pinned_message"])
        answer = "Твоя заявка удалена."
    else:
        answer = "У тебя нет заявки на игру."
    bot.send_message(message.chat.id, answer)


@bot.message_handler(
    func=lambda message: message.chat.type in ("group", "supergroup"),
    regexp=f"^/skip@{bot.get_me().username}$"
)
def skip_discussion(message):
    existing_poll = database.polls.find_one({'chat': message.chat.id})
    if existing_poll:
        bot.send_message(
            message.chat.id,
            'В этом чате уже идёт опрос!',
            reply_to_message_id=existing_poll['message_id']
        )
        return

    player_game = database.games.find_one({
        'stage': 0,
        'players': {'$elemMatch': {
            'alive': True,
            'id': message.from_user.id
        }},
        'chat': message.chat.id,
    })

    if not player_game:
        return

    peace_team = set()
    mafia_team = set()

    for player in player_game['players']:
        if player['alive']:
            if player['role'] in ('don', 'mafia'):
                mafia_team.add(player['id'])
            else:
                peace_team.add(player['id'])

    peace_votes = 0
    mafia_votes = 0
    if message.from_user.id in peace_team:
        peace_votes += 1
    else:
        mafia_votes += 1

    poll = {
        'chat': message.chat.id,
        'creator': get_name(message.from_user),
        'peace_count': peace_votes,
        'peace_required': 2 * len(peace_team) // 3,
        'mafia_count': mafia_votes,
        'mafia_required': 2 * len(mafia_team) // 3,
        'votes': [message.from_user.id],
    }

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text='Проголосовать',
            callback_data='poll'
        )
    )

    answer = f'{poll["creator"]} предлагает пропустить обсуждение.'
    poll['message_id'] = bot.send_message(message.chat.id, answer, reply_markup=keyboard).message_id
    database.polls.insert_one(poll)


@bot.callback_query_handler(func=lambda call: call.data == 'poll')
def poll_vote(call):
    message_id = call.message.message_id
    poll = database.polls.find_one({'message_id': message_id})

    if not poll:
        bot.edit_message_text(
            'Опрос больше не существует.',
            chat_id=call.message.chat.id,
            message_id=message_id
        )
        return

    if call.from_user.id in poll['votes']:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text='Твой голос уже был учтён.',
        )
        return

    player_game = database.games.find_one({
        'players': {'$elemMatch': {
            'alive': True,
            'id': call.from_user.id
        }},
        'chat': call.message.chat.id
    })

    if not player_game:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text='Ты не можешь голосовать.',
        )
        return

    increment_value = {}
    mafia_count = poll['mafia_count']
    peace_count = poll['peace_count']

    for player in player_game['players']:
        if player['id'] == call.from_user.id:
            if player['role'] in ('don', 'mafia'):
                increment_value['mafia_count'] = 1
                mafia_count += 1
            else:
                increment_value['peace_count'] = 1
                peace_count += 1

    if mafia_count >= poll['mafia_required'] and peace_count >= poll['peace_required']:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=message_id
        )
        go_to_next_stage(player_game)
        return

    database.polls.update_one({
        '$addToSet': {'votes': call.from_user.id},
        '$inc': increment_value
    })

    bot.answer_callback_query(
        callback_query_id=call.id,
        show_alert=False,
        text='Голос учтён.'
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "shot"
)
def callback_inline(call):
    player_game = database.games.find_one({
        "stage": 4,
        "players": {"$elemMatch": {
            "alive": True,
            "role": {"$in": ["don", "mafia"]},
            "id": call.from_user.id
        }},
        "chat": call.message.chat.id
    })

    if player_game and call.from_user.id not in player_game['played']:
        victim = int(re.match(r"(\d+)\. .*", call.message.text).group(1)) - 1
        database.games.update_one(
            {'_id': player_game['_id']},
            {'$addToSet': {'played': call.from_user.id},
             '$push': {'shots': victim}}
        )

        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text=f"Выстрел произведён в игрока {victim+1}"
        )

    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Ты не можешь участвовать в стрельбе"
        )


@bot.message_handler(
    func=lambda message: message.from_user.id == config.ADMIN_ID,
    commands=["reset"]
)
def reset(message):
    database.games.delete_many({})
    bot.send_message(message.chat.id, "База игр сброшена!")


@bot.message_handler(
    func=lambda message: message.from_user.id == config.ADMIN_ID,
    commands=["database"]
)
def print_database(message):
    print(list(database.games.find()))
    bot.send_message(message.chat.id, "Все документы базы данных игр выведены в терминал!")


@bot.message_handler(
    func=lambda message: message.chat.type in ("group", "supergroup")
)
def night_speak(message):
    game = database.games.find_one({"players.id": message.from_user.id, "chat": message.chat.id})
    if game:
        player = next(p for p in game["players"] if p["id"] == message.from_user.id)
        delete = False
        if game['stage'] in (2, 7):
            victim = game.get('victim')
            if victim is not None and victim != message.from_user.id:
                delete = True
        elif not player.get('alive', True) or game['stage'] not in (0, -4):
            delete = True
        if delete:
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            except ApiException:
                logger.error('Ошибка API при удалении сообщения', exc_info=True)
        return

    game = database.croco.find_one({"chat": message.chat.id})
    if game and re.search(r'\b{}\b'.format(game['word']), message.text.lower().replace('ё', 'е')):
        if message.from_user.id == game["player"]:
            bot.reply_to(message, "Игра окончена! Нельзя самому называть слово!")
        else:
            bot.reply_to(message, "Игра окончена! Это верное слово!")
        database.croco.delete_one({"_id": game["_id"]})


def remove_overtimed_requests():
    while True:
        delete_result = database.requests.delete_many({"time": {"$lte": time()}})
        deleted_count = delete_result.deleted_count
        if deleted_count > 0:
            logger.info(f"Удалено просроченных заявок: {deleted_count}")


def is_game_over(game):
    try:
        alive_players = [p for p in game['players'] if p['alive']]
        mafia = sum(p['role'] in ('don', 'mafia') for p in alive_players)
        return 1 if not mafia else 2 if mafia >= len(alive_players) - mafia else 0
    except KeyError:
        return 0


def stage_cycle():
    while True:
        games_to_modify = database.games.find({"next_stage_time": {"$lte": time()}})
        for game in games_to_modify:
            game_state = is_game_over(game)
            if game_state:
                role = role_titles['peace' if game_state == 1 else 'mafia']
                try_to_send_message(
                    game['chat'],
                    f'Игра окончена! Победили игроки команды "{role}"!\n\nРоли были распределены следующий образом:\n' +
                    '\n'.join([f'{i+1}. {p["name"]} - {role_titles[p["role"]]}' for i, p in enumerate(game['players'])])
                )
                database.games.delete_one({'_id': game['_id']})
                continue

            game = go_to_next_stage(game)


def croco_cycle():
    while True:
        curtime = time()
        games = list(database.croco.find({"time": {"$lte": curtime}}))
        for game in games:
            if game["stage"] == 0:
                database.croco.update_one({"_id": game["_id"]}, {"$set": {"stage": 1, "time": curtime + 60}})
                try_to_send_message(game["chat"], f"{game['name'].capitalize()}, до конца игры осталась минута!")
            else:
                database.croco.delete_one({"_id": game["_id"]})
                try_to_send_message(game["chat"], f"Игра окончена! {game['name'].capitalize()} проигрывает, загаданное слово было {game['word']}.")


def start_thread(name=None, target=None, *args, daemon=True, **kwargs):
    thread = Thread(*args, name=name, target=target, daemon=daemon, **kwargs)
    logger.debug(f'Запускаю процесс <{thread.name}>')
    thread.start()


app = flask.Flask(__name__)


@app.before_request
def limit_remote_addr():
    if flask.request.remote_addr not in config.IP_RANGE:
        flask.abort(403)


@app.route('/' + config.TOKEN, methods=["POST"])
def webhook():
    if flask.request.headers.get("content-type") == "application/json":
        json_string = flask.request.get_data().decode('utf-8')
        update = Update.de_json(json_string)
        log_update(update)
        bot.process_new_updates([update])
        return ""
    else:
        flask.abort(403)


def main():
    start_thread("Stage Cycle", stage_cycle)
    start_thread("Removing Requests", remove_overtimed_requests)
    start_thread("Crocodile Cycle", croco_cycle)

    bot.remove_webhook()
    url = 'https://{}:{}/'.format(config.SERVER_IP, config.SERVER_PORT)
    bot.set_webhook(url=url + config.TOKEN)

    logger.debug(f"Запускаю приложение по адресу {url}")
    app.run(host=config.SERVER_IP,
            port=config.SERVER_PORT,
            ssl_context=(config.SSL_CERT, config.SSL_PRIV),
            debug=False)
