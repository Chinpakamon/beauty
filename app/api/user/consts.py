import enum


class Role(enum.StrEnum):
    USER = "USER"
    MASTER = "MASTER"
    ADMIN = "ADMIN"


class RegistrationRole(enum.StrEnum):
    USER = "USER"
    MASTER = "MASTER"


class UserOrderByType(enum.StrEnum):
    CREATED_AT_ASC = "CREATED_AT_ASC"
    CREATED_AT_DESC = "CREATED_AT_DESC"
    FIRST_NAME_ASC = "FIRST_NAME_ASC"
    FIRST_NAME_DESC = "FIRST_NAME_DESC"
    LAST_NAME_ASC = "LAST_NAME_ASC"
    LAST_NAME_DESC = "LAST_NAME_DESC"
    EMAIL_ASC = "EMAIL_ASC"
    EMAIL_DESC = "EMAIL_DESC"
