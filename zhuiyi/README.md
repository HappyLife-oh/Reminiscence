# 追忆 - AI数字人系统

> "此情可待成追忆，只是当时已惘然"

追忆是一个轻量级AI数字人系统，通过分析用户的聊天记录、音频等数据，提取语言风格、音色等特征，结合系统提示词、RAG技术和云端LLM API，实现"赛博永生"。

## 核心特性

- **语言风格克隆**：学习目标人物的说话习惯、用词偏好、表达方式
- **声音克隆**：基于MiMo TTS API复刻目标人物的音色
- **数字人形象**：轻量级数字人，支持表情动画和唇形同步
- **记忆系统**：ChromaDB向量数据库，RAG检索相关记忆
- **Prompt工程**：分层Prompt设计，情感模拟，Few-shot示例
- **多API支持**：MiMo/DeepSeek/OpenAI/通义千问/智谱GLM/Kimi
- **零硬件门槛**：任何电脑都能运行

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Tauri 2.0 + React 19 + TypeScript |
| 后端 | Python FastAPI |
| 向量数据库 | ChromaDB |
| AI对话 | MiMo API (mimo-v2.5-pro) |
| 语音合成 | MiMo TTS API |
| 数字人 | 轻量级CSS动画 |

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.9
- Rust >= 1.70（Tauri需要）

### 1. 配置API密钥

```bash
cd zhuiyi/backend
cp .env.example .env
```

编辑 `.env` 文件，填入MiMo API密钥：

```env
MIMO_API_KEY=your_api_key_here
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
DEFAULT_PROVIDER=mimo
DEFAULT_MODEL=mimo-v2.5-pro
```

### 2. 安装依赖

```bash
# 前端依赖
cd zhuiyi
npm install

# 后端依赖
cd zhuiyi/backend
pip install -r requirements.txt
```

### 3. 启动服务

**方式一：使用启动脚本（Windows）**

```bash
zhuiyi/start.bat
```

**方式二：手动启动**

```bash
# 终端1：启动后端
cd zhuiyi/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端2：启动前端
cd zhuiyi
npm run dev
```

### 4. 访问应用

- 前端界面：http://localhost:1420
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## 项目结构

```
zhuiyi/
├── src/                          # 前端 React
│   ├── App.tsx                   # 主应用
│   ├── App.css                   # 样式
│   └── main.tsx                  # 入口
├── src-tauri/                    # Tauri 后端
├── backend/                      # Python 后端
│   ├── main.py                   # FastAPI 入口
│   ├── .env                      # API 配置
│   ├── models/
│   │   └── data_models.py        # 数据模型
│   ├── routers/
│   │   ├── chat.py               # 聊天 API
│   │   ├── config.py             # 配置 API
│   │   ├── data_import.py        # 数据导入 API
│   │   ├── tts.py                # 语音合成 API
│   │   └── avatar.py             # 数字人 API
│   └── services/
│       ├── llm_service.py        # LLM 调用服务
│       ├── config_service.py     # 配置管理
│       ├── data_parser.py        # 数据解析器
│       ├── feature_extractor.py  # 特征提取
│       ├── character_service.py  # 人物管理
│       ├── memory_service.py     # 记忆系统（RAG）
│       ├── prompt_service.py     # Prompt 工程
│       ├── tts_service.py        # TTS 语音合成
│       └── avatar_service.py     # 数字人服务
├── plans/                        # 项目规划文档
├── start.bat                     # Windows 启动脚本
└── README.md
```

## API接口

### 聊天接口

```bash
# 流式聊天
curl -X POST http://localhost:8000/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}], "provider": "mimo", "stream": true}'

# 带人物档案的聊天
curl -X POST http://localhost:8000/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}], "character_id": "char_xxx", "stream": true}'
```

### 数据导入接口

```bash
# 文件导入
curl -X POST http://localhost:8000/api/data/import/file \
  -F "file=@chat.txt" -F "character_name=小明" -F "file_type=txt"

# 文本导入
curl -X POST http://localhost:8000/api/data/import/text \
  -F "content=..." -F "character_name=小明" -F "file_type=txt"
```

### 语音合成接口

```bash
# 文本转语音
curl -X POST http://localhost:8000/api/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "你好", "model": "tts"}' --output speech.mp3

# 声音克隆
curl -X POST http://localhost:8000/api/tts/voice-clone \
  -F "audio=@reference.mp3" -F "text=你好" --output cloned.mp3
```

### 数字人接口

```bash
# 获取数字人状态
curl http://localhost:8000/api/avatar/{character_id}/state?emotion=joy

# 上传头像
curl -X POST http://localhost:8000/api/avatar/{character_id}/image \
  -F "image=@avatar.png"
```

## 支持的API服务商

| 服务商 | 特点 | 价格 |
|--------|------|------|
| **MiMo** | 对话+TTS+声音克隆 | 按量计费 |
| **DeepSeek** | 便宜、中文好 | ¥1/百万token |
| **OpenAI** | 效果最好 | $2.5/百万token |
| **通义千问** | 稳定、国内服务 | ¥2/百万token |
| **智谱GLM** | 中文优化 | ¥5/百万token |
| **Kimi** | 长文本支持 | ¥1/百万token |

## 开发阶段

- [x] 阶段一：项目基础搭建
- [x] 阶段二：数据处理与特征提取
- [x] 阶段三：记忆系统与RAG
- [x] 阶段四：Prompt工程优化
- [x] 阶段五：声音克隆（MiMo TTS）
- [x] 阶段六：数字人（轻量版）
- [x] 阶段七：系统集成与优化

## 许可证

MIT License
