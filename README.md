# 追忆 Reminiscence

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
  <img src="https://img.shields.io/badge/python-3.9+-yellow" alt="python">
  <img src="https://img.shields.io/badge/node-18+-yellow" alt="node">
</p>

> **此情可待成追忆，只是当时已惘然。**

追忆是一个AI驱动的数字人永生系统。通过分析聊天记录、音频等数据，学习一个人的说话风格、音色、性格特征，让心中那个人在数字世界中"赛博永生"。

---

## ✨ 核心功能

| 功能 | 描述 | 技术实现 |
|------|------|----------|
| 🗣️ **语言风格克隆** | 学习说话习惯、口头禅、表达方式 | 特征提取 + Prompt工程 |
| 🎵 **声音克隆** | 复刻音色、语调、说话节奏 | MiMo TTS VoiceClone |
| 🧠 **记忆系统** | 记住共同经历，自然提及 | ChromaDB RAG |
| 😊 **情感模拟** | 根据对话动态调整情感状态 | 情感分析 + 状态机 |
| 👤 **数字人形象** | 表情动画、唇形同步 | 轻量级CSS动画 |
| 📱 **多平台数据** | 支持微信/QQ/短信等聊天记录 | 多格式解析器 |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Tauri + React)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 聊天界面  │  │ 数据导入  │  │ 人物管理  │  │ 设置页面  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP API
┌─────────────────────────┴───────────────────────────────┐
│                  后端 (Python FastAPI)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 聊天路由  │  │ 数据导入  │  │ TTS服务  │  │ 数字人   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │             │             │        │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐ │
│  │Prompt引擎│  │特征提取器│  │MiMo TTS  │  │表情引擎  │ │
│  └────┬─────┘  └────┬─────┘  └──────────┘  └──────────┘ │
│       │             │                                     │
│  ┌────┴─────┐  ┌────┴─────┐                              │
│  │RAG记忆库 │  │数据解析器│                              │
│  └──────────┘  └──────────┘                              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│                    云端服务 (MiMo API)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ LLM对话  │  │ TTS合成  │  │ 声音克隆  │               │
│  └──────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 方式一：下载安装包（推荐）

