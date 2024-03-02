import { DynamicConfig } from "./DynamicConfig";

export type DanmuEvent = {
    'type': 'danmu',
    'filterd': boolean,
    'uid': number,
    'uname': string,
    'msg': string
};

export type GiftEvent = {
    'type': 'gift',
    'filterd': boolean,
    'uid': number,
    'uname': string,
    'giftName': string,
    'num': number
};

export type LikeEvent = {
    'type': 'like',
    'filterd': boolean,
    'uid': number,
    'uname': string
};

export type WelcomeEvent = {
    'type': 'welcome',
    'filterd': boolean,
    'uid': number,
    'uname': string
};

export type ConfigEvent = DynamicConfig;

export type StatsEvent = {
    "events": (DanmuEvent | GiftEvent | LikeEvent | WelcomeEvent)[],
    "stats": {
        'filteredDanmu': number,
        'rawDanmu': number,
        'filteredGift': number,
        'rawGift': number,
        'filteredWelcome': number,
        'rawWelcome': number,
        'filteredLike': number,
        'rawLike': number,
        'cpuUsage': number,
        'messagesQueueLength': number,
        'delay': number
    }
};

export type WebsocketBroadcastMessage = {
    "type": "stats",
    "data": StatsEvent
} | {
    "type": "config",
    "data": ConfigEvent
};