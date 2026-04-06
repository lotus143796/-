import re

def run_security_scan(code: str) -> str:
    vulns = []
    # SQL注入
    if re.search(r'execute\s*\(\s*["\'].*?\+', code, re.I) or re.search(r'execute\s*\(\s*f["\'].*?\{', code, re.I):
        vulns.append(("HIGH", "SQL Injection", "动态拼接SQL", "使用参数化查询"))
    # 硬编码密钥
    if re.search(r'(api_key|password|secret|token)\s*=\s*["\'][^"\']+["\']', code, re.I):
        vulns.append(("CRITICAL", "Hardcoded Secret", "密钥硬编码", "使用环境变量"))
    # 命令注入
    if re.search(r'os\.system\s*\(.*?\+', code, re.I) or re.search(r'subprocess\.(call|run).*shell=True', code, re.I):
        vulns.append(("HIGH", "Command Injection", "命令注入风险", "避免 shell=True"))
    # eval
    if re.search(r'eval\s*\(', code):
        vulns.append(("HIGH", "Unsafe Eval", "eval 使用", "使用 ast.literal_eval"))
    if not vulns:
        return "安全扫描未发现明显漏洞"
    output = ["=== 安全漏洞报告 ==="]
    for sev, typ, desc, fix in vulns:
        output.append(f"[{sev}] {typ}: {desc} -> 建议: {fix}")
    return "\n".join(output)