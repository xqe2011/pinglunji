from .live import liveEvent
from .filter import filterDanmu, filterGift, filterLike, filterSubscribe, filterWelcome
from .stats import setOutputMessagesLength, appendDanmuFilteredStats, appendGiftFilteredStats, appendWelcomeFilteredStats, appendLikeFilteredStats, appendSubscribeFilteredStats
import time

messagesQueue = []
haveReadMessages = []

def popMessagesQueue():
    global messagesQueue, haveReadMessages
    if len(messagesQueue) == 0:
        return None
    data = messagesQueue.pop(0)
    setOutputMessagesLength(len(messagesQueue))
    haveReadMessages.append(data)
    return data

def getHaveReadMessages():
    global haveReadMessages
    return haveReadMessages

def messagesQueueAppend(data):
    global messagesQueue
    messagesQueue.append(data)
    setOutputMessagesLength(len(messagesQueue))

def messagesQueueAppendAtStart(data):
    global messagesQueue
    messagesQueue.insert(0, data)
    setOutputMessagesLength(len(messagesQueue))

@liveEvent.on('danmu')
async def onDanmu(uid, uname, isFansMedalBelongToLive, fansMedalLevel, isFansMedalVIP, msg, isEmoji):
    if filterDanmu(uid, uname, isFansMedalBelongToLive, fansMedalLevel, isFansMedalVIP, msg, isEmoji):
        appendDanmuFilteredStats(uid=uid, uname=uname, msg=msg, isEmoji=isEmoji, filterd=False)
        messagesQueueAppend({
            'type': 'danmu',
            'time': time.time(),
            'uid': uid,
            'uname': uname,
            'msg': msg
        })
    else:
        appendDanmuFilteredStats(uid=uid, uname=uname, msg=msg, isEmoji=isEmoji, filterd=True)

@liveEvent.on('gift')
async def onGift(uid, uname, price, giftName, num):
    def deduplicateCallback(userInfo, giftName):
        giftInfo = userInfo['gifts'][giftName]
        messagesQueueAppend({
            'type': 'gift',
            'time': time.time(),
            'uid': userInfo['uid'],
            'uname': userInfo['uname'],
            'giftName': giftName,
            'num': giftInfo['count']
        })
    result = filterGift(uid, uname, price, giftName, num, deduplicateCallback)
    if result == True:
        appendGiftFilteredStats(uid=uid, uname=uname, giftName=giftName, num=num, filterd=False)
        messagesQueueAppend({
            'type': 'gift',
            'time': time.time(),
            'uid': uid,
            'uname': uname,
            'giftName': giftName,
            'num': num
        })
    else:
        appendGiftFilteredStats(uid=uid, uname=uname, giftName=giftName, num=num, filterd=(result != None))

@liveEvent.on('like')
async def onLike(uid, uname):
    if filterLike(uid, uname):
        appendLikeFilteredStats(uid=uid, uname=uname, filterd=False)
        messagesQueueAppend({
            'type': 'like',
            'time': time.time(),
            'uid': uid,
            'uname': uname
        })
    else:
        appendLikeFilteredStats(uid=uid, uname=uname, filterd=True)

@liveEvent.on('subscribe')
async def onSubscribe(uid, uname, isFansMedalBelongToLive, fansMedalLevel, fansMedalGuardLevel):
    if filterSubscribe(uid, uname, isFansMedalBelongToLive, fansMedalLevel, fansMedalGuardLevel):
        appendSubscribeFilteredStats(uid=uid, uname=uname, filterd=False)
        messagesQueueAppend({
            'type': 'subscribe',
            'time': time.time(),
            'uid': uid,
            'uname': uname
        })
    else:
        appendSubscribeFilteredStats(uid=uid, uname=uname, filterd=True)

@liveEvent.on('welcome')
async def onWelcome(uid, uname, isFansMedalBelongToLive, fansMedalLevel, isFansMedalVIP):
    if filterWelcome(uid, uname, isFansMedalBelongToLive, fansMedalLevel, isFansMedalVIP):
        appendWelcomeFilteredStats(uid=uid, uname=uname, filterd=False)
        messagesQueueAppend({
            'type': 'welcome',
            'time': time.time(),
            'uid': uid,
            'uname': uname
        })
    else:
        appendWelcomeFilteredStats(uid=uid, uname=uname, filterd=True)

async def markAllMessagesInvalid():
    global messagesQueue
    messagesQueue = [{
        'type': 'system',
        'time': time.time(),
        'msg': "已清空弹幕列表"
    }]
    setOutputMessagesLength(len(messagesQueue))