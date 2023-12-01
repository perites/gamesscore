from flask_login import UserMixin, current_user
import json

import confg

from work_with_db import UsersHelper, GamesHelper
uh = UsersHelper()
gh = GamesHelper()


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self.user_id = self.id
        # self.role = self.get_field("role")

    def criterias_to_order(self, criterias_order, criterias):
        orderd_cryterias = {}
        for key in criterias_order:
            for criteria in criterias:
                if criteria["criteria_name"] == key:
                    orderd_cryterias[key] = criteria['criteria_values']

        return orderd_cryterias

    def get_fields(self, request: dict):
        if "all_criterias" in request.keys() and request["all_criterias"] == 1:
            info = uh.users_collection.find_one({"_id": self.user_id}, request)

            info["all_criterias"] = self.criterias_to_order(info["all_criterias"]["order"], info["all_criterias"]["criterias"])
            return info

        return uh.users_collection.find_one({"_id": self.user_id}, request)

    def get_pipeline(self, user_pipeline: dict):
        pipeline = [{"$match": {"_id": self.user_id}}]
        pipeline.append(user_pipeline)
        return list(uh.users_collection.aggregate(pipeline))[0]

    def validate_criterias_in_games(self, all_games_with_criterias, all_criterias_names, games_additional_info=None):

        if games_additional_info:
            games_additional_info = {_game['_id']: {'image': _game['image'], 'name': _game['display_name']} for _game in games_additional_info}
        else:
            games_additional_info = None
        valid_games_list = {}

        for game in all_games_with_criterias:
            game["criterias"] = {criteria_obj["criteria_name"]: criteria_obj["criteria_value"] for criteria_obj in game["criterias"]}

            valid_game_criterias_list = {}
            for criteria in all_criterias_names:

                if criteria not in game["criterias"]:
                    valid_game_criterias_list[criteria] = "-"
                else:
                    valid_game_criterias_list[criteria] = game["criterias"][criteria]

            valid_games_list[game["game_id"]] = {}
            del game["criterias"]

            valid_games_list[game["game_id"]]["criterias"] = valid_game_criterias_list

            valid_games_list[game["game_id"]]["info"] = game
            valid_games_list[game["game_id"]]["additional_info"] = games_additional_info[game['game_id']] if games_additional_info else None

            # print(valid_games_list[game["game_id"]]["criterias"])

        return valid_games_list

    def update_field(self, field, value, r_type="dict"):
        match r_type:
            case "dict":
                uh.users_collection.update_one({"_id": self.user_id}, {"$set": {field: value}})
            case "list":
                uh.users_collection.update_one({"_id": self.user_id}, {"$addToSet": {field: value}})

    def add_criteria(self, new_criteria_name, new_values=None):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {
                "$addToSet": {
                    "all_criterias.criterias": {"criteria_name": new_criteria_name, "criteria_values": new_values if new_values else []},
                    "all_criterias.order": new_criteria_name
                }
            }
        )

    def change_criteria(self, old_criteria_name, new_criteria_name, new_criteria_values, info):
        if old_criteria_name != new_criteria_name or list(new_criteria_values.values()) != info["all_criterias"][old_criteria_name]:

            self.delete_criteria(old_criteria_name)
            self.add_criteria(new_criteria_name, list(new_criteria_values.values()))

            # info["game"]["criterias"] = {criteria_obj["criteria_name"]: criteria_obj["criteria_value"] for criteria_obj in info["game"]["criterias"]}
            # print(info['games'])
            for game, game_info in info["games"].items():
                if game_info["criterias"].get(old_criteria_name) and game_info["criterias"][old_criteria_name] != "-":
                    print("in if")
                    print(f'need to change_criteria { new_criteria_name }in {game}, was {game_info["criterias"][old_criteria_name]}, will be {new_criteria_values[game_info["criterias"][old_criteria_name]]}')

                    uh.users_collection.update_one(
                        {"_id": self.user_id, "games.game_id": game},
                        {"$pull": {"games.$.criterias": {"criteria_name": old_criteria_name}}})

                    uh.users_collection.update_one(
                        {"_id": self.user_id, "games.game_id": game},
                        {"$addToSet": {"games.$.criterias": {"criteria_name": new_criteria_name, "criteria_value": new_criteria_values[game_info['criterias'][old_criteria_name]]}}}
                    )

                    # if is_new:

    def delete_criteria(self, criteria_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$pull": {
                "all_criterias.criterias": {"criteria_name": criteria_name},
                "all_criterias.order": criteria_name
            }})

    def user_add_new_game(self, game_id):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$addToSet": {"games": {"game_id": game_id,
                                     "criterias": [],
                                     "Started playing": "",
                                     "Status": "",
                                     "Hours played": "",
                                     "Tags": []}}}
        )

    def update_user_game(self, game_id, updated_info):
        uh.users_collection.update_one(
            {"_id": self.user_id, "games.game_id": game_id},
            {"$set": {"games.$": updated_info}}
        )

    def delete_game(self, game_id):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$pull": {"games": {"game_id": game_id}}}
        )

    def add_to_favorites(self, fav_type, obj_id):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$addToSet": {f"favorites.{fav_type}": obj_id},
             })

    def remove_from_favorites(self, fav_type, obj_id):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$pull": {f"favorites.{fav_type}": obj_id},
             })

    def get_games(self, games_id_list: list, request: dict=None):
        return gh.games_collection.find({"_id": {"$in": games_id_list}}, request)

    # def get_all_criterias(self):
    #     all_criterias = self.get_field("all_criterias")
    #     all_criterias["Status"] = confg.statuses
    #     return json.dumps(all_criterias)

    # def get_all_collections(self):
    #     return json.dumps(self.get_field("collections"))

    # def get_game(self, game_id, request):
    #     return gh.games_collection.find_one({"_id": game_id}, request)

        # print(criterias_order, criterias)

    # def get_tags(self, game):
    #     tags_str = game.get("Tags")
    #     return list(map(lambda x: x.strip(), tags_str.split(";")))[0:-1] if tags_str else []

    # def all_games_amount(self):
    #     return len(self.get_field("games").keys())

    # def account_created(self):
    #     return self.get_one_field("account_created")

    # def get_user_request(self, *request):
    #     #     # if "all_criterias" in request[1].keys() and request[1]["all_criterias"] == 1:
    #     #     #     info = uh.users_collection.find_one(*request)
    #     #     #     info["all_criterias"] = self.criterias_to_order(info["all_criterias"]["order"], info["all_criterias"]["criterias"])
    #     #     #     return info

    #     return uh.users_collection.find_one(*request)

    # def update_game_field(self, game_id, field_name, new_field_values):
    #     all_games = current_user.get_field("games")
    #     if not all_games.get(game_id):
    #         all_games[game_id] = {}
    #     all_games[game_id][field_name] = new_field_values
    #     self.add_field("games", all_games)

    # def get_game_image(self, game_id):
    #     return gh.get_game_image(game_id)

    # def delete_value_from_criteria(self, criteria, value):
    #     uh.users_collection.update_one(
    #         {"_id": self.user_id},
    #         {"$pull": {f"all_criterias.criterias.{criteria}": value}}
    #     )

    # def add_value_to_criteria(self, criteria, value):
    #     print(f"add {value} to {criteria}")
    #     uh.users_collection.update_one(
    #         {"_id": self.user_id},
    #         {"$addToSet": {f"all_criterias.criterias.{criteria}": value}}
    #     )

    # def find_game(self, game_id):
    #     return gh.find_game_by_id(game_id)

    def add_collection(self, collection_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$set": {f"collections.{collection_name}": {}}}
        )

    def delete_collection(self, collection_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$unset": {f"collections.{collection_name}": ""}}
        )

    def change_collection_name(self, old_collection_name, new_collection_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$set": {f"collections.{new_collection_name}": self.get_field("collections")[old_collection_name]}}
        )

        self.delete_collection(old_collection_name)
