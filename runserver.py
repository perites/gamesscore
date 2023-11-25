from flask import Flask, render_template, request, redirect, url_for

from login_logic import *
from decorators import error_catcher

from forms import *
from flask_bootstrap import Bootstrap5
from flask_cors import CORS

from exceptions import UserNotFound, UserAlreadyExist, CantBeEmpty


# створювати свої списки
# улюблене
# персональна статистика ( скільки награно, тд)

# пошук ігор ( з головної ?)

# у гри показувати скільки середнеє награли в  гру
# статистика на сторінку гри

# брати інфу з стіму ?

# видавець гри, сторінка видавця
# франшизи

# статистика

# сортування ігор, клікання на елементи

app = Flask(__name__)
app.config["SECRET_KEY"] = 'c42e8d7afdsdfds56342385cb9e30b6b'
CORS(app)
login_manager.init_app(app)
csrf = CSRFProtect(app)
bootstrap = Bootstrap5(app)


@app.route("/", methods=["GET", "POST"])
def home():
    try:
        data = request.get_json()
        message = data.get('message')
        # Process the data as needed
        return jsonify({'status': 'success', "message": message})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route("/login", methods=["GET", "POST"])
@error_catcher
def login():
    # print(request.args.to_dict())
    form = LoginForm()

    if request.method == "GET":
        if isinstance(current_user, User):
            return authenticate(current_user.user_id, "", True)
        return render_template("login.html", form=form)

    user_id = form.user_id.data
    password = form.password.data
    return authenticate(user_id, password)


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


@app.route('/logout')
@error_catcher
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/profile/<user_id>/", methods=["GET"])
# @error_catcher
def user_page(user_id):
    try:
        user_id = User(user_id)
    except Exception:
        raise UserNotFound
    return render_template("user_page.html", user_id=user_id)


@app.route("/profile/<user_id>/list", methods=["GET"])
# @error_catcher
def user_list_get(user_id):
    user_id = User(user_id)
    all_games = user_id.get_field("games")
    return render_template("user_list.html", user_id=user_id, all_games=all_games)


@app.route("/settings", methods=["GET", "POST"])
# @error_catcher
@login_required
def user_settings():

    steam_form = SteamAccountForm()
    steam_form.steam_link.default = current_user.get_field("steam_link")
    steam_form.process()

    basic_criterias = confg.basic_criterias
    user_show_info = current_user.get_field("show_info")

    rest_criterias = [el for el in basic_criterias if el not in user_show_info]

    criterias = current_user.get_field("all_criterias")
    form = request.form.to_dict()

    for field in form.values():
        if not field:
            raise CantBeEmpty

    if not form:
        return render_template("user_settings.html", criterias=criterias, need_to_edit=None, steam_form=steam_form, rest_criterias=rest_criterias, user_show_info=user_show_info)
    elif need_to_edit := form.get("working_criteria_name_start_edit"):
        return render_template("user_settings.html", criterias=criterias, need_to_edit=need_to_edit, steam_form=steam_form, rest_criterias=rest_criterias, user_show_info=user_show_info)

    elif need_to_delete_criteria := form.get("delete_criteria"):
        current_user.delete_criteria(need_to_delete_criteria)
        return redirect(url_for("user_settings"))

    elif form.get("add_value"):
        current_user.add_value_to_criteria(form["add_value"], form["new_value"])
        criterias = current_user.get_field("all_criterias")
        return render_template("user_settings.html", criterias=criterias, need_to_edit=form["add_value"], steam_form=steam_form, rest_criterias=rest_criterias, user_show_info=user_show_info)

    elif form.get("add_criteria"):
        # print(form["new_criteria_name"])
        current_user.add_criteria(form["new_criteria_name"])
        return redirect(url_for("user_settings"))

    elif steam_link := form.get("steam_link"):
        current_user.add_field("steam_link", steam_link)
        return redirect(url_for("user_settings"))

    elif form.get("update_basic_criterias"):
        user_show_info = []
        for field in form:
            print(form)
            if not field.startswith("__checkbox"):
                continue
            user_show_info.append(form[field])
        current_user.add_field("show_info", user_show_info)
        return redirect(url_for("user_settings"))

    changing_criteria_name = form["working_criteria_name_commit"]

    new_values = []
    for value in form:
        if "__name" not in value or value.split("__")[0] + "__checkbox" in form:
            if "__checkbox" in value:
                current_user.delete_value_from_criteria(changing_criteria_name, form[value])
            continue
        new_values.append(form[value])
    current_user.change_criteria(changing_criteria_name, form["criteria_name"], new_values)

    return redirect(url_for("user_settings"))


