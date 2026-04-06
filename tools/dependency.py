import ast
def analyze_dependencies(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"语法错误: {e}"
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return f"依赖: {', '.join(imports) if imports else '无'}"