import os
import re
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0.4)

# プロンプト読み込み
with open("prompts/writer_prompt.txt", "r", encoding="utf-8") as f:
    template = f.read()

prompt = PromptTemplate.from_template(template)
chain = prompt | llm

# 目次ファイル読み込み
with open("output/toc.md", "r", encoding="utf-8") as f:
    toc_lines = f.readlines()

# 正規表現で章タイトル抽出（例：1. [はじめに](#introduction)）
section_titles = []
for line in toc_lines:
    match = re.match(r"\d+\.\s+\[([^\]]+)\]", line)
    if match:
        section_titles.append(match.group(1))

# 各セクションに対して本文生成
output_text = "# MCP-Router ドキュメント\n\n"

for title in section_titles:
    print(f"⏳ 生成中: {title}...")
    inputs = {
        "section_title": title,
        "purpose": f"{title} に関する技術的な説明をMarkdown形式で書いてください"
    }
    result = chain.invoke(inputs)
    output_text += result.content + "\n\n"

# 保存
os.makedirs("output", exist_ok=True)
with open("output/from_toc_document.md", "w", encoding="utf-8") as f:
    f.write(output_text)

print("✅ 全セクション生成完了：output/from_toc_document.md をチェック！")
