# 91Download

91 镜像站视频批量下载工具，基于 CustomTkinter 现代界面。

## 功能

- 批量爬取 / 搜索 / 单视频下载
- M3U8 并发切片 + AES 解密 + FFmpeg 合并
- SOCKS5 代理支持
- 封面预览 / 实时进度 / 防重复下载

## 快速使用

### 下载运行（推荐）

去 [Releases](https://github.com/BiliNico-com/91Download/releases) 下载最新 zip，解压后双击 `91Download.exe` 即可。

### 从源码运行

```bash
pip install -r requirements.txt
python main_ui.py
```

## 构建

推送 tag 自动触发 GitHub Actions 编译：

```bash
git tag v1.0.0
git push origin v1.0.0
```

## 依赖

```
customtkinter  requests  Pillow  pycryptodome
```
