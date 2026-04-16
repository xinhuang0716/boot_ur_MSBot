# Getting Started: Azure Bot Framework + Ollama LLM

一個以 Python 實作的 Bot Framework 入門範例，整合本機 Ollama LLM，展示對話記憶、卡片訊息與回饋收集等核心功能。

---

## Architecture Overview

**本機測試（Emulator）** — 直連，無需 Azure Bot Service：

```
Bot Framework Emulator
          │
          │  POST /api/messages（直連，App ID/Password 留空）
          ▼
┌─────────────────────────────────────┐
│  app.py  (port 3978)                │
│  BotFrameworkAdapter → OllamaBot    │
│  ConversationState (對話記憶)        │
└──────────────┬──────────────────────┘
               │  POST /api/generate
               ▼
┌─────────────────────────────────────┐
│  Ollama  (port 11434)               │
└─────────────────────────────────────┘
```

**雲端部署（Teams / Web Chat 等）** — 流量經過 Azure Bot Service 驗證：

```
使用者 (Teams / Web Chat)
          │
          ▼
Azure Bot Service  (驗證 Token + 路由)
          │
          │  POST /api/messages（需 App ID + App Password）
          ▼
┌─────────────────────────────────────┐
│  app.py  (HTTPS, 公開端點)           │
│  BotFrameworkAdapter → OllamaBot    │
│  ConversationState (對話記憶)        │
└──────────────┬──────────────────────┘
               │  POST /api/generate
               ▼
┌─────────────────────────────────────┐
│  Ollama  (雲端可連線)                │
└─────────────────────────────────────┘
```

---

## Features

| 功能 | 說明 |
|---|---|
| LLM 對話 | 透過 Ollama `/api/generate` 取得 LLM 回覆 |
| **對話記憶** | 將歷史訊息拼接進 prompt，讓模型記得上下文 |
| Hero Card | 輸入 `hero card` 展示 Hero Card 範例 |
| Adaptive Card | 輸入 `adaptive card` 展示 Adaptive Card 範例 |
| 回饋收集 | 每則 LLM 回覆附帶 👍 / 👎，收集評分與留言至 `log/feedback.json` |

---

## Project Structure

```
├── app.py              # HTTP 伺服器入口，Adapter 設定、State 初始化
├── config.py           # 所有環境變數與可調參數的統一入口
├── pyproject.toml      # 依賴管理（uv）
│
├── bot/
│   ├── handler.py      # Bot 核心邏輯：訊息路由、對話記憶、回饋狀態
│   ├── cards.py        # Hero Card / Adaptive Card 建構器
│   └── feedback.py     # 回饋資料寫入 JSON
│
├── services/
│   └── ollama.py       # Ollama API 非同步客戶端
│
└── log/
    └── feedback.json   # 回饋紀錄（自動建立）
```

---

## Getting Started

### 1. Prequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) 並已拉取模型：`ollama pull gemma3:4b`

### 2. Virtual Environment and Dependencies

```bash
uv sync
```

### 3. 設定環境變數（可選）

本機測試可略過，預設值即可運作。若需要調整，建立 `.env`：

```env
# Azure Bot 憑證（本機測試留空）
MicrosoftAppId=
MicrosoftAppPassword=

# Ollama 服務位置與模型
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# 對話歷史最多保留幾則訊息（預設 20，即 10 回合）
HISTORY_LIMIT=20
```

### 4. 啟動 Bot

```bash
uv run python app.py
```

啟動後輸出：

```
Bot started
  Bot URL      : http://localhost:3978/api/messages
  Health URL   : http://localhost:3978/health
  Ollama       : http://localhost:11434
```

### 5. 使用 Bot Framework Emulator 測試

1. 下載 [Bot Framework Emulator](https://github.com/microsoft/BotFramework-Emulator/releases)
2. **Open Bot** → Bot URL 填入 `http://localhost:3978/api/messages`
3. App ID / Password 留空
4. 開始對話

---

## Core Concepts

### Turn（回合）

每次使用者送出訊息，Bot Framework 建立一個 **Turn**，執行完畢後立即釋放。所有需要跨回合保留的資料，都必須存入 State。

### ConversationState（對話狀態）

本專案透過 `ConversationState` + `MemoryStorage` 保存兩份資料：

| Property | 型別 | 用途 |
|---|---|---|
| `pending_feedback` | `dict \| None` | 暫存待補充留言的回饋 |
| `chat_history` | `list[dict]` | 對話歷史，傳給 Ollama 做上下文 |

> `MemoryStorage` 存在記憶體中，Bot 重啟後自動清空。若需持久化，可替換為 `CosmosDbPartitionedStorage` 或 `BlobStorage`。

### 對話記憶實作

歷史訊息以 Prompt 拼接方式傳給 Ollama：

```
user: my name is tom
assistant: Hello, Tom! How can I help you?
User: what's my name?
Assistant:
```

`HISTORY_LIMIT`（預設 20）控制最多保留幾則，避免 prompt 過長。

---

## API Reference

### Ollama

| 項目 | 內容 |
|---|---|
| Endpoint | `POST /api/generate` |
| Request | `{"model": "...", "system": "...", "prompt": "...", "stream": false}` |
| Response | `{"response": "<LLM 回覆>"}` |

### Bot Framework 訊息端點

| 項目 | 內容 |
|---|---|
| Endpoint | `POST /api/messages` |
| 說明 | Azure Bot Service 路由，遵循 Bot Framework Activity 協定 |

### Health Check

| 項目 | 內容 |
|---|---|
| Endpoint | `GET /health` |
| Response | `{"status": "ok"}` |

---

## Deply to Azure

1. 建立 **Azure Bot** 資源，取得 App ID 與 App Password
2. 設定環境變數 `MicrosoftAppId`、`MicrosoftAppPassword`
3. 將專案部署至可公開存取的 HTTPS 服務
4. Azure Bot → **Messaging Endpoint** 填入 `https://<your-host>/api/messages`
5. 確認 `OLLAMA_BASE_URL` 指向雲端可連線的 Ollama 服務

---

## Further Improvements

- 替換 `MemoryStorage` 為 Azure Cosmos DB 實現持久化對話記憶
- 將 Ollama 換成 Azure OpenAI（`/chat/completions` 格式與 `chat_history` 直接相容）
- 在 `system` 欄位加入角色設定，客製化 Bot 人設

