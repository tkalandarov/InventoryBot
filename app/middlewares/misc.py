from app.db.operations import *
from app.keyboards import get_username
from os import walk


def get_filenames(path):
    logs = []
    for (dirpath, dirnames, filenames) in walk(path):
        logs.extend(filenames)
        break

    return logs
