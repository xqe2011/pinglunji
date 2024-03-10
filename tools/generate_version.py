import json, sys

with open("./version.json", "w") as f1:
    f1.write(json.dumps({
        "version": sys.argv[1]
    }, indent=4, ensure_ascii=False))