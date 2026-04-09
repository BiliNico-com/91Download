#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
91Download - 91镜像站视频下载器
基于 CustomTkinter 的现代化界面
"""

import os
import sys
import json
import logging
import threading
import time
import subprocess
import io
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    print("错误: 请先安装 customtkinter: pip install customtkinter")
    sys.exit(1)

# ---- 爬虫核心模块 ----
_CRAWLER_DIR = Path(__file__).parent  # crawler_core.py 在同目录下
if str(_CRAWLER_DIR) not in sys.path:
    sys.path.insert(0, str(_CRAWLER_DIR))

from crawler_core import (
    CrawlerCore, MIRROR_SITES, LIST_TYPES,
    LIST_TYPE_ALIASES, DEFAULT_HEADERS, download_image
)

# ==================== 配置 ====================

APP_DIR = Path(__file__).parent
CONFIG_FILE = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "output_dir": str(APP_DIR / "downloads"),
    "ffmpeg_path": "",
    "proxy_enabled": False,
    "proxy_host": "127.0.0.1",
    "proxy_port": "1080",
    "proxy_user": "",
    "proxy_pass": "",
    "site": "https://ml0987.xyz",
    "list_type": "list",
    "page_start": 1,
    "page_end": 3,
    "title_with_author": True,
    "sort_by_upload_date": True,
}

# ==================== 日志 ====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==================== 设计令牌系统 ====================

class Theme:
    """全局设计令牌"""
    PRIMARY = "#6366f1"
    PRIMARY_HOVER = "#4f46e5"
    PRIMARY_DARK = "#3730a3"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"

    GRADIENT_START = "#6366f1"
    GRADIENT_END = "#8b5cf6"

    BG_BODY = "#f0f4f8"
    BG_CARD = "#ffffff"
    BG_SIDEBAR = "#ffffff"
    BG_INPUT = "#f8fafc"
    BG_HOVER = "#eef2ff"

    TEXT_PRIMARY = "#1e293b"
    TEXT_SECONDARY = "#64748b"
    TEXT_MUTED = "#94a3b8"

    BORDER_COLOR = "#e2e8f0"

    CARD_RADIUS = 16
    INPUT_RADIUS = 10
    BTN_RADIUS = 8


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


# ==================== 主应用类 ====================

class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("视频下载器")
        self.geometry("1200x750")
        self.minsize(1000, 680)
        self.configure(fg_color=Theme.BG_BODY)

        # 加载配置
        self.config = load_config()

        # 核心状态
        self.crawler = None
        self.crawl_thread = None
        self._crawl_stopping = False
        self._cover_photo = None
        self._search_cover_photo = None
        self._batch_total_videos = 0
        self._batch_done_videos = 0
        self._batch_success = 0

        try:
            from PIL import Image, ImageTk
            self._has_pil = True
        except ImportError:
            self._has_pil = False

        # 当前页面名跟踪
        self.current_page_name = ctk.StringVar(value="batch")

        # 构建UI
        self._build_sidebar()
        self._build_main_area()
        self._show_initial_page()

        # 静默环境检查
        self.after(500, self._silent_env_check)

    # ================================================================
    #  布局构建：侧边栏 + 内容区
    # ================================================================

    def _build_sidebar(self):
        """左侧导航栏"""
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=Theme.BG_SIDEBAR,
                                     corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 品牌 Logo 区
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(24, 16))

        logo_lbl = ctk.CTkLabel(brand, text="📥", font=ctk.CTkFont(size=28))
        logo_lbl.pack(anchor="w")
        name_lbl = ctk.CTkLabel(brand, text="91Download",
                                 font=ctk.CTkFont(size=17, weight="bold"),
                                 text_color=Theme.TEXT_PRIMARY)
        name_lbl.pack(anchor="w", pady=(2, 0))

        # 分隔线
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=Theme.BORDER_COLOR)
        sep.pack(fill="x", padx=20, pady=(0, 12))

        # 导航按钮
        nav_items = [
            ("📦", "批量爬取", "batch"),
            ("🔍", "搜索",     "search"),
            ("🎬", "单视频",   "single"),
            ("⚙️", "设置",     "settings"),
            ("📋", "运行日志", "logs"),
            ("✅", "环境检测", "envcheck"),
        ]

        self.nav_buttons = {}
        self.nav_frames = {}

        for i, (icon, label, page_name) in enumerate(nav_items):
            nav_btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {label}",
                font=ctk.CTkFont(size=14),
                fg_color="transparent" if page_name != "batch" else Theme.BG_HOVER,
                hover_color=Theme.BG_HOVER,
                text_color=Theme.PRIMARY if page_name == "batch" else Theme.TEXT_SECONDARY,
                anchor="w",
                height=42,
                corner_radius=Theme.INPUT_RADIUS,
                command=lambda pn=page_name: self.show_frame(pn),
            )
            nav_btn.grid(row=i+1, column=0, sticky="ew", padx=(12, 12), pady=2)
            self.nav_buttons[page_name] = nav_btn
            self.nav_frames[page_name] = (nav_btn, nav_btn)

    def _build_main_area(self):
        """右侧内容区"""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="left", fill="both", expand=True, padx=(0, 0))

        # 顶部标题栏
        self.header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header.pack(fill="x", padx=24, pady=(24, 0))

        self.page_title = ctk.CTkLabel(
            self.header, text="📦 批量爬取",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=Theme.TEXT_PRIMARY
        )
        self.page_title.pack(side="left")

        self.page_subtitle = ctk.CTkLabel(
            self.header, text="按页面范围批量下载视频资源",
            font=ctk.CTkFont(size=13), text_color=Theme.TEXT_SECONDARY
        )
        self.page_title.pack(side="left")  # fix pack order
        self.page_subtitle.pack(side="left", padx=(12, 0))

        status_box = ctk.CTkFrame(self.header, fg_color="#d1fae5", corner_radius=20)
        status_box.pack(side="right", padx=(10, 0), pady=(4, 0))
        ctk.CTkLabel(status_box, text="● 就绪", text_color=Theme.SUCCESS,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(padx=14, pady=6)

        # 页面容器
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, padx=20, pady=(16, 20))

        # 构建各页面
        self.pages = {}
        self._build_batch_page()      # pages["batch"]
        self._build_search_page()     # pages["search"]
        self._build_single_page()     # pages["single"]
        self._build_settings_page()   # pages["settings"]
        self._build_logs_page()       # pages["logs"]
        self._build_envcheck_page()   # pages["envcheck"]

    def _show_initial_page(self):
        """显示初始页面"""
        for name, frame in self.pages.items():
            if name == "batch":
                self._place_frame(frame)
            else:
                frame.place_forget()

    def show_frame(self, page_name: str):
        """切换显示的页面"""
        # 隐藏所有
        for name, frame in self.pages.items():
            frame.place_forget()

        # 显示目标页
        target = self.pages.get(page_name)
        if target:
            self._place_frame(target)
            self.current_page_name.set(page_name)

        # 更新标题
        titles = {
            "batch":   ("📦 批量爬取", "按页面范围批量下载视频资源"),
            "search":  ("🔍 搜索",     "通过关键词搜索并下载视频"),
            "single":  ("🎬 单视频",   "加载单个视频列表并选择性下载"),
            "settings":("⚙️ 应用配置", "保存目录、代理、下载选项"),
            "logs":    ("📋 运行日志", "查看程序执行记录"),
            "envcheck":("✅ 环境检查", "检查依赖是否安装完整"),
        }
        title, subtitle = titles.get(page_name, ("", ""))
        self.page_title.configure(text=title)
        self.page_subtitle.configure(text=subtitle)

        # 更新导航高亮
        for pn, (nav_btn, _) in self.nav_frames.items():
            if pn == page_name:
                nav_btn.configure(fg_color=Theme.BG_HOVER, text_color=Theme.PRIMARY,
                                   font=ctk.CTkFont(size=14, weight="bold"))
            else:
                nav_btn.configure(fg_color="transparent", text_color=Theme.TEXT_SECONDARY,
                                   font=ctk.CTkFont(size=14))

    def _place_frame(self, frame):
        """放置页面框架"""
        frame.place(in_=self.content_area, relx=0.5, rely=0.5, anchor="center",
                    relwidth=1.0, relheight=1.0)

    # ====================================================================
    #  工具方法
    # ====================================================================

    @staticmethod
    def _format_bytes(b: float) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024:
                return f"{b:.1f} {unit}" if unit != 'B' else f"{int(b)} {unit}"
            b /= 1024
        return f"{b:.2f} TB"

    @staticmethod
    def _format_speed(bps: float) -> str:
        return ModernApp._format_bytes(bps) + "/s"

    def _log_to_ui(self, text_widget, message, level="info"):
        """线程安全写入日志到指定文本框"""
        def _append():
            timestamp = time.strftime("%H:%M:%S")
            prefix = {"error": "✗", "warn": "⚠", "info": "ℹ"}.get(level, "·")
            text_widget.insert("end", f"[{timestamp}] {prefix} {message}\n")
            text_widget.see("end")
        try:
            self.after(0, _append)
        except Exception:
            pass

    def _status_to_ui(self, text_widget, text):
        if text_widget is None:
            return
        try:
            self.after(0, lambda tw=text_widget, t=text: tw.insert("end", f"{t}\n") or tw.see("end"))
        except Exception:
            pass

    def _update_progress(self, progressbar, current, total, label_widget=None, label_text=None):
        if total > 0:
            percent = (current / total) * 100
            try:
                self.after(0, lambda pb=progressbar: pb.configure(value=percent))
                if label_widget and label_text:
                    self.after(0, lambda lw=label_widget, lt=label_text: lw.configure(text=lt))
            except Exception:
                pass

    def _confirm_dialog(self, opts: dict) -> str:
        """倒计时确认弹窗（CustomTkinter版）"""
        result = {"value": opts.get("default", opts["choices"][0][0])}
        ready = threading.Event()
        dialog_ref = [None]

        def _show():
            try:
                dialog = ctk.CTkToplevel(self)
                dialog.title(opts.get("title", "提示"))
                dialog.geometry("480x260")
                dialog.resizable(False, False)
                dialog.attributes("-topmost", True)
                dialog.transient(self)

                dialog.update_idletasks()
                x = (dialog.winfo_screenwidth() // 2) - 240
                y = (dialog.winfo_screenheight() // 2) - 130
                dialog.geometry(f"480x260+{x}+{y}")

                dialog_ref[0] = dialog

                msg_label = ctk.CTkLabel(dialog, text=opts.get("message", ""),
                                         font=ctk.CTkFont(size=14), wraplength=420,
                                         justify="left")
                msg_label.pack(padx=30, pady=(25, 5))

                countdown_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11),
                                            text_color=Theme.TEXT_MUTED)
                countdown_lbl.pack(pady=5)

                btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
                btn_frame.pack(pady=15)

                remaining = {"count": opts.get("countdown", 10)}
                selected = {"value": opts.get("default", opts["choices"][0][0])}
                timer_job = {"id": None}
                _closed = [False]

                def do_close():
                    if _closed[0]:
                        return
                    _closed[0] = True
                    if timer_job["id"]:
                        try:
                            dialog.after_cancel(timer_job["id"])
                        except Exception:
                            pass
                    try:
                        dialog.destroy()
                    except Exception:
                        pass
                    ready.set()

                def update_countdown():
                    if _closed[0]:
                        return
                    if getattr(self, '_crawl_stopping', False) or \
                       (self.crawler and getattr(self.crawler, '_stop_flag', False)):
                        result["value"] = opts["choices"][-1][0]
                        do_close()
                        return
                    if remaining["count"] > 0:
                        default_label = next((l for v, l in opts['choices'] if v == selected['value']), "")
                        countdown_lbl.configure(text=f"【{remaining['count']} 秒后自动选择「{default_label}】】")
                        remaining["count"] -= 1
                        timer_job["id"] = dialog.after(1000, update_countdown)
                    else:
                        result["value"] = selected["value"]
                        do_close()

                def on_select(value, label):
                    if _closed[0]:
                        return
                    selected["value"] = value
                    do_close()

                for value, label_text in opts["choices"]:
                    is_default = value == opts.get("default")
                    ctk.CTkButton(btn_frame, text=label_text,
                                  font=ctk.CTkFont(size=13),
                                  width=140, height=36,
                                  fg_color=Theme.PRIMARY if is_default else Theme.BG_INPUT,
                                  hover_color=Theme.PRIMARY_HOVER if is_default else Theme.BG_HOVER,
                                  text_color="white" if is_default else Theme.TEXT_PRIMARY,
                                  command=lambda v=value, l=label_text: on_select(v, l)).pack(side="left", padx=6)

                def on_esc(e=None):
                    if opts["choices"]:
                        on_select(opts["choices"][-1][0], opts["choices"][-1][1])
                dialog.bind("<Escape>", on_esc)
                dialog.protocol("WM_DELETE_WINDOW", lambda: on_select(
                    opts["choices"][-1][0], opts["choices"][-1][1]))

                timer_job["id"] = dialog.after(1000, update_countdown)
            except Exception as e:
                result["value"] = opts.get("default", opts["choices"][0][0] if opts.get("choices") else "")
                ready.set()

        self.after(0, _show)

        deadline = time.time() + (opts.get("countdown", 10)) + 30
        while time.time() < deadline:
            if ready.is_set():
                break
            if getattr(self, '_crawl_stopping', False) or \
               (self.crawler and getattr(self.crawler, '_stop_flag', False)):
                if dialog_ref[0]:
                    try:
                        if dialog_ref[0].winfo_exists():
                            dialog_ref[0].destroy()
                    except Exception:
                        pass
                ready.set()
                break
            time.sleep(0.3)
        else:
            if not ready.is_set():
                result["value"] = opts.get("default", opts["choices"][0][0] if opts.get("choices") else "")
                ready.set()
        return result["value"]

    # ====================================================================
    #  批量爬取 Tab
    # ====================================================================

    def _build_batch_page(self):
        frame = ctk.CTkScrollableFrame(self.content_area, fg_color=Theme.BG_BODY)
        self.pages["batch"] = frame

        # 配置卡片
        card = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        card.pack(fill="x", pady=(0, 12))

        header = ctk.CTkLabel(card, text="🔧 爬取设置",
                               font=ctk.CTkFont(size=15, weight="bold"),
                               text_color=Theme.TEXT_PRIMARY, anchor="w")
        header.pack(fill="x", padx=20, pady=(16, 8))

        # 第一行：站点 + 列表类型
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(row1, text="站点:", font=ctk.CTkFont(size=13),
                      text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.site_var = ctk.StringVar(value=self.config.get("site", ""))
        site_values = [""] + list(MIRROR_SITES.values())
        site_combo = ctk.CTkOptionMenu(row1, variable=self.site_var, values=site_values,
                                         width=160, height=32, font=ctk.CTkFont(size=13),
                                         fg_color=Theme.BG_INPUT, button_color=Theme.BG_INPUT,
                                         button_hover_color=Theme.BG_HOVER)
        site_combo.pack(side="left", padx=(8, 20))

        ctk.CTkLabel(row1, text="列表:", font=ctk.CTkFont(size=13),
                      text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.list_type_var = ctk.StringVar(value=self.config.get("list_type", "list"))
        type_combo = ctk.CTkOptionMenu(row1, variable=self.list_type_var,
                                        values=["视频", "周榜", "月榜", "5分钟+", "10分钟+"],
                                        width=110, height=32, font=ctk.CTkFont(size=13),
                                        fg_color=Theme.BG_INPUT, button_color=Theme.BG_INPUT)
        type_combo.pack(side="left", padx=(8, 0))

        # 第二行：页码 + 按钮
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(row2, text="页码:", font=ctk.CTkFont(size=13),
                      text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.page_start_var = ctk.StringVar(value=str(self.config.get("page_start", 1)))
        start_entry = ctk.CTkEntry(row2, textvariable=self.page_start_var, width=55, height=32,
                                    font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT)
        start_entry.pack(side="left", padx=(8, 4))

        ctk.CTkLabel(row2, text="~", font=ctk.CTkFont(size=14)).pack(side="left")
        self.page_end_var = ctk.StringVar(value=str(self.config.get("page_end", 3)))
        end_entry = ctk.CTkEntry(row2, textvariable=self.page_end_var, width=55, height=32,
                                  font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT)
        end_entry.pack(side="left", padx=(4, 16))

        ctk.CTkButton(row2, text="▶ 开始爬取", width=100, height=32,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._start_crawl).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row2, text="■ 停止", width=80, height=32,
                       fg_color=Theme.ERROR, hover_color="#dc2626",
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._stop_crawl).pack(side="left")

        # 双栏区域
        bottom = ctk.CTkFrame(frame, fg_color="transparent")
        bottom.pack(fill="both", expand=True, pady=(0, 0))

        # 左侧封面预览
        cover_card = ctk.CTkFrame(bottom, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        cover_card.pack(side="left", fill="y", padx=(0, 12))
        cover_card.configure(width=230)
        cover_card.pack_propagate(False)

        ctk.CTkLabel(cover_card, text="当前视频", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(pady=(14, 8), anchor="w", padx=16)
        self.cover_label = ctk.CTkLabel(cover_card, text="等待爬取...",
                                         font=ctk.CTkFont(size=12), text_color=Theme.TEXT_MUTED)
        self.cover_label.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.preview_title_label = ctk.CTkLabel(cover_card, text="", font=ctk.CTkFont(size=10),
                                                text_color=Theme.TEXT_SECONDARY, wraplength=200)
        self.preview_title_label.pack(fill="x", padx=16, pady=(0, 12))

        # 右侧进度区
        right_card = ctk.CTkFrame(bottom, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        right_card.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(right_card, text="下载进度", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(pady=(14, 8), anchor="w", padx=16)

        self.crawl_overall_label = ctk.CTkLabel(right_card, text="就绪",
                                                 font=ctk.CTkFont(size=12), anchor="w")
        self.crawl_overall_label.pack(fill="x", padx=16)

        self.crawl_progress = ctk.CTkProgressBar(right_card, mode="determinate", height=6)
        self.crawl_progress.set(0)
        self.crawl_progress.pack(fill="x", padx=16, pady=(6, 4))

        self.crawl_slice_label = ctk.CTkLabel(right_card, text="", font=ctk.CTkFont(size=11),
                                               text_color="#555", anchor="w")
        self.crawl_slice_label.pack(fill="x", padx=16)

        self.crawl_merge_label = ctk.CTkLabel(right_card, text="", font=ctk.CTkFont(size=11),
                                               text_color="#888", anchor="w")
        self.crawl_merge_label.pack(fill="x", padx=16)
        self.crawl_merge_progress = ctk.CTkProgressBar(right_card, mode="determinate", height=6)
        self.crawl_merge_progress.set(0)
        self.crawl_merge_progress.pack(fill="x", padx=16, pady=(4, 6))

        speed_row = ctk.CTkFrame(right_card, fg_color="transparent")
        speed_row.pack(fill="x", padx=16, pady=(0, 8))
        self.crawl_speed_label = ctk.CTkLabel(speed_row, text="", font=ctk.CTkFont(size=11),
                                               text_color=Theme.PRIMARY, anchor="w")
        self.crawl_speed_label.pack(side="left")
        self.crawl_traffic_label = ctk.CTkLabel(speed_row, text="", font=ctk.CTkFont(size=11),
                                                 text_color="#555", anchor="e")
        self.crawl_traffic_label.pack(side="right")

        # 日志区域
        log_btn_row = ctk.CTkFrame(right_card, fg_color="transparent")
        log_btn_row.pack(fill="x", padx=16, pady=(4, 0))
        self._crawl_log_visible = ctk.BooleanVar(value=False)
        self._crawl_log_toggle_btn = ctk.CTkButton(log_btn_row, text="📋 日志 ▸", width=80, height=28,
                                                    fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER,
                                                    font=ctk.CTkFont(size=11), command=self._toggle_crawl_log)
        self._crawl_log_toggle_btn.pack(side="left")
        ctk.CTkButton(log_btn_row, text="💾 导出", width=70, height=28,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER,
                       font=ctk.CTkFont(size=11),
                       command=lambda: self._export_tab_log("批量爬取")).pack(side="right")

        self._crawl_log_frame = ctk.CTkFrame(right_card, fg_color=Theme.BG_INPUT)
        self.crawl_status_text = ctk.CTkTextbox(self._crawl_log_frame, height=150,
                                                  font=ctk.CTkFont(size=11, family="Consolas"),
                                                  fg_color=Theme.BG_CARD, corner_radius=8)
        self.crawl_status_text.pack(fill="both", expand=True, padx=4, pady=4)

    # ====================================================================
    #  搜索 Tab
    # ====================================================================

    def _build_search_page(self):
        frame = ctk.CTkScrollableFrame(self.content_area, fg_color=Theme.BG_BODY)
        self.pages["search"] = frame

        card = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        card.pack(fill="x", pady=(0, 12))

        header = ctk.CTkLabel(card, text="🔍 搜索设置",
                               font=ctk.CTkFont(size=15, weight="bold"), text_color=Theme.TEXT_PRIMARY)
        header.pack(fill="x", padx=20, pady=(16, 8))

        # 第一行：站点 + 类型 + 关键词 + 统计
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(0, 8))

        left_part = ctk.CTkFrame(row1, fg_color="transparent")
        left_part.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(left_part, text="站点:", font=ctk.CTkFont(size=13),
                      text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.search_site_var = ctk.StringVar()
        site_combo = ctk.CTkOptionMenu(left_part, variable=self.search_site_var,
                                         values=[""] + list(MIRROR_SITES.values()),
                                         width=160, height=32, font=ctk.CTkFont(size=13),
                                         fg_color=Theme.BG_INPUT, button_color=Theme.BG_INPUT)
        site_combo.pack(side="left", padx=(8, 16))

        ctk.CTkLabel(left_part, text="类型:", font=ctk.CTkFont(size=13),
                      text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.search_type_var = ctk.StringVar(value="搜视频")
        stype_combo = ctk.CTkOptionMenu(left_part, variable=self.search_type_var,
                                          values=["搜视频", "搜作者"],
                                          width=90, height=32, font=ctk.CTkFont(size=13),
                                          fg_color=Theme.BG_INPUT, button_color=Theme.BG_INPUT,
                                          command=lambda _: self._toggle_search_mode())
        stype_combo.pack(side="left", padx=(8, 16))

        ctk.CTkLabel(left_part, text="关键词:", font=ctk.CTkFont(size=13),
                      text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.search_keyword_var = ctk.StringVar()
        kw_entry = ctk.CTkEntry(left_part, textvariable=self.search_keyword_var, width=180, height=32,
                                 font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT)
        kw_entry.pack(side="left", padx=(8, 0))
        kw_entry.bind("<Return>", lambda e: self._on_search_action())

        # 统计标签
        stats_part = ctk.CTkFrame(row1, fg_color="transparent")
        stats_part.pack(side="right", padx=(10, 0))
        self.search_stats_found_label = ctk.CTkLabel(stats_part, text="",
                                                     font=ctk.CTkFont(size=13, weight="bold"),
                                                     text_color=Theme.ERROR)
        self.search_stats_found_label.pack(side="left", padx=(0, 15))
        self.search_stats_done_label = ctk.CTkLabel(stats_part, text="",
                                                     font=ctk.CTkFont(size=13, weight="bold"),
                                                     text_color=Theme.ERROR)
        self.search_stats_done_label.pack(side="left")

        # 搜视频模式行
        self.search_video_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.search_video_frame.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(self.search_video_frame, text="排序:",
                      text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.search_sort_var = ctk.StringVar(value="最新")
        sort_combo = ctk.CTkOptionMenu(self.search_video_frame, variable=self.search_sort_var,
                                         values=["最新", "最热"], width=80, height=32,
                                         font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT,
                                         button_color=Theme.BG_INPUT)
        sort_combo.pack(side="left", padx=(8, 16))

        ctk.CTkLabel(self.search_video_frame, text="页码:", text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.search_page_start_var = ctk.StringVar(value="1")
        ctk.CTkEntry(self.search_video_frame, textvariable=self.search_page_start_var, width=50, height=32,
                      font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT).pack(side="left", padx=(8, 4))
        ctk.CTkLabel(self.search_video_frame, text="~").pack(side="left")
        self.search_page_end_var = ctk.StringVar(value="3")
        ctk.CTkEntry(self.search_video_frame, textvariable=self.search_page_end_var, width=50, height=32,
                      font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT).pack(side="left", padx=(4, 16))

        ctk.CTkButton(self.search_video_frame, text="▶ 搜索并下载", width=110, height=32,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._start_search).pack(side="left", padx=(0, 8))
        ctk.CTkButton(self.search_video_frame, text="■ 停止", width=70, height=32,
                       fg_color=Theme.ERROR, hover_color="#dc2626",
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._stop_crawl).pack(side="left")

        # 搜作者模式行（初始隐藏）
        self.search_author_frame = ctk.CTkFrame(card, fg_color="transparent")

        ctk.CTkButton(self.search_author_frame, text="🔍 搜索作者", width=100, height=30,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=12), corner_radius=Theme.BTN_RADIUS,
                       command=lambda: self._search_authors(append=False)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(self.search_author_frame, text="➕ 追加", width=65, height=30,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER,
                       font=ctk.CTkFont(size=12), corner_radius=Theme.BTN_RADIUS,
                       command=lambda: self._search_authors(append=True)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(self.search_author_frame, text="全选", width=50, height=30,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER,
                       font=ctk.CTkFont(size=12), corner_radius=Theme.BTN_RADIUS,
                       command=self._select_all_authors).pack(side="left", padx=(0, 6))
        ctk.CTkButton(self.search_author_frame, text="清空队列", width=75, height=30,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER,
                       font=ctk.CTkFont(size=12), corner_radius=Theme.BTN_RADIUS,
                       command=self._clear_author_queue).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(self.search_author_frame, text="页码:", text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.search_author_page_start_var = ctk.StringVar(value="1")
        ctk.CTkEntry(self.search_author_frame, textvariable=self.search_author_page_start_var,
                      width=45, height=30, font=ctk.CTkFont(size=12), fg_color=Theme.BG_INPUT).pack(side="left", padx=(6, 4))
        ctk.CTkLabel(self.search_author_frame, text="~").pack(side="left")
        self.search_author_page_end_var = ctk.StringVar(value="1")
        ctk.CTkEntry(self.search_author_frame, textvariable=self.search_author_page_end_var,
                      width=45, height=30, font=ctk.CTkFont(size=12), fg_color=Theme.BG_INPUT).pack(side="left", padx=(4, 12))
        ctk.CTkButton(self.search_author_frame, text="▶ 下载选中作者", width=115, height=30,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=12, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._start_author_crawl).pack(side="left", padx=(0, 6))
        ctk.CTkButton(self.search_author_frame, text="■ 停止", width=60, height=30,
                       fg_color=Theme.ERROR, hover_color="#dc2626",
                       font=ctk.CTkFont(size=12), corner_radius=Theme.BTN_RADIUS,
                       command=self._stop_crawl).pack(side="left")

        # 作者队列区域
        self.search_author_list_frame = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        self._author_queue_items = []
        self._author_selected = set()

        aq_inner = ctk.CTkFrame(self.search_author_list_frame, fg_color="transparent")
        aq_inner.pack(fill="x", padx=16, pady=(12, 8))

        aq_toolbar = ctk.CTkFrame(aq_inner, fg_color="transparent")
        aq_toolbar.pack(fill="x", pady=(0, 6))
        self._author_count_label = ctk.CTkLabel(aq_toolbar, text="队列: 0 人 | 0 个视频",
                                                   font=ctk.CTkFont(size=11), text_color=Theme.TEXT_SECONDARY)
        self._author_count_label.pack(side="left")

        # Tag容器（用CTkScrollableFrame）
        self._author_tag_scroll = ctk.CTkScrollableFrame(aq_inner, height=90, fg_color=Theme.BG_INPUT,
                                                          corner_radius=8)
        self._author_tag_scroll.pack(fill="both", expand=True)
        self._author_tag_frame = self._author_tag_scroll

        # 下方双栏
        bottom = ctk.CTkFrame(frame, fg_color="transparent")
        bottom.pack(fill="both", expand=True)

        # 封面
        scard = ctk.CTkFrame(bottom, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        scard.pack(side="left", fill="y", padx=(0, 12))
        scard.configure(width=230)
        scard.pack_propagate(False)
        ctk.CTkLabel(scard, text="当前视频", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(pady=(14, 8), anchor="w", padx=16)
        self.search_cover_label = ctk.CTkLabel(scard, text="等待搜索...",
                                                font=ctk.CTkFont(size=12), text_color=Theme.TEXT_MUTED)
        self.search_cover_label.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.search_preview_title_label = ctk.CTkLabel(scard, text="", font=ctk.CTkFont(size=10),
                                                         text_color=Theme.TEXT_SECONDARY, wraplength=200)
        self.search_preview_title_label.pack(fill="x", padx=16, pady=(0, 12))

        # 进度
        rcard = ctk.CTkFrame(bottom, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        rcard.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(rcard, text="下载进度", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(pady=(14, 8), anchor="w", padx=16)

        self.search_overall_label = ctk.CTkLabel(rcard, text="就绪", font=ctk.CTkFont(size=12))
        self.search_overall_label.pack(fill="x", padx=16)

        self.search_progress = ctk.CTkProgressBar(rcard, mode="determinate", height=6)
        self.search_progress.set(0)
        self.search_progress.pack(fill="x", padx=16, pady=(6, 4))

        self.search_slice_label = ctk.CTkLabel(rcard, text="", font=ctk.CTkFont(size=11), text_color="#555")
        self.search_slice_label.pack(fill="x", padx=16)

        self.search_merge_label = ctk.CTkLabel(rcard, text="", font=ctk.CTkFont(size=11), text_color="#888")
        self.search_merge_label.pack(fill="x", padx=16)
        self.search_merge_progress = ctk.CTkProgressBar(rcard, mode="determinate", height=6)
        self.search_merge_progress.set(0)
        self.search_merge_progress.pack(fill="x", padx=16, pady=(4, 6))

        spd_row = ctk.CTkFrame(rcard, fg_color="transparent")
        spd_row.pack(fill="x", padx=16, pady=(0, 8))
        self.search_speed_label = ctk.CTkLabel(spd_row, text="", font=ctk.CTkFont(size=11),
                                                text_color=Theme.PRIMARY, anchor="w")
        self.search_speed_label.pack(side="left")
        self.search_traffic_label = ctk.CTkLabel(spd_row, text="", font=ctk.CTkFont(size=11), text_color="#555")
        self.search_traffic_label.pack(side="right")

        # 搜索日志
        slog_btn = ctk.CTkFrame(rcard, fg_color="transparent")
        slog_btn.pack(fill="x", padx=16, pady=(4, 0))
        self._search_log_visible = ctk.BooleanVar(value=False)
        ctk.CTkButton(slog_btn, text="📋 日志 ▸", width=80, height=28,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER, font=ctk.CTkFont(size=11),
                       command=self._toggle_search_log).pack(side="left")
        ctk.CTkButton(slog_btn, text="💾 导出", width=70, height=28,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER, font=ctk.CTkFont(size=11),
                       command=lambda: self._export_tab_log("搜索")).pack(side="right")
        self._search_log_frame = ctk.CTkFrame(rcard, fg_color=Theme.BG_INPUT)
        self.search_status_text = ctk.CTkTextbox(self._search_log_frame, height=150,
                                                  font=ctk.CTkFont(size=11, family="Consolas"),
                                                  fg_color=Theme.BG_CARD, corner_radius=8)
        self.search_status_text.pack(fill="both", expand=True, padx=4, pady=4)

    # ====================================================================
    #  单视频 Tab
    # ====================================================================

    def _build_single_page(self):
        frame = ctk.CTkScrollableFrame(self.content_area, fg_color=Theme.BG_BODY)
        self.pages["single"] = frame

        # 顶部控制
        top = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        top.pack(fill="x", pady=(0, 12))

        top_inner = ctk.CTkFrame(top, fg_color="transparent")
        top_inner.pack(fill="x", padx=16, pady=(14, 10))

        ctk.CTkLabel(top_inner, text="站点:", text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.single_site_var = ctk.StringVar()
        ctk.CTkOptionMenu(top_inner, variable=self.single_site_var,
                           values=[""] + list(MIRROR_SITES.values()), width=140, height=32,
                           font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT, button_color=Theme.BG_INPUT).pack(side="left", padx=(6, 12))

        ctk.CTkLabel(top_inner, text="类型:", text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.single_type_var = ctk.StringVar(value="视频")
        ctk.CTkOptionMenu(top_inner, variable=self.single_type_var,
                           values=list(LIST_TYPE_ALIASES.keys()), width=85, height=32,
                           font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT, button_color=Theme.BG_INPUT).pack(side="left", padx=(6, 12))

        # 翻页
        ctk.CTkButton(top_inner, text="◀", width=34, height=32,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER,
                       font=ctk.CTkFont(size=14), command=self._single_prev_page).pack(side="left", padx=(4, 2))
        ctk.CTkLabel(top_inner, text=" 第 ", text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.single_page_var = ctk.StringVar(value="1")
        pg_entry = ctk.CTkEntry(top_inner, textvariable=self.single_page_var, width=46, height=32,
                                 font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT)
        pg_entry.pack(side="left", padx=(2, 2))
        pg_entry.bind("<Return>", lambda e: self._load_single_page())
        ctk.CTkLabel(top_inner, text=" 页 ", text_color=Theme.TEXT_SECONDARY).pack(side="left")
        ctk.CTkButton(top_inner, text="▶", width=34, height=32,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER,
                       font=ctk.CTkFont(size=14), command=self._single_next_page).pack(side="left", padx=(2, 8))

        ctk.CTkButton(top_inner, text="📋 加载", width=65, height=32,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._load_single_page).pack(side="left")

        # 操作栏
        action = ctk.CTkFrame(frame, fg_color="transparent")
        action.pack(fill="x", pady=(0, 8))

        self.single_status_label = ctk.CTkLabel(action, text="点击「加载」获取视频列表",
                                                  font=ctk.CTkFont(size=12), text_color=Theme.TEXT_SECONDARY)
        self.single_status_label.pack(side="left", padx=8)

        ctk.CTkButton(action, text="▶ 下载选中", width=95, height=32,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._start_single_batch).pack(side="right", padx=6)

        self.single_select_all_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(action, text="全选", variable=self.single_select_all_var,
                         font=ctk.CTkFont(size=13), command=self._single_toggle_all).pack(side="right", padx=6)

        # 进度卡片
        pcard = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        pcard.pack(fill="x", pady=(0, 8))

        pc_header = ctk.CTkLabel(pcard, text="📊 下载进度", font=ctk.CTkFont(size=13, weight="bold"),
                                   text_color=Theme.TEXT_PRIMARY)
        pc_header.pack(anchor="w", padx=16, pady=(12, 6))

        self.single_overall_label = ctk.CTkLabel(pcard, text="就绪", font=ctk.CTkFont(size=12))
        self.single_overall_label.pack(fill="x", padx=16)

        prog_r1 = ctk.CTkFrame(pcard, fg_color="transparent")
        prog_r1.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(prog_r1, text="切片:", width=38, text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.single_progress = ctk.CTkProgressBar(prog_r1, mode="determinate", height=6)
        self.single_progress.set(0)
        self.single_progress.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.single_slice_label = ctk.CTkLabel(prog_r1, text="", font=ctk.CTkFont(size=11), text_color="#555", width=100)
        self.single_slice_label.pack(side="left")

        merge_r = ctk.CTkFrame(pcard, fg_color="transparent")
        merge_r.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(merge_r, text="合并:", width=38, text_color=Theme.TEXT_SECONDARY).pack(side="left")
        self.single_merge_progress = ctk.CTkProgressBar(merge_r, mode="determinate", height=6)
        self.single_merge_progress.set(0)
        self.single_merge_progress.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.single_merge_label = ctk.CTkLabel(merge_r, text="", font=ctk.CTkFont(size=11), text_color="#888", width=100)
        self.single_merge_label.pack(side="left")

        spd_r = ctk.CTkFrame(pcard, fg_color="transparent")
        spd_r.pack(fill="x", padx=16, pady=(4, 8))
        self.single_speed_label = ctk.CTkLabel(spd_r, text="", font=ctk.CTkFont(size=11), text_color=Theme.PRIMARY)
        self.single_speed_label.pack(side="left")
        self.single_traffic_label = ctk.CTkLabel(spd_r, text="", font=ctk.CTkFont(size=11), text_color="#555")
        self.single_traffic_label.pack(side="right")

        # 日志
        sl_btn = ctk.CTkFrame(pcard, fg_color="transparent")
        sl_btn.pack(fill="x", padx=16, pady=(4, 8))
        self._single_log_visible = ctk.BooleanVar(value=False)
        ctk.CTkButton(sl_btn, text="📋 日志 ▸", width=80, height=28,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER, font=ctk.CTkFont(size=11),
                       command=self._toggle_single_log).pack(side="left")
        ctk.CTkButton(sl_btn, text="💾 导出", width=70, height=28,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER, font=ctk.CTkFont(size=11),
                       command=lambda: self._export_tab_log("单视频")).pack(side="right")
        self._single_log_frame = ctk.CTkFrame(pcard, fg_color=Theme.BG_INPUT)
        self.single_log_text = ctk.CTkTextbox(self._single_log_frame, height=100,
                                                font=ctk.CTkFont(size=11, family="Consolas"),
                                                fg_color=Theme.BG_CARD, corner_radius=8)
        self.single_log_text.pack(fill="x", padx=4, pady=4)

        # 手动URL输入
        mcard = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        mcard.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(mcard, text="🔗 手动输入 URL（可选）", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(12, 6))
        mrow = ctk.CTkFrame(mcard, fg_color="transparent")
        mrow.pack(fill="x", padx=16, pady=(0, 12))
        self.url_var = ctk.StringVar()
        ctk.CTkEntry(mrow, textvariable=self.url_var, height=32,
                      font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.title_var = ctk.StringVar()
        ctk.CTkEntry(mrow, textvariable=self.title_var, width=200, height=32,
                      font=ctk.CTkFont(size=13), fg_color=Theme.BG_INPUT).pack(side="left", padx=(0, 8))
        ctk.CTkButton(mrow, text="⬇ 下载", width=60, height=32,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._start_single_manual).pack(side="left")

    # ====================================================================
    #  设置 Tab
    # ====================================================================

    def _build_settings_page(self):
        frame = ctk.CTkScrollableFrame(self.content_area, fg_color=Theme.BG_BODY)
        self.pages["settings"] = frame

        # 标题
        ctk.CTkLabel(frame, text="⚙️ 应用设置", font=ctk.CTkFont(size=20, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(pady=(8, 16))

        # 保存目录
        dcard = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        dcard.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(dcard, text="📁 保存目录", font=ctk.CTkFont(size=14, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))
        self.save_dir_var = ctk.StringVar(value=self.config["output_dir"])
        ctk.CTkEntry(dcard, textvariable=self.save_dir_var, height=34, font=ctk.CTkFont(size=13),
                      fg_color=Theme.BG_INPUT).pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkButton(dcard, text="📂 选择目录...", width=120, height=32,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER, font=ctk.CTkFont(size=12),
                       command=self._browse_dir).pack(anchor="w", padx=16, pady=(0, 14))

        # 下载设置
        dlcard = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        dlcard.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(dlcard, text="⬇️ 下载选项", font=ctk.CTkFont(size=14, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))

        self.title_with_author_var = ctk.BooleanVar(value=self.config.get("title_with_author", True))
        ctk.CTkCheckBox(dlcard, text="标题包含上传者（标题 - 作者名）", variable=self.title_with_author_var,
                         font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(0, 6))

        self.sort_by_upload_date_var = ctk.BooleanVar(value=self.config.get("sort_by_upload_date", True))
        ctk.CTkCheckBox(dlcard, text="按视频上传日期分类（关闭则全部存到下载当天）", variable=self.sort_by_upload_date_var,
                         font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(0, 14))

        # 代理设置
        pcard = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        pcard.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(pcard, text="🌐 SOCKS5 代理（可选）", font=ctk.CTkFont(size=14, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))

        self.proxy_enabled_var = ctk.BooleanVar(value=self.config.get("proxy_enabled", False))
        ctk.CTkCheckBox(pcard, text="启用代理", variable=self.proxy_enabled_var,
                         font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(0, 8))

        pr1 = ctk.CTkFrame(pcard, fg_color="transparent")
        pr1.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(pr1, text="主机:", width=35, text_color=Theme.TEXT_SECONDARY, font=ctk.CTkFont(size=12)).pack(side="left")
        self.proxy_host_var = ctk.StringVar(value=self.config["proxy_host"])
        ctk.CTkEntry(pr1, textvariable=self.proxy_host_var, height=32, font=ctk.CTkFont(size=13),
                      fg_color=Theme.BG_INPUT).pack(side="left", fill="x", expand=True, padx=(6, 10))
        ctk.CTkLabel(pr1, text="端口:", text_color=Theme.TEXT_SECONDARY, font=ctk.CTkFont(size=12)).pack(side="left")
        self.proxy_port_var = ctk.StringVar(value=self.config["proxy_port"])
        ctk.CTkEntry(pr1, textvariable=self.proxy_port_var, width=68, height=32, font=ctk.CTkFont(size=13),
                      fg_color=Theme.BG_INPUT).pack(side="left", padx=(6, 0))

        pr2 = ctk.CTkFrame(pcard, fg_color="transparent")
        pr2.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(pr2, text="账号:", width=35, text_color=Theme.TEXT_SECONDARY, font=ctk.CTkFont(size=12)).pack(side="left")
        self.proxy_user_var = ctk.StringVar(value=self.config["proxy_user"])
        ctk.CTkEntry(pr2, textvariable=self.proxy_user_var, height=32, font=ctk.CTkFont(size=13),
                      fg_color=Theme.BG_INPUT).pack(side="left", fill="x", expand=True, padx=(6, 10))
        ctk.CTkLabel(pr2, text="密码:", text_color=Theme.TEXT_SECONDARY, font=ctk.CTkFont(size=12)).pack(side="left")
        self.proxy_pass_var = ctk.StringVar(value=self.config["proxy_pass"])
        ctk.CTkEntry(pr2, textvariable=self.proxy_pass_var, width=90, height=32, font=ctk.CTkFont(size=13),
                      fg_color=Theme.BG_INPUT, show="*").pack(side="left", padx=(6, 0))

        btn_row = ctk.CTkFrame(pcard, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 14))
        ctk.CTkButton(btn_row, text="🔌 测试代理连接", width=130, height=32,
                       fg_color=Theme.INFO, hover_color="#2563eb", font=ctk.CTkFont(size=12, weight="bold"),
                       corner_radius=Theme.BTN_RADIUS, command=self._test_proxy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="💾 保存设置", width=100, height=32,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=12, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._save_settings).pack(side="left")
        ctk.CTkButton(btn_row, text="🔧 检查环境", width=100, height=32,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER, font=ctk.CTkFont(size=12),
                       corner_radius=Theme.BTN_RADIUS, command=self._manual_env_check).pack(side="left", padx=(8, 0))

    # ====================================================================
    #  运行日志 Tab
    # ====================================================================

    def _build_logs_page(self):
        frame = ctk.CTkFrame(self.content_area, fg_color=Theme.BG_BODY)
        self.pages["logs"] = frame

        ctk.CTkLabel(frame, text="📋 程序运行日志", font=ctk.CTkFont(size=18, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 8), anchor="w", padx=20)
        ctk.CTkLabel(frame, text="程序级日志，关闭后自动清空", font=ctk.CTkFont(size=11),
                      text_color=Theme.TEXT_MUTED).pack(pady=(0, 12), anchor="w", padx=20)

        self.log_text = ctk.CTkTextbox(frame, height=400, font=ctk.CTkFont(size=12, family="Consolas"),
                                         fg_color=Theme.BG_CARD, corner_radius=12)
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(btn_row, text="🗑️ 清空日志", width=100, height=32,
                       fg_color=Theme.ERROR, hover_color="#dc2626", font=ctk.CTkFont(size=12),
                       corner_radius=Theme.BTN_RADIUS, command=self._clear_log).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="📤 导出日志...", width=110, height=32,
                       fg_color=Theme.BG_INPUT, hover_color=Theme.BG_HOVER, font=ctk.CTkFont(size=12),
                       corner_radius=Theme.BTN_RADIUS, command=self._export_log).pack(side="left")

        # 重定向 Python logging
        class _LogHandler(logging.Handler):
            def __init__(self, tw): super().__init__(); self.tw = tw
            def emit(self, record):
                msg = self.format(record)
                try:
                    self.tw.after(0, lambda m=msg, t=self.tw: (t.insert("end", m+"\n"), t.see("end")))
                except Exception: pass

        self._log_handler = _LogHandler(self.log_text)
        self._log_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(self._log_handler)

    # ====================================================================
    #  环境检测 Tab
    # ====================================================================

    def _build_envcheck_page(self):
        frame = ctk.CTkScrollableFrame(self.content_area, fg_color=Theme.BG_BODY)
        self.pages["envcheck"] = frame

        ctk.CTkLabel(frame, text="✅ 运行环境检查", font=ctk.CTkFont(size=18, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(pady=(16, 12))

        ecard = ctk.CTkFrame(frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CARD_RADIUS)
        ecard.pack(fill="both", expand=True, padx=0, pady=(0, 12))

        ctk.CTkLabel(ecard, text="检查结果", font=ctk.CTkFont(size=14, weight="bold"),
                      text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))

        self.env_textbox = ctk.CTkTextbox(ecard, height=300, font=ctk.CTkFont(size=12, family="Consolas"),
                                            fg_color=Theme.BG_INPUT, corner_radius=10)
        self.env_textbox.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 16))
        ctk.CTkButton(btn_row, text="🔄 重新检查", width=110, height=34,
                       fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._manual_env_check).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="🐍 安装依赖", width=110, height=34,
                       fg_color=Theme.WARNING, hover_color="#d97706",
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._install_deps).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="⬇ 下载 ffmpeg", width=120, height=34,
                       fg_color=Theme.INFO, hover_color="#2563eb",
                       font=ctk.CTkFont(size=13, weight="bold"), corner_radius=Theme.BTN_RADIUS,
                       command=self._download_ffmpeg).pack(side="left")

    # ================================================================
    #  业务逻辑：与原版 app.py 完全一致的回调实现
    # ================================================================

    def _toggle_crawl_log(self):
        self._crawl_log_visible.set(not self._crawl_log_visible.get())
        if self._crawl_log_visible.get():
            self._crawl_log_frame.pack(fill="both", expand=True, pady=(8, 0))
            self._crawl_log_toggle_btn.configure(text="📋 日志 ▾")
        else:
            self._crawl_log_frame.pack_forget()
            self._crawl_log_toggle_btn.configure(text="📋 日志 ▸")

    def _toggle_search_log(self):
        self._search_log_visible.set(not self._search_log_visible.get())
        if self._search_log_visible.get():
            self._search_log_frame.pack(fill="both", expand=True, pady=(8, 0))
        else:
            self._search_log_frame.pack_forget()

    def _toggle_single_log(self):
        self._single_log_visible.set(not self._single_log_visible.get())
        if self._single_log_visible.get():
            self._single_log_frame.pack(fill="x", pady=(8, 0))
        else:
            self._single_log_frame.pack_forget()

    def _toggle_search_mode(self):
        is_author = self.search_type_var.get() == "搜作者"
        if is_author:
            self.search_video_frame.pack_forget()
            self.search_author_frame.pack(fill="x", pady=(0, 8))
            self.search_author_list_frame.pack(fill="x", pady=(0, 8))
        else:
            self.search_author_frame.pack_forget()
            self.search_author_list_frame.pack_forget()
            self.search_video_frame.pack(fill="x", pady=(0, 8))

    def _on_search_action(self):
        if self.search_type_var.get() == "搜作者":
            self._search_authors()
        else:
            self._start_search()

    # ---- 封面预览 ----

    def _update_cover_preview(self, info: dict):
        cover_url = info.get("cover", "")
        title = info.get("title", "")
        try:
            self.after(0, lambda: self.preview_title_label.configure(text=title))
        except Exception:
            pass
        if not cover_url:
            return
        img_data = download_image(cover_url)
        if not img_data:
            return
        def show_image():
            try:
                if self._has_pil:
                    from PIL import Image, ImageTk
                    img = Image.open(io.BytesIO(img_data))
                    img.thumbnail((200, 130), Image.LANCZOS)
                    self._cover_photo = ImageTk.PhotoImage(img)
                    self.cover_label.configure(image=self._cover_photo, text="")
                else:
                    import tkinter as tk
                    self._cover_photo = tk.PhotoImage(data=img_data)
                    self.cover_label.configure(image=self._cover_photo, text="")
            except Exception:
                self.cover_label.configure(text="封面加载失败\n(需要 Pillow)")
        try:
            self.after(0, show_image)
        except Exception:
            pass

    def _update_search_cover_preview(self, info: dict):
        cover_url = info.get("cover", "")
        title = info.get("title", "")
        try:
            self.after(0, lambda: self.search_preview_title_label.configure(text=title))
        except Exception:
            pass
        if not cover_url:
            return
        img_data = download_image(cover_url)
        if not img_data:
            return
        def show_image():
            try:
                if self._has_pil:
                    from PIL import Image, ImageTk
                    img = Image.open(io.BytesIO(img_data))
                    img.thumbnail((200, 130), Image.LANCZOS)
                    self._search_cover_photo = ImageTk.PhotoImage(img)
                    self.search_cover_label.configure(image=self._search_cover_photo, text="")
                else:
                    import tkinter as tk
                    self._search_cover_photo = tk.PhotoImage(data=img_data)
                    self.search_cover_label.configure(image=self._search_cover_photo, text="")
            except Exception:
                self.search_cover_label.configure(text="封面加载失败")
        try:
            self.after(0, show_image)
        except Exception:
            pass

    # ---- 批量爬取 ----

    def _start_crawl(self):
        if self.crawl_thread and self.crawl_thread.is_alive():
            self._show_warning("正在运行中，请先停止")
            return
        self._crawl_stopping = False
        if not self.site_var.get().strip():
            self._show_warning("请先选择站点")
            return
        if not self._crawl_log_visible.get():
            self._toggle_crawl_log()

        def on_progress(current, total):
            pct = f"{current}/{total}" if total > 0 else "?"
            self._update_progress(self.crawl_progress, current, total,
                                   self.crawl_slice_label, f"切片: {pct}")
            if current <= 1:
                self.after(0, lambda: self.crawl_merge_progress.configure(value=0))
                self.after(0, lambda: self.crawl_merge_label.configure(text="切片下载中..."))
                self.after(0, lambda: self.crawl_speed_label.configure(text="速度: --"))
                self.after(0, lambda: self.crawl_traffic_label.configure(text="流量: 0 B"))

        def on_speed(gspeed, tbytes):
            self.after(0, lambda s=gspeed, t=tbytes: [
                self.crawl_speed_label.configure(text=f"速度: {self._format_speed(s)}"),
                self.crawl_traffic_label.configure(text=f"流量: {self._format_bytes(t)}"),
            ])

        self.crawler = CrawlerCore(self.config, log_callback=lambda m, l="info": self._log_to_ui(self.crawl_status_text, m, l),
                                    progress_callback=on_progress, info_callback=self._update_cover_preview,
                                    base_url=self.site_var.get(),
                                    merge_progress_callback=lambda p, s: self.after(0, lambda: [
                                        self.crawl_merge_progress.configure(value=p),
                                        self.crawl_merge_label.configure(text=f"合并 MP4: {p}%{f'，速度: {s}' if s else ''}")
                                    ]),
                                    speed_callback=on_speed)

        def run():
            try:
                self.after(0, lambda: self.crawl_overall_label.configure(text="正在爬取..."))
                result = self.crawler.crawl_batch(
                    page_start=int(self.page_start_var.get()),
                    page_end=int(self.page_end_var.get()),
                    list_type=self.list_type_var.get())
                success = result.get("success", 0); skipped = result.get("skipped", 0)
                self.after(0, lambda: self.crawl_overall_label.configure(
                    text=f"完成 — 新下载: {success}，跳过: {skipped}"))
                self._status_to_ui(self.crawl_status_text,
                    f"── 批量爬取完成（新下载: {success}，跳过: {skipped}） ──")
            except Exception as e:
                self._status_to_ui(self.crawl_status_text, f"错误: {e}")
                logger.exception("批量爬取失败")

        self.crawl_thread = threading.Thread(target=run, daemon=True)
        self.crawl_thread.start()

    def _stop_crawl(self):
        if self.crawler:
            try: self.crawler.flush_history()
            except Exception: pass
            self.crawler.stop()
            self._crawl_stopping = True
            self.crawl_thread = None
            self._status_to_ui(getattr(self, 'crawl_status_text', None), "── 已停止 ──")
            self._status_to_ui(getattr(self, 'search_status_text', None), "── 已停止 ──")
            self._status_to_ui(getattr(self, 'single_log_text', None), "── 已停止 ──")
            try:
                for lbl in ['crawl_overall_label', 'single_overall_label', 'search_overall_label']:
                    if hasattr(self, lbl):
                        self.after(0, lambda l=getattr(self, lbl): l.configure(text="已停止"))
            except Exception: pass

    # ---- 搜索 ----

    def _start_search(self):
        if self.crawl_thread and self.crawl_thread.is_alive():
            self._show_warning("正在运行中，请先停止"); return
        self._crawl_stopping = False
        if not self.search_site_var.get().strip():
            self._show_warning("请先选择站点"); return
        keyword = self.search_keyword_var.get().strip()
        if not keyword:
            self._show_warning("请输入搜索关键词"); return
        if not self._search_log_visible.get(): self._toggle_search_log()

        sort_map = {"最新": "new", "最热": "hot"}
        sort = sort_map.get(self.search_sort_var.get(), "new")

        def on_prog(c, t):
            pct = f"{c}/{t}" if t > 0 else "?"
            self._update_progress(self.search_progress, c, t, self.search_slice_label, f"切片: {pct}")
            if c <= 1:
                for w in [lambda: self.search_merge_progress.configure(value=0),
                           lambda: self.search_merge_label.configure(text="切片下载中..."),
                           lambda: self.search_speed_label.configure(text="速度: --"),
                           lambda: self.search_traffic_label.configure(text="流量: 0 B")]:
                    self.after(0, w)

        def on_spd(g, t):
            self.after(0, lambda s=g, tt=t: [
                self.search_speed_label.configure(text=f"速度: {self._format_speed(s)}"),
                self.search_traffic_label.configure(text=f"流量: {self._format_bytes(tt)}"),
            ])

        self.crawler = CrawlerCore(self.config,
            log_callback=lambda m, l="info": self._log_to_ui(self.search_status_text, m, l),
            progress_callback=on_prog, info_callback=self._update_search_cover_preview,
            base_url=self.search_site_var.get(),
            merge_progress_callback=lambda p, s: self.after(0, lambda: [
                self.search_merge_progress.configure(value=p),
                self.search_merge_label.configure(text=f"合并 MP4: {p}%{f'，速度: {s}' if s else ''}")
            ]), speed_callback=on_spd)

        def on_ss(stats):
            self.after(0, lambda s=stats: [
                self.search_overall_label.configure(
                    text=f"总计 {s['total']} 个视频（已下载 {s['downloaded']}/待下载 {s['pending']}/{s['total']})"),
                self.search_stats_found_label.configure(text=f"已搜索{s['total']}个视频"),
            ])
        self.crawler.search_stats_callback = on_ss

        def on_sp(done, tp, total):
            self.after(0, lambda d=done, t=total: [
                self.search_overall_label.configure(text=f"已处理 {d}/{t} 个视频"),
                self.search_stats_done_label.configure(text=f"已下载{d}个视频"),
            ])
        self.crawler.search_progress_callback = on_sp

        self.after(0, lambda: [
            self.search_stats_found_label.configure(text=""),
            self.search_stats_done_label.configure(text="已下载0个视频"),
        ])

        def run():
            try:
                self.after(0, lambda: self.search_overall_label.configure(text="正在预扫描搜索结果..."))
                self.after(0, lambda: [
                    self.search_stats_found_label.configure(text=""),
                    self.search_stats_done_label.configure(text="已下载0个视频"),
                    self.search_merge_progress.configure(value=0),
                    self.search_merge_label.configure(text=""),
                ])
                result = self.crawler.crawl_search(keyword=keyword,
                    page_start=int(self.search_page_start_var.get()),
                    page_end=int(self.search_page_end_var.get()), sort=sort)
                success = result.get("success", 0); skipped = result.get("skipped", 0)
                self.after(0, lambda: self.search_overall_label.configure(
                    text=f"完成 — 新下载: {success}，跳过: {skipped}（总计 {success+skipped}）"))
                self._status_to_ui(self.search_status_text,
                    f"── 搜索下载完成（新下载: {success}，跳过: {skipped}） ──")
            except Exception as e:
                self._status_to_ui(self.search_status_text, f"错误: {e}")
                logger.exception("搜索下载失败")

        self.crawl_thread = threading.Thread(target=run, daemon=True)
        self.crawl_thread.start()

    # ---- 搜索作者 ----

    def _search_authors(self, append=False):
        raw = self.search_keyword_var.get().strip()
        if not raw:
            self._show_warning("请输入搜索关键词"); return
        if not self.search_site_var.get().strip():
            self._show_warning("请先选择站点"); return

        import re
        keywords = [k.strip() for k in re.split(r'[,，\n\s]+', raw) if k.strip()]

        if not append:
            for widget in self._author_tag_frame.winfo_children():
                widget.destroy()
            self._author_queue_items.clear(); self._author_selected.clear()

        mt = "追加搜索" if append else "搜索"
        self.search_overall_label.configure(text=f"正在{mt} {len(keywords)} 个关键词...")

        def run():
            try:
                crawler = CrawlerCore(self.config, base_url=self.search_site_var.get())
                all_new = []
                existing_params = {a["param"] for a in self._author_queue_items}
                for kw in keywords:
                    if append:
                        self.after(0, lambda k=kw: self.search_overall_label.configure(text=f"追加搜索中... 关键词: {k}"))
                    found = crawler.search_authors(kw)
                    for a in found:
                        if a.get("param", "") not in existing_params:
                            all_new.append(a); existing_params.add(a.get("param", ""))

                authors = all_new
                if authors:
                    self.after(0, lambda: self.search_overall_label.configure(text=f"找到 {len(authors)} 个新作者，正在获取页数..."))
                    for author in authors:
                        try:
                            author["page_count"] = crawler.get_author_page_count(author["url"])
                        except Exception: author["page_count"] = 1
            except Exception as e:
                self.after(0, lambda: self.search_overall_label.configure(text=f"搜索失败: {e}")); return

            def show_results():
                if not authors:
                    self.search_overall_label.configure(text=f"{mt}: 未找到新作者"); return
                max_pages = max(a.get("page_count", 1) for a in authors)
                old_end = int(self.search_author_page_end_var.get())
                self.search_author_page_start_var.set("1")
                self.search_author_page_end_var.set(str(max(old_end, max_pages)))
                for author in authors:
                    self._author_queue_items.append(author)
                    self._author_selected.add(author.get("param", ""))
                    self._add_author_tag(author)
                self._update_queue_stats()
                total = len(self._author_queue_items)
                mt2 = "追加了" if append else "搜索到"
                self.search_overall_label.configure(text=f"作者队列: 共 {total} 人（本次{mt2} {len(authors)} 人）")

            self.after(0, show_results)
        threading.Thread(target=run, daemon=True).start()

    def _select_all_authors(self):
        self._author_selected.update(item["param"] for item in self._author_queue_items)
        self._refresh_author_tags()

    def _deselect_all_authors(self):
        self._author_selected.clear()
        self._refresh_author_tags()

    def _clear_author_queue(self):
        if not self._author_queue_items: return
        count = len(self._author_queue_items)
        for widget in self._author_tag_frame.winfo_children():
            widget.destroy()
        self._author_queue_items.clear(); self._author_selected.clear()
        self._update_queue_stats()

    def _add_author_tag(self, author):
        name = author.get("name", "未知")
        count = author.get("count", 0)
        pages = author.get("page_count", "?")
        param = author.get("param", name)

        chip = ctk.CTkFrame(self._author_tag_frame, fg_color=Theme.BG_INPUT, corner_radius=8, height=56)
        chip.pack(side="left", padx=3, pady=2)
        chip.pack_propagate(False)

        is_sel = param in self._author_selected
        bg = Theme.PRIMARY if is_sel else Theme.BG_INPUT
        txt_col = "white" if is_sel else Theme.TEXT_PRIMARY

        info = ctk.CTkLabel(chip, text=f"{name}\n{count}v·{pages}p",
                             font=ctk.CTkFont(size=10), text_color=txt_col,
                             justify="center", fg_color="transparent")
        info.pack(expand=True, fill="both", padx=8, pady=4)

        def toggle(e=None, p=param, ch=chip, lb=info):
            if p in self._author_selected: self._author_selected.discard(p); nb=Theme.BG_INPUT; nc=Theme.TEXT_PRIMARY
            else: self._author_selected.add(p); nb=Theme.PRIMARY; nc="white"
            ch.configure(fg_color=nb); lb.configure(text_color=nc)

        chip.bind("<Button-1>", toggle); info.bind("<Button-1>", toggle)

        del_btn = ctk.CTkLabel(chip, text="✕", font=ctk.CTkFont(size=10), text_color=Theme.TEXT_MUTED,
                                 width=16, fg_color="transparent")
        del_btn.place(relx=0.96, rely=0.04)
        def rm(p=param):
            for i, item in enumerate(self._author_queue_items):
                if item["param"] == p:
                    self._author_queue_items.pop(i)
                    self._author_selected.discard(p)
                    chip.destroy(); break
            self._update_queue_stats()
        del_btn.bind("<Button-1>", lambda e, fn=rm: fn())

    def _refresh_author_tags(self):
        for child in self._author_tag_frame.winfo_children():
            idx = list(self._author_tag_frame.winfo_children()).index(child)
            if idx >= len(self._author_queue_items): continue
            param = self._author_queue_items[idx]["param"]
            is_sel = param in self._author_selected
            bg = Theme.PRIMARY if is_sel else Theme.BG_INPUT
            tc = "white" if is_sel else Theme.TEXT_PRIMARY
            child.configure(fg_color=bg)
            for sub in child.winfo_children():
                if isinstance(sub, ctk.CTkLabel) and "✕" not in sub.cget("text"):
                    sub.configure(text_color=tc)

    def _update_queue_stats(self):
        total = len(self._author_queue_items)
        videos = sum(a.get("count", 0) for a in self._author_queue_items)
        sel = len(self._author_selected & {a["param"] for a in self._author_queue_items})
        self._author_count_label.configure(text=f"队列: {total} 人 | {videos} 个视频 | 已选 {sel}")
        self.search_stats_found_label.configure(text=f"队列共{videos}个视频")

    def _start_author_crawl(self):
        if self.crawl_thread and self.crawl_thread.is_alive():
            self._show_warning("正在运行中，请先停止"); return
        self._crawl_stopping = False
        if self.crawler:
            try: self.crawler.stop()
            except: pass
            self.crawler = None
        if not self.search_site_var.get().strip():
            self._show_warning("请先选择站点"); return
        selected = [a for a in self._author_queue_items if a.get("param") in self._author_selected]
        if not selected:
            self._show_warning("请勾选至少一个作者"); return
        names = ", ".join(a["name"] for a in selected)
        self._log_to_ui(self.search_status_text, f"准备爬取作者: {names}")
        if not self._search_log_visible.get(): self._toggle_search_log()

        def on_prog(c, t):
            pct = f"{c}/{t}" if t > 0 else "?"
            self._update_progress(self.search_progress, c, t, self.search_slice_label, f"切片: {pct}")
            if c <= 1:
                self.after(0, lambda: self.search_merge_progress.configure(value=0))
                self.after(0, lambda: self.search_merge_label.configure(text="切片下载中..."))
                self.after(0, lambda: self.search_speed_label.configure(text="速度: --"))
                self.after(0, lambda: self.search_traffic_label.configure(text="流量: 0 B"))

        def on_mp(p, s):
            self.after(0, lambda: [self.search_merge_progress.configure(value=p),
                                      self.search_merge_label.configure(text=f"合并 MP4: {p}%{f'，速度: {s}' if s else ''}")])

        def on_sp(g, t):
            self.after(0, lambda s=g, tt=t: [
                self.search_speed_label.configure(text=f"速度: {self._format_speed(s)}"),
                self.search_traffic_label.configure(text=f"流量: {self._format_bytes(tt)}"),
            ])

        self.crawler = CrawlerCore(self.config, log_callback=lambda m,l="info": self._log_to_ui(self.search_status_text,m,l),
                                    progress_callback=on_prog, info_callback=self._update_search_cover_preview,
                                    confirm_callback=self._confirm_dialog, base_url=self.search_site_var.get(),
                                    merge_progress_callback=on_mp, speed_callback=on_sp)

        def on_op(d):
            self.after(0, lambda dd=d: self.search_stats_done_label.configure(text=f"已下载{dd}个视频"))
        self.crawler.overall_progress_callback = on_op

        def on_ap(c, t):
            aname = selected[c-1].get("name","?") if c <= len(selected) else "?"
            self.after(0, lambda cn=c, tn=t, n=aname: self.search_overall_label.configure(text=f"📂 作者 {cn}/{tn}: {n}"))
        self.crawler.author_progress_callback = on_ap

        def run():
            try:
                ta = len(selected)
                self.after(0, lambda: self.search_overall_label.configure(text=f"准备下载 {ta} 个作者的视频..."))
                self.after(0, lambda: self.search_merge_progress.configure(value=0))
                result = self.crawler.crawl_authors(selected,
                    page_start=int(self.search_author_page_start_var.get()),
                    page_end=int(self.search_author_page_end_var.get()))
                success = result.get("success",0); skipped = result.get("skipped",0)
                dt = success+skipped
                self.after(0, lambda: self.search_stats_done_label.configure(text=f"已下载{dt}个视频"))
                self.after(0, lambda: self.search_overall_label.configure(text=f"完成 — 新下载: {success}，跳过: {skipped}"))
                self._status_to_ui(self.search_status_text, f"── 作者下载完成（新下载: {success}，跳过: {skipped}） ──")
            except Exception as e:
                self._status_to_ui(self.search_status_text, f"错误: {e}")

        self.crawl_thread = threading.Thread(target=run, daemon=True)
        self.crawl_thread.start()

    # ---- 单视频 ----

    THUMB_W = 160; THUMB_H = 100

    def _load_single_page(self):
        if not self.single_site_var.get().strip():
            self._show_warning("请先选择站点"); return
        page = self.single_page_var.get(); site = self.single_site_var.get()
        type_name = self.single_type_var.get(); list_key = LIST_TYPE_ALIASES.get(type_name, type_name)
        url_pattern = LIST_TYPES.get(list_key, "list-{page}.htm")
        self.single_status_label.configure(text=f"正在加载第 {page} 页...")
        # 清空旧内容
        grid_container = self._find_grid_container()
        if grid_container:
            for w in grid_container.winfo_children(): w.destroy()
        self._single_videos = []; self._single_check_vars = []; self._single_thumb_refs = []

        def run():
            try:
                crawler = CrawlerCore(config={}, base_url=site)
                list_url = f"{site}/{url_pattern.format(page=page)}"
                videos = crawler._extract_video_urls(list_url)
            except Exception as e:
                self.after(0, lambda e=e: self.single_status_label.configure(text=f"加载失败: {e}")); return
            self.after(0, lambda v=videos: self._show_single_videos(v))
        threading.Thread(target=run, daemon=True).start()

    def _find_grid_container(self):
        """找到单视频Tab中的grid容器"""
        single_page = self.pages.get("single")
        if not single_page: return None
        for child in single_page.winfo_children():
            if hasattr(child, 'winfo_children') and any('grid' in str(type(c)).lower() for c in child.winfo_children()):
                for sub in child.winfo_children():
                    if isinstance(sub, ctk.CTkFrame) or isinstance(sub, ctk.CTkScrollableFrame):
                        return sub
        return None

    def _ensure_single_grid(self):
        """确保视频网格存在"""
        single_page = self.pages.get("single")
        if not single_page: return None
        # 查找已有的网格容器或创建新的
        for child in single_page.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child != single_page:
                for sub in child.winfo_children():
                    if isinstance(sub, ctk.CTkScrollableFrame):
                        return sub
        return None

    def _show_single_videos(self, videos):
        self._single_videos = videos
        if not videos:
            self.single_status_label.configure(text="当前页没有视频"); return

        downloaded = 0
        try:
            output_dir = Path(self.config.get("output_dir", APP_DIR / "downloads"))
            hist_path = output_dir / "download_history.json"
            history = {}
            if hist_path.exists(): history = json.loads(hist_path.read_text(encoding="utf-8"))
            archive_path = output_dir / "download_history_ids.json"
            archive_ids = set()
            if archive_path.exists(): archive_ids = set(json.loads(archive_path.read_text(encoding="utf-8")))
            for v in videos:
                vid = v.get("id")
                if vid and (vid in history or vid in archive_ids): downloaded += 1
        except Exception: pass

        total = len(videos)
        if downloaded > 0:
            self.single_status_label.configure(text=f"第 {self.single_page_var.get()} 页 — 共 {total} 个视频（已下载 {downloaded}/{total}）")
        else:
            self.single_status_label.configure(text=f"第 {self.single_page_var.get()} 页 — 共 {total} 个视频")

        # 在单视频页面创建网格
        single_frame = self.pages["single"]

        # 创建或找到网格容器
        grid_container = ctk.CTkScrollableFrame(single_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True, padx=0, pady=8)

        cols = 3; tw, th = self.THUMB_W, self.THUMB_H
        for idx, video in enumerate(videos):
            card = ctk.CTkFrame(grid_container, fg_color=Theme.BG_CARD, corner_radius=10)
            card.grid(row=idx//cols, column=idx%cols, padx=8, pady=8, sticky="nsew")

            var = ctk.BooleanVar(value=True)
            self._single_check_vars.append((var, video))
            cb = ctk.CTkCheckBox(card, text="", variable=var, width=18, checkbox_width=18, checkbox_height=18)
            cb.grid(row=0, column=0, sticky="ne", padx=4, pady=4)

            placeholder = ctk.CTkImage(light_image=self._create_placeholder(tw, th), size=(tw, th))
            self._single_thumb_refs.append(placeholder)
            cover_label = ctk.CTkLabel(card, text="加载中...", image=placeholder, compound="top",
                                         font=ctk.CTkFont(size=10), text_color=Theme.TEXT_MUTED)
            cover_label.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=(0, 4))

            ttl = video.get("title", "")[:45]
            title_label = ctk.CTkLabel(card, text=ttl, font=ctk.CTkFont(size=10),
                                         text_color=Theme.TEXT_PRIMARY, wraplength=170, anchor="w", justify="left")
            title_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 6))

            cover_url = video.get("cover", "")
            if cover_url:
                threading.Thread(target=self._load_single_cover, args=(cover_url, cover_label, tw, th), daemon=True).start()

            def toggle_ck(v=var): v.set(not v.get())
            cover_label.bind("<Button-1>", lambda e, v=var: toggle_ck(v))
            title_label.bind("<Button-1>", lambda e, v=var: toggle_ck(v))
            card.bind("<Button-1>", lambda e, v=var: toggle_ck(v))

        self.single_select_all_var.set(True)

    def _create_placeholder(self, w, h):
        """创建占位图"""
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (w, h), "#e0e0e0")
            return ctk.CTkImage(img, size=(w, h))
        except Exception:
            return None

    def _load_single_cover(self, url, label, tw=160, th=100):
        try:
            import urllib.request
            from io import BytesIO
            req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = BytesIO(resp.read())
            from PIL import Image
            img = Image.open(data); img = img.resize((tw, th), Image.LANCZOS)
            photo = ctk.CTkImage(img, size=(tw, th))
            self._single_thumb_refs.append(photo)
            self.after(0, lambda l=label, p=photo: l.configure(image=p, text=""))
        except Exception:
            self.after(0, lambda l=label: l.configure(text="封面加载失败"))

    def _single_toggle_all(self):
        sel = self.single_select_all_var.get()
        for var, _ in self._single_check_vars: var.set(sel)

    def _single_prev_page(self):
        p = int(self.single_page_var.get()) or 1
        if p > 1: self.single_page_var.set(str(p-1)); self._load_single_page()

    def _single_next_page(self):
        self.single_page_var.set(str(int(self.single_page_var.get() or 1)+1))
        self._load_single_page()

    def _start_single_batch(self):
        if not self.single_site_var.get().strip():
            self._show_warning("请先选择站点"); return
        selected = [(var, video) for var, video in self._single_check_vars if var.get()]
        if not selected:
            self._show_warning("请至少勾选一个视频"); return
        if self.crawl_thread and self.crawl_thread.is_alive():
            self._show_warning("正在运行中，请先停止"); return
        self.crawl_thread = None; self.crawler = None
        self._log_to_ui(self.single_log_text, f"准备下载 {len(selected)} 个视频")
        if not self._single_log_visible.get(): self._toggle_single_log()

        def on_prog(c, t):
            pct = f"{c}/{t}" if t>0 else "?"
            self.after(0, lambda: self.single_progress.configure(value=c*100//max(t,1)))
            self.after(0, lambda: self.single_slice_label.configure(text=pct))
            if c <= 1:
                for w in [lambda:self.single_merge_progress.configure(value=0),
                          lambda:self.single_merge_label.configure(text="切片下载中..."),
                          lambda:self.single_speed_label.configure(text="速度: --"),
                          lambda:self.single_traffic_label.configure(text="流量: 0 B")]: self.after(0, w)

        def on_sp(g,t):
            self.after(0, lambda s=g,tt=t: [
                self.single_speed_label.configure(text=f"速度: {self._format_speed(s)}"),
                self.single_traffic_label.configure(text=f"流量: {self._format_bytes(tt)}"),
            ])

        try:
            self.crawler = CrawlerCore(self.config, log_callback=lambda m,l="info": self._log_to_ui(self.single_log_text,m,l),
                                        progress_callback=on_prog, base_url=self.single_site_var.get(),
                                        merge_progress_callback=lambda p,s: self.after(0,lambda:[
                                            self.single_merge_progress.configure(value=p),
                                            self.single_merge_label.configure(text=f"{p}%{f' {s}' if s else ''}")
                                        ]), speed_callback=on_sp)
        except Exception as e:
            self._log_to_ui(self.single_log_text, f"创建 CrawlerCore 失败: {e}"); return

        def run():
            self._log_to_ui(self.single_log_text, "下载线程已启动")
            success=0; skipped=0; total=len(selected)
            for i,(var,video) in enumerate(selected):
                if self.crawler._stop_flag: self._log_to_ui(self.single_log_text,"已停止"); break
                vid=video.get("id"); title=video.get("title",""); url=video.get("url","")
                self.after(0, lambda t=title,n=i+1,tn=total: self.single_overall_label.configure(text=f"[{n}/{tn}] {t[:40]}"))
                self._log_to_ui(self.single_log_text,f"开始处理: {title[:30]} (url={url[:60]})")
                try:
                    ok = self.crawler.download_single(url, video_id=vid)
                    self._log_to_ui(self.single_log_text,f"  download_single 返回: {ok}")
                    if ok:
                        if vid and self.crawler._history.get(vid,{}).get("download_time"): success+=1
                        else: skipped+=1
                except Exception as e:
                    import traceback; self._log_to_ui(self.single_log_text,f"✗ 下载失败 [{title}]: {e}\n{traceback.format_exc()}")
            self.after(0, lambda: self.single_overall_label.configure(text=f"完成 — 新下载: {success}，跳过: {skipped}"))
            self._log_to_ui(self.single_log_text, f"── 下载完成（新下载: {success}，跳过: {skipped}） ──")
        self.crawl_thread = threading.Thread(target=run, daemon=True)
        self.crawl_thread.start()

    def _start_single_manual(self):
        url = self.url_var.get().strip()
        if not url: self._show_warning("请输入视频URL"); return
        if not self.single_site_var.get().strip(): self._show_warning("请先选择站点"); return
        if self.crawl_thread and self.crawl_thread.is_alive(): self._show_warning("正在运行中，请先停止"); return
        title = self.title_var.get().strip() or None
        def on_prog(c,t):
            pct=f"{c}/{t}"if t>0 else"?"; self.after(0,lambda:self.single_progress.configure(value=c*100//max(t,1)))
            self.after(0,lambda:self.single_slice_label.configure(text=pct))
            if c<=1:
                for w in[lambda:self.single_merge_progress.configure(value=0),lambda:self.single_merge_label.configure(text="切片下载中..."),lambda:self.single_speed_label.configure(text="速度: --"),lambda:self.single_traffic_label.configure(text="流量: 0 B")]:self.after(0,w)
        def on_sp(g,t):
            self.after(0,lambda s=g,tt=t:[self.single_speed_label.configure(text=f"速度: {self._format_speed(s)}"),self.single_traffic_label.configure(text=f"流量: {self._format_bytes(tt)}")])
        self.crawler=CrawlerCore(self.config,log_callback=lambda m,l="info":self._log_to_ui(self.single_log_text,m,l),progress_callback=on_prog,base_url=self.single_site_var.get(),merge_progress_callback=lambda p,s:self.after(0,lambda:[self.single_merge_progress.configure(value=p),self.single_merge_label.configure(text=f"{p}%{f' {s}' if s else''}")]),speed_callback=on_sp)
        def run():
            try:
                self.after(0,lambda:self.single_overall_label.configure(text="正在下载..."));self.after(0,lambda:self.single_merge_progress.configure(value=0));self.after(0,lambda:self.single_merge_label.configure(text=""))
                self.crawler.download_single(url,title);self.after(0,lambda:self.single_overall_label.configure(text="下载完成"));self._log_to_ui(self.single_log_text,"── 下载完成 ──")
            except Exception as e: self._log_to_ui(self.single_log_text,f"错误: {e}")
        self.crawl_thread=threading.Thread(target=run,daemon=True);self.crawl_thread.start()

    # ---- 设置/环境/工具 ----

    def _browse_dir(self):
        from tkinter import filedialog
        path = filedialog.askdirectory()
        if path: self.save_dir_var.set(path)

    def _save_settings(self):
        self.config.update({
            "output_dir": self.save_dir_var.get(), "site": self.site_var.get() or "https://ml0987.xyz",
            "title_with_author": self.title_with_author_var.get(), "sort_by_upload_date": self.sort_by_upload_date_var.get(),
            "proxy_enabled": self.proxy_enabled_var.get(), "proxy_host": self.proxy_host_var.get(),
            "proxy_port": self.proxy_port_var.get(), "proxy_user": self.proxy_user_var.get(),
            "proxy_pass": self.proxy_pass_var.get(),
        })
        save_config(self.config)
        self._show_info("保存成功")

    def _clear_log(self): self.log_text.delete("0.0", "end")

    def _export_log(self):
        from tkinter import filedialog, messagebox
        filepath=filedialog.asksaveasfilename(title="导出日志", defaultextension=".log", filetypes=[("日志文件","*.log"),("文本","*.txt")], initialfile=f"app_log_{time.strftime('%Y%m%d_%H%M%S')}.log")
        if filepath:
            try:
                content=self.log_text.get("0.0","end")
                with open(filepath,"w",encoding="utf-8") as f: f.write(content)
                messagebox.showinfo("导出成功",f"日志已保存到:\n{filepath}")
            except Exception as e: messagebox.showerror("导出失败",str(e))

    def _export_tab_log(self,tab_name):
        from tkinter import filedialog, messagebox
        map={"批量爬取":self.crawl_status_text,"搜索":self.search_status_text,"单视频":self.single_log_text}
        tw=map.get(tab_name)
        if not tw:return
        filepath=filedialog.asksaveasfilename(title=f"导出{tab_name}日志",defaultextension=".log",filetypes=[("日志","*.log"),("文本","*.txt")],initialfile=f"{tab_name}_log_{time.strftime('%Y%m%d_%H%M%S')}.log")
        if filepath:
            try:
                with open(filepath,"w",encoding="utf-8") as f: f.write(tw.get("0.0","end"))
                messagebox.showinfo("导出成功",f"{tab_name}日志已保存到:\n{filepath}")
            except Exception as e: messagebox.showerror("导出失败",str(e))

    def _test_proxy(self):
        host=self.proxy_host_var.get().strip(); port=self.proxy_port_var.get().strip()
        user=self.proxy_user_var.get().strip(); passwd=self.proxy_pass_var.get().strip()
        use=self.proxy_enabled_var.get()
        if (not host or not port) and use:
            self._show_warning("勾选了启用代理，请填写主机和端口");return
        rw=ctk.CTkToplevel(self);rw.title("代理测试");rw.geometry("450x320");rw.resizable(False,False)
        rt=ctk.CTkTextbox(rw,height=280,font=ctk.CTkFont(size=11,family="Consolas"),fg_color=Theme.BG_CARD,corner_radius=10)
        rt.pack(fill="both",expand=True,padx=12,pady=12)
        def ap(t,tag=None):
            cm={"green":"#2e7d32","red":"#c62828","orange":"#e65100"}
            if tag and tag in cm:
                rt.insert("end",t+"\n",tag)
            else:
                rt.insert("end",t+"\n")
            rt.see("end")
        if use: ap(f"代理: socks5h://{host}:{port}\n")
        else: ap("模式: 直连（未启用代理）\n")
        def run_test():
            import requests as req
            proxies={"http":f"socks5h://{user}:{passwd}@{host}:{port}","https":f"socks5h://{user}:{passwd}@{host}:{port}"} if (use and user and passwd) else ({"http":f"socks5h://{host}:{port}","https":f"socks5h://{host}:{port}"} if use else None)
            targets=[("Google","https://www.google.com"),("YouTube","https://www.youtube.com"),("Twitter/X","https://x.com")]
            for name,url in targets:
                self.after(0,lambda n=name:ap(f"正在测试 {n}..."))
                try:
                    resp=req.get(url,proxies=proxies,timeout=10,allow_redirects=False)
                    s=resp.status_code
                    if 200<=s<400: self.after(0,lambda n=name,st=s:ap(f"  ✓ {name} — HTTP {st}","green"))
                    else: self.after(0,lambda n=name,st=s:ap(f"  ✗ {name} — HTTP {st}","orange"))
                except Exception as e: self.after(0,lambda n=name,err=str(e)[:100]:ap(f"  ✗ {name} — {err}","red"))
            self.after(0,lambda:ap("\n── 测试完成 ──"))
        threading.Thread(target=run_test,daemon=True).start()

    # ---- 环境检测 ----

    def get_ffmpeg_path(self):
        if getattr(sys,'frozen',False): return Path(sys.executable).parent/"ffmpeg.exe"
        return APP_DIR/"ffmpeg.exe"

    def _silent_env_check(self):
        errors=[]
        fp=self.get_ffmpeg_path()
        if not fp.exists():errors.append(f"ffmpeg.exe 未找到（需放在: {fp.parent}）")
        try: import requests
        except: errors.append("requests 未安装")
        try: from Crypto.Cipher import AES
        except: errors.append("pycryptodome 未安装")
        if errors: self._check_environment(errors)
        else: self._check_environment([])

    def _manual_env_check(self):
        errors=[]
        fp=self.get_ffmpeg_path()
        if not fp.exists():errors.append(f"ffmpeg.exe 未找到（需放在: {fp.parent}）")
        try: import requests
        except: errors.append("requests 未安装")
        if not self._has_pil: errors.append("Pillow 未安装")
        try: from Crypto.Cipher import AES
        except: errors.append("pycryptodome 未安装")
        self._check_environment(errors)

    def _check_environment(self,errors):
        self.env_textbox.delete("0.0","end")
        fp=self.get_ffmpeg_path()
        def ap(text,status):
            colors={"OK":"green","FAIL":"red","WARN":"orange"}
            self.env_textbox.insert("end",text+"\n")
        if fp.exists(): ap(f"ffmpeg: OK  ({fp})","OK")
        else: ap(f"ffmpeg: 未找到","FAIL"); ap(f"  请放置于: {fp.parent}","WARN")
        try:
            import requests; ap(f"requests: OK (v{requests.__version__})","OK")
        except: ap("requests: 未安装","FAIL")
        if self._has_pil: ap("Pillow: OK (封面预览可用)","OK")
        else: ap("Pillow: 未安装","WARN")
        try:
            from Crypto.Cipher import AES; ap("pycryptodome: OK (AES 解密可用)","OK")
        except: ap("pycryptodome 未安装","WARN")
        if errors:
            ap(""); ap("⚠ 以下问题需要解决:")
            for e in errors: ap(f"  ✗ {e}")
        else: ap(""); ap("✓ 环境检查通过，所有依赖就绪")

    def _install_deps(self):
        self.env_textbox.insert("end","\n正在安装依赖...\n");self.update()
        try:
            result=subprocess.run([sys.executable,"-m","pip","install","-r",str(APP_DIR/"requirements.txt")],capture_output=True,text=True)
            self.env_textbox.insert("end",result.stdout)
            if result.returncode==0: self.env_textbox.insert("end","\n依赖安装成功\n")
            else: self.env_textbox.insert("end",f"\n安装失败: {result.stderr}\n")
            self._check_environment([])
        except Exception as e: self.env_textbox.insert("end",f"\n安装失败: {e}\n")

    def _download_ffmpeg(self):
        import webbrowser;webbrowser.open("https://www.gyan.dev/ffmpeg/builds/")
        self._show_info("请下载 ffmpeg-release-essentials.zip，解压后将 ffmpeg.exe 放到程序目录")

    # ---- 通用弹窗 ----

    def _show_warning(self,msg):
        from tkinter import messagebox;messagebox.showwarning("警告",msg)

    def _show_info(self,msg):
        from tkinter import messagebox;messagebox.showinfo("提示",msg)


# ==================== 配置读写 ====================

def load_config()->dict:
    cfg=DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE,encoding="utf-8") as f: cfg.update(json.load(f))
        except Exception as e: logger.warning(f"加载配置失败: {e}")
    return cfg

def save_config(cfg:dict):
    try:
        with open(CONFIG_FILE,"w",encoding="utf-8") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
    except Exception as e: logger.error(f"保存配置失败: {e}")


# ==================== 入口 ====================

def main():
    app = ModernApp()
    def on_closing():
        if hasattr(app,'crawler') and app.crawler:
            try: app.crawler.flush_history()
            except: pass
        app.destroy()
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
