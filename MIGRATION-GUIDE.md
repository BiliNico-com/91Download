# WebSpider Pro — UI 改造迁移指南

> **目标**：将现有原生 Tkinter 界面升级为 CustomTkinter 现代风格  
> **源文件**：`main_ui.py`（完整可运行的新版 UI 代码）  
> **日期**：2026-04-09

---

## 一、现状分析

### 你现有的界面结构（6个Tab）

| Tab 名称 | 功能 | 原始控件 |
|----------|------|---------|
| **批量爬取** | 按页码范围批量下载视频 | 下拉框(站点/列表) + Spinbox(页码) + 开始/停止按钮 + 视频列表 + 进度区 |
| **搜索** | 关键词搜索并下载 | 同上 + 额外关键词输入框 + 类型选择 |
| **单视频** | 加载单个视频列表选择性下载 | 分页控件(◀ 页码 ▶) + 加载按钮 + 全选checkbox |
| **设置** | 保存目录、下载选项、SOCKS5代理 | 路径输入+浏览按钮、Checkbox、主机端口账号密码 |
| **运行日志** | 显示程序执行记录 | Text文本框 + 清空/导出按钮 |
| **环境检测** | 检查ffmpeg/requests等依赖 | 结果Text框 + 重检/安装/下载按钮 |

### 原界面问题诊断

| 问题 | 具体表现 | 严重度 |
|------|---------|--------|
| **视觉陈旧** | 原生 Tkinter 灰色风格，无圆角、无渐变、无阴影 | ⭐⭐⭐ |
| **Tab导航扁平** | 6个Tab平铺在顶部，信息层级不清晰 | ⭐⭐⭐ |
| **空间利用率低** | 大面积空白，控件排列松散 | ⭐⭐ |
| **缺乏状态反馈** | 无统计卡片、无实时进度指示器 | ⭐⭐ |
| **色彩单调** | 只有系统默认灰蓝配色，无品牌感 | ⭐⭐ |

---

## 二、改造方案总览

### 架构变更

```
┌─────────────────────────────────────────────┐
│  旧布局 (原生Tkinter)                        │
│  ┌──────────────────────────────────┐      │
│  │ [批量爬取][搜索][单视频]...       │ ← Tab栏 │
│  ├──────────────────────────────────┤      │
│  │                                  │      │
│  │        Tab 内容区域               │      │
│  │                                  │      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘

                    ↓ 改造 ↓

┌─────────────────────────────────────────────┐
│  新布局 (CustomTkinter 现代版)               │
│ ┌──────────┬──────────────────────────────┐ │
│ │          │  📦 批量爬取                 │ │
│ │  🕷️     │  按页面范围批量下载...         │ │
│ │ 品牌    │  [● 就绪]                    │ │
│ │          ├──────────────────────────────┤ │
│ │ ┌──────┐│                              │ │
│ │ │📦批量 ││  ┌─────────┐  ┌──────────┐  │ │
│ │ │🔍搜索 ││  │ 配置卡片 │  │ 视频+进度│  │ │
│ │ │🎬单个 ││  └─────────┘  └──────────┘  │ │
│ │ │⚙️设置 ││                              │ │
│ │ │📋日志 ││                              │ │
│ │ │✅环境 ││                              │ │
│ │ └──────┘│                              │ │
│ │ [Pro卡] │                              │ │
│ └──────────┴──────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 核心改造点

| # | 改造项 | 旧 → 新 |
|---|--------|--------|
| 1 | **导航方式** | 顶部 Tab → 左侧边栏垂直导航（图标+文字） |
| 2 | **整体框架** | `ttk.Notebook` → CustomTkinter Frame 切换 |
| 3 | **页面标题** | 无 → 每页顶部大标题 + 副标题说明 |
| 4 | **配置区域** | LabelFrame 平铺 → 圆角卡片 (Card) 容器 |
| 5 | **下拉框** | `ttk.Combobox` → `ctk.CTkOptionMenu`（现代风格）|
| 6 | **按钮样式** | 默认灰色 → 渐变主色 / 语义色（红/绿/蓝）|
| 7 | **背景色** | 系统灰色 `#f0f0f0` → 浅蓝灰 `#f0f4f8` |
| 8 | **文字颜色** | 系统黑色 → 层次化灰阶 (`#1e293b` → `#94a3b8`) |
| 9 | **圆角** | 0px (方角) → 12~16px (大圆角) |
| 10 | **间距** | 紧凑 → 宽松舒适 (20~28px 内边距) |
| 11 | **新增元素** | — | 状态指示器(就绪/运行)、品牌Logo、升级提示卡 |

