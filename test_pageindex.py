import asyncio
import sys
import os

# 確保能讀取到 app 目錄
sys.path.append(os.getcwd())

from app.services.pageindex_service import query

async def test():
    question = "台積電的應收票據及帳款淨額是多少？"
    print(f"🚀 正在發送問題: {question}")
    
    answer, sources = await query(question)
    
    print("\n" + "="*50)
    print(f"回答內容:\n{answer}")
    print(f"\n來源文件: {sources}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test())