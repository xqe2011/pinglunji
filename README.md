# 企鹅评论机
为语音读评论而生的抖音直播评论机。
- 支持无障碍，对于视力障碍群体可以完全实现自己操作和控制
- 支持高速语音，比常规评论机的语速更快，可以在大量评论时降低语音延迟
- 支持多种过滤功能，如屏蔽词/表情包等
- 支持图表显示评论机实时数据，方便在线调节参数
- 支持中文/英文
- 支持远程控制功能，你可以连接远程服务器后通过分享链接让其他人控制评论机

## 使用方法
- 点击[这里](https://github.com/xqe2011/pinglunji/releases/download/latest/installer.exe)下载最新版
- 打开下载的文件并点击安装，安装完成后在桌面打开企鹅评论机图标
- 在弹出的企鹅评论机配置页面处设置好直播间号，重启评论机

# 常用键位
部分游戏会占用所有键位，此时全局键位功能将失效。 
| 场景 | 键位 | 功能 |
|---|---|---|
| 网页 | Ctrl+S | 保存配置 |
| 任何时候 | Ctrl+Alt+等于号 | 音量增加 |
| 任何时候 | Ctrl+Alt+减号 | 音量减少 |
| 任何时候 | Ctrl+Alt+左方括号 | 语速增加 |
| 任何时候 | Ctrl+Alt+右方括号 | 语速减少 |
| 任何时候 | Ctrl+Alt+M | 音频输出切换 |
| 任何时候 | Alt+F6 | 查看评论延迟 |
| 任何时候 | Ctrl+Alt+F5 | 清空评论 |
| 任何时候 | Alt+F7 | 历史模式查看上一条礼物 |
| 任何时候 | Alt+F8 | 历史模式查看上一条评论 |
| 任何时候 | Alt+T | 历史模式查看下一条礼物 |
| 任何时候 | Alt+Y | 历史模式查看下一条评论 |
| 任何时候 | Alt+F9 | 历史模式回到最新评论 |

## 贡献本项目
### 克隆并安装依赖
请先安装Python和Go, 可在对应语言官网下载安装
```
git clone --recurse-submodules https://github.com/xqe2011/pinglunji
pip install -r requirements.txt
set GO111MODULE=on
go install github.com/zeromicro/go-zero/tools/goctl@latest
goctl env check --install --verbose --force
```
### 编译Proto
```
python -m tools.generate_proto
```
### 编译配置页面
```
cd web
npm run build
cd ../
mv ./web/dist ./static
```
### 启动主程序
```
python launcher.py
```
### 打包
```
pyinstaller launcher.spec
```