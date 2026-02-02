# PageRAG - 完整啟動與操作 SOP

本文件提供系統的完整啟動標準作業程序 (Standard Operating Procedure)。

---

## 📋 前置需求檢查清單

在開始之前，請確認以下環境：

- [ ] Python 3.10+ 已安裝
- [ ] Docker 與 Docker Compose 已安裝並正常運行
- [ ] Git 已安裝
- [ ] OpenAI API Key（必須）

---

## 🚀 完整啟動 SOP

### 階段 1：初始環境設定（僅需執行一次）

#### 1.1 取得專案
```bash
cd /path/to/your/workspace
# 如果是從 Git 下載
git clone <your-repo-url>
cd PageRAG
```

#### 1.2 設定環境變數
```bash
# 複製環境變數範本
cp .env.example .env
```

**編輯 `.env` 檔案**，填入您的 API Key：
```bash
# 使用任何編輯器打開 .env
nano .env  # 或 vim .env 或 code .env
```

填入以下內容（**必須**）：
```env
OPENAI_API_KEY=sk-proj-你的實際OpenAI金鑰
CHATGPT_API_KEY=sk-proj-你的實際OpenAI金鑰  # 與上面相同
QDRANT_URL=http://localhost:6333
```
> **💡 提示**：`OPENAI_API_KEY` 和 `CHATGPT_API_KEY` 請填入**相同的值**。

#### 1.3 建立 Python 虛擬環境

**Mac / Linux：**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows：**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### 1.4 安裝 Python 相依套件
```bash
pip install -r requirements.txt
```

> ⏱️ **預計時間**：2-5 分鐘（依網路速度）

---

### 階段 2：啟動服務（每次使用前執行）

#### 2.1 啟動 Docker 容器
```bash
cd docker
docker-compose up -d
```

**檢查容器狀態：**
```bash
docker-compose ps
```

應該看到：
```
NAME                 STATUS
pagerag-backend      Up
pagerag-qdrant       Up
```

> **🔍 驗證**：
> - 前端：開啟瀏覽器訪問 http://localhost:8000（應該會看到聊天介面）
> - Qdrant：訪問 http://localhost:6333/dashboard（資料庫管理介面）

---

### 階段 3：資料匯入（首次使用或新增資料時）

#### 3.1 匯入 RAG 資料（一般文件檢索）

**步驟：**
1. 將 `.txt` 文字檔案放入 `data/rag_source/` 資料夾
2. 執行處理腳本：

```bash
# 確保虛擬環境已啟動
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 執行 RAG 資料處理
python scripts/process_rag.py
```

**預期輸出：**
```
Starting RAG processing...
Loaded 1 documents from data/rag_source/sample.txt
Split into 15 chunks.
Successfully indexed documents to Qdrant.
```

#### 3.2 匯入 PageIndex 資料（特定文件查找）

**步驟：**
1. 將 PDF 檔案放入 `data/file/` 資料夾
2. 執行處理腳本：

```bash
# 確保虛擬環境已啟動
python scripts/process_pageindex.py
```

**預期輸出：**
```
Starting PageIndex processing...

Processing your_document.pdf...
Parsing PDF...
✓ Successfully indexed: your_document
  Index saved to: data/pageindex_indices/your_document_structure.json

PageIndex processing complete.
```

> ⚠️ **注意**：PageIndex 處理會呼叫 OpenAI API，大型 PDF 可能需要數分鐘且產生 API 費用。

---

### 階段 4：使用系統

#### 4.1 開啟網頁介面
在瀏覽器中訪問：**http://localhost:8000**

#### 4.2 使用「一般聊天」模式（RAG）
直接在輸入框輸入問題，系統會從 `data/rag_source/` 的資料中檢索答案。

**範例：**
```
使用者：請問文件中提到的主要功能是什麼？
AI：根據您提供的文件...
來源：sample.txt
```

