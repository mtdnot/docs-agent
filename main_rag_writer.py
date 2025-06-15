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
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
split_docs = splitter.split_documents(all_docs)

# TSXファイルからルート定義ファイルを探索
def find_possible_routes(base_dir):
    routes = set()
    for root, _, files in os.walk(base_dir):
        print("root:{root},{files}")
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

for full_path in routed_files:
    short_path = re.sub(r"^/home/ubuntu/dev/work/mcp-router/", "", full_path)
    print(f"short_path:{short_path}")
# 対象ページを絞り込み

page_docs = [doc for doc in split_docs if doc.metadata.get("path", "") in short_path]
print(f"Number of page_docs: {len(page_docs)}")
# ベクトルDB作成
vectordb = Chroma.from_documents(page_docs, OpenAIEmbeddings(), persist_directory="vectorstore")

# Retriever + LLM
retriever = vectordb.as_retriever(search_kwargs={"k": 5})
llm = ChatOpenAI(model="gpt-4", temperature=0.4)
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

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
    print(f" セクション: {section}")
    result = qa_chain.invoke(f"『{section}』について、製品MCP-Routerに即して、利用者の視点から必要な情報のみを簡潔に説明してください（200字以内）")
    with open(f"output/sections/{section.replace('/', '_')}.md", "w", encoding="utf-8") as f:
        f.write(f"## {section}\n\n{result}")

print("全章の本文生成が完了しました。output/sections/ に出力されています。")
