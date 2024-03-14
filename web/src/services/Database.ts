import axios from 'axios';
import { DynamicConfig } from '@/types/DynamicConfig';
import { WebsocketBroadcastMessage } from '@/types/WebsocketBroadcastMessage';
import { Subscriber } from '@/services/Subscriber';
import { EngineConfig } from '@/types/EngineConfig';
import Pusher from 'pusher-js';
import { Channel } from 'pusher-js';

let connectMode: "remote" | "local" = "local";
let websocketClient: WebSocket | undefined = undefined;
let pusherClient: Pusher | undefined = undefined;
let pusherChannel: Channel | undefined = undefined;
export const onWSMessages = new Subscriber<(data: WebsocketBroadcastMessage) => void>();
export const onServerState = new Subscriber<(ready: boolean) => void>(true, true);

async function wsRequest(method: string, args: any = {}) {
    /* 检查服务器状态 */
    await new Promise((resolve, reject) => {
        function callback(ready: boolean) {
            onServerState.unsubscribe(callback);
            ready ? resolve(undefined) : reject(new Error("Server not ready"));
        };
        onServerState.subscribe(callback);
    });
    const id = Math.floor(Math.random() * 100000000);
    const data = {
        id,
        method,
        args
    };
    if (connectMode === "local") {
        websocketClient?.send(JSON.stringify({ "type": "request", data }));
    } else {
        pusherChannel?.trigger("client-request", data);
    }
    return await new Promise((resolve, reject) => {
        function callback(msg: WebsocketBroadcastMessage) {
            if (msg.type === "response" && msg.data.id === id) {
                onWSMessages.unsubscribe(callback);
                if (msg.data.status != 0) {
                    reject(new Error(msg.data.msg))
                } else {
                    resolve(msg.data.msg);
                }
            }
        };
        onWSMessages.subscribe(callback);
    });
}

export async function getVoices() {
    const data = await wsRequest('getVoices');
    return data as { name: string, language: string }[];
}

export async function getDynamicConfig() {
    const data = await wsRequest('getDynamicConfig');
    return data as DynamicConfig;
}

export async function updateDynamicConfig(config: DynamicConfig) {
    await wsRequest('updateDynamicConfig', { config } );
}

export async function getEngineConfig() {
    const data = await wsRequest('getEngineConfig');
    return data as EngineConfig;
}

export async function updateEngineConfig(config: EngineConfig) {
    await wsRequest('updateEngineConfig', { config });
}

export async function getSpeakers() {
    const data = await wsRequest('getSpeakers');
    return data as string[];
}

export async function flushQueue() {
    await wsRequest('flush');
}

export async function getRemoteURL() {
    return (await wsRequest('getRemoteURL')) as string;
}

export async function flushRemoteURL() {
    await wsRequest('flushRemoteURL');
}

export async function getRunningMode() {
    return { 'remote': connectMode === "remote" } as { 'remote': boolean };
}

export async function connectLocal() {
    connectMode = "local";
    onServerState.emit(false);

    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    websocketClient = new WebSocket(`${protocol}${window.location.host}/client`);
    websocketClient.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onWSMessages.emit(data);
    };
    websocketClient.onopen = () => {
        console.log('[Database] Connected');
        onServerState.emit(true);
    };
    websocketClient.onclose = () => {
        console.log('[Database] Disconnected');
        onServerState.emit('connecting');
        setTimeout(() => connectLocal(), 1000);
    };
    
}

function onPusherConnected(channel: string) {
    console.log('[Database] Connected pusher client');
    const localPusherChannel = pusherClient?.subscribe(channel) as Channel;
    let subscribed = false;
    let signin = false;
    let onlined = false;
    localPusherChannel.bind("pusher:subscription_succeeded", () => {
        console.log('[Database] Subscribed pusher channel');
        pusherChannel = localPusherChannel;
        subscribed = true;
        if (subscribed && signin && onlined)
            onServerState.emit(true);
    });
    pusherClient?.bind("pusher:signin_success", () => {
        console.log('[Database] Sign in pusher user');
        signin = true;
        if (subscribed && signin && onlined)
            onServerState.emit(true);
    });
    pusherClient?.user.watchlist.bind("online", (event: { user_ids: string[] }) => {
        let serverConnected = false;
        event.user_ids.map(val => val.startsWith("server-") && (serverConnected = true));
        if (serverConnected) {
            onlined = true;
            if (subscribed && signin && onlined)
                onServerState.emit(true);
        }
    });
    pusherClient?.user.watchlist.bind("offline", (event: { user_ids: string[] }) => {
        let serverDisconnected = false;
        event.user_ids.map(val => val.startsWith("server-") && (serverDisconnected = true));
        if (serverDisconnected) {
            onServerState.emit(false);
        }
    });
    pusherClient?.signin();
    localPusherChannel?.bind("client-stats", (data: WebsocketBroadcastMessage['data']) => onWSMessages.emit({ "type": "stats", data }));
    localPusherChannel?.bind("client-config", (data: WebsocketBroadcastMessage['data']) => onWSMessages.emit({ "type": "config", data }));
    localPusherChannel?.bind("client-response", (data: WebsocketBroadcastMessage['data']) => onWSMessages.emit({ "type": "response", data }));
}

export async function connectRemote(url: string, channel: string, token: string) {
    connectMode = "remote";
    onServerState.emit(false);

    const response = await axios.get(url + "/config");

    if (response.status !== 200) {
        console.log('[Database] Cannot fetch pusher config, retrying...');
        setTimeout(() => connectRemote(url, channel, token), 1000);
    }

    if (typeof response.data['cluster'] !== "undefined") {
        pusherClient = new Pusher(response.data['key'], {
            cluster: response.data['cluster'],
            userAuthentication: {
                customHandler: async (params, callback) => {
                    const response = await axios.get(url + `/authorizeUser?role=client&socket_id=${params.socketId}&channel=${channel}&token=${token}`);
                    if (response.status !== 200) {
                        console.log(`[Database] Failed to authorize user`)
                        callback(new Error(`Failed to authorize user`), null);
                    } else {
                        console.log(`[Database] Authorized user: ${JSON.parse(response.data['user_data'])['id']}`)
                        callback(null, response.data);
                    }
                }
            },
            channelAuthorization: {
                customHandler: async (params, callback) => {
                    const response = await axios.get(url + `/authorizeChannel?socket_id=${params.socketId}&channel=${params.channelName}&token=${token}`);
                    if (response.status !== 200) {
                        console.log(`[Database] Failed to authorize channel: ${params.channelName}`)
                        callback(new Error(`Failed to authorize channel: ${params.channelName}`), null);
                    } else {
                        console.log(`[Database] Authorized channel: ${params.channelName}`)
                        callback(null, { auth: response.data['auth'] });
                    }
                }
            }
        });
    }
    pusherClient?.connection.bind("connected", () => onPusherConnected(channel));
    pusherClient?.connect();
}

function onServerStateEmit(ready: boolean) {
    console.log("[Database] Server ready changed to " + ready)
}

export async function init() {
    onServerState.unsubscribe(onServerStateEmit);
    onServerState.subscribe(onServerStateEmit);
}