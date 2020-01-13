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


from config import LOGGER_LEVEL
import logging


class c:
    l = '\033[0;32m'
    g = '\033[0;37m'
    e = '\033[0m'


def configure_logger():
    logger = logging.getLogger("mafbot")
    logger.setLevel(LOGGER_LEVEL)
    terminal_logger = logging.StreamHandler()
    formatter = logging.Formatter(f"\r{c.g}[%(asctime)s.%(msecs).03d]{c.e} %(message)s", datefmt="%H:%M:%S")
    terminal_logger.setFormatter(formatter)
    logger.addHandler(terminal_logger)
    logger.propagate = False
    return logger


logging.getLogger('werkzeug').setLevel(logging.ERROR)
logger = configure_logger()


def log_update(update):
    if update.message:
        chat = update.message.chat.id
        id = update.message.from_user.id
        msg = update.message.text if update.message.text else ''
        qc = c.e
    elif update.callback_query:
        chat = update.callback_query.message.chat.id
        id = update.callback_query.from_user.id
        msg = update.callback_query.data
        qc = c.l
    else:
        return

    logger.info(f'<{chat:>14}:{id:<9}> {qc}{repr(msg)[1:-1]}{c.e}')