@app.route("/update-criterias", methods=["GET", "POST"])
# @error_catcher
def update_order_values():
    if request.method == "GET":
        return redirect("/")
    if request.method == "POST":
        criterias_order = {}
        for dic in request.get_json()["itemOrder"]:
            criterias_order[dic['id']] = [dic['id'], dic["order"]]

        uh.add_field_to_user(dic["user"], {"criterias_order": criterias_order})
        return "", 200


@app.route("/game/<game_id>", methods=["GET"])
def game_page_get(game_id):

    game = gh.find_game_by_id(game_id)
    if not game:
        return "404"
    return render_template("game_page.html", game=game)


@app.route("/game/add", methods=["GET", "POST"])
@login_required
def add_game_page():
    if current_user.role != "admin":
        return "dont have permission"

    form = AddGameForm()
    if request.method == 'GET':
        return render_template("add_game_page.html", form=form)

    new_game_name = form.name.data
    gh.add_game(new_game_name)
    return redirect(f"/game/{new_game_name}")


@app.route("/game/<game_id>/change", methods=["GET", "POST"])
@login_required
def change_game_page(game_id):
    if current_user.role != "admin":
        return "dont have permission"

    form = AddGameFieldForm()
    if request.method == 'GET':
        return render_template("change_game_page.html", form=form)

    new_field_name = form.new_field_name.data
    new_field_value = form.new_field_value.data
    gh.add_field_to_game(game_id, new_field_name, new_field_value)
    return redirect(f"/game/{game_id}")


@app.route("/change/game/<game_id>", methods=["GET", "POST"])
@login_required
def change_user_game_page(game_id):

    if request.method == "GET":

        if not (all_games := current_user.get_field("games")).get(game_id):
            all_games[game_id] = {"criterias": {}}
            current_user.add_field("games", all_games)

        for attr in GameInfoForm.__dict__.copy():
            if not attr.startswith("D_"):
                continue
            delattr(GameInfoForm, attr)

        valid_game_criterias = current_user.get_valid_games_criterias().get(game_id)
        if not valid_game_criterias:
            valid_game_criterias = {}
            for criteria_name in current_user.get_field("all_criterias"):
                valid_game_criterias[criteria_name] = "-"

        for criteria_name, criteria_values in current_user.get_field("all_criterias").items():
            if (current_value := valid_game_criterias.get(criteria_name)):
                setattr(GameInfoForm, "D_" + criteria_name, SelectField(criteria_name, choices=criteria_values + ["-"], default=current_value))
            else:
                setattr(GameInfoForm, "D_" + criteria_name, SelectField(criteria_name, choices=criteria_values + ["-"], default="-"))

        setattr(GameInfoForm, "D_" + "submit", SubmitField("Commit"))

        form = GameInfoForm()

        if date := current_user.get_field("games")[game_id].get("Started playing"):
            form.started_playing.default = datetime.strptime(date, "%d-%m-%Y")
        else:
            form.started_playing.default = datetime.now()

        form.status.default = current_user.get_field("games")[game_id].get("Status")
        form.hours_played.default = current_user.get_field("games")[game_id].get("Hours played")
        form.process()

        return render_template("change_user_game_page.html", game_id=game_id, form=form)

    form = request.form.to_dict()

    if form.get("delete_from_account"):
        current_user.delete_game(game_id)
        return redirect(f"/profile/{current_user.user_id}/list")

    valid_game_criterias = current_user.get_valid_games_criterias().get(game_id)

    for criteria, value in valid_game_criterias.items():
        valid_game_criterias[criteria] = form["D_" + criteria]

    current_user.update_game_field(game_id, "criterias", valid_game_criterias)

    print(form)
    current_user.update_game_field(game_id, "Status", form["status"])
    if len((date := form['started_playing'].split('-'))) == 3:
        date = f"{date[2]}-{date[1]}-{date[0]}"
    else:
        date = None
    current_user.update_game_field(game_id, "Started playing", date)
    current_user.update_game_field(game_id, "Hours played", form["hours_played"])

    return redirect(f"/profile/{current_user.user_id}/list#{game_id}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
