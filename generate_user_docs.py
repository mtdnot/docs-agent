import os
import re
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

vectordb = Chroma(persist_directory="vectorstore", embedding_function=None)  # Embeddingsは読み込み済みを前提
retriever = vectordb.as_retriever(search_kwargs={"k": 5})
llm = ChatOpenAI(model="gpt-4", temperature=0.4)
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

prompt = """以下のコードは、MCP-RouterのあるUIコンポーネント（React）に対応する実装です。
このコードから、「ユーザー向けのドキュメント」に掲載する章の本文を生成してください。
対象はエンドユーザーであり、彼らがこの機能をどう使うかや、何ができるのかに関心があります。
内部の実装や開発者向けの情報ではなく、「どう役立つか」「どう使うか」に焦点を当ててください。
文章は300〜400字程度で、口調はフラットで説明的、ドキュメント的にしてください。"""

output_dir = "output/docs"
os.makedirs(output_dir, exist_ok=True)

# Chroma に格納されている全ドキュメントパスを取得
docs = vectordb._collection.get(include=["metadatas", "documents"])
paths = [m["path"] for m in docs["metadatas"] if "path" in m]

for path in paths:
    component_name = os.path.splitext(os.path.basename(path))[0]
    query = f"{prompt}\n\nファイル名: {component_name}.tsx"
    result = qa_chain.invoke(query)
    output_path = os.path.join(output_dir, f"{component_name}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {component_name}\n\n{result}")

print("ユーザー向けドキュメント生成が完了しました。")
