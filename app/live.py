import re, asyncio, aiohttp, traceback
import requests, gzip
from pyee import AsyncIOEventEmitter
from .live_proto import *
from .logger import timeLog
from .tool import isAllCharactersEmoji

session = None
client = None
anchorID = 0
liveEvent = AsyncIOEventEmitter()

def onConnected(command):
    liveEvent.emit('connected', True)

def onDanmuCallback(command: ChatMessage):
    global anchorID
    uid = command.user.id
    uname = command.user.nickname
    msg = command.content
    isFansMedalBelongToLive = command.user.fans_club.data.anchor_id == anchorID
    fansMedalLevel = command.user.fans_club.data.level
    isFansMedalVIP = command.user.follow_info.follow_status == 2
    isEmoji = isAllCharactersEmoji(msg)
    timeLog(f"[Danmu] {uname}: {msg}")
    liveEvent.emit('danmu', uid, uname, isFansMedalBelongToLive, fansMedalLevel, isFansMedalVIP, msg, isEmoji)

def onLikeCallback(command: LikeMessage):
    uid = command.user.id
    uname = command.user.nickname
    timeLog(f"[Like] {uname} liked the stream.")
    liveEvent.emit('like', uid, uname)

def onWelcomeCallback(command: MemberMessage):
    global anchorID
    uid = command.user.id
    uname = command.user.nickname
    isFansMedalBelongToLive = command.user.fans_club.data.anchor_id == anchorID
    fansMedalLevel = command.user.fans_club.data.level
    isFansMedalVIP = command.user.follow_info.follow_status == 2
    timeLog(f"[Welcome] {uname} entered the stream.")
    liveEvent.emit('welcome', uid, uname, isFansMedalBelongToLive, fansMedalLevel, isFansMedalVIP)

def onGiftCallback(command: GiftMessage):
    uid = command.user.id
    uname = command.user.nickname
    giftName = command.gift.name
    num = command.combo_count
    price = command.gift.diamond_count / 10
    timeLog(f"[Gift] {uname} bought {price:.1f}元的{giftName} x {num}.")
    liveEvent.emit('gift', uid, uname, price, giftName, num)

async def callback(type, data, callbackFn):
    try:
        callbackFn(type().FromString(data))
    except:
        timeLog(f'[Live] Exception happened when calling callback')
        traceback.print_exc()

async def onMessage(method, data):
    timeLog(f'[Live] Received Server method: {method}')
    if method == 'WebcastLikeMessage':
        await callback(LikeMessage, data, onLikeCallback)
    elif method == 'WebcastMemberMessage':
        await callback(MemberMessage, data, onWelcomeCallback)
    elif method == 'WebcastGiftMessage':
        await callback(GiftMessage, data, onGiftCallback)
    if method == 'WebcastChatMessage':
        await callback(ChatMessage, data, onDanmuCallback)

async def keepHeartbeatTask():
    global client
    while True:
        if client.closed or client._closing:
            timeLog(f'[Live] Gave up sending Heartbeat, because connection closed')
            return
        obj = WssResponse(payload_type='hb')
        await client.send_bytes(obj.SerializeToString())
        timeLog(f'[Live] Sent heartbeat')
        await asyncio.sleep(10)

async def receiveMessagesTask():
    global client
    async for msg in client:
        if msg.type == aiohttp.WSMsgType.BINARY:
            # 解析指令
            wssPackage = WssResponse().FromString(msg.data)
            payloadPackage = Response().FromString(gzip.decompress(wssPackage.payload))
            # 自动回复ACK
            if payloadPackage.need_ack:
                obj = WssResponse(logid=wssPackage.logid, payload_type=payloadPackage.internal_ext)
                if not client.closed and not client._closing:
                    await client.send_bytes(obj.SerializeToString())
                    timeLog('[Live] Sent ACK')
            # 消息处理器
            for msgPayload in payloadPackage.messages:
                await onMessage(msgPayload.method, msgPayload.payload)
        elif msg.type == aiohttp.WSMsgType.CLOSED or msg.type == aiohttp.WSMsgType.ERROR:
            timeLog(f'[Live] Connection closed, retrying after 3 seconds...')
            return

