from pymongo import MongoClient, ASCENDING

import confg

import datetime


class DbHelper():
    def __init__(self):
        self.client = MongoClient(*confg.client)
        self.db = self.client[confg.database_name]


class UsersHelper(DbHelper):
    def __init__(self):
        super().__init__()
        self.users_collection = self.db["users_collection"]


class GamesHelper(DbHelper):
    def __init__(self):
        super().__init__()
        self.games_collection = self.db["games_collection"]

    def get_games_ids_and_names(self, games_id_list=None):
        return list(self.games_collection.find({}, {"_id": 1, "display_name": 1}))
