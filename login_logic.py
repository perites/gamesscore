from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import render_template, redirect, request

# from work_with_db import UsersHelper, GamesHelper
from user_class import User, uh, gh
login_manager = LoginManager()
login_manager.login_view = 'login'
# uh = UsersHelper()
# gh = GamesHelper()


SESSION = []


@login_manager.user_loader
def load_user(user_id):
    for user_id in SESSION:
        if user_id == user_id:
            return User(user_id)


def authenticate(user_id, password, already_log=False):
    user = uh.find_user_by_id(user_id)

    next_url = request.args.get('next')
    if user and user["password"] == password or already_log:

        user = User(user_id)
        login_user(user)
        SESSION.append(user.user_id)

        return redirect(next_url) if next_url else redirect(f"/profile/{user_id}")

    return redirect(f'/login?next={next_url}')
