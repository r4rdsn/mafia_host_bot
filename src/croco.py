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

import codecs
import random
from os.path import getsize

FILE_PATH = '/root/alfbot/base/words.txt'
FILE_SIZE = getsize(FILE_PATH)

def get_word():
    with codecs.open(FILE_PATH, 'r', encoding='cp1251') as base:
        offset = random.randrange(FILE_SIZE)
        base.seek(offset)
        base.readline()
        word = base.readline()[:-2]
    return word
