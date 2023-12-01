from flask import Flask, render_template, request, redirect, url_for, jsonify

from login_logic import *
from decorators import error_catcher, if_exist

from forms import *
from flask_bootstrap import Bootstrap5
from flask_cors import CORS

from exceptions import UserNotFound, UserAlreadyExist, CantBeEmpty, GameNotFound, CollectionNotFound

import json
# брати інфу з стіму ?
# for game in user_id.get_field("games"):
#     total_spend += game["Hours played"]

# персональна статистика ( скільки награно годин всього, улюблене, діаграма ( всього награнао, зараз граю), найчастіший тег з кожної категорії):


# створювати свої списки

# добавадять игры ( поиск) - страница колекции
# переключатель edit mode - страница колекции и страница КоллекЦИЙ

# у гри показувати скільки середнеє награли в  гру
# статистика на сторінку гри, скільки грають, скільки пограли тд

# коментарии к играм
# видавець гри, сторінка видавця
# франшизи


app = Flask(__name__)
app.config["SECRET_KEY"] = 'c42e8d7afdsdfds56342385cb9e30b6b'
CORS(app)
login_manager.init_app(app)
csrf = CSRFProtect(app)
bootstrap = Bootstrap5(app)


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("main.html")


@app.route("/login", methods=["GET"])
@error_catcher
def login():
    if isinstance(current_user, User):
        return authenticate(current_user.user_id, "", True)
    return render_template("login.html", form=LoginForm())


@app.route("/login", methods=["POST"])
@error_catcher
def login_post():
    form = request.form.to_dict()
    user_id = form["user_id"]
    password = form["password"]
    return authenticate(user_id, password)


@app.route('/logout')
@error_catcher
def logout():
    logout_user()
    return redirect(url_for('login'))

# @app.route("/create-account", methods=["GET", "POST"])
# @error_catcher
# def create_account():
#     form = CreateForm()
#     if request.method == "GET":
#         return render_template("create_account.html", form=form)

#     user_id = form.user_id.data
#     password = form.password.data
#     mail = form.mail.data
#     try:
#         uh.add_user(user_id, {"password": password, "mail": mail})
#     except Exception:
#         raise UserAlreadyExist
#     return authenticate(user_id, password)


@app.route("/profile/<user_id>/", methods=["GET"])
# @error_catcher
@if_exist("user-nth")
def user_page_get(user_id):

    user_id = User(user_id)
    info = user_id.get_fields({
        "account_created": 1,
        "steam_link": 1,
        "favorites": 1,
        "all_criterias": 1,
        "games_amount": {"$size": "$games"}
    })
    # print(info)
    info["favorites"]["games"] = list(user_id.get_games(info["favorites"]["games"], {"display_name": 1, "_id": 0}))

    # info["all_criterias"] = user_id.criterias_to_order(info["all_criterias"]["order"], info["all_criterias"]["criterias"])
    return render_template("user_page.html", info=info)


@ app.route("/profile/<user_id>/list", methods=["GET"])
# @error_catcher
@if_exist("user-nth")
def user_list_get(user_id):
    user = User(user_id)

    user_status = request.args.to_dict().get("status")
    user_tag = request.args.to_dict().get("tag")

    if user_status and user_tag:
        info = user.get_pipeline({"$project": {
            "_id": 1,
            "games": {
                "$filter": {
                    "input": "$games",
                    "as": "game",
                    "cond": {
                        "$and": [
                            {"$eq": ["$$game.Status", user_status]},
                            {"$in": [user_tag, "$$game.Tags"]}]
                    }
                }
            },
            "show_info": 1,
            "all_criterias": 1
        }})

    elif user_status:
        info = user.get_pipeline({"$project": {
            "_id": 1,
            "games": {
                "$filter": {
                    "input": "$games",
                    "as": "game",
                    "cond": {"$eq": ["$$game.Status", user_status]}
                }
            },
            "show_info": 1,
            "all_criterias": 1
        }})

    elif user_tag:
        info = user.get_pipeline({"$project": {
            "_id": 1,
            "games": {
                "$filter": {
                    "input": "$games",
                    "as": "game",
                    "cond": {"$in": [user_tag, "$$game.Tags"]}
                }
            },
            "show_info": 1,
            "all_criterias": 1
        }})

    else:
        info = user.get_fields({"show_info": 1, "games": 1, "all_criterias": 1})

    if not info.get("games"):
        info['games'] = []

    info["order"] = info["all_criterias"].copy()
    info['order']['Status'] = confg.statuses
    info["all_criterias"] = info["all_criterias"].keys()

    games_name = [game["game_id"] for game in info["games"]]
    games_additional_info = list(user.get_games(games_name, {"display_name": 1, "image": 1}))
    info["games"] = user.validate_criterias_in_games(info["games"], info["all_criterias"], games_additional_info)

    return render_template("user_list.html", confg_statuses=confg.statuses, user_status=user_status, info=info, json=json.dumps)


