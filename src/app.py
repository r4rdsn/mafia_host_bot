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


import config
from .logger import logger, log_update
from .database import database
from .game import stop_game, role_titles
from .stages import go_to_next_stage
from .bot import bot

import flask
from time import time
from threading import Thread
from telebot.types import Update


def remove_overtimed_requests():
    while True:
        delete_result = database.requests.delete_many({'time': {'$lte': time()}})
        deleted_count = delete_result.deleted_count
        if deleted_count > 0:
            logger.info(f'Удалено просроченных заявок: {deleted_count}')


def is_game_over(game):
    try:
        alive_players = [p for p in game['players'] if p['alive']]
        mafia = sum(p['role'] in ('don', 'mafia') for p in alive_players)
        return 1 if not mafia else 2 if mafia >= len(alive_players) - mafia else 0
    except KeyError:
        return 0


def stage_cycle():
    while True:
        games_to_modify = database.games.find({'game': 'mafia', 'next_stage_time': {'$lte': time()}})
        for game in games_to_modify:
            game_state = is_game_over(game)
            if game_state:
                role = role_titles['peace' if game_state == 1 else 'mafia']
                for player in game['players']:
                    player_role = player['role'] if player['role'] != 'don' else 'mafia'
                    inc_dict = {'total': 1, f'{player_role}.total': 1}
                    if (
                        (game_state == 1 and player_role != 'mafia') or
                        (game_state == 2 and player_role == 'mafia')
                    ):
                        inc_dict['win'] = 1
                        inc_dict[f'{player_role}.win'] = 1
                    database.stats.update_one(
                        {'id': player['id'], 'chat': game['chat']},
                        {'$set': {'name': player['full_name']}, '$inc': inc_dict},
                        upsert=True
                    )
                stop_game(game, reason=f'Победили игроки команды "{role}"!')
                continue

            game = go_to_next_stage(game)


def croco_cycle():
    while True:
        curtime = time()
        games = list(database.games.find({'game': 'croco', 'time': {'$lte': curtime}}))
        for game in games:
            if game['stage'] == 0:
                database.games.update_one({'_id': game['_id']}, {'$set': {'stage': 1, 'time': curtime + 60}})
                bot.try_to_send_message(game['chat'], f'{game["name"].capitalize()}, до конца игры осталась минута!')
            else:
                database.games.delete_one({'_id': game['_id']})
                bot.try_to_send_message(game['chat'], f'Игра окончена! {game["name"].capitalize()} проигрывает, загаданное слово было {game["word"]}.')
                database.stats.update_one(
                    {'id': game['player'], 'chat': game['chat']},
                    {'$set': {'name': game['full_name']}, '$inc': {'croco.total': 1}},
                    upsert=True
                )


def start_thread(name=None, target=None, *args, daemon=True, **kwargs):
    thread = Thread(*args, name=name, target=target, daemon=daemon, **kwargs)
    logger.debug(f'Запускаю процесс <{thread.name}>')
    thread.start()


def run_app():
    app = flask.Flask(__name__)

    @app.route('/' + config.TOKEN, methods=['POST'])
    def webhook():
        if flask.request.headers.get('content-type') == 'application/json':
            json_string = flask.request.get_data().decode('utf-8')
            update = Update.de_json(json_string)
            log_update(update)
            bot.process_new_updates([update])
            return ''
        else:
            flask.abort(403)

    app.run(
        host=config.SERVER_IP,
        port=config.SERVER_PORT,
        ssl_context=(config.SSL_CERT, config.SSL_PRIV),
        debug=False
    )


def main():
    start_thread('Stage Cycle', stage_cycle)
    start_thread('Removing Requests', remove_overtimed_requests)
    start_thread('Crocodile Cycle', croco_cycle)

    if config.SET_WEBHOOK:
        url = f'https://{config.SERVER_IP}:{config.SERVER_PORT}/'
        logger.debug(f'Запускаю приложение по адресу {url}')
        run_app()
        bot.remove_webhook()
        bot.set_webhook(url=url + config.TOKEN)
    else:
        bot.polling()