async def connectLive(liveID):
    global session, client
    roomInfoURL = f"https://live.douyin.com/{liveID}"
    headers = {
        'authority': 'live.douyin.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        'cookie': 'xgplayer_user_id=251959789708; passport_assist_user=Cj1YUtyK7x-Br11SPK-ckKl61u5KX_SherEuuGPYIkLjtmV3X8m3EU1BAGVoO541Sp_jwUa8lBlNmbaOQqheGkoKPOVVH42rXu6KEb9WR85pUw4_qNHfbcotEO-cml5itrJowMBlYXDaB-GDqJwNMxMElMoZUycGhzdNVAT4XxCJ_74NGImv1lQgASIBA3Iymus%3D; n_mh=nNwOatDm453msvu0tqEj4bZm3NsIprwo6zSkIjLfICk; LOGIN_STATUS=1; store-region=cn-sh; store-region-src=uid; sid_guard=b177a545374483168432b16b963f04d5%7C1697713285%7C5183999%7CMon%2C+18-Dec-2023+11%3A01%3A24+GMT; ttwid=1%7C9SEGPfK9oK2Ku60vf6jyt7h6JWbBu4N_-kwQdU-SPd8%7C1697721607%7Cc406088cffa073546db29932058720720521571b92ba67ba902a70e5aaffd5d6; odin_tt=1f738575cbcd5084c21c7172736e90f845037328a006beefec4260bf8257290e2d31b437856575c6caeccf88af429213; __live_version__=%221.1.1.6725%22; device_web_cpu_core=16; device_web_memory_size=8; live_use_vvc=%22false%22; csrf_session_id=38b68b1e672a92baa9dcb4d6fd1c5325; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; __ac_nonce=0658d6780004b23f5d0a8; __ac_signature=_02B4Z6wo00f01Klw1CQAAIDAXxndAbr7OHypUNCAAE.WSwYKFjGSE9AfNTumbVmy1cCS8zqYTadqTl8vHoAv7RMb8THl082YemGIElJtZYhmiH-NnOx53mVMRC7MM8xuavIXc-9rE7ZEgXaA13; webcast_leading_last_show_time=1703765888956; webcast_leading_total_show_times=1; webcast_local_quality=sd; xg_device_score=7.90435294117647; live_can_add_dy_2_desktop=%221%22; msToken=sTwrsWOpxsxXsirEl0V0d0hkbGLze4faRtqNZrIZIuY8GYgo2J9a0RcrN7r_l179C9AQHmmloI94oDvV8_owiAg6zHueq7lX6TgbKBN6OZnyfvZ6OJyo2SQYawIB_g==; tt_scid=NyxJTt.vWxv79efmWAzT2ZAiLSuybiEOWF0wiVYs5KngMuBf8oz5sqzpg5XoSPmie930; pwa2=%220%7C0%7C1%7C0%22; download_guide=%223%2F20231228%2F0%22; msToken=of81bsT85wrbQ9nVOK3WZqQwwku95KW-wLfjFZOef2Orr8PRQVte27t6Mkc_9c_ROePolK97lKVG3IL5xrW6GY6mdUDB0EcBPfnm8-OAShXzlELOxBBCdiQYIjCGpQ==; IsDouyinActive=false; odin_tt=7409a7607c84ba28f27c62495a206c66926666f2bbf038c847b27817acbdbff28c3cf5930de4681d3cfd4c1139dd557e; ttwid=1%7C9SEGPfK9oK2Ku60vf6jyt7h6JWbBu4N_-kwQdU-SPd8%7C1697721607%7Cc406088cffa073546db29932058720720521571b92ba67ba902a70e5aaffd5d6',
        'referer': 'https://live.douyin.com/721566130345?cover_type=&enter_from_merge=web_live&enter_method=web_card&game_name=&is_recommend=&live_type=game&more_detail=&room_id=7317569386624125734&stream_type=vertical&title_type=&web_live_tab=all',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    }
    response = requests.get(roomInfoURL, headers=headers)
    roomInfo = re.search(r'room\\":{.*\\"id_str\\":\\"(\d+)\\".*,\\"status\\":(\d+).*"title\\":\\"([^"]*)\\"', response.text)
    ttwID = response.cookies.get("ttwid")
    isLiveStarted = roomInfo.group(2) != '4'
    livePushID = re.search(r'roomId\\":\\"(\d+)\\"', response.text).group(1)
    anchorID = re.search(r'anchor\\":{\\"id_str\\":\\"(\d+)\\"', response.text).group(1)
    timeLog(f'[Live] Got live room info, livePushID: {livePushID}, anchorID: {anchorID}, ttwID: {ttwID}, isLiveStarted: {isLiveStarted}')

    websocketURL = f'wss://webcast3-ws-web-lq.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:{livePushID}|wss_push_did:7188358506633528844|dim_log_id:20230521093022204E5B327EF20D5CDFC6|fetch_time:1684632622323|seq:1|wss_info:0-1684632622323-0-0|wrds_kvs:WebcastRoomRankMessage-1684632106402346965_WebcastRoomStatsMessage-1684632616357153318&cursor=t-1684632622323_r-1_d-1_u-1_h-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&maxCacheMessageNumber=20&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&user_unique_id=7188358506633528844&device_platform=web&cookie_enabled=true&screen_width=1440&screen_height=900&browser_language=zh&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0%20(Macintosh;%20Intel%20Mac%20OS%20X%2010_15_7)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/113.0.0.0%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id={livePushID}&heartbeatDuration=0&signature=00000000'
    headers = {
        'cookie': f'ttwid={ttwID}',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    session = aiohttp.ClientSession()
    client = await session.ws_connect(websocketURL, headers=headers)
    # 创建任务
    asyncio.create_task(keepHeartbeatTask())
    asyncio.create_task(receiveMessagesTask())
    while True:
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            timeLog(f'[Live] System exiting, closing websocket connection')
            await client.close()
            await session.close()
            return

asyncio.run(connectLive(757069520376))