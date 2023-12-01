from flask_login import LoginManager, login_user
from flask import redirect, request

from user_class import User, uh

login_manager = LoginManager()
login_manager.login_view = 'login'

SESSION = []


@login_manager.user_loader
def load_user(user_id):
    for user_id in SESSION:
        if user_id == user_id:
            return User(user_id)


def authenticate(user_id, password, already_log=False):
    user = uh.users_collection.find_one({"_id": user_id}, {"password": 1})

    next_url = request.args.get('next')
    if user and user["password"] == password or already_log:
        user = User(user_id)
        login_user(user)
        SESSION.append(user.user_id)

        return redirect(next_url) if next_url else redirect(f"/profile/{user_id}")

    return redirect(f'/login?next={next_url}')
