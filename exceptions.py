class UserNotFound(Exception):
    def __str__(self):
        return "User you are looking for not found"


class UserAlreadyExist(Exception):
    def __str__(self):
        return "This username already taken, please try another"


class CantBeEmpty(Exception):
    def __str__(self):
        return "Value cant be empty"
