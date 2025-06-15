import os
import re
from dotenv import load_dotenv
from github_loader import all_docs
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

load_dotenv()

# TSXファイルからルート定義ファイルを探索
def find_possible_routes(base_dir):
    routes = set()
    print("checking files")
    for root, _, files in os.walk("./components/src/"):
        print(f"root:{root},{files}")
        for file in files:
            if file.endswith(".tsx"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "<Route" in content or "useRoutes(" in content or "createBrowserRouter" in content:
                    routes.add(path)
    return routes

# ルートファイルを探す
possible_routes = find_possible_routes("./src/components/")
print(f"Found {len(possible_routes)} route files: {possible_routes}")
