import os
import sys
import json
import glob
from typing import Tuple, List, Dict, Any
from dotenv import load_dotenv
import fitz  # PyMuPDF

# Add PageIndex library to path for utility functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib', 'PageIndex'))

from openai import OpenAI

load_dotenv()

INDEX_DIR = "lib/PageIndex/tests/results"
PDF_DIR = "lib/PageIndex/tests/pdfs"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("CHATGPT_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = "gpt-4o-mini"
# OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini") # 改為 gpt-4o-mini 以支援更大 Context

def extract_text_from_pdf(doc_name: str, start_page: int, end_page: int) -> str:
    """從 PDF 文件的特定頁碼範圍提取文字 (1-based index)。"""
    pdf_path = os.path.join(PDF_DIR, f"{doc_name}.pdf")
    if not os.path.exists(pdf_path):
        return ""
    
    try:
        doc = fitz.open(pdf_path)
        text = ""
        # 配合 search.py 的邏輯：1-based 轉 0-based
        start_idx = max(0, start_page - 1)
        end_idx = min(doc.page_count, end_page)
        
        for i in range(start_idx, end_idx):
            text += doc[i].get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"提取 PDF 文字時出錯: {e}")
        return ""

async def query(message: str) -> Tuple[str, List[str]]:
    """
    完全比照 PageIndex/search.py 的四階段查詢邏輯。
    """
    if not OPENAI_API_KEY:
        return "錯誤：找不到 OPENAI_API_KEY 或 CHATGPT_API_KEY。", []
    
    try:
        # 1. 加載文檔結構 (Step 1: Load Structure)
        index_files = glob.glob(os.path.join(INDEX_DIR, "*_structure.json"))
        if not index_files:
            return "找不到索引檔案。請先執行 'python scripts/process_pageindex.py'。", []
        
        indices = {}
        for index_file in index_files:
            doc_name = os.path.basename(index_file).replace("_structure.json", "")
            with open(index_file, 'r', encoding='utf-8') as f:
                indices[doc_name] = json.load(f)

        # 初始化 OpenAI Client
        client_kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL
        client = OpenAI(**client_kwargs)

        # 1.5 文件初選 (如果有多份文件)
        doc_descriptions = "\n".join([f"- {name}" for name in indices.keys()])
        doc_selection_prompt = f"從以下文件中挑選最相關的一個：\n{doc_descriptions}\n問題：{message}\n請直接輸出名稱。"
        
        res = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": doc_selection_prompt}],
            temperature=0
        )
        selected_doc = res.choices[0].message.content.strip()
        if selected_doc not in indices:
            selected_doc = list(indices.keys())[0]

        # 2. 樹搜索階段 (Step 2: Tree Search)
        # 取得該文件的結構
        index_data = indices[selected_doc]
        tree_structure = index_data.get('structure', index_data) if isinstance(index_data, dict) else index_data

        search_prompt = f"""
        You are given a question and a tree structure of a document.
        Each node contains a title and page range (start_index, end_index).
        Your task is to identify the nodes that are most likely to contain the answer to the question.

        Question: {message}

        Document Structure:
        {json.dumps(tree_structure, indent=2, ensure_ascii=False)}

        Please return a JSON object with the following format:
        {{
            "thinking": "繁體中文解釋你的分析邏輯...",
            "relevant_nodes": [
                {{
                    "title": "Node Title",
                    "start_index": <start_page_number>,
                    "end_index": <end_page_number>
                }}
            ]
        }}
        Directly return the JSON only. 務必使用繁體中文進行思考說明。
        """

        search_res = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": search_prompt}],
            temperature=0
        )
        
        raw_search = search_res.choices[0].message.content.strip()
        if "```json" in raw_search:
            raw_search = raw_search.split("```json")[1].split("```")[0]
        elif "```" in raw_search:
            raw_search = raw_search.split("```")[1].split("```")[0]
            
        search_result = json.loads(raw_search)
        nodes = search_result.get("relevant_nodes", [])

        # 3. 內容提取階段 (Step 3: Content Extraction)
        context_text = ""
        for node in nodes:
            start = node.get("start_index")
            end = node.get("end_index")
            title = node.get("title")
            if start is not None and end is not None:
                text = extract_text_from_pdf(selected_doc, start, end)
                context_text += f"\n--- Section: {title} (Pages {start}-{end}) ---\n{text}\n"

        if not context_text:
            return "無法從文件中提取相關內容。", [f"{selected_doc}.pdf"]

        # 4. 答案生成階段 (Step 4: Answer Generation)
        answer_prompt = f"""你是一個專業的分析師。請根據以下提供的上下文內容回答問題。

### 上下文內容：
{context_text}

### 使用者問題：
{message}

### 回答規範：
1. 必須使用繁體中文。
2. 根據提供的內容進行精確回答，列出具體數字和金額。
3. 如果內容中沒有答案，請說不知道。

答案："""

        answer_res = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": answer_prompt}],
            temperature=0
        )
        
        return answer_res.choices[0].message.content, [f"{selected_doc}.pdf"]

    except Exception as e:
        print(f"PageIndex Query Error: {e}")
        return f"查詢出錯：{str(e)}", []


def get_tree_summary(tree: dict) -> str:
    """Extract a summary from the tree structure."""
    if isinstance(tree, dict):
        if 'doc_description' in tree:
            return tree['doc_description']
        if 'title' in tree:
            return tree['title']
    return "Indexed document"
