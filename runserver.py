import requests
from flask import Flask, url_for, jsonify, render_template
from flask_login import logout_user, current_user, login_required

from forms import *
from flask_bootstrap import Bootstrap5
from flask_cors import CORS

from login_logic import *
from decorators import error_catcher, if_exist
from user_class import gh

import json

# TODO брати інфу з стіму ?
# TODO адмін сторінка
# TODO рекомендації від користувачів
# TODO коментарии к играм


# TODO for game in user_id.get_field("games"):
# TODO     total_spend += game["Hours played"]
# TODO персональна статистика ( скільки награно годин всього, улюблене, діаграма ( всього награнао, зараз граю), найчастіший тег з кожної категорії):
# TODO у гри показувати скільки середнеє награли в  гру
# TODO статистика на сторінку гри, скільки грають, скільки пограли тд


# TODO видавець гри, сторінка видавця
# TODO франшизи


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
@error_catcher
@if_exist("user-nth")
def user_page_get(user_id):
    user = User(user_id)
    info = user.get_fields({
        "account_created": 1,
        "steam_link": 1,
        "favorites": 1,
        "all_criterias": 1,
        "games_amount": {"$size": "$games"}
    })
    info["favorites"]["games"] = list(user.get_games(info["favorites"]["games"], {"display_name": 1, "_id": 0}))

    return render_template("user_page.html", info=info)


@app.route("/profile/<user_id>/list", methods=["GET"])
@error_catcher
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

    return render_template("user_list.html", confg_statuses=confg.statuses, user_status=user_status, info=info,
                           json=json.dumps)


@app.route("/settings", methods=["GET"])
# @error_catcher
@login_required
def user_settings_get():
    info = current_user.get_fields({"all_criterias": 1, "show_info": 1, "steam_link": 1})

    steam_form = SteamAccountForm()
    steam_form.steam_link.default = info["steam_link"]
    steam_form.process()

    user_show_info = info["show_info"]
    rest_criterias = [el for el in confg.basic_criterias if el not in user_show_info]

    return render_template("user_settings.html", criterias=info["all_criterias"], steam_form=steam_form,
                           rest_criterias=rest_criterias, user_show_info=user_show_info)


@app.route("/settings", methods=["POST"])
# @error_catcher
@login_required
def user_settings_post():
    form = request.form.to_dict()

    if steam_link := form.get("steam_link"):
        current_user.update_field("steam_link", steam_link)
        return redirect(url_for("user_settings_get"))

    match form['action']:
        case "change_criteria":
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

            current_user.change_criteria(form["change_criteria_name"], form["new_criteria_name"], new_values, info)

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


@app.route("/game/<game_id>", methods=["GET"])
@error_catcher
@login_required
@if_exist("game-game")
def game_page_get(game, game_id):
    if current_user.is_authenticated:
        user_info = current_user.get_fields({"games": {"$elemMatch": {"game_id": game_id}}, "favorites.games": 1})
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


@app.route("/game/<game_id>", methods=["POST"])
@error_catcher
def game_page_post(game_id):
    if request.form.get("add_to_favorites") and len(
            current_user.get_fields({"favorites.games": 1})["favorites"]["games"]) < 10:
        current_user.add_to_favorites("games", game_id)
    elif request.form.get('remove_from_favorites'):
        current_user.remove_from_favorites("games", game_id)

    return redirect(f"/game/{game_id}")


@app.route("/change/game/<game_id>", methods=["GET"])
@login_required
@if_exist("game-name-image")
def change_user_game_page_get(game_additional_info, game_id):
    info = current_user.get_fields({"games": {"$elemMatch": {"game_id": game_id}}, "all_criterias": 1})

    if not info.get("games"):
        current_user.user_add_new_game(game_id)
        info = current_user.get_fields({"games": {"$elemMatch": {"game_id": game_id}}, "all_criterias": 1})

    info['game'] = info["games"][0]
    del info["games"]

    info["game"] = \
        current_user.validate_criterias_in_games([info["game"]], info["all_criterias"], [game_additional_info])[game_id]

    info["game"]["game_id"] = game_id

    for attr in GameInfoForm.__dict__.copy():
        if not attr.startswith("D_"):
            continue
        delattr(GameInfoForm, attr)

    for criteria_name, criteria_values in info["all_criterias"].items():
        if current_value := info["game"]["criterias"].get(criteria_name):
            setattr(GameInfoForm, "D_" + criteria_name,
                    SelectField(criteria_name, choices=criteria_values + ["-"], default=current_value))
        else:
            setattr(GameInfoForm, "D_" + criteria_name,
                    SelectField(criteria_name, choices=criteria_values + ["-"], default="-"))

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

    return render_template("change_user_game_page.html", info=info, form=form)


