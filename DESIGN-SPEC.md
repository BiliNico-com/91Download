# WebSpider Pro — UI 设计系统规范

> **项目**：Python 智能爬虫程序用户界面  
> **设计版本**：v1.0  
> **设计语言**：现代仪表盘风格（参考 JobTrotti 风格）  
> **设计师**：UI Designer Agent 🎨  
> **日期**：2026-04-09

---

## 🎨 一、设计基础

### 1.1 设计理念

本界面遵循 **"功能优先，美学并行"** 的原则，参考了现代化 SaaS 仪表盘的最佳实践：

| 原则 | 说明 |
|------|------|
| **信息层级清晰** | 通过卡片分区、色彩对比和字号梯度建立视觉层次 |
| **操作效率至上** | 核心操作（创建任务、启动爬取）一触即达 |
| **实时反馈丰富** | 进度条、状态指示器、数据趋势图提供即时反馈 |
| **一致的设计语言** | 统一的圆角、阴影、间距体系贯穿全局 |

### 1.2 色彩系统

#### 主色调 (Primary) — Indigo
用于品牌标识、主要操作按钮、活跃导航态。

```
--color-primary-50:   #eef2ff   （极浅背景）
--color-primary-100:  #e0e7ff   （浅背景/标签）
--color-primary-200:  #c7d2fe   （边框高亮）
--color-primary-300:  #a5b4fc   （悬停态边框）
--color-primary-400:  #818cf8   （聚焦态边框）
--color-primary-500:  #6366f1   ★ 主色（按钮/图标）
--color-primary-600:  #4f46e5   （深主色/激活态文字）
--color-primary-700:  #4338ca   （深色按下态）
--color-primary-800:  #3730a3   
--color-primary-900:  #312e81   （最深主色）
```

#### 语义色 (Semantic Colors)

| 用途 | 色值 | 使用场景 |
|------|------|----------|
| ✅ 成功 | `#10b981` | 运行成功、正向指标、完成状态 |
| ⚠️ 警告 | `#f59e0b` | 待处理、中等优先级 |
| ❌ 错误 | `#ef4444` | 失败、异常、错误提示 |
| ℹ️ 信息 | `#3b82f6` | 中性提示、信息类 |

#### 中性灰阶 (Neutral Grays)

```
--color-gray-50:  #f8fafc   页面背景
--color-gray-100: #f1f5f9   卡片边框 / 分割线
--color-gray-200: #e2e8f0   输入框默认边框
--color-gray-300: #cbd5e1   占位符文字 / 禁用态
--color-gray-400: #94a3b8   辅助说明文字
--color-gray-500: #64748b   次要文字
--color-gray-600: #475569   正文文字
--color-gray-700: #334155   标题文字
--color-gray-800: #1e293b   重要标题
--color-gray-900: #0f172a   最高强调文字
```

#### 渐变色 (Gradients)

| 名称 | 渐变方向 | 色值 | 使用场景 |
|------|----------|------|----------|
| Primary Gradient | 135° | `#6366f1 → #8b5cf6` | 主CTA按钮、升级卡背景 |
| Blue Card | 135° | `#3b82f6 → #2563eb` | 任务卡片（蓝色系） |
| Purple Card | 135° | `#8b5cf6 → #7c3aed` | 任务卡片（紫色系） |
| Orange Card | 135° | `#f97316 → #ea580c` | 任务卡片（橙色系） |

### 1.3 字体系统

**字体族**: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

| 级别 | 大小 | 字重 | 行高 | 使用场景 |
|------|------|------|------|----------|
| XS | 12px (0.75rem) | Medium (500) | 1.5 | 标签、徽章、辅助信息 |
| SM | 14px (0.875rem) | Medium (500) | 1.5 | 导航项、表单标签、正文 |
| Base | 16px (1rem) | Regular (400) | 1.6 | 默认正文字体 |
| LG | 18px (1.125rem) | Semibold (600) | 1.4 | 区块标题、面板标题 |
| XL | 20px (1.25rem) | Bold (700) | 1.3 | 页面标题 |
| 2XL | 24px (1.5rem) | ExtraBold (800) | 1.2 | 统计数字 |
| 3XL | 30px (1.875rem) | ExtraBold (800) | 1.2 | 大型统计数值 |

### 1.4 间距系统

基于 **4px 基准单位** 的等比数列：

