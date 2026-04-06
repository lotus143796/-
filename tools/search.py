import re
def search_code(code: str, pattern: str) -> str:
    try:
        matches = re.findall(pattern, code, re.IGNORECASE)
        if matches:
            return f"找到 {len(matches)} 处匹配:\n" + "\n".join(matches[:10])
        return "未找到匹配"
    except Exception as e:
        return f"正则错误: {e}"