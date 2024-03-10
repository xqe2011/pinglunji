from quart import Quart, websocket, send_from_directory
from quart_cors import cors
from .config import updateJsonConfig, getJsonConfig
import asyncio, json, os, webbrowser
from .logger import timeLog
from .messages_handler import markAllMessagesInvalid
from .tts import getAllVoices, getAllSpeakers
from .remote import setHttpCallFunction, clearRemoteCredential, getDashboardURL

staticFilesPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static')
events = {}
app = Quart(__name__, static_folder=staticFilesPath, static_url_path='/')
app = cors(app, allow_origin='*')
tasks = []
allWSClients = []

def registerEvent(localOnly):
    def decorator(func):
        async def wrappedFunc(local, *args, **kwargs):
            if localOnly and not local:
                return -1, 'not support this method in remote mode'
            return await func(*args, **kwargs)
        wrappedFunc.__name__ = func.__name__
        events[func.__name__] = wrappedFunc
        return wrappedFunc
    return decorator

@app.route('/', methods=['GET'])
async def index():
    global staticFilesPath
    return await send_from_directory(staticFilesPath, 'index.html')

@app.after_request
def addHeader(response):
    response.cache_control.no_cache = True
    return response

@registerEvent(False)
async def getSpeakers():
    return 0, getAllSpeakers()

@registerEvent(False)
async def getVoices():
    return 0, getAllVoices()

@registerEvent(False)
async def flush():
    await markAllMessagesInvalid()
    return 0, 'ok'

@registerEvent(False)
async def getDynamicConfig():
    return 0, getJsonConfig()['dynamic']

@registerEvent(False)
async def updateDynamicConfig(config):
    nowJsonConfig = getJsonConfig()
    nowJsonConfig['dynamic'] = config
    await updateJsonConfig(nowJsonConfig)
    return 0, 'ok'

@registerEvent(True)
async def getEngineConfig():
    data = getJsonConfig()['engine']
    return 0, data

@registerEvent(True)
async def updateEngineConfig(config):
    nowJsonConfig = getJsonConfig()
    nowJsonConfig['engine'] = config
    await updateJsonConfig(nowJsonConfig)
    return 0, 'ok'

@registerEvent(True)
async def getRemoteURL():
    return 0, await getDashboardURL()

@registerEvent(True)
async def flushRemoteURL():
    await clearRemoteCredential()
    return 0, 'ok'

async def call(method, args, local):
    if method in events:
        return await events[method](local, **args)
    else:
        return -1, 'not support'

@app.websocket('/client')
async def ws():
    try:
        allWSClients.append(websocket._get_current_object())
        while True:
            # 检查输入
            try:
                data = json.loads(await websocket.receive())
            except json.JSONDecodeError:
                continue
            # 处理RPC调用
            if 'type' in data and data['type'] == "request" and 'method' in data["data"] and 'args' in data["data"] and 'id' in data["data"]:
                timeLog(f'[Websocket] Handling local RPC call, method: {data["data"]["method"]}')
                status, msg = await call(data['data']["method"], data['data']["args"], True)
                response = {
                    "type": "response",
                    "data": {
                        "id": data["data"]["id"],
                        "status": status,
                        "msg": msg
                    }
                }
                await websocket.send(json.dumps(response))
    except asyncio.CancelledError:
        allWSClients.remove(websocket)
        raise

@app.before_serving
async def startup():
    webbrowser.register('edge', None, webbrowser.GenericBrowser(os.environ['ProgramFiles(x86)'] + r'\Microsoft\Edge\Application\msedge_proxy.exe'), preferred=True)
    webbrowser.open('http://127.0.0.1:7070', new=1, autoraise=True)
    for task in tasks:
        app.add_background_task(task)

@app.after_serving
async def cleanup():
    for task in app.background_tasks:
        task.cancel()

async def broadcastWSMessage(message):
    for ws in allWSClients:
        await ws.send(json.dumps(message, ensure_ascii=False))

def startHttpServer(backgroundTasks):
    global tasks
    tasks = backgroundTasks
    setHttpCallFunction(call)
    timeLog('[HTTP] Started, url: http://127.0.0.1:7070')
    app.run(host='0.0.0.0', port=7070)