import enum


class ServiceTypeOrderByType(enum.StrEnum):
    CREATED_AT_ASC = "CREATED_AT_ASC"
    CREATED_AT_DESC = "CREATED_AT_DESC"
    NAME_ASC = "NAME_ASC"
    NAME_DESC = "NAME_DESC"
