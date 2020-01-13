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


from pymongo import MongoClient, ReturnDocument

client = MongoClient()
database = client.mafia_host_bot


def get_new_id(collection):
    counter = database.counter.find_one_and_update(
        {"_id": collection},
        {"$inc": {"next": 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True
    )

    return counter["next"]
