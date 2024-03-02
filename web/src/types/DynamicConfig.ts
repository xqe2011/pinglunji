export type DynamicConfig = {
    "system": {
        "alertWhenMessagesQueueLonger": {
            "enable": boolean,
            "threshold": number,
            "interval": number
        }
    },
    "tts": {
        "readSymbolEnable": boolean,
        "speaker": string,
        "volume": number,
        "voice": string,
        "rate": number,
        "history": {
            "voice": string,
            "rate": number,
            "volume": number
        }
    },
    "filter": {
        "danmu": {
            "enable": boolean,
            "symbolEnable": boolean,
            "emojiEnable": boolean,
            "deduplicate": boolean,
            "isFansMedalBelongToLive": boolean,
            "fansMedalLevelBigger": number,
            "isFansMedalVIP": boolean,
            "lengthShorter": number,
            "blacklistKeywords": string[],
            "blacklistUsers": string[],
            "whitelistUsers": string[],
            "whitelistKeywords": string[]
        },
        "gift": {
            "enable": boolean,
            "deduplicateTime": number,
            "moneyGiftPriceBigger": number,
        },
        "welcome": {
            "enable": boolean,
            "isFansMedalBelongToLive": boolean,
            "fansMedalLevelBigger": number,
            "isFansMedalVIP": boolean,
        },
        "like": {
            "enable": boolean,
            "deduplicate": boolean,
        },
    }
};