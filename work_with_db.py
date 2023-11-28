from pymongo import MongoClient

import confg

import datetime


class DbHelper():
    def __init__(self):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client[confg.database_name]
        self.users_collection = self.db["users_collection"]
        self.games_collection = self.db["games_collection"]


class UsersHelper(DbHelper):
    def all_users(self):
        return list(self.users_collection.find())

    def add_user(self, user_name, new_field: None):
        self.users_collection.insert_one({"_id": user_name, "account_created": datetime.datetime.now().strftime("%d/%m/%Y"),
                                          "games": {}, "all_criterias": {}, "role": "user",
                                          "show_info": ["status", "started_playing", "hours_played"],
                                          })

        if new_field:
            self.add_field_to_user(user_name, new_field)

    def add_field_to_user(self, _id, new_field):
        self.users_collection.update_one({"_id": _id}, {"$set": new_field})

    def find_user_by_id(self, _id):
        return self.users_collection.find_one({"_id": _id}, {"password": 1})

    def get_request(self, request):
        return self.users_collection.aggregate(request)


class GamesHelper(DbHelper):
    def find_game_by_id(self, game_id):
        return self.games_collection.find_one({"_id": game_id})

    def get_request(self, games_id_list, request):
        return self.games_collection.find({"_id": {"$in": games_id_list}}, request)

    def get_game_image(self, game_id):
        return self.find_game_by_id(game_id)["image"]

    def add_game(self, new_game_name):
        self.games_collection.insert_one({"_id": new_game_name})

    def get_games_ids_and_names(self):
        return list(self.games_collection.find({}, {"_id": 1, "display_name": 1}))

    def add_field_to_game(self, _id, new_field_name, new_field_value):
        self.games_collection.update_one({"_id": _id}, {"$set": {new_field_name: new_field_value}})


# my_acc = {
#     "password": "e",
#     "games": {
#         "rdr2": {
#             "criterias": {
#                 "Open world": "big",
#                 "Plot": "5"
#             },
#             "status": "Completed",
#             "started_playing": "14-03-2023",
#             "hours_played": "110"
#         },
#         "sekiro": {
#             "criterias": {
#                 "Open world": "normall",
#                 "Plot": "4"
#             },
#             "status": "Completed",
#             "started_playing": "10-07-2023",
#             "hours_played": "165"
#         },
#         "horizon": {
#             "criterias": {
#                 "Open world": "big",
#                 "Plot": "4"
#             }
#         }
#     },
#     "role": "admin",
#     "account_created": "23-11-2023",
#     "all_criterias": {
#         "Plot": [
#             "1",
#             "2",
#             "4",
#             "5",
#             "3"
#         ],
#         "Open world": [
#             "small",
#             "normall",
#             "big"
#         ],
#         "test": [
#             "yes",
#             "no"
#         ]
#     },
#     "show_info": [
#         "status",
#         "started_playing",
#         "hours_played"
#     ],
#     "steam_link": "https://steamcommunity.com/id/perites/"
# }

# new_data = {"games": {"rdr2": {"plot": 4, "open_world": "big"},
#                       "horizon": {"plot": 5, "open_world": "big"}}}


# uh = UsersHelper()
# uh.add_user("perite", my_acc)
# uh.add_field_to_user("perite", new_data)
# dbh.users_collection.drop()
# # for x in dbh.all_users():
# #     print(x)
# print(dbh.all_users())
# # dbh.add_user("der")
# print(dbh.all_users())

# user = {
#     "_id": "rdr2"
#     "year": 2018
# }
# result = users_collection.insert_one(user)
# result = users_collection.find({"_id": "1"})
# for user in result:
#     print(user, user["name"])
# # print()
