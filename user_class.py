from flask_login import UserMixin

from work_with_db import UsersHelper, GamesHelper

uh = UsersHelper()
gh = GamesHelper()


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self.user_id = self.id

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

            info["all_criterias"] = self.criterias_to_order(info["all_criterias"]["order"],
                                                            info["all_criterias"]["criterias"])
            return info

        return uh.users_collection.find_one({"_id": self.user_id}, request)

    def get_pipeline(self, user_pipeline: dict):
        pipeline = [{"$match": {"_id": self.user_id}}]
        pipeline.append(user_pipeline)
        return list(uh.users_collection.aggregate(pipeline))[0]

    def validate_criterias_in_games(self, all_games_with_criterias, all_criterias_names, games_additional_info=None):

        if games_additional_info:
            games_additional_info = {_game['_id']: {'image': _game['image'], 'name': _game['display_name']} for _game in
                                     games_additional_info}
        else:
            games_additional_info = None
        valid_games_list = {}

        for game in all_games_with_criterias:
            game["criterias"] = {criteria_obj["criteria_name"]: criteria_obj["criteria_value"] for criteria_obj in
                                 game["criterias"]}

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
            valid_games_list[game["game_id"]]["additional_info"] = games_additional_info[
                game['game_id']] if games_additional_info else None

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
                    "all_criterias.criterias": {"criteria_name": new_criteria_name,
                                                "criteria_values": new_values if new_values else []},
                    "all_criterias.order": new_criteria_name
                }
            }
        )

    def change_criteria(self, old_criteria_name, new_criteria_name, new_criteria_values, info):
        if (if_new := old_criteria_name != new_criteria_name) or list(new_criteria_values.values()) != \
                info["all_criterias"][
                    old_criteria_name]:

            self.delete_criteria(old_criteria_name, if_new)
            self.add_criteria(new_criteria_name, list(new_criteria_values.values()))

            for game, game_info in info["games"].items():
                if game_info["criterias"].get(old_criteria_name) and game_info["criterias"][old_criteria_name] != "-":
                    print("in if")
                    print(
                        f'need to change_criteria {new_criteria_name}in {game}, was {game_info["criterias"][old_criteria_name]}, will be {new_criteria_values[game_info["criterias"][old_criteria_name]]}')

                    uh.users_collection.update_one(
                        {"_id": self.user_id, "games.game_id": game},
                        {"$pull": {"games.$.criterias": {"criteria_name": old_criteria_name}}})

                    uh.users_collection.update_one(
                        {"_id": self.user_id, "games.game_id": game},
                        {"$addToSet": {"games.$.criterias": {"criteria_name": new_criteria_name,
                                                             "criteria_value": new_criteria_values[
                                                                 game_info['criterias'][old_criteria_name]]}}}
                    )

                    # if is_new:

    def delete_criteria(self, criteria_name, if_new):
        if not if_new:
            uh.users_collection.update_one(
                {"_id": self.user_id},
                {"$pull": {
                    "all_criterias.criterias": {"criteria_name": criteria_name}
                }})
            return

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

    def get_games(self, games_id_list: list, request: dict = None):
        return list(gh.games_collection.find({"_id": {"$in": games_id_list}}, request))

    def add_info_to_games_from_collections(self, collections: dict):
        games_names = []
        for collection in collections:
            for game_obj in collection["games"]:
                games_names.append(game_obj['game_id'])

        # games_names = user.extract_games_names_from_collections(collection["collections"])
        games_additional_info = self.get_games(games_names, {"_id": 1, "display_name": 1, "image": 1})
        games_additional_info = {game["_id"]: (game["display_name"], game['image']) for game in games_additional_info}
        for game in collections[0]['games']:
            game['info'] = games_additional_info[game['game_id']]

        return collections[0]

    def add_collection(self, new_collection_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$addToSet": {"collections": {"collection_name": new_collection_name,
                                           "games": [],
                                           "games_order": [],
                                           "collection_note": ""}}}
        )

    def delete_collection(self, collection_name):
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$pull": {"collections": {"collection_name": collection_name}}}
        )

    def uptade_collection(self, new_collection: dict, collection_name):

        self.delete_collection(collection_name)
        uh.users_collection.update_one(
            {"_id": self.user_id},
            {"$addToSet": {"collections": new_collection}}
        )
