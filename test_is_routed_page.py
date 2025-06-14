from github_loader import all_docs
import os

def find_possible_routes(base_dir):
    routes = set()
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".tsx"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "<Route" in content or "useRoutes(" in content or "createBrowserRouter" in content:
                    routes.add(os.path.relpath(path).replace("\\", "/"))
    return routes

possible_route_files = find_possible_routes(".")

def is_routed_page(doc):
    path = doc.metadata.get("path", "")
    return path in possible_route_files or "App.tsx" in path

# 検証用出力
routed = [doc.metadata["path"] for doc in all_docs if is_routed_page(doc)]

print("✅ routed pages:")
for path in routed:
    print(" -", path)
