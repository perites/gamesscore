from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import render_template, redirect, request

from work_with_db import UsersHelper, GamesHelper

login_manager = LoginManager()
login_manager.login_view = 'login'
uh = UsersHelper()
gh = GamesHelper()

SESSION = []

# make all criterias an array


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self.user_id = self.id
        self.role = self.get_field("role")

    def all_games_amount(self):
        return len(self.get_field("games").keys())

    def account_created(self):
        return self.get_field("account_created")

    def add_field(self, field, value):
        uh.add_field_to_user(self.id, {field: value})

    def get_field(self, field):
        if field == "all_criterias":
            orderd_cryterias = {}
            current_user_criterias = uh.find_user_by_id(self.id)["all_criterias"]
            for key in self.get_field("criterias_order"):
                orderd_cryterias[key] = current_user_criterias[key]

            return orderd_cryterias

        return uh.find_user_by_id(self.id).get(field)

    def get_valid_games_criterias(self):
        valid_criterias_games_list = {}
        all_games_with_criterias = self.get_field("games")
        for game, game_info in all_games_with_criterias.items():
            valid_criterias_games_list[game] = {}
            for criteria in self.get_field("all_criterias").keys():
                if criteria not in game_info["criterias"].keys():
                    valid_criterias_games_list[game][criteria] = "-"
                else:
                    valid_criterias_games_list[game][criteria] = game_info["criterias"][criteria]

        return valid_criterias_games_list

    def update_game_field(self, game_id, field_name, new_field_values):
        all_games = current_user.get_field("games")
        if not all_games.get(game_id):
            all_games[game_id] = {}
        all_games[game_id][field_name] = new_field_values
        self.add_field("games", all_games)

    def get_game_image(self, game_id):
        return gh.get_game_image(game_id)

    def delete_game(self, game_id):
        all_games = self.get_field("games")
        del all_games[game_id]
        self.add_field("games", all_games)

    def add_criteria(self, new_criteria_name):
        uh.users_collection.update_many(
            {"_id": self.user_id},
            {"$set": {f"all_criterias.{new_criteria_name}": []},
             "$addToSet": {"_criterias_order": new_criteria_name}}  # fddddddddddddddddddddddddddddddddddddddddddddddddd
        )

    def change_criteria(self, old_criteria_name, new_criteria_name, new_criteria_values):
        all_criterias = self.get_field("all_criterias")
        del all_criterias[old_criteria_name]
        all_criterias[new_criteria_name] = new_criteria_values
        self.add_field("all_criterias", all_criterias)

    def delete_criteria(self, criteria_name):
        all_criterias = self.get_field("all_criterias")
        del all_criterias[criteria_name]
        self.add_field("all_criterias", all_criterias)

        criterias_order = current_user.get_field("criterias_order")
        del criterias_order[criteria_name]
        self.add_field("criterias_order", criterias_order)

    def delete_value_from_criteria(self, criteria, value):
        all_criterias = self.get_field("all_criterias")
        print(all_criterias)
        all_criterias[criteria].remove(value)
        print(all_criterias)
        self.add_field("all_criterias", all_criterias)

    def add_value_to_criteria(self, criteria, value):
        all_criterias = self.get_field("all_criterias")
        all_criterias[criteria].append(value)
        self.add_field("all_criterias", all_criterias)


@ login_manager.user_loader
def load_user(user_id):
    for user in SESSION:
        if user.user_id == user_id:
            return user


def authenticate(user_id, password, already_log=False, ):
    user = uh.find_user_by_id(user_id)
    if user and user["password"] == password or already_log:

        user = User(user_id)
        login_user(user)
        SESSION.append(user)

        next_url = request.args.get('next')
        return redirect(next_url) if next_url else redirect(f"/profile/{user_id}")

    return redirect('/login')
