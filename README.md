# 🕷️ WebSpider Pro — 视频下载器 (Modern UI)

<div align="center">

**基于 CustomTkinter 的现代化视频批量下载工具**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

[功能介绍](#-功能特性) · [快速开始](#-快速开始) · [使用说明](#-使用说明) · [构建发布](#-构建发布)

</div>

---

## ✨ 功能特性

| 模块 | 功能 |
|:-----|:-----|
| **📦 批量爬取** | 选择站点 / 列表类型 / 页码范围，一键批量下载视频 |
| **🔍 搜索** | 关键词搜索视频或作者，支持最新/最热排序 |
| **🎬 单视频** | 分页浏览 + 视频卡片网格 + 勾选下载 + 手动 URL 输入 |
| **⚙️ 设置** | 保存路径 / 文件命名规则 / SOCKS5 代理配置 |
| **📋 运行日志** | 实时日志输出 / 清空 / 导出 |
| **✅ 环境检测** | 一键检查 ffmpeg、requests、Pillow 等依赖 |

### 核心能力

- ⚡ **并发切片下载** — M3U8 TS 分片多线程加速
- 🔒 **AES 解密** — 自动处理加密视频流
- 🎬 **FFmpeg 合并** — TS → MP4 自动转码合并
- 🖼️ **封面预览** — 异步加载视频缩略图
- 🌐 **SOCKS5 代理** — 支持代理访问，内置连接测试
- 🚫 **防重复下载** — 已完成记录，跳过已下载视频
- 📊 **实时统计** — 下载速度 / 进度条 / 流量统计

### UI 特性

- 🎨 **CustomTkinter** 现代圆角界面，深浅色主题适配
- 📐 左侧垂直导航栏 + 右侧内容区双栏布局
- 💜 渐变主色调 + 语义化按钮（主操作/危险/次要）
- 🔄 实时进度反馈（切片进度 + 合并进度双进度条）

---

## 🚀 快速开始

### 环境要求

- **Python** 3.10+
- **Windows** 10/11（GUI 界面）
- **FFmpeg**（用于视频合并，程序可自动下载）

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/webspider-pro.git
cd webspider-pro

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python main_ui.py
```

> 首次运行会自动创建 `config.json` 配置文件和 `downloads/` 下载目录。

---

## 📖 使用说明

### 批量爬取

1. 在左侧导航选择 **📦 批量爬取**
2. 选择目标站点和列表类型
3. 设置起始页码和结束页码
4. 点击 **▶ 开始爬取**
5. 查看实时进度：封面预览 → 切片下载 → 合并 MP4

### 搜索下载

1. 切换到 **🔍 搜索** 标签
2. 输入关键词，回车或点击搜索按钮
3. 切换「搜视频」或「搜作者」模式
4. 搜索结果支持勾选后批量下载

### 单视频下载

1. 在 **🎬 单视频** 中选择站点和列表类型
2. 点击「加载」获取当前页码的视频列表
3. 勾选需要的视频，点击「下载选中」
4. 或直接粘贴视频 URL 到手动输入框下载

### 代理设置

在 **⚙️ 设置** 中配置 SOCKS5 代理：

- 填写主机、端口、账号密码
- 启用代理开关
- 可测试到 Google / YouTube / Twitter 的连通性

### 环境检测

切换到 **✅ 环境检测** 标签：

- 自动检查 Python 依赖是否安装完整
- 检测 FFmpeg 是否可用
- 一键安装缺失依赖 / 下载 FFmpeg

---

## 🏗️ 项目结构

```
webspider-pro/
├── main_ui.py              # 主程序入口（UI + 全部业务逻辑）
├── crawler_core.py         # 爬虫核心引擎（M3U8解析/TS下载/解密/合并）
├── config.json             # 运行配置（首次运行自动生成）
├── downloads/              # 默认下载目录
│   └── completed.json      # 已完成记录（防重复）
├── requirements.txt        # Python 依赖
├── web-spider-ui.html      # HTML 原型设计稿
├── DESIGN-SPEC.md          # 设计规范文档
├── MIGRATION-GUIDE.md      # UI 改造迁移指南
├── README.md               # 项目说明
└── .github/
    └── workflows/
        └── build.yml       # CI/CD 自动打包
```

---

## 🔧 构建 release（exe 打包）

项目已配置 GitHub Actions，推送 tag 后自动构建：

```bash
# 创建并推送版本号
git tag v1.0.0
git push origin v1.0.0
```

Actions 会自动：
1. 安装 Python 3.12 + 全部依赖
2. 使用 PyInstaller 打包成单文件 exe
3. 上传 Release Artifact

也可以本地构建：

```bash
# 安装打包工具
pip install pyinstaller

# 打包（单文件模式）
pyinstaller --onefile --windowed --name "WebSpider-Pro" --icon=icon.ico main_ui.py

# 输出在 dist/WebSpider-Pro.exe
```

---

## 📦 依赖清单

```
customtkinter>=5.2.2    # 现代 Tkinter UI 框架
requests>=2.31          # HTTP 请求
Pillow>=10.0            # 图片处理（封面）
pycryptodome>=3.19      # AES 解密
PyInstaller>=6.0        # 打包为 exe（可选）
```

---

## ⚙️ 配置说明

`config.json` 配置项：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `output_dir` | 下载保存路径 | `./downloads` |
| `ffmpeg_path` | FFmpeg 路径（空则自动查找） | `""` |
| `proxy_enabled` | 是否启用 SOCKS5 代理 | `false` |
| `proxy_host` | 代理主机 | `"127.0.0.1"` |
| `proxy_port` | 代理端口 | `"1080"` |
| `tag_author` | 文件名包含上传者名称 | `true` |
| `date_folder` | 按上传日期分子目录 | `true` |

---

## 📄 License

MIT License

---

<div align="center">

Made with ❤️ using [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

</div>