# @ app.route("/profile/<user_id>/collections", methods=["GET", "POST"])
# # @error_catcher
# def collections(user_id):
#     if request.method == "GET":
#         try:
#             user_id = User(user_id)
#         except Exception:
#             raise UserNotFound

#         return render_template("collections.html", user_id=user_id, form=AddCollection())

#     form = request.form.to_dict()
#     current_user.add_collection(form["new_collection_name"])

#     return redirect(f"/profile/{current_user.user_id}/collections/{form['new_collection_name']}")


# @ app.route("/profile/<user_id>/collections/<collection_name>", methods=["GET", "POST"])
# # @error_catcher
# def one_collection(user_id, collection_name):
#     try:
#         if not uh.users_collection.find_one({"_id": user_id}):
#             user_id = User(user_id)
#     except Exception:
#         raise UserNotFound

#     try:
#         collection = user_id.get_field("collections")[collection_name]
#     except Exception:
#         raise CollectionNotFound

#     if request.method == "GET":

#         return render_template("one_collection.html", collection={"content": collection, "name": collection_name}, user_id=user_id)

#     form = request.form.to_dict()
#     match form["action"]:

#         case "Delete":
#             current_user.delete_collection(collection_name)
#             return redirect(f'/profile/{current_user.user_id}/collections')
#             # print(f"Delete col {collection_name}")
#         case "ChangeName":
#             current_user.change_collection_name(collection_name, form['new_collection_name'])
#             return redirect(f'/profile/{current_user.user_id}/collections/{form["new_collection_name"]}')
#             # check if already name taken
#             # print(f"change name for col {collection_name} to { form['new_collection_name']}")


# @ app.route("/user-update-collection", methods=["POST"])
# def user_update_collection():
#     request_dic = request.get_json()["SendedInfo"]
#     print(f"user {request_dic['user']}need to add game {request_dic['add_game']} to collection {request_dic['collection']}")
#     return "", 200


@ app.route("/settings", methods=["GET"])
# @error_catcher
@ login_required
def user_settings_get():

    info = current_user.get_fields({"all_criterias": 1, "show_info": 1, "steam_link": 1})

    steam_form = SteamAccountForm()
    steam_form.steam_link.default = info["steam_link"]
    steam_form.process()

    user_show_info = info["show_info"]
    rest_criterias = [el for el in confg.basic_criterias if el not in user_show_info]

    return render_template("user_settings.html", criterias=info["all_criterias"], steam_form=steam_form, rest_criterias=rest_criterias, user_show_info=user_show_info)


