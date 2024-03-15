import pysher, requests, json, asyncio
from .logger import timeLog
from .config import getJsonConfig, updateJsonConfig
from .version import version

client = None
channel = None
asyncLoop = None
dashboardURL = None
httpCallFunction = None

def setHttpCallFunction(func):
    global httpCallFunction
    httpCallFunction = func

async def getDashboardURL():
    return dashboardURL

async def clearRemoteCredential():
    config = getJsonConfig()
    config['kvdb']['remote']["server"] = ""
    config['kvdb']['remote']["channel"] = ""
    config['kvdb']['remote']["token"] = ""
    await updateJsonConfig(config)
    timeLog(f'[Remote] Cleared credential')

async def remoteWSBroadcast(data):
    global channel
    if channel != None:
        channel.trigger("client-" + data['type'], data['data'])

async def callAsync(method, id, args):
    timeLog(f'[Remote] Handling remote RPC call, method: {method}')
    status, msg = await httpCallFunction(method, args, False)
    data = {
        "id": id,
        "status": status,
        "msg": msg
    }
    channel.trigger("client-response", data)

def onRequest(jsonString):
    data = json.loads(jsonString)
    asyncio.run_coroutine_threadsafe(callAsync(data['method'], data['id'], data['args']), asyncLoop)

def signin():
    config = getJsonConfig()
    response = requests.get(f"{config['kvdb']['remote']['server']}/authorizeUser?role=server&socket_id={client.connection.socket_id}&channel={config['kvdb']['remote']['channel']}&token={config['kvdb']['remote']['token']}")
    response.raise_for_status()
    data = response.json()
    client.connection.send_event("pusher:signin", data)

def onSignIn(inputChannel):
    # 只有订阅并登录成功才算是完全建立频道连接，保存频道信息
    global channel
    channel = inputChannel
    timeLog(f"[Remote] Sign in")

def onSubscriptionSucceeded():
    timeLog(f"[Remote] Channel subscribed")
    signin()

def subscribe(server, channelName, token):
    global dashboardURL
    config = getJsonConfig()
    # 首先尝试存储的token是否可以使用
    useNew = True
    if server == config['kvdb']['remote']['server']:
        try:
            response = requests.get(f"{config['kvdb']['remote']['server']}/authorizeChannel?dashboard=pinglunji&version={version}&socket_id={client.connection.socket_id}&channel={config['kvdb']['remote']['channel']}&token={config['kvdb']['remote']['token']}")
            response.raise_for_status()
            data = response.json()
            channelName = config['kvdb']['remote']['channel']
            token = config['kvdb']['remote']['token']
            useNew = False
            timeLog(f'[Remote] Old credential valid, using the old one')
        except:
            pass
    if useNew:
        timeLog(f'[Remote] Old credential invalid, using the new one')
        response = requests.get(f"{server}/authorizeChannel?dashboard=pinglunji&version={version}&socket_id={client.connection.socket_id}&channel={channelName}&token={token}")
        response.raise_for_status()
        data = response.json()
        # 保存登录信息，供下次使用
        config['kvdb']['remote']["server"] = server
        config['kvdb']['remote']["channel"] = channelName
        config['kvdb']['remote']["token"] = token
        asyncio.run_coroutine_threadsafe(updateJsonConfig(config), asyncLoop)
    timeLog(f'[Remote] Got credential and dashboard url from server, auth: {data["auth"]}, url: {data["url"]}')
    dashboardURL = data["url"]
    inputChannel = client.subscribe(channelName, data["auth"])
    inputChannel.bind("client-request", onRequest)
    client.connection.bind("pusher:signin_success", lambda *_, **__: onSignIn(inputChannel))
    inputChannel.bind("pusher_internal:subscription_succeeded", lambda *_, **__: onSubscriptionSucceeded())

def onClientError(data):
    timeLog(f'[Remote] Error occurred: {json.dumps(data, ensure_ascii=False)}')

async def initRemote():
    global client, asyncLoop
    asyncLoop = asyncio.get_running_loop()
    config = getJsonConfig()
    if not config['engine']['remote']['enable']:
        timeLog(f'[Remote] Remote Disabled')
        return
    try:
        response = requests.get(f"{config['engine']['remote']['server']}/config")
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
    client.connection.bind('pusher:connection_established', lambda _: subscribe(config['engine']['remote']['server'], channel, token))
    client.connection.bind("pusher:error", onClientError)
    client.connect()