前往 [Releases](https://github.com/HappyLife-oh/Reminiscence/releases) 页面下载最新版本的 Windows 安装包。

### 方式二：从源码运行

#### 环境要求

- **Node.js** >= 18
- **Python** >= 3.9
- **Rust** >= 1.70（仅Tauri桌面版需要）

#### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/HappyLife-oh/Reminiscence.git
cd Reminiscence

# 2. 安装前端依赖
cd zhuiyi
npm install

# 3. 安装后端依赖
cd backend
pip install -r requirements.txt

# 4. 配置API密钥
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

#### 启动服务

```bash
# 方式一：使用启动脚本（Windows）
双击 zhuiyi/start.bat

# 方式二：手动启动
# 终端1：启动后端
cd zhuiyi/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端2：启动前端
cd zhuiyi
npm run dev
```

访问 http://localhost:1420 开始使用。

---

## 📖 使用指南

### 第一步：配置API

1. 访问 [MiMo开放平台](https://platform.xiaomimimo.com/) 获取API密钥
2. 在应用设置中填入API密钥

### 第二步：导入数据

支持多种数据导入方式：

| 方式 | 说明 |
|------|------|
| 📁 **文件上传** | 支持 TXT、CSV、JSON 格式 |
| 📋 **粘贴文本** | 直接粘贴聊天记录 |
| 🔍 **自动检测** | 自动识别文件格式和编码 |

**聊天记录格式示例：**
```
2024-01-01 12:00 小明: 你好啊
2024-01-01 12:01 小红: 你好
2024-01-01 12:02 小明: 哈哈 今天天气不错
```

### 第三步：开始对话

1. 在侧边栏选择导入的人物
2. 开始对话，系统会自动使用该人物的语言风格回复
3. 支持文字和语音两种交互方式

---

## 🔧 API接口

### 聊天接口

```bash
# 流式聊天
POST /api/chat/completions
{
  "messages": [{"role": "user", "content": "你好"}],
  "character_id": "char_xxx",  # 可选，指定人物
  "provider": "mimo",          # 可选，指定API服务商
  "stream": true
}
```

### 数据导入接口

```bash
# 文件导入
POST /api/data/import/file
FormData: file, character_name, file_type

# 文本导入
POST /api/data/import/text
FormData: content, character_name, file_type
```

### 语音合成接口

```bash
# 文本转语音
POST /api/tts/synthesize
{"text": "你好", "model": "tts"}

# 声音克隆
POST /api/tts/voice-clone
FormData: audio, text
```

### 数字人接口

```bash
# 获取数字人状态
GET /api/avatar/{character_id}/state?emotion=joy

# 上传头像
POST /api/avatar/{character_id}/image
FormData: image
```

完整API文档请访问 http://localhost:8000/docs

---

## 📁 项目结构

```
Reminiscence/
├── .github/workflows/          # GitHub Actions
│   └── build.yml              # 自动构建配置
├── plans/                      # 项目规划文档
│   └── 追忆-项目规划.md
├── zhuiyi/                     # 主项目目录
│   ├── src/                   # 前端 React
│   │   ├── App.tsx           # 主应用组件
│   │   ├── App.css           # 样式文件
│   │   └── main.tsx          # 入口文件
│   ├── src-tauri/            # Tauri 桌面应用
│   │   ├── src/              # Rust 源码
│   │   ├── Cargo.toml        # Rust 依赖
│   │   └── tauri.conf.json   # Tauri 配置
│   ├── backend/              # Python 后端
│   │   ├── main.py           # FastAPI 入口
│   │   ├── .env.example      # 环境变量模板
│   │   ├── requirements.txt  # Python 依赖
│   │   ├── models/           # 数据模型
│   │   ├── routers/          # API 路由
│   │   │   ├── chat.py      # 聊天接口
│   │   │   ├── config.py    # 配置接口
│   │   │   ├── data_import.py # 数据导入
│   │   │   ├── tts.py       # 语音合成
│   │   │   └── avatar.py    # 数字人
│   │   └── services/         # 业务服务
│   │       ├── llm_service.py      # LLM调用
│   │       ├── config_service.py   # 配置管理
│   │       ├── data_parser.py      # 数据解析
│   │       ├── feature_extractor.py # 特征提取
│   │       ├── character_service.py # 人物管理
│   │       ├── memory_service.py   # 记忆系统
│   │       ├── prompt_service.py   # Prompt工程
│   │       ├── tts_service.py      # TTS服务
│   │       └── avatar_service.py   # 数字人服务
│   ├── package.json          # 前端依赖
│   ├── vite.config.ts        # Vite 配置
│   ├── tsconfig.json         # TypeScript 配置
│   └── start.bat             # Windows 启动脚本
└── README.md                 # 项目说明
```

---

## 🛠️ 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **前端** | Tauri 2.0 + React 19 + TypeScript | 桌面应用框架 |
| **后端** | Python FastAPI | API服务 |
| **向量数据库** | ChromaDB | RAG记忆检索 |
| **AI对话** | MiMo-V2.5-Pro | 语言模型 |
| **语音合成** | MiMo TTS | 文本转语音 |
| **声音克隆** | MiMo VoiceClone | 声音复刻 |
| **NLP** | jieba + snownlp | 中文分词、情感分析 |
| **构建** | GitHub Actions | 自动构建 |

---

## 🌐 支持的API服务商

| 服务商 | 模型 | 特点 | 价格 |
|--------|------|------|------|
| **MiMo** | mimo-v2.5-pro | 对话+TTS+声音克隆 | 按量计费 |
| **DeepSeek** | deepseek-chat | 便宜、中文好 | ¥1/百万token |
| **OpenAI** | gpt-4o-mini | 效果最好 | $2.5/百万token |
| **通义千问** | qwen-turbo | 稳定、国内服务 | ¥2/百万token |
| **智谱GLM** | glm-4-flash | 中文优化 | ¥5/百万token |
| **Kimi** | moonshot-v1-8k | 长文本支持 | ¥1/百万token |

---

## 📋 开发进度

- [x] **阶段一**：项目基础搭建
- [x] **阶段二**：数据处理与特征提取
- [x] **阶段三**：记忆系统与RAG
- [x] **阶段四**：Prompt工程优化
- [x] **阶段五**：声音克隆（MiMo TTS）
- [x] **阶段六**：数字人（轻量版）
- [x] **阶段七**：系统集成与优化

---

## 🔄 自动构建

项目使用 GitHub Actions 自动构建 Windows 安装包。

### 触发方式

- **标签触发**：推送 `v*` 标签（如 `git tag v1.0.0`）
- **手动触发**：在 GitHub Actions 页面点击 "Run workflow"

### 构建产物

- **MSI 安装包**：标准 Windows 安装程序
- **NSIS 安装程序**：自定义安装程序

### 创建发布版本

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

## 🙏 致谢

- [MiMo](https://platform.xiaomimimo.com/) - 提供AI模型服务
- [Tauri](https://tauri.app/) - 桌面应用框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库

---

<p align="center">
  <i>此情可待成追忆，只是当时已惘然。</i>
</p>
