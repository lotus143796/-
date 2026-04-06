import os
from pathlib import Path
from typing import List, Optional

DEFAULT_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".rb", ".php"
}
EXCLUDE_DIRS = {
    "venv", "env", "__pycache__", ".git", "node_modules", "dist", "build", "target", ".idea", ".vscode"
}

def scan_project(root_path: str, extensions: List[str] = None) -> List[dict]:
    """递归扫描项目，返回文件信息列表"""
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS
    root = Path(root_path).resolve()
    files = []
    for path in root.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in extensions:
            rel_path = str(path.relative_to(root))
            files.append({
                "path": str(path),
                "rel_path": rel_path,
                "extension": path.suffix
            })
    return files