import os

os.makedirs('.tmp', exist_ok=True)

with open('./DouyinBarrageGrab/BarrageGrab/proto/wss.proto', 'r', encoding='utf8') as f1:
    with open('./DouyinBarrageGrab/BarrageGrab/proto/message.proto', 'r', encoding='utf8') as f2:
        with open('.tmp/live_proto.proto', 'w', encoding='utf8') as f3:
            f3.write(f1.read() + f2.read().replace('syntax = "proto3";', ''))
os.chdir(".tmp")
os.system("protoc --python_betterproto_out=. live_proto.proto")
os.system("copy .\\live_proto.py ..\\app")