---

## 三、控件映射对照表

### 3.1 批量爬取 Tab

```
旧代码                          新代码
────────                        ────────
Label("爬取设置")                → _create_card(parent, "爬取配置")   [带标题的圆角卡片]
Combobox(站点)                   → CTkOptionMenu(variable=batch_site_var, ...)
Combobox(列表:list)              → CTkOptionMenu(variable=batch_list_var, ...)
Spinbox(页码: 1 ~ 3)             → CTkEntry(textvariable=start/end_page)
Button("▶ 开始爬取")             → CTkButton(fg_color=PRIMARY, ...)     [紫蓝色主按钮]
Button("■ 停止")                 → CTkButton(fg_color=ERROR, ...)       [红色停止按钮]

Labelframe("当前视频")           → _create_card(parent, "当前视频")
Text/Listbox (视频列表)          → CTkTextbox(state="disabled")

Labelframe("下载进度")           → _create_card(parent, "下载进度")
Label("就绪")                    → CTkLabel(font=bold)
Text (日志区)                    → CTkTextbox(height=80)
Button("日志")                   → CTkButton(fg_color=BG_INPUT, ...)   [浅灰次要按钮]
Button("导出")                   → 同上
```

### 3.2 搜索 Tab

与批量爬取结构相同，额外增加：
```
Entry(关键词)                    → CTkEntry(textvariable=search_keyword)
Combobox(排序:最新)              → CTkOptionMenu(variable=search_sort_var, ...)
```

### 3.3 单视频 Tab

```
旧代码                          新代码
────────                        ────────
Combobox(站点/类型)              → CTkOptionMenu(...)
Spinbox(页码) + ◀ ▶ 按钮        → CTkEntry + CTkButton(◀/▶)
Button("加载")                   → CTkButton(fg_color=BG_INPUT, ...)
Button("下载选中")               → CTkButton(fg_color=PRIMARY, ...)
Checkbutton("全选")              → CTkCheckbutton(...)

Label("点击加载获取...")         → CTkLabel(text_color=MUTED)

Labelframe("下载进度")           → _create_card(parent, "下载进度")
  Entry(就绪/切片/合并) ×3       → CTkEntry ×3
  Button(日志/导出)              → CTkButton ×2

Labelframe("手动URL")            → _create_card(parent, "手动输入 URL")
  Entry(URL)                     → CTkEntry
  Button(下载)                   → CTkButton(fg_color=PRIMARY, ...)
```

### 3.4 设置 Tab

```
旧代码                          新代码
────────                        ────────
Label("应用设置" - 居中大标题)   → CTkLabel(font=size22, bold)

Labelframe("保存目录")           → _create_card(parent, "保存目录")
Entry(路径)                      → CTkEntry(textvariable=save_dir)
Button("选择目录...")            → CTkButton(command=_browse_dir)

Labelframe("下载设置")           → _create_card(parent, "下载设置")
Checkbutton("标签包含上传者")    → CTkCheckbutton(variable=tag_author_var)
Checkbutton("按日期分类")        → CTkCheckbutton(variable=date_folder_var)

Labelframe("SOCKS5代理")         → _create_card(parent, "SOCKS5 代理（可选）")
Checkbutton("启用代理")          → CTkCheckbutton(variable=proxy_enable)
Entry(主机/端口/账号/密码)       → CTkEntry (密码用 show="●")
Button("测试代理连接")           → CTkButton(fg_color=BG_INPUT, ...)

Button("保存设置")               → CTkButton(fg_color=PRIMARY, ...)
Button("检查环境")               → CTkButton(fg_color=BG_INPUT, ...)
```

### 3.5 运行日志 Tab