```
--space-1:  4px     元素内部微调
--space-2:  8px     小元素间距 / 图标与文字间距
--space-3:  12px    表单内边距 / 列表项紧凑间距
--space-4:  16px    卡片内标准间距 / 组件间隙
--space-5:  20px    区块内边距增强
--space-6:  24px    主要区块间距 / 卡片外边距
--space-8:  32px    内容区大间距
--space-10: 40px    区域分隔距离
--space-12: 48px    页面级大间距
```

### 1.5 圆角系统

```
--radius-sm:     6px      小元素（输入框聚焦态）
--radius-md:     8px      卡片基础圆角
--radius-lg:     12px     按钮、图标容器
--radius-xl:     16px     大卡片、面板容器
--radius-2xl:    24px     升级卡片、特殊强调区域
--radius-full:   9999px   圆形元素（头像、药丸标签、全圆按钮）
```

### 1.6 阴影系统

```
--shadow-xs:  0 1px 2px 0 rgb(0 0 0 / 0.05)        极轻悬浮感
--shadow-sm:  0 1px 3px 0 rgb(0 0 0 / 0.1),         卡片默认
              0 1px 2px -1px rgb(0 0 0 / 0.1)
--shadow-md:  0 4px 6px -1px rgb(0 0 0 / 0.1),       悬停提升
              0 2px 4px -2px rgb(0 0 0 / 0.1)
--shadow-lg:  0 10px 15px -3px rgb(0 0 0 / 0.1),     弹窗/模态框
              0 4px 6px -4px rgb(0 0 0 / 0.1)
--shadow-xl:  0 20px 25px -5px rgb(0 0 0 / 0.1),     特殊强调
              0 8px 10px -6px rgb(0 0 0 / 0.1)
```

---

## 🧱 二、组件库

### 2.1 侧边栏 (Sidebar)

**尺寸**: 固定宽度 `260px`, 全屏高度 `100vh`  
**背景**: 白色 (`#ffffff`) + 右侧 `1px solid #f1f5f9` 分割线  
**结构**:

```
┌─────────────────────┐
│ 🕷️ WebSpider Pro    │ ← 品牌区 (padding: 24px)
├─────────────────────┤
│ 主要功能             │ ← 分区标题
│ ◆ 工作台 [active]   │ ← 导航项 (active = 高亮+左侧竖条)
│ ◇ 网络爬虫           │
│ ◇ 数据导出 [badge:3]│
│ ◇ 任务管理           │
│                      │
│ 数据分析             │
│ ◇ 统计分析           │
│ ◇ 数据趋势           │
│ ◇ 数据报表           │
│                      │
│ 设置                 │
│ ◇ 全局设置           │
│ ◇ 帮助中心           │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ 🚀 升级到Pro     │ │ ← 渐变升级卡片
│ │ 解锁高级功能...   │ │
│ │ [立即升级]       │ │
│ └─────────────────┘ │
└─────────────────────┘
```

**交互规则**:
- 导航项 hover: `background: #f8fafc`, `color: #334155`
- 导航项 active: `background: #eef2ff`, `color: #4f46e5`, 左侧 `3px` 竖条
- 过渡动画: `150ms ease`

### 2.2 顶部导航 (Top Header)

**尺寸**: 固定高度 `72px`  
**行为**: `position: sticky; top: 0`  
**背景**: 半透明白 `rgba(255,255,255,0.9)` + `backdrop-filter: blur(10px)`  

**结构**:
```
┌──────────────────────────────────────────────────────────┐
│ 👋 欢迎回来，开发者！                    [🔍搜索] [🔔][☀️][W] │
│ 管理你的爬取任务...🔥                                       │
└──────────────────────────────────────────────────────────┘
```

**搜索框规格**:
- 宽度: `320px`
- 形状: `border-radius: 9999px` (全圆)
- 内边距: `12px 16px 12px 38px` (左侧留出图标空间)
- 图标定位: `absolute left: 16px`
- 聚焦态: 边框变为 `#818cf8`, 背景 `white`, 外发光 `0 0 0 3px rgba(99,102,241,0.1)`

**用户头像**:
- 尺寸: `42x42px`
- 背景: 线性渐变 `#f472b6 → #c084fc` (粉紫)
- 边框: `2px solid white` + `box-shadow`
- Hover: `scale(1.05)` + 加重阴影

### 2.3 统计卡片 (Stat Cards)

**布局**: 4列网格 (`grid-template-columns: repeat(4, 1fr)`)  
**间距**: `gap: 24px`  
**结构**:

