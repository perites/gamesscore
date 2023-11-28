from functools import wraps
from flask import render_template

from work_with_db import UsersHelper, GamesHelper

from exceptions import UserNotFound, GameNotFound

uh = UsersHelper()
gh = GamesHelper()


def error_catcher(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        try:
            return func(*args, **kwds)
        except Exception as e:
            return render_template("error_page.html", error=e)

    return wrapper


def if_exist(value):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwds):
            match value:
                case "user-nth":
                    if not uh.users_collection.find_one({"_id": kwds["user_id"]}, {"_id": 1}):
                        raise UserNotFound
                    return func(*args, **kwds)

                case "game-game":
                    game = gh.games_collection.find_one({"_id": kwds["game_id"]})
                    if not game:
                        raise GameNotFound
                    return func(game, *args, **kwds)

                case "game-name-image":
                    game = gh.games_collection.find_one({"_id": kwds["game_id"]}, {"display_name": 1, "image": 1})
                    if not game:
                        raise GameNotFound
                    return func(game, *args, **kwds)

        return wrapper
    return decorator
