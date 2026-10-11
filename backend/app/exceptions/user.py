class UserAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class InvalidAccessTokenError(Exception):
    pass

class AdminRequiredError(Exception):
    pass