```
┌──────────────────────────┐
│ ═══════════════ (顶部3px色条)
│ [图标]          [+12.5%] │ ← 头部：图标 + 趋势徽章
│                         │
│ 2,847                   │ ← 数值 (30px, ExtraBold)
│ 今日采集总量            │ ← 标签 (14px, gray-500)
└──────────────────────────┘
```

**四张卡片配色**:
| 序号 | 图标底色 | 顶部色条渐变 | 含义 |
|------|---------|-------------|------|
| 1 | `#eef2ff` + `#6366f1` 文字 | `#6366f1 → #818cf8` | 采集总量 |
| 2 | `#ecfdf5` + `#10b981` 文字 | `#10b981 → #34d399` | 成功任务 |
| 3 | `#fffbeb` + `#f59e0b` 文字 | `#f59e0b → #fbbf24` | 响应时间 |
| 4 | `#fef2f2` + `#ef4444` 文字 | `#ef4444 → #f87171` | 失败异常 |

**Hover**: `translateY(-2px)` + `box-shadow-lg`

### 2.4 爬虫配置面板 (Config Panel)

位于左侧，包含以下控件：

#### URL 输入框
- 类型: `<input type="text">`
- 样式: `border-radius: 12px`, `border: 2px solid #e2e8f0`, 背景 `#f8fafc`
- 聚焦态: 同搜索框逻辑

#### 目标网站标签 (Tag Chips)
- 形状: `border-radius: 9999px` (全圆药丸形)
- 背景: `#eef2ff`, 文字 `#4f46e5`, 边框 `#c7d2fe`
- 内含删除按钮 ×, hover 变红
- 点击删除时: 缩放消失动画 `scale(0) → opacity(0) → remove`

#### 滑块控件 (Range Slider)
- 轨道: `height: 6px`, 圆角全圆, `background: #e2e8f0`
- 滑块头: `20x20px` 圆形, `background: #6366f1`, `border: 3px white`, 阴影发光
- 拖动时联动上方数值显示

#### 下拉选择器 (Custom Select)
- 自定义箭头 SVG 图标
- 其余样式同输入框

#### 任务类型切换按钮组 (Toggle Group)
- 三按钮并排: `深度爬取 | 单页提取 | 增量更新`
- 默认态: 白底 + 灰边框
- Active 态: `#6366f1` 底色 + 白字

#### 主操作 CTA 按钮
- 尺寸: `width: 100%`, `padding: 16px 24px`
- 背景: 渐变 `#6366f1 → #8b5cf6`
- 圆角: `16px`
- 阴影: `0 4px 14px rgba(99,102,241,0.35)`
- Hover: 上浮 2px + 阴影加重
- 包含播放 ▶ 图标 + 文字

#### 进度条
- 轨道: `height: 6px`, `background: #e2e8f0`
- 填充: 渐变 `#6366f1 → #8b5cf6`
- 动画: shimmer 光泽扫过效果 (2s 循环)

### 2.5 任务卡片 (Task Cards)

**布局**: 3列网格 (`grid-template-columns: repeat(3, 1fr)`)  
**最小高度**: `160px`  
**三种配色变体**:

```
┌─────────────────────────────┐
│ ══════════════════════════  │ ← 渐变背景 + 右上装饰圆圈
│ [📰图标] 新闻资讯抓取       │
│         新浪 / 网易 / 腾讯  │
│                             │
│ [全站] [深度 3]            │ ← 半透明药丸标签
│                             │
│ 📊28,000条/日   [运行中]    │ ← 底部信息行
└─────────────────────────────┘
```

**Hover 效果**: `translateY(-4px)` + `shadow-xl`  
**装饰**: 右上角半透明白色圆形 (`rgba(255,255,255,0.08)`) 增加层次

### 2.6 热门任务列表 (Task List)

每项结构:
- 左: 44x44px 圆角图标容器 + Emoji
- 中: 任务名称 (semibold) + 来源描述 (xs灰色)
- 右: 数值统计 (bold)
- 分隔线: 底部 1px `#f1f5f9`
- Hover: 整行 `background: #f8fafc`

### 2.7 数据趋势图表 (Trend Chart)

- 类型: SVG 折线图 (纯 CSS/SVG 实现，无需图表库)
- 双线: 主线 (红色 `#ef4444`) + 次线 (紫色 `#6366f1`)
- 主线下方带面积填充 (渐变透明度 0.3→0)
- 数据点: 6px 圆点, hover 放大到 7px
- 峰值 Tooltip: 深色气泡标注
- 时间轴: 底部月份标签
- 控制按钮: 周/月/日 切换, Active 为红色填充

