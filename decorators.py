from functools import wraps
from flask import render_template
from flask_login import current_user

from work_with_db import UsersHelper, GamesHelper

from exceptions import UserNotFound, GameNotFound, CollectionNotFound

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


def if_exist(value: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwds):
            match value:
                case "user-nth":
                    if not uh.users_collection.find_one({"_id": kwds["user_id"]}, {"_id": 1}):
                        raise UserNotFound
                    return func(*args, **kwds)

                case "user-collection":
                    if not kwds.get("user_id"):
                        kwds['user_id'] = current_user.user_id

                    collection = uh.users_collection.find_one(
                        {"_id": kwds["user_id"]},
                        {"_id": 1,
                         "collections": {"$elemMatch": {"collection_name": kwds["collection_name"]}}})

                    if (user_not_found := not collection.get("_id")) or not collection.get("collections"):
                        raise UserNotFound if user_not_found else CollectionNotFound
                    return func(collection["collections"], *args, **kwds)

                case "user-collections":
                    collections = uh.users_collection.find_one({"_id": kwds["user_id"]},
                                                               {"_id": 1, "collections": {"collection_name": 1}})
                    if not collections["_id"] or not collections["collections"]:
                        raise UserNotFound
                    return func(collections, *args, **kwds)

                case "game-game":
                    game = gh.games_collection.find_one({"_id": kwds["game_id"]})
                    if not game:
                        raise GameNotFound
                    return func(game, *args, **kwds)

                case "game-name-image":
                    game_info = gh.games_collection.find_one({"_id": kwds["game_id"]}, {"display_name": 1, "image": 1})
                    if not game_info:
                        raise GameNotFound
                    return func(game_info, *args, **kwds)

        return wrapper

    return decorator