@ app.route("/settings", methods=["POST"])
# @error_catcher
@ login_required
def user_settings_post():
    form = request.form.to_dict()
    # print(form)

    # return "a"

    # for field in form.values():
    #     if not field:
    #         raise CantBeEmpty

    # if not form:
    # return render_template("user_2_settings.html", criterias=criterias, need_to_edit=None, steam_form=steam_form, rest_criterias=rest_criterias, user_show_info=user_show_info)

    # elif need_to_edit := form.get("working_criteria_name_start_edit"):
    # return render_template("user_2_settings.html", criterias=criterias, need_to_edit=need_to_edit, steam_form=steam_form, rest_criterias=rest_criterias, user_show_info=user_show_info)

    if steam_link := form.get("steam_link"):
        current_user.update_field("steam_link", steam_link)
        return redirect(url_for("user_settings_get"))

    match form['action']:
        case "change_criteria":
            # print(form)
            new_values, values_to_delete = {}, []
            for name in form:
                if not name.startswith("__name"):
                    if name.startswith("__checkbox"):
                        values_to_delete.append(form[name])
                    continue

                new_values[name.split("__name")[1]] = form[name]

            for value in values_to_delete:
                del new_values[value]

            info = current_user.get_fields({"all_criterias": 1, "games": {"criterias": 1, "game_id": 1}})
            info["games"] = current_user.validate_criterias_in_games(info["games"], info["all_criterias"])
            # print(info)

            current_user.change_criteria(form["change_criteria_name"], form["new_criteria_name"], new_values, info)

            # print(new_values, values_to_delete, form["new_criteria_name"], form["change_criteria_name"])

        case "new_criteria":
            new_criteria_name = form["new_criteria_name"]
            current_user.add_criteria(new_criteria_name)

        case "delete_criteria":
            delete_criteria_name = form['delete_criteria_name']
            current_user.delete_criteria(delete_criteria_name)

        case "update_criterias_order":
            criterias_order = []
            for field in form:
                if not field.startswith("__name"):
                    continue
                criterias_order.append(form[field])
            current_user.update_field("all_criterias.order", criterias_order)

        case "update_basic_criterias":
            user_show_info = []
            for field in form:
                if not field.startswith("__checkbox"):
                    continue
                user_show_info.append(form[field])
            current_user.update_field("show_info", user_show_info)

    return redirect(url_for("user_settings_get"))

    # elif form.get("add_value"):
    #     current_user.add_value_to_criteria(form["add_value"], form["new_value"])
    #     criterias = current_user.get_field("all_criterias")
    #     return render_template("user_2_settings.html", criterias=criterias, need_to_edit=form["add_value"], steam_form=steam_form, rest_criterias=rest_criterias, user_show_info=user_show_info)

    # elif form.get("update_basic_criterias"):
    #     user_show_info = []
    #     for field in form:
    #         # print(form)
    #         if not field.startswith("__checkbox"):
    #             continue
    #         user_show_info.append(form[field])
    #     current_user.add_field("show_info", user_show_info)
    #     return redirect(url_for("user_settings"))

    # changing_criteria_name = form["working_criteria_name_commit"]

    # new_values = {}
    # # print(form)

    # for value in form:
    #     if "__name" not in value or value.split("__")[0] + "__checkbox" in form:
    #         if "__checkbox" in value:
    #             current_user.delete_value_from_criteria(changing_criteria_name, form[value])
    #         continue
    #     new_values[value.split("__name")[0]] = form[value]

    # # print(new_values)
    # current_user.change_criteria(changing_criteria_name, form["criteria_name"], new_values)

    # return redirect(url_for("user_settings"))


# @ app.route("/setting-update-criterias", methods=["GET", "POST"])
# # @error_catcher
# def update_order_values():
#     if request.method == "GET":
#         return redirect("/")
#     if request.method == "POST":

#         criterias_order = []
#         print(request.get_json()["itemOrder"])
#         for dic in (request_dic := request.get_json()["itemOrder"]):
#             criterias_order.insert(dic["order"], dic['id'])
#         uh.add_field_to_user(request_dic[0]["user"], {"all_criterias.order": criterias_order})
#         return "", 200


@ app.route("/game/<game_id>", methods=["GET"])
# @error_catcher
# @login_required
@ if_exist("game-game")
def game_page_get(game, game_id):
    if current_user.is_authenticated:
        user_info = current_user.get_fields({"games": {"$elemMatch": {"game_id": game_id}}, "favorites.games": 1})
        # print(user_info)
        if user_info.get("games"):
            if user_info["games"][0]["game_id"] in user_info["favorites"]["games"]:
                favorite, have_game = 1, 1
            else:
                favorite, have_game = None, 1
        else:
            favorite, have_game = None, None
    else:
        favorite, have_game = None, None

    return render_template("game_page.html", game=game, favorite=favorite, have_game=have_game)


@ app.route("/game/<game_id>", methods=["POST"])
@ error_catcher
def game_page_post(game_id):
    if request.form.get("add_to_favorites") and len(current_user.get_fields({"favorites.games": 1})["favorites"]["games"]) < 10:
        current_user.add_to_favorites("games", game_id)
    elif request.form.get('remove_from_favorites'):
        current_user.remove_from_favorites("games", game_id)

    return redirect(f"/game/{game_id}")


# @ app.route("/game/add", methods=["GET", "POST"])
# # @ login_required
# def add_game_page():
#     # if current_user.role != "admin":
#     #     return "dont have permission"

#     form = AddGameForm()
#     if request.method == 'GET':
#         return render_template("add_game_page.html", form=form)

#     new_game_name = form.name.data
#     gh.add_game(new_game_name)
#     return redirect(f"/game/{new_game_name}")


# @ app.route("/game/<game_id>/change", methods=["GET", "POST"])
# @ login_required
# def change_game_page(game_id):
#     if current_user.role != "admin":
#         return "dont have permission"

#     form = AddGameFieldForm()
#     if request.method == 'GET':
#         return render_template("change_game_page.html", form=form)