```
旧代码                          新代码
────────                        ────────
Text(日志内容, font=Consolas)   → CTkTextbox(font=("Consolas",12), border_width=2)
Button("清空日志")              → CTkButton(fg_color=ERROR, ...)
Button("导出日志...")           → CTkButton(fg_color=BG_INPUT, ...)
```

### 3.6 环境检测 Tab

```
旧代码                          新代码
────────                        ────────
Label("运行环境检查" - 标题)     → CTkLabel(font=size22, bold)
Text(检测结果)                  → CTkTextbox(font=("Consolas",12))
Button("重新检查")              → CTkButton(fg_color=PRIMARY, command=_check_env)
Button("安装Python依赖")        → CTkButton(fg_color=WARNING, ...)
Button("下载 ffmpeg")           → CTkButton(fg_color=INFO, ...)
```

---

## 四、如何集成到你的项目中

### 步骤 1：安装依赖

```bash
pip install customtkinter
```

### 步骤 2：替换你的 GUI 入口

```python
# === 旧代码入口（示例）===
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("视频下载器")

notebook = ttk.Notebook(root)
# ... 创建各 Tab ...

root.mainloop()

# ========== 替换为 ==========

# === 新代码入口 ===
from main_ui import ModernApp

app = ModernApp()   # 自动创建窗口和所有UI
app.mainloop()
```

### 步骤 3：绑定业务逻辑

`main_ui.py` 中的所有控件都通过 `textvariable` 绑定了变量，你只需：

```python
# 获取用户设置的值
site = app.batch_site_var.get()        # "选择站点"
page_start = app.batch_start_page.get()  # "1"
save_path = app.save_dir.get()

# 绑定按钮回调
# 在 _build_batch_page 中修改 start_btn 的 command:
start_btn.configure(command=self.start_batch_crawl)

# 在类中添加方法:
def start_batch_crawl(self):
    site = self.batch_site_var.get()
    start = self.batch_start_page.get()
    end = self.batch_end_page.get()
    print(f"开始爬取: {site}, 页 {start}-{end}")
    # ... 你的爬取逻辑 ...
```

### 步骤 4：保留你的核心逻辑

**关键原则：UI 和逻辑分离**

```
你的项目结构建议：
project/
├── core/
│   ├── crawler.py        # 核心爬虫逻辑（不动）
│   ├── downloader.py     # 下载逻辑（不动）
│   ├── config.py         # 配置管理（不动）
│   └── utils.py          # 工具函数（不动）
├── ui/
│   └── main_ui.py        # ★ 新版界面（已提供）
├── main.py               # 入口：导入 core + 启动 UI
└── requirements.txt      # customtkinter + 你的其他依赖
```

---

## 五、设计令牌速查（供后续微调使用）

所有颜色/尺寸集中在 `Theme` 类中，一处修改全局生效：

```python
# 修改主题色（例如换成绿色系）：
class Theme:
    PRIMARY = "#10b981"        # 改成绿色
    PRIMARY_HOVER = "#059669"
    GRADIENT_START = "#10b981"
    GRADEND_END = "#34d399"

# 修改圆角大小：
CARD_RADIUS = 24             # 更圆润
INPUT_RADIUS = 16

# 修改侧边栏宽度：
SIDEBAR_WIDTH = 280          # 更宽的侧边栏
```

---

## 六、已知限制 & 后续优化方向

| 项目 | 当前状态 | 建议 |
|------|---------|------|
| **暗色模式** | 仅支持 Light | 可通过 `ctk.set_appearance_mode("dark")` 开启，但需调整部分硬编码色值 |
| **多语言** | 中文硬编码 | 可提取为 i18n 字典 |
| **图标系统** | Emoji 文字图标 | 生产环境可换为 PNG/SVG 图标或 `tkinter.PhotoImage` |
| **图表组件** | 未包含 | 可集成 `matplotlib` 嵌入 `CTkFrame`，展示下载速度曲线 |
| **托盘最小化** | 未实现 | 可用 `pystray` 库实现系统托盘 |

---

*本指南由 UI Designer Agent 🎨 编写，配合 `main_ui.py` 使用效果最佳。*
