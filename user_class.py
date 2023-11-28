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

    # def get_all_criterias(self):
    #     all_criterias = self.get_field("all_criterias")
    #     all_criterias["Status"] = confg.statuses
    #     return json.dumps(all_criterias)

    def get_all_collections(self):
        return json.dumps(self.get_field("collections"))

    def get_games(self, games_id_list: list, request: list=None):
        return gh.games_collection.find({"_id": {"$in": games_id_list}}, request)

    def get_game(self, game_id, request):
        return gh.games_collection.find_one({"_id": game_id}, request)

    def criterias_to_order(self, criterias_order, criterias):
        orderd_cryterias = {}
        for key in criterias_order:
            for criteria in criterias:
                if criteria["criteria_name"] == key:
                    orderd_cryterias[key] = criteria['criteria_values']

        return orderd_cryterias

        # print(criterias_order, criterias)

    # def get_tags(self, game):
    #     tags_str = game.get("Tags")
    #     return list(map(lambda x: x.strip(), tags_str.split(";")))[0:-1] if tags_str else []

    # def all_games_amount(self):
    #     return len(self.get_field("games").keys())

    # def account_created(self):
    #     return self.get_one_field("account_created")

    def update_field(self, field, value, r_type="dict"):
        match r_type:
            case "dict":
                uh.users_collection.update_one({"_id": self.user_id}, {"$set": {field: value}})
            case "list":
                uh.users_collection.update_one({"_id": self.user_id}, {"$addToSet": {field: value}})

    def user_add_new_game(self, game_id):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$addToSet": {f"games": {"game_id": game_id,
                                      "criterias": [],
                                      "Started playing": "",
                                      "Status": "",
                                      "Hours played": "",
                                      "Tags": ""}}}
        )

    def update_user_game(self, game_id, updated_info):
        uh.users_collection.update_one(
            {"_id": self.user_id, "games.game_id": game_id},
            {"$set": {"games.$": updated_info}}
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

    def get_user_request(self, *request):
        if "all_criterias" in request[1].keys() and request[1]["all_criterias"] == 1:
            info = uh.users_collection.find_one(*request)
            info["all_criterias"] = self.criterias_to_order(info["all_criterias"]["order"], info["all_criterias"]["criterias"])
            return info

        return uh.users_collection.find_one(*request)

    def get_field(self, field):
        if field == "all_criterias":
            info = uh.get_request(self.id, {field: 1})[field]
            info["all_criterias"] = self.criterias_to_order(info["order"], info["criterias"])
            return info['all_criterias']

        return uh.get_request(self.id, {field: 1})[field]

    def get_fields(self, request: list):
        if "all_criterias" in request.keys() and request["all_criterias"] == 1:
            info = list(uh.get_request([{"$match": {"_id": self.user_id}}, {"$project": request}]))[0]

            info["all_criterias"] = self.criterias_to_order(info["all_criterias"]["order"], info["all_criterias"]["criterias"])
            return info

        return list(uh.get_request([{"$match": {"_id": self.user_id}}, {"$project": request}]))[0]

    def get_valid_games(self, all_games_with_criterias, all_criterias_names, games_additional_info, status=None, tag=None):

        games_additional_info = {_game['_id']: {'image': _game['image'], 'name': _game['display_name']} for _game in games_additional_info}
        valid_games_list = {}

        for game in all_games_with_criterias:

            if status and game["Status"] != status:
                continue
            if tag and tag not in game["Tags"]:
                continue

            valid_criterias_games_list = {}
            for criteria in all_criterias_names:
                if criteria not in game["criterias"].keys():
                    valid_criterias_games_list[criteria] = "-"
                else:
                    valid_criterias_games_list[criteria] = game["criterias"][criteria]

            valid_games_list[game["game_id"]] = {}
            del game["criterias"]

            valid_games_list[game["game_id"]]["criterias"] = valid_criterias_games_list

            game["Tags"] = list(map(lambda x: x.strip(), game["Tags"].split(";")[0:-1]))
            valid_games_list[game["game_id"]]["info"] = game
            valid_games_list[game["game_id"]]["additional_info"] = games_additional_info[game['game_id']]

        # print(valid_games_list)
        return valid_games_list

    # def update_game_field(self, game_id, field_name, new_field_values):
    #     all_games = current_user.get_field("games")
    #     if not all_games.get(game_id):
    #         all_games[game_id] = {}
    #     all_games[game_id][field_name] = new_field_values
    #     self.add_field("games", all_games)

    def get_game_image(self, game_id):
        return gh.get_game_image(game_id)

    def delete_game(self, game_id):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$pull": {"games": {"game_id": game_id}}}
        )

    def add_criteria(self, new_criteria_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$set": {f"all_criterias.criterias.{new_criteria_name}": []},
             "$addToSet": {f"all_criterias.order": new_criteria_name}}
        )

    def change_criteria(self, old_criteria_name, new_criteria_name, new_criteria_values):
        if (is_new := old_criteria_name != new_criteria_name) or list(new_criteria_values.values()) != self.get_fields({"all_criterias": 1})["all_criterias"][old_criteria_name]:

            # uh.users_collection.update_one(
            #     {"_id": self.user_id},
            #     {"$set": {f"all_criterias.criterias.{new_criteria_name}": list(new_criteria_values.values())},
            #      "$addToSet": {"all_criterias.order": new_criteria_name}}
            # )
          #       $elemMatch: {
          # "crietrias": {}

          #{"$elemMatch": {f"criterias.{old_criteria_name}": "$exists"}}

            print(list(uh.users_collection.find({"_id": self.id}, {'games': {"$elemMatch": {f"criterias": "$exists"}}})))
            return

            for game, game_criterias in self.get_fields({'games': {"criterias": 1}}.items()):
                if game_criterias.get(old_criteria_name) and game_criterias[old_criteria_name] != "-":
                    # print()
                    print(f"need to change_criteria { new_criteria_name }in {game}, was {game_criterias[old_criteria_name]}, will be {new_criteria_values[game_criterias[old_criteria_name]]}")

                    #
                    # uh.users_collection.update_one(
                    #     {"_id": self.user_id},
                    #     {"$set": {f"games.{game}.criterias.{new_criteria_name}": new_criteria_values[game_data['criterias'][old_criteria_name]]}}
                    # )

                    if is_new:
                        uh.users_collection.update_one(
                            {"_id": self.user_id},
                            {"$unset": {f"games.{game}.criterias.{old_criteria_name}": ""}, })

            if is_new:
                self.delete_criteria(old_criteria_name)
                # uh.users_collection.update_one(
                #     {"_id": self.user_id},
                #     {"$unset": {f"all_criterias.criterias.{old_criteria_name}": ""},
                #      "$pull": {"all_criterias.order": old_criteria_name}})

    def delete_criteria(self, criteria_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$unset": {f"all_criterias.criterias.{criteria_name}": ""},
             "$pull": {"all_criterias.order": criteria_name}})

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
