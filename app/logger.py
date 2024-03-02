import datetime, sys

file = open("./log.txt", mode='w', encoding='utf-8')

sys.stdout.reconfigure(line_buffering=True)
def timeLog(string):
    now = datetime.datetime.now()
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S') + ',{:03d}'.format(now.microsecond // 1000)}] {string}")
    file.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S') + ',{:03d}'.format(now.microsecond // 1000)}] {string}\n")
    file.flush()