import pysher, requests, json, asyncio
from .logger import timeLog
from .http import call

client = None
channel = None
asyncLoop = None

async def remoteWSBroadcast(data):
    global channel
    if channel != None:
        channel.trigger("client-" + data['type'], data['data'])

async def callAsync(method, id, args):
    timeLog(f'[Remote] Handling remote RPC call, method: {method}')
    status, msg = await call(method, args, False)
    data = {
        "id": id,
        "status": status,
        "msg": msg
    }
    channel.trigger("client-response", data)

def onRequest(jsonString):
    data = json.loads(jsonString)
    asyncio.run_coroutine_threadsafe(callAsync(data['method'], data['id'], data['args']), asyncLoop)

def onSubscriptionSucceeded(inputChannel):
    global channel
    channel = inputChannel
    timeLog(f"[Remote] Channel subscribed")

def subscribe(channelName, token):
    response = requests.get(f"https://fuwuji.nuozi.club/authorizeChannel?dashboard=danmuji&version=v1.4.0&socket_id={client.connection.socket_id}&channel={channelName}&token={token}")
    response.raise_for_status()
    data = response.json()
    timeLog(f'[Remote] Got credential and dashboard url from server, auth: {data["auth"]}, url: {data["url"]}')
    inputChannel = client.subscribe(channelName, data["auth"])
    # 只有订阅成功才算是完全建立频道连接，保存频道信息
    inputChannel.bind("pusher_internal:subscription_succeeded", lambda *_, **__: onSubscriptionSucceeded(inputChannel))
    inputChannel.bind("client-request", onRequest)

def onClientError(data):
    timeLog(f'[Remote] Error occurred: {json.dumps(data, ensure_ascii=False)}')

def onClientClosed(data):
    timeLog(f'[Remote] Error occurred: {json.dumps(data, ensure_ascii=False)}')

async def initRemote():
    global client, asyncLoop
    asyncLoop = asyncio.get_running_loop()
    try:
        response = requests.get("https://fuwuji.nuozi.club/config")
        response.raise_for_status()
    except:
        timeLog(f'[Remote] Cannot fetch pusher config, retrying after 3 seconds...')
        await asyncio.sleep(3)
        asyncio.create_task(initRemote())
        return
    data = response.json()
    token = data["token"]
    channel = data["channel"]
    hostInfo = { "custom_host": data['host'], "port": data['port'], "secure": data['secure'] } if 'host' in data else { "cluster": data['cluster'] }
    client = pysher.Pusher(data["key"], **hostInfo)
    client.connection.bind('pusher:connection_established', lambda _: subscribe(channel, token))
    client.connection.bind("pusher:error", onClientError)
    client.connect()
