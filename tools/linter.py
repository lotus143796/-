# tools/linter.py
import subprocess
import tempfile
import os
import re
from typing import Optional

def detect_language(code: str, file_path: str = None) -> str:
    """自动检测代码语言"""
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust',
            '.cpp': 'cpp', '.c': 'cpp', '.h': 'cpp'
        }
        if ext in lang_map:
            return lang_map[ext]
    # 基于内容检测
    if re.search(r'def\s+\w+\s*\(', code):
        return 'python'
    if re.search(r'function\s+\w+\s*\(', code) or re.search(r'const\s+\w+\s*=', code):
        return 'javascript'
    if re.search(r'public\s+class\s+\w+', code):
        return 'java'
    if re.search(r'func\s+\w+\s*\(', code):
        return 'go'
    return 'unknown'

def run_linter(file_path: Optional[str], code: str) -> str:
    lang = detect_language(code, file_path)
    if lang == 'python':
        return _run_pylint(code, file_path)
    elif lang == 'javascript':
        return _run_eslint(code, file_path)
    elif lang == 'java':
        return "Java 静态分析需要安装 checkstyle，暂未集成。"
    else:
        return _basic_analysis(code)

def _run_pylint(code: str, file_path: Optional[str]) -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    try:
        result = subprocess.run(
            ['pylint', temp_path, '--output-format=text',
             '--msg-template="{path}:{line}:{column}: {msg_id} {msg}"'],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout
        if result.returncode not in (0, 32):
            output += f"\n[WARN] {result.stderr}"
        return output if output.strip() else "pylint 未发现问题"
    except Exception as e:
        return f"pylint 执行失败: {str(e)}"
    finally:
        os.unlink(temp_path)

def _run_eslint(code: str, file_path: Optional[str]) -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(code)
        temp_path = f.name
    try:
        result = subprocess.run(
            ['npx', 'eslint', temp_path, '--format', 'compact'],
            capture_output=True, text=True, timeout=30, shell=True
        )
        return result.stdout if result.stdout.strip() else "eslint 未发现问题"
    except Exception as e:
        return f"eslint 执行失败: {str(e)}"
    finally:
        os.unlink(temp_path)

def _basic_analysis(code: str) -> str:
    issues = []
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        if len(line) > 100:
            issues.append(f"Line {i}: 行长度超过 100 字符")
        if line.strip().startswith('#') and 'TODO' in line:
            issues.append(f"Line {i}: 发现 TODO 注释")
        if 'print(' in line and not line.strip().startswith('#'):
            issues.append(f"Line {i}: 发现 print 语句，建议使用 logging")
    return "\n".join(issues) if issues else "基础分析未发现明显问题"