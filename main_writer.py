import os
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

# テスト用入力（他のセクションに変えてもOK）
inputs = {
    "section_title": "MCPサーバーの一元管理",
    "purpose": "複数のMCPサーバーをGUI上で管理する方法について説明する"
}

result = chain.invoke(inputs)

# 保存
os.makedirs("output", exist_ok=True)
with open("output/server_management.md", "w", encoding="utf-8") as f:
    f.write(result.content)

print("✅ 本文生成完了：output/server_management.md を見てね")
