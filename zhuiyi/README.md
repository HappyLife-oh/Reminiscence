# 追忆 - AI数字人系统

> "此情可待成追忆，只是当时已惘然"

追忆是一个轻量级AI数字人系统，通过分析用户的聊天记录、音频等数据，提取语言风格、音色等特征，结合系统提示词、RAG技术和云端LLM API，实现"赛博永生"。

## 核心特性

- **语言风格克隆**：学习目标人物的说话习惯、用词偏好、表达方式
- **声音克隆**：复刻目标人物的音色、语调、说话节奏
- **数字人形象**：基于照片生成数字人视觉形象
- **多API支持**：支持DeepSeek、OpenAI、通义千问、智谱GLM、Kimi等
- **零硬件门槛**：任何电脑都能运行

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Tauri 2.0 + React + TypeScript |
| 后端 | Python FastAPI |
| 数据库 | ChromaDB + SQLite |
| AI引擎 | 云端LLM API + GPT-SoVITS + SadTalker |

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.9
- Rust >= 1.70（Tauri需要）

### 1. 配置API密钥

复制 `.env.example` 为 `.env`，填入你的API密钥：

```bash
cd zhuiyi/backend
cp .env.example .env
```

编辑 `.env` 文件，至少配置一个API服务商的密钥：

```env
# 推荐使用DeepSeek（便宜且中文效果好）
DEEPSEEK_API_KEY=your_api_key_here
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
# 双击运行
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
├── src/                    # 前端React代码
│   ├── App.tsx            # 主应用组件
│   ├── App.css            # 样式文件
│   └── main.tsx           # 入口文件
├── src-tauri/             # Tauri后端（Rust）
│   ├── src/
│   │   ├── main.rs        # Rust入口
│   │   └── lib.rs         # Tauri命令
│   ├── Cargo.toml         # Rust依赖
│   └── tauri.conf.json    # Tauri配置
├── backend/               # Python后端
│   ├── main.py            # FastAPI入口
│   ├── routers/           # API路由
│   │   ├── chat.py        # 聊天接口
│   │   └── config.py      # 配置接口
│   ├── services/          # 业务服务
│   │   ├── llm_service.py # LLM调用服务
│   │   └── config_service.py # 配置服务
│   ├── requirements.txt   # Python依赖
│   └── .env.example       # 环境变量模板
├── plans/                 # 项目规划文档
│   └── 追忆-项目规划.md
├── package.json           # 前端依赖
├── vite.config.ts         # Vite配置
├── tsconfig.json          # TypeScript配置
└── start.bat              # Windows启动脚本
```

## API接口

### 聊天接口

```bash
# 流式聊天
curl -X POST http://localhost:8000/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "deepseek",
    "stream": true
  }'

# 获取可用服务商
curl http://localhost:8000/api/chat/providers
```

### 配置接口

```bash
# 获取所有服务商
curl http://localhost:8000/api/config/providers

# 更新服务商配置
curl -X POST http://localhost:8000/api/config/providers/deepseek \
  -H "Content-Type: application/json" \
  -d '{"name": "deepseek", "api_key": "your_key", "base_url": "https://api.deepseek.com"}'
```

## 支持的API服务商

| 服务商 | 特点 | 价格 | 推荐场景 |
|--------|------|------|----------|
| DeepSeek | 便宜、中文好 | ¥1/百万token | 日常使用首选 |
| OpenAI | 效果最好 | $2.5/百万token | 追求最佳效果 |
| 通义千问 | 稳定、国内服务 | ¥2/百万token | 稳定性要求高 |
| 智谱GLM | 中文优化 | ¥5/百万token | 中文场景 |
| Kimi | 长文本支持 | ¥1/百万token | 长对话场景 |

## 开发阶段

- [x] 阶段一：项目基础搭建
- [ ] 阶段二：数据处理与特征提取
- [ ] 阶段三：记忆系统与RAG
- [ ] 阶段四：Prompt工程优化
- [ ] 阶段五：声音克隆（轻量版）
- [ ] 阶段六：数字人（轻量版）
- [ ] 阶段七：系统集成与优化

## 许可证

MIT License
