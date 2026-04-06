import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def build_dependency_graph(files: List[dict]) -> Dict[str, Set[str]]:
    """构建文件之间的依赖图（基于 import 语句）"""
    graph = defaultdict(set)
    for file_info in files:
        path = file_info["rel_path"]
        ext = file_info["extension"]
        try:
            with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        imports = extract_imports(content, ext)
        for imp in imports:
            # 简单映射：将模块名映射到可能的文件路径
            target_file = imp.replace(".", "/") + ext
            if target_file in [f["rel_path"] for f in files]:
                graph[path].add(target_file)
    return graph

def extract_imports(content: str, ext: str) -> List[str]:
    patterns = {
        ".py": r'^(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
        ".java": r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*);',
        ".js": r'^import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
        ".go": r'^import\s+"([^"]+)"',
    }
    pattern = patterns.get(ext, r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)')
    matches = re.findall(pattern, content, re.MULTILINE)
    return [m.split('.')[0] for m in matches]

def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """检测循环依赖（简单 DFS）"""
    visited = set()
    stack = set()
    cycles = []

    def dfs(node, path):
        if node in stack:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        stack.add(node)
        for neighbor in graph.get(node, []):
            dfs(neighbor, path + [node])
        stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])
    return cycles