@app.route("/change/game/<game_id>", methods=["POST"])
@login_required
def change_user_game_page_post(game_id):
    form = request.form.to_dict()

    if form.get("delete_from_account"):
        current_user.delete_game(game_id)
        return redirect(f"/profile/{current_user.user_id}/list")

    all_criterias = current_user.get_fields({"all_criterias.order": 1})["all_criterias"]["order"]
    valid_game_criterias = {}
    for criteria in all_criterias:
        valid_game_criterias[criteria] = form["D_" + criteria]

    if len((date := form['started_playing'].split('-'))) == 3:
        date = f"{date[2]}-{date[1]}-{date[0]}"
    else:
        date = None

    valid_game_criterias = [{"criteria_name": criteria_name, "criteria_value": criteria_value} for
                            criteria_name, criteria_value in valid_game_criterias.items()]
    current_user.update_user_game(game_id, {"game_id": game_id,
                                            "criterias": valid_game_criterias,
                                            "Status": form["status"],
                                            "Started playing": date,
                                            "Hours played": form["hours_played"],
                                            "Tags": [tag.strip() for tag in form["tags"].split(";") if tag.strip()]
                                            })

    return redirect(f"/profile/{current_user.user_id}/list#{game_id}")


@app.route("/profile/<user_id>/collections", methods=["GET"])
# @error_catcher
@if_exist("user-collections")
def collections_get(collections, user_id):
    user = User(user_id)
    return render_template("collections.html", collections=collections, user=user)


@app.route("/profile/<user_id>/collections", methods=["POST"])
# @error_catcher
def collections_post(user_id):
    user = User(user_id)
    new_collection_name = request.form.to_dict()["new_collection_name"]
    if not uh.users_collection.find_one(
            {"_id": current_user.user_id},
            {"_id": 1,
             "collections": {"$elemMatch": {"collection_name": new_collection_name}}}).get("collections"):
        user.add_collection(new_collection_name)
    return redirect(f'/collections/{new_collection_name}/edit')


@app.route("/profile/<user_id>/collections/<collection_name>", methods=["GET"])
# @error_catcher
@if_exist("user-collection")
def collection_get(collection, user_id, collection_name):
    user = User(user_id)

    collection = user.add_info_to_games_from_collections(collection)

    return render_template("user_collection.html", collection=collection)


@app.route("/collections/<collection_name>/edit", methods=["GET"])
# @error_catcher
@login_required
@if_exist("user-collection")
def collection_edit_get(collection, user_id, collection_name):
    collection = current_user.add_info_to_games_from_collections(collection)
    return render_template("user_collection_edit.html", collection=collection)


@app.route("/collections/<collection_name>/edit", methods=["POST"])
def collection_edit_post(collection_name):
    form = request.form.to_dict()
    match form["action"]:
        case "change_collection":
            games_to_delete = []
            new_notes = {}
            for field in form:
                if not field.startswith("__note"):
                    if field.startswith("__checkbox"):
                        games_to_delete.append(field[10:])
                    continue
                new_notes[field[6:]] = form[field]

            # print(new_notes, games_to_delete, form['new_collection_name'])
            new_collection = {"collection_name": form['new_collection_name'],
                              "games": [],
                              "games_order": list(new_notes.keys()),
                              "collection_note": form["collection_note"]}
            for game_id, note in new_notes.items():
                if game_id in games_to_delete:
                    continue
                new_collection["games"].append({
                    "game_id": game_id,
                    "note": note
                })

            current_user.uptade_collection(new_collection, collection_name)
            return redirect(f"/profile/{current_user.user_id}/collections/{form['new_collection_name']}")

        case "delete_collection":
            current_user.delete_collection(collection_name)
            return redirect(f"/profile/{current_user.user_id}/collections")


# Api
@app.route("/api/all-games", methods=["GET"])
def api_all_games():
    return jsonify(gh.get_games_ids_and_names())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
