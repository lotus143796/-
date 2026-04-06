#!/usr/bin/env python3
"""
CLI工具：代码审查智能体
支持单文件或整个项目的代码审查，输出JSON格式报告。
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到sys.path，以便导入模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from agent.core import CodeReviewAgent
except ModuleNotFoundError as e:
    print(f"导入模块失败：{e}")
    print("请确保已安装所需依赖：pip install -r requirements.txt")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="代码审查智能体 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 审查单个文件，输出到控制台
  python cli.py --path /path/to/file.py

  # 审查整个项目，保存结果到文件
  python cli.py --path /path/to/project --output report.json

  # 指定API密钥和模型
  python cli.py --path /path/to/file.py --api-key sk-xxx --model deepseek-chat

  # 从环境变量读取API密钥（DEEPSEEK_API_KEY）
  export DEEPSEEK_API_KEY=sk-xxx
  python cli.py --path /path/to/file.py
"""
    )
    parser.add_argument(
        "--path",
        required=True,
        help="要审查的文件或目录路径",
    )
    parser.add_argument(
        "--output",
        help="输出JSON文件路径（可选，默认输出到控制台）",
    )
    parser.add_argument(
        "--mode",
        choices=["single", "project"],
        help="审查模式：single（单文件）或 project（整个项目）。若不指定，则根据路径自动判断（文件→single，目录→project）",
    )
    parser.add_argument(
        "--api-key",
        help="DeepSeek API密钥。若不提供，则从环境变量 DEEPSEEK_API_KEY 读取",
    )
    parser.add_argument(
        "--model",
        default="deepseek-chat",
        help="模型名称（默认：deepseek-chat）",
    )

    args = parser.parse_args()

    # 确定API密钥
    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误：未提供API密钥。请通过 --api-key 参数或环境变量 DEEPSEEK_API_KEY 设置。", file=sys.stderr)
        return 1

    # 检查路径是否存在
    path = Path(args.path).absolute()
    if not path.exists():
        print(f"错误：路径不存在：{path}", file=sys.stderr)
        return 1

    # 自动判断模式
    if args.mode:
        mode = args.mode
    else:
        mode = "single" if path.is_file() else "project"

    # 创建审查智能体
    try:
        agent = CodeReviewAgent(api_key=api_key, model=args.model)
    except Exception as e:
        print(f"创建审查智能体失败：{e}", file=sys.stderr)
        return 1

    # 执行审查
    try:
        if mode == "single":
            if not path.is_file():
                print(f"错误：单文件模式需要文件路径，但提供的是目录：{path}", file=sys.stderr)
                return 1
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            result = agent.run(code, file_path=str(path))
        else:  # project mode
            if not path.is_dir():
                print(f"错误：项目模式需要目录路径，但提供的是文件：{path}", file=sys.stderr)
                return 1
            result = agent.run_on_project(str(path))
    except Exception as e:
        print(f"审查过程出错：{e}", file=sys.stderr)
        return 1

    # 输出结果
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(f"审查结果已保存至：{output_path}")
        except Exception as e:
            print(f"写入输出文件失败：{e}", file=sys.stderr)
            return 1
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())