---

## 📱 三、响应式断点策略

| 断点 | 宽度范围 | 布局变化 |
|------|----------|----------|
| Desktop XL | ≥1400px | 完整双栏布局, 4统计卡, 3列任务卡, 双列底部 |
| Desktop | 1200–1399px | 任务卡变 2列, 底部单列堆叠 |
| Tablet | 768–1199px | 配置面板移到上方(单列), 统计卡 2列 |
| Mobile | <768px | 侧边栏隐藏, 单列全宽, 所有组件纵向排列 |

```css
/* 关键断点 */
@media (max-width: 1400px) { .task-cards-grid { grid-columns: repeat(2, 1fr); } }
@media (max-width: 1200px) { .main-grid { grid-template-columns: 1fr; } }
@media (max-width: 768px) { 
  .sidebar { transform: translateX(-100%); } 
  .main-content { margin-left: 0; }
}
```

---

## ♿ 四、可访问性合规 (WCAG AA)

### 色彩对比度
- 正常文本 (14px+): 最低 **4.5:1** 对比度 ✅
  - `#334155` on `#ffffff` = 8.6:1 ✅
  - `#4f46e5` on `#ffffff` = 7.5:1 ✅
  - `#64748b` on `#ffffff` = 4.5:1 ✅ (刚好达标)
- 大文本 (18px+): 最低 **3:1** 对比度 ✅

### 交互可达性
- 所有可点击元素: 最小触控目标 **40×40px** (按钮/导航项)
- 焦点指示器: `outline: 2px solid var(--color-primary-500); outline-offset: 2px`
- Tab 键顺序: 符合视觉阅读顺序
- ARIA 标签建议: 为图标按钮添加 `aria-label`

### 动画偏好
- 支持 `prefers-reduced-motion`: 应禁用进度条 shimmer 和悬停位移动画
- 建议 CSS 补充:
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
  ```

---

## 🔧 五、开发者交接规格

### 文件清单
| 文件 | 说明 |
|------|------|
| `web-spider-ui.html` | 完整交互原型 (单文件, 含内联CSS+JS) |
| `DESIGN-SPEC.md` | 本设计规范文档 |

### 技术实现建议

#### Python GUI 框架映射
如果使用 Python 构建 GUI，推荐以下框架对应方案：

| 组件 | PySide6/Qt | Tkinter CustomTkinter | DearPyGui |
|------|-----------|---------------------|-----------|
| 侧边栏 | QDockWidget / QWidget | Frame with custom styling | dpg.group |
| 统计卡片 | QFrame + QGridLayout | CTkFrame | dpg.group |
| 滑块 | QSlider | CTkSlider | dpg.slider_int |
| 任务卡片 | QFrame (styled) | CTkFrame | dpg.group |
| 图表 | QtCharts / pyqtgraph | matplotlib embed | dpg.plot_line |
| 进度条 | QProgressBar | CTkProgressBar | dpg.progress_bar |

#### CSS 设计令牌导出
可直接提取 `:root` 变量供前端使用，或转换为 Python 字典配置：
```python
THEME = {
    "primary": "#6366f1",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "bg_body": "#f0f4f8",
    "bg_card": "#ffffff",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "radius_lg": "12px",
    "radius_xl": "16px",
    "shadow_md": "0 4px 6px rgba(0,0,0,0.1)",
}
```

### 图标资源
当前使用 SVG inline 图标（Heroicons 风格），可替换为以下方案:
- **Lucide Icons** (https://lucide.dev) — 开源, 风格统一
- **Phosphor Icons** — 多种粗细可选
- **Material Symbols** — Google 出品, 丰富的语义图标

---

## 📐 六、关键度量速查

| 属性 | 值 |
|------|-----|
| 侧边栏宽度 | 260px |
| 顶栏高度 | 72px |
| 卡片圆角 | 16px (xl) |
| 按钮圆角 | 9999px (全圆) 或 16px |
| 内容区内边距 | 32px |
| 统计卡网格 | 4列 |
| 任务卡网格 | 3列 |
| 主色调 | Indigo (#6366f1) |
| 字体 | Inter (Google Fonts) |
| 基准间距 | 4px |
| 过渡时长 | 150ms (快) / 250ms (中) / 350ms (慢) |

---

*本文档由 UI Designer Agent 🎨 生成，基于现代化仪表盘设计最佳实践。*
