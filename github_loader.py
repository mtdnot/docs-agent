from github import Github
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()

token = os.environ["GITHUB_TOKEN"]
repo_name = os.environ["GITHUB_REPOSITORY"]

g = Github(token)
repo = g.get_repo(repo_name)
contents = repo.get_contents("")

all_docs = []

max_attempts = 5
attempt = 0

while contents:
#while contents and attempt < max_attempts:
#    attempt += 1
    file_content = contents.pop(0)
    if file_content.type == "dir":
        contents.extend(repo.get_contents(file_content.path))
    else:
        if file_content.path.endswith((".tsx")):
#        if file_content.path.endswith((".md", ".ts", ".tsx", ".jsx", ".html", ".json")):
            print(f"checking {file_content.path}...")
            decoded = file_content.decoded_content.decode("utf-8")
            doc = Document(page_content=decoded, metadata={"path": file_content.path})
            all_docs.append(doc)

# all_docs に必要な Document が全部入ってる状態
print(f"Documents count: {len(all_docs)}")
