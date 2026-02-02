# PageRAG - 可對話型 AI 應用平台操作指南

本專案是一個AI 對話平台，具備「一般文件檢索 (RAG)」與「特定文件查找 (PageIndex)」功能。

## 🚀 快速開始

**首次使用者**，請參考 **[SOP.md](SOP.md)** 完整啟動標準作業程序。

**已完成設定的使用者**，快速啟動：
```bash
source venv/bin/activate        # 啟動虛擬環境
cd docker && docker-compose up -d  # 啟動服務
# 訪問 http://localhost:8000
```

---

以下是完整的操作步驟流程。

## 1. 初始環境設定 (只需做一次)

在開始之前，請確保您的 `.env` 檔案已設定好。

1. **複製設定檔範本**：
   ```bash
   cp .env.example .env
   ```
2. **編輯 `.env`**：
   打開 `.env` 檔案，填入您的 OpenAI API Key：
   ```text
   OPENAI_API_KEY=sk-proj-xxxxxxxx...
   CHATGPT_API_KEY=sk-proj-xxxxxxxx...  # PageIndex 使用此變數名稱
   ```
   > **重要**：PageIndex 使用 `CHATGPT_API_KEY`，請填入與 `OPENAI_API_KEY` 相同的值。

3. **建立與啟動虛擬環境**

   **Mac / Linux**:
   ```bash
   # 建立 venv
   python3 -m venv venv
   
   # 啟動 venv
   source venv/bin/activate
   ```

   **Windows**:
   ```powershell
   # 建立 venv
   python -m venv venv
   
   # 啟動 venv
   .\venv\Scripts\activate
   ```

4. **安裝相依套件** (確保虛擬環境已啟動):
   ```bash
   pip install -r requirements.txt
   ```

---

## 2. 啟動基礎設施 (Docker)

為了讓資料處理腳本可以將資料存入資料庫，我們必須**先啟動 Qdrant 資料庫**。

請執行以下指令啟動 Docker 容器（包含後端與 Qdrant 資料庫）：

```bash
cd docker
docker-compose up --build -d
```

> **注意**：
> *   `--build`：確保會重新建置最新的 Docker Image。
> *   `-d`：在背景執行。
> *   執行後，Qdrant 資料庫會在 `localhost:6333` 運行，後端網站會在 `localhost:8000` 運行。

---

## 3. 資料準備與預處理 (RAG & PageIndex)

### A. 一般文件檢索 (RAG) - 使用 Qdrant
這個功能是用來回答「基於大量公開資訊」的問題。

1.  **準備資料**：
    *   去公開資訊觀測站或其他來源下載 `.txt` 文字檔。
    *   將檔案放入專案根目錄下的 **`data/rag_source/`** 資料夾中。
    
2.  **執行處理腳本**：
    *   確保 Docker (Qdrant) 已經在運行中 (步驟 2)。
    *   回到專案根目錄，執行以下 Python 指令：
    ```bash
    python scripts/process_rag.py
    ```
    *   **結果**：腳本會讀取資料夾內的檔案，切分文字，轉換成向量，並存入 Qdrant 資料庫中。

### B. 特定文件查找 - 使用 PageIndex
這個功能是用來「精準尋找」特定文件內容（工具箱 -> 找尋文件）。

1.  **準備資料**：
    *   下載您想要被搜尋的 PDF 或文件。
    *   將檔案放入專案根目錄下的 **`data/file/`** 資料夾中。

2.  **執行處理腳本**：
    *   回到專案根目錄，執行以下 Python 指令：
    ```bash
    python scripts/process_pageindex.py
    ```
    *   **結果**：腳本會為檔案建立索引，並儲存在 `data/pageindex_indices/` 中供後端讀取。

---

## 4. 開始使用平台

完成上述步驟後，您的平台已經準備就緒且擁有資料了。

1.  **打開瀏覽器**：
    前往 [http://localhost:8000](http://localhost:8000)

2.  **使用功能**：
    *   **一般聊天**：直接輸入文字。
    *   **RAG 查詢**：如果您的問題與 `data/rag_source` 內的資料有關，AI 會自動透過 LangChain 去 Qdrant 搜尋相關內容回答。
    *   **特定文件查找**：
        1. 點選對話框下方的 "工具" 選單。
        2. 選擇 "Find Documents (PageIndex)"。
        3. 針對您放入 `data/file` 的文件進行提問。

---

## 常見問題

*   **Q: 我新增了新的 RAG 文件，需要重啟 Docker 嗎？**
    *   A: 不需要。只需再次執行 `python scripts/process_rag.py`，新資料就會被加入資料庫。

*   **Q: 我修改了後端程式碼 (`app/` 資料夾)，需要重啟 Docker 嗎？**
    *   A: 需要。請執行 `cd docker && docker-compose restart backend` 來套用程式碼變更。

*   **Q: 如何停止所有服務？**
    *   A: 執行 `cd docker && docker-compose down`。

## 5. 清除資料與重置 (Reset)

如果您想要刪除 Qdrant 內的所有資料，有兩種方式：

### 重置整個資料庫 (最徹底)
由於我們在 `docker-compose.yml` 中使用了 Volume 將資料掛載到本地的 `data/qdrant_data` 資料夾，僅僅刪除 Container **不會** 刪除資料。

要完全重置，請執行以下步驟：

1.  停止容器：
    ```bash
    cd docker
    docker-compose down
    ```
2.  刪除本地的資料庫檔案：
    ```bash
    # 回到專案根目錄
    rm -rf data/qdrant_data/*
    ```
3.  重新啟動容器：
    ```bash
    cd docker
    docker-compose up -d
    ```
    此時您的 Qdrant 就是全新的，裡面沒有任何資料。
