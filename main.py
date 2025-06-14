import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI  # ← 最新推奨
from langchain_core.runnables import RunnableSequence

load_dotenv()

# LLMインスタンス
llm = ChatOpenAI(model="gpt-4", temperature=0.3)

# プロンプト準備
with open("prompts/structure_prompt.txt", "r", encoding="utf-8") as f:
    template = f.read()

prompt = PromptTemplate.from_template(template)

# パイプ構成（Prompt → LLM）
chain = prompt | llm

# 入力
inputs = {
    "product_name": "MCP-Router",
    "description": "複数のMCPサーバーを一元管理できるデスクトップアプリケーション。AIエージェントの統合にも対応。",
    "audience": "LLM開発者、AIツール統合に関心のある技術者"
}

# 実行
result = chain.invoke(inputs)

# 結果保存
os.makedirs("output", exist_ok=True)
with open("output/toc.md", "w", encoding="utf-8") as f:
    f.write(result.content)

print("✅ 目次生成完了：output/toc.md を見てね")
