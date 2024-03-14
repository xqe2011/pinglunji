<template>
    <v-card class="mx-auto" elevation="4" @keydown="onKeydown">
        <v-card-title>
            <div><p tabindex="0">引擎配置 - 重启生效</p></div>
        </v-card-title>

        <v-form class="overflow-auto">
            <v-btn v-if="config.remote.enable" class="copy-button" block :loading="copying" color="yellow" @click="onCopyRemoteURL">复制远程连接链接</v-btn>
            <v-btn v-if="config.remote.enable" class="flush-button" block :loading="flushing" color="red" @click="onFlushRemoteURL">刷新远程连接密钥</v-btn>
            <v-divider v-if="config.remote.enable"></v-divider>

            <v-text-field v-model="config.douyin.liveID" label="直播间号" aria-label="直播间号"></v-text-field>
            <v-divider></v-divider>

            <v-switch v-model="config.remote.enable" inset color="blue" label="启用远程控制" aria-label="启用远程控制"></v-switch>
            <v-text-field v-model="config.remote.server" label="服务器地址" aria-label="远程控制的服务器地址"></v-text-field>
            
            <v-divider></v-divider>
            <v-btn class="save-button" :loading="saving" color="blue" @click="onSave" aria-label="引擎配置保存(可以使用键盘Ctrl+S保存)" block>保存</v-btn>
        </v-form>
    </v-card>
</template>

<style scoped>
.v-card {
    display: flex;
    flex-direction: column;
}
.v-form {
    padding: 0 16px 16px 16px;
}
.v-card-title {
    display: flex;
}
.v-card-title > div {
    flex-grow: 1;
    display: flex;
    align-items: center;
}
.v-card-title > .v-btn {
    margin-left: 8px;
}
.save-button {
    margin-top: 16px;
}
.copy-button, .flush-button {
    margin-bottom: 16px;
}
.block-divider {
    margin-bottom: 22px;
}
</style>

<script lang="ts" setup>
import { ref } from 'vue';
import { EngineConfig } from "../types/EngineConfig";
import { getEngineConfig, updateEngineConfig, onServerState, getRemoteURL, flushRemoteURL } from '@/services/Database';
import copy from 'clipboard-copy';

const config = ref(undefined as unknown as EngineConfig);
config.value = {
    douyin: {
        liveID: 0,
    },
    remote: {
        enable: false,
        server: ""
    },
};
const saving = ref(false);
const copying = ref(false);
const flushing = ref(false);

function onSave() {
    saving.value = true;
    /* 强制转换number类型 */
    config.value.douyin.liveID = Number(config.value.douyin.liveID);

    updateEngineConfig(config.value).then(val => {
        saving.value = false;
        alert('保存成功');
    }).catch(err => {
        console.error(err);
        saving.value = false;
        alert('保存失败');
    });
}

onServerState.subscribe(ready => {
    if (ready) {
        getEngineConfig().then(msg => {
            config.value = msg;
        });
    }
});

function onKeydown(event: KeyboardEvent) {
    if (event.ctrlKey && event.key === 's' || event.metaKey && event.key === 's') {
        event.preventDefault();
        onSave();
    }
}

function onCopyRemoteURL() {
    getRemoteURL().then(url => {
        copying.value = false;
        copy(url).then(() => {
            alert('已复制到剪切板');
        });
    }).catch(err => {
        console.error(err);
        copying.value = false;
        alert('获取失败');
    });
}

function onFlushRemoteURL() {
    flushRemoteURL().then(url => {
        flushing.value = false;
        alert('刷新成功，重启生效');
    }).catch(err => {
        console.error(err);
        flushing.value = false;
        alert('刷新失败');
    });
}
</script>