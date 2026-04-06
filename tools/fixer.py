import re
import subprocess
import tempfile
import os

def apply_fix(original_code: str, issue: dict) -> str:
    issue_type = issue.get('type', '').lower()
    if 'sql' in issue_type:
        return _fix_sql(original_code)
    elif 'secret' in issue_type:
        return _fix_secret(original_code)
    elif 'style' in issue_type:
        return _fix_style(original_code, issue)
    elif 'performance' in issue_type:
        return _fix_performance(original_code, issue)
    elif 'security' in issue_type:
        return _fix_security(original_code, issue)
    else:
        return original_code + "\n# FIXME: 请手动修复"

def verify_fix(original_code: str, fixed_code: str, file_ext: str = ".py") -> dict:
    # 语法验证
    try:
        compile(fixed_code, "<string>", "exec")
        syntax_ok = True
    except SyntaxError as e:
        return {"success": False, "error": f"语法错误: {e}"}
    # 可选：运行单元测试（需要用户提供测试命令）
    return {"success": True, "syntax_valid": True}

def _fix_sql(code: str) -> str:
    return re.sub(r'(execute\s*\(\s*["\'])(.*?)(["\']\s*\+)', r'\1\2?\3 # 使用参数化查询', code)

def _fix_secret(code: str) -> str:
    return re.sub(r'(api_key|password)\s*=\s*["\'][^"\']+["\']', r'\1 = os.getenv("\1")', code, flags=re.I)

def _fix_style(code: str, issue: dict) -> str:
    """修复代码风格问题，如缺少文档字符串、行长度等"""
    description = issue.get('description', '').lower()
    suggestion = issue.get('suggestion', '')
    line_num = issue.get('line', 1)

    lines = code.split('\n')
    if line_num <= 0 or line_num > len(lines):
        return code

    line_index = line_num - 1
    line = lines[line_index]

    # 处理缺少模块文档字符串的情况
    if 'missing module docstring' in description:
        # 在文件开头添加模块文档字符串
        docstring = '"""Module docstring."""'
        lines.insert(0, docstring)
        return '\n'.join(lines)

    # 处理行长度过长的情况
    if 'line too long' in description:
        # 简单换行：在最后一个空格处分割
        if len(line) > 100:
            # 尝试在最后一个逗号或空格处分割
            if ',' in line:
                split_point = line.rfind(',', 0, 100)
                if split_point > 0:
                    lines[line_index] = line[:split_point+1] + '\n    ' + line[split_point+1:].lstrip()
            else:
                split_point = line.rfind(' ', 0, 100)
                if split_point > 0:
                    lines[line_index] = line[:split_point] + '\n    ' + line[split_point+1:].lstrip()
        return '\n'.join(lines)

    return code

def _fix_performance(code: str, issue: dict) -> str:
    """修复性能问题，如低效循环、重复计算等"""
    description = issue.get('description', '').lower()
    lines = code.split('\n')

    # 处理低效循环
    if 'inefficient loop' in description:
        # 将 for i in range(len(list)) 改为 for item in list
        for i, line in enumerate(lines):
            if 'for i in range(len(' in line and ')):' in line:
                # 简单替换
                lines[i] = line.replace('for i in range(len(', 'for item in ').replace(')):', '):')
                # 后续可能需要替换循环体内的索引访问，但这里暂不处理
                break

    # 处理重复计算
    if 'repeated computation' in description:
        # 识别重复表达式并提取到变量
        # 这里只做简单演示
        pass

    return '\n'.join(lines)

def _fix_security(code: str, issue: dict) -> str:
    """修复安全问题，如 SQL 注入、硬编码密钥等"""
    # SQL 注入已经在 _fix_sql 中处理
    # 硬编码密钥已经在 _fix_secret 中处理
    # 这里可以处理其他安全问题
    description = issue.get('description', '').lower()

    if 'eval' in description:
        # 将 eval 替换为 ast.literal_eval
        code = re.sub(r'eval\(', 'ast.literal_eval(', code)
        # 确保导入了 ast
        if 'import ast' not in code:
            code = 'import ast\n' + code

    if 'shell injection' in description:
        # 将 shell=True 改为 shell=False
        code = re.sub(r'shell\s*=\s*True', 'shell=False', code, flags=re.IGNORECASE)

    return code