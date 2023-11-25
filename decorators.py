from functools import wraps
from flask import render_template


def error_catcher(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        try:
            return func(*args, **kwds)

        except Exception as e:
            return render_template("error_page.html", error=e)

    return wrapper