#     new_field_name = form.new_field_name.data
#     new_field_value = form.new_field_value.data
#     gh.add_field_to_game(game_id, new_field_name, new_field_value)
#     return redirect(f"/game/{game_id}")


@ app.route("/change/game/<game_id>", methods=["GET"])
@ login_required
@ if_exist("game-name-image")
def change_user_game_page_get(game_additional_info, game_id):
    # info = current_user.get_fields({"games": {"$elemMatch": {"game_id": game_id}}, "all_criterias": 1})
    # info = current_user.get_user_request({"_id": current_user.id}, {"games": {"$elemMatch": {"game_id": game_id}}, "all_criterias": 1})
    info = current_user.get_fields({"games": {"$elemMatch": {"game_id": game_id}}, "all_criterias": 1})
    # print(info["all_criterias"])
    # print(info)
    # return info
    if not info.get("games"):
        # print("innnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn")
        current_user.user_add_new_game(game_id)
        info = current_user.get_fields({"games": {"$elemMatch": {"game_id": game_id}}, "all_criterias": 1})
        # print(info["all_criterias"])

    # print(info[''])
    info['game'] = info["games"][0]
    del info["games"]

    # print(info)
    # info["all_criterias"] = current_user.criterias_to_order(info["all_criterias"]["order"], info["all_criterias"]["criterias"])
    # print(info["all_criterias"])

    # print(info["game"]["criterias"], "-----------------------------")
    # info["game"]["criterias"] = {criteria_obj["criteria_name"]: criteria_obj["criteria_value"] for criteria_obj in info["game"]["criterias"]}

    # print(info["game"]["criterias"], "-----------------------------")

    info["game"] = current_user.validate_criterias_in_games([info["game"]], info["all_criterias"], [game_additional_info])[game_id]

    info["game"]["game_id"] = game_id

    for attr in GameInfoForm.__dict__.copy():
        if not attr.startswith("D_"):
            continue
        delattr(GameInfoForm, attr)

    # print(info["all_criterias"], "==================================")
    for criteria_name, criteria_values in info["all_criterias"].items():
        if (current_value := info["game"]["criterias"].get(criteria_name)):
            setattr(GameInfoForm, "D_" + criteria_name, SelectField(criteria_name, choices=criteria_values + ["-"], default=current_value))
        else:
            setattr(GameInfoForm, "D_" + criteria_name, SelectField(criteria_name, choices=criteria_values + ["-"], default="-"))

    setattr(GameInfoForm, "D_" + "submit", SubmitField("Commit"))

    form = GameInfoForm()

    if date := info["game"]["info"].get("Started playing"):
        form.started_playing.default = datetime.strptime(date, "%d-%m-%Y")
    else:
        form.started_playing.default = datetime.now()

    form.status.default = info["game"]["info"].get("Status")
    form.hours_played.default = info["game"]["info"].get("Hours played")
    form.tags.default = "; ".join(info["game"]["info"].get("Tags"))
    form.process()

    # print(info)
    # print(info['game']["additional_info"]['name'])
    # print(info['game']['game_id'])
    return render_template("change_user_game_page.html", info=info, form=form)


@ app.route("/change/game/<game_id>", methods=["POST"])
@ login_required
def change_user_game_page_post(game_id):
    form = request.form.to_dict()

    if form.get("delete_from_account"):
        current_user.delete_game(game_id)
        return redirect(f"/profile/{current_user.user_id}/list")

    all_criterias = current_user.get_fields({"all_criterias.order": 1})["all_criterias"]["order"]
    # print(all_criterias)
    valid_game_criterias = {}
    for criteria in all_criterias:
        valid_game_criterias[criteria] = form["D_" + criteria]

    if len((date := form['started_playing'].split('-'))) == 3:
        date = f"{date[2]}-{date[1]}-{date[0]}"
    else:
        date = None

    valid_game_criterias = [{"criteria_name": criteria_name, "criteria_value": criteria_value} for criteria_name, criteria_value in valid_game_criterias.items()]
    current_user.update_user_game(game_id, {"game_id": game_id,
                                            "criterias": valid_game_criterias,
                                            "Status": form["status"],
                                            "Started playing": date,
                                            "Hours played": form["hours_played"],
                                            "Tags": [tag.strip() for tag in form["tags"].split(";") if tag.strip()]
                                            })

    return redirect(f"/profile/{current_user.user_id}/list#{game_id}")


# Api
@ app.route("/api/all-games", methods=["GET"])
def api_all_games():
    return jsonify(gh.get_games_ids_and_names())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
