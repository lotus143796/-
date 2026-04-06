import os
from scanners.project_scanner import scan_project
from scanners.dep_graph import build_dependency_graph, find_cycles

def analyze_project(project_path: str) -> str:
    files = scan_project(project_path)
    if not files:
        return "未找到代码文件"
    graph = build_dependency_graph(files)
    cycles = find_cycles(graph)
    output = [f"=== 项目分析 ===", f"文件数: {len(files)}"]
    if cycles:
        output.append(f"⚠️ 发现 {len(cycles)} 个循环依赖:")
        for cycle in cycles[:5]:
            output.append(" -> ".join(cycle))
    else:
        output.append("✅ 无循环依赖")
    return "\n".join(output)