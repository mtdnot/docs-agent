import os
import re
from dotenv import load_dotenv
from github_loader import all_docs
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

load_dotenv()

dev_dir_root = "/home/ubuntu/dev/work/mcp-router/src/components/"

# 文書を分割
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
split_docs = splitter.split_documents(all_docs)

# TSXファイルからルート定義ファイルを探索
def find_possible_routes(base_dir):
    routes = set()
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".tsx"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "<Route" in content or "useRoutes(" in content or "createBrowserRouter" in content:
                    routes.add(path)
    return routes

# App.tsxからルートコンポーネント抽出
def extract_routed_components_from_app(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    route_targets = set()
    route_pattern = re.compile(r"element=\{<([A-Z]\w*)")
    for match in route_pattern.finditer(content):
        component_name = match.group(1)
        route_targets.add(component_name)

    return route_targets

# コンポーネント名からファイルパスを特定
def resolve_component_to_file(component_name, search_root=dev_dir_root):
    for root, _, files in os.walk(search_root):
        for file in files:
            if file.endswith(".tsx") and file.removesuffix(".tsx").endswith(component_name):
                return os.path.join(root, file)
    return None

print("--- DEBUGGING ---")

# ルートファイルを探す
possible_routes = find_possible_routes(dev_dir_root)
print(f"Found {len(possible_routes)} route files: {possible_routes}")
# routed_components抽出
routed_components = set()
for route_file in possible_routes:
    routed_components.update(extract_routed_components_from_app(route_file))
print(f"Found {len(routed_components)} component names: {routed_components}")
# ファイルパスに変換
routed_files = set()
for comp in routed_components:
    path = resolve_component_to_file(comp)
    if path:
        routed_files.add(path)
routed_files.update(possible_routes)  # ルート定義ファイルも対象
print(f"Resolved {len(routed_files)} file paths: {routed_files}")

# short_path をまとめてセットにする（全ファイル分）
short_paths = {
    re.sub(r"^/home/ubuntu/dev/work/mcp-router/", "", full_path)
    for full_path in routed_files
}
for short_path in short_paths:
    print(f"short_path: {short_path}")

# 対象ページを絞り込み

page_docs = [
    (doc.metadata["path"], doc)
    for doc in split_docs
    if doc.metadata.get("path", "") in short_paths
]

print(f"Number of page_docs: {len(page_docs)}")

print("page_docsパス一覧:")
for path, _ in page_docs:
    print("-", path)

from collections import defaultdict


# ベクトルDB作成
#vectordb = Chroma.from_documents([doc for (_, doc) in page_docs], OpenAIEmbeddings(), persist_directory="vectorstore")
#vectordb = Chroma.from_documents(split_docs, OpenAIEmbeddings(), persist_directory="vectorstore")
#vectordb = Chroma(
#    persist_directory="vectorstore",
#    embedding_function=OpenAIEmbeddings()
#)
#
vectordb = Chroma.from_documents(
    [doc for (_, doc) in page_docs],
    OpenAIEmbeddings(),
    persist_directory="vectorstore"
)


# Retriever + LLM
retriever = vectordb.as_retriever(search_kwargs={"k": 5})
llm = ChatOpenAI(model="gpt-4", temperature=0.4)
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)


# ================
# ユーザー向けドキュメント（1ページ1ファイル）
# ================

user_doc_prompt = """以下のコードは、MCP-RouterのあるUIコンポーネント（React）に対応する実装です。
このコードから、「ユーザー向けのドキュメント」に掲載する章の本文を生成してください。
対象はエンドユーザーであり、彼らがこの機能をどう使うかや、何ができるのかに関心があります。
内部の実装や開発者向けの情報ではなく、「どう役立つか」「どう使うか」に焦点を当ててください。
文章は300〜400字程度で、口調はフラットで説明的、ドキュメント的にしてください。"""

output_dir = "output/docs/tsx"
os.makedirs(output_dir, exist_ok=True)

# pathごとにチャンクをまとめる
grouped_docs = defaultdict(list)

for path, doc in page_docs:
    grouped_docs[path].append(doc)
print(f"grouped_docs 件数: {len(grouped_docs)}")
# 各ページに対して要約生成
for path, docs in grouped_docs.items():
    print(path)
    component_name = os.path.splitext(os.path.basename(path))[0]
    query = user_doc_prompt
    #print(docs)

    
    # チャンク内容を結合して確認
    joined_text = "\n".join(doc.page_content for doc in docs)

    # ★ チャンクの内容を目視確認（ここ追加）★
    print(f"\n==== {component_name} チャンク全体（{len(joined_text)}文字） ====\n")
    print(joined_text[:1000])  # 長すぎると大変なので先頭1000文字くらいでOK
    print("\n========================================\n")
    
    if len(joined_text.strip()) < 100:
        print(f"⚠️ Skipping {component_name}: 内容が少なすぎる")
        continue

    from langchain.chains.question_answering import load_qa_chain

    llm = ChatOpenAI(model="gpt-4", temperature=0.4)
    qa_chain = load_qa_chain(llm, chain_type="stuff")

    # あとはページごとに
    result = qa_chain.run(input_documents=docs, question=query)

    
#    result_raw = qa_chain.invoke({
#        "query": query,
#        "input_documents": docs
#    })
    
#    result = result_raw["result"]

    # エラー時のフォールバック
    if not result.strip() or "わかりません" in result or "提供されていない" in result:
        result = "この機能の説明は現在準備中です。後日更新予定です。"

    print(f"file:{component_name}")
    print(f"result:{result}")    
    with open(os.path.join(output_dir, f"{component_name}.md"), "w", encoding="utf-8") as f:
        f.write(f"# {component_name}\n\n{result}")

print("ユーザー向けドキュメント生成完了（output/docs/tsx）")

'''

# TOC 読み込み
with open("output/toc.md", "r", encoding="utf-8") as f:
    toc_lines = f.readlines()

# セクション抽出
sections = []
for line in toc_lines:
    if line.startswith("## "):
        sections.append(line.strip("#\n ").strip())
    elif re.match(r"^\s*-\s+\[.+\]\(.+\)", line):
        match = re.match(r"^\s*-\s+\[(.+?)\]\(.+\)", line)
        if match:
            sections.append(match.group(1))

# 生成
os.makedirs("output/sections", exist_ok=True)
for section in sections:
    if not section:
        continue
    Print(f" セクション: {section}")
    result = qa_chain.invoke(f"『{section}』について、製品MCP-Routerに即して、利用者の視点から必要な情報のみを簡潔に説明してください（200字以内）")
    with open(f"output/sections/{section.replace('/', '_')}.md", "w", encoding="utf-8") as f:
        f.write(f"## {section}\n\n{result}")

print("全章の本文生成が完了しました。output/sections/ に出力されています。")
'''