#### 4.3 使用「特定文件查找」模式（PageIndex）
1. 點擊輸入框下方的 **「工具」** 按鈕
2. 選擇 **「Find Documents (PageIndex)」**
3. 輸入關於 PDF 內容的問題

**範例：**
```
使用者：第三章討論了什麼主題？
AI：根據文件第三章...
來源：your_document.pdf
```

---

## 🛠️ 日常操作指令

### 啟動系統
```bash
# 1. 啟動虛擬環境
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 2. 啟動 Docker
cd docker
docker-compose up -d

# 3. 訪問 http://localhost:8000
```

### 停止系統
```bash
cd docker
docker-compose down
```

### 查看日誌
```bash
# 即時查看後端日誌
docker logs -f pagerag-backend

# 查看 Qdrant 日誌
docker logs -f pagerag-qdrant
```

### 重啟服務
```bash
cd docker
docker-compose restart backend  # 重啟後端
docker-compose restart qdrant   # 重啟資料庫
```

---

## 🔧 資料管理

### 新增 RAG 資料
```bash
# 1. 將新的 .txt 檔案放入 data/rag_source/
# 2. 執行
python scripts/process_rag.py
```

### 新增 PageIndex 文件
```bash
# 1. 將新的 PDF 檔案放入 data/file/
# 2. 執行
python scripts/process_pageindex.py
```

### 清除所有 RAG 資料
```bash
cd docker
docker-compose down
rm -rf ../data/qdrant_data/*
docker-compose up -d
# 重新執行 process_rag.py
```

### 清除 PageIndex 索引
```bash
rm -rf data/pageindex_indices/*
# 重新執行 process_pageindex.py
```

---

## ❌ 常見問題排除

### 問題 1：無法訪問 http://localhost:8000
**排查步驟：**
```bash
# 檢查容器狀態
docker-compose ps

# 查看後端日誌
docker logs pagerag-backend

# 確認端口未被佔用
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

### 問題 2：API Key 錯誤
**檢查：**
```bash
# 確認 .env 檔案內容
cat .env

# 重新啟動容器
docker-compose restart backend
```

### 問題 3：Qdrant 連線失敗
```bash
# 確認 Qdrant 運行中
docker logs pagerag-qdrant

# 測試連線
curl http://localhost:6333/collections
```

### 問題 4：PageIndex 處理失敗
**常見原因：**
- API Key 未設定
- PDF 檔案損壞
- 網路問題（無法呼叫 OpenAI）

**解決：**
```bash
# 檢查 .env
grep CHATGPT_API_KEY .env

# 測試 OpenAI 連線
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## 📊 系統架構圖

```
使用者
  ↓
前端 (localhost:8000)
  ↓
FastAPI 後端
  ├─ RAG Service → Qdrant (localhost:6333)
  └─ PageIndex Service → JSON 索引檔案
```

---

## 🎓 進階使用

### 本地開發模式（不使用 Docker）
```bash
# 啟動 Qdrant（需要單獨安裝）
# 或使用 Docker 只跑 Qdrant：
docker run -p 6333:6333 qdrant/qdrant

# 啟動 FastAPI（熱重載）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 修改後端代碼後重新部署
```bash
cd docker
docker-compose down
docker-compose up --build -d
```

---

## ✅ 快速啟動檢查清單

第一次使用：
- [ ] 設定 `.env` API Key
- [ ] 建立虛擬環境 `venv`
- [ ] 安裝套件 `pip install -r requirements.txt`
- [ ] 啟動 Docker `docker-compose up -d`
- [ ] 上傳資料到 `data/rag_source/` 或 `data/file/`
- [ ] 執行資料處理腳本
- [ ] 訪問 http://localhost:8000

日常使用：
- [ ] 啟動虛擬環境
- [ ] 啟動 Docker `docker-compose up -d`
- [ ] 訪問 http://localhost:8000

---

若有其他問題，請檢查日誌檔案或查閲專案 Issue。
