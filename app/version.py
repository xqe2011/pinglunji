import json, os

info = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../version.json'), encoding='utf-8', mode='r'))

version = info["version"]