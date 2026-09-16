import os
import json


def load_json(path):
    data = {}

    if os.path.isfile(path):
        with open(path, "r", encoding='utf-8') as f:
            data = json.load(f)
    else:
        print("File doesn't exist", path)

    return data


def save_json(path, data):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
