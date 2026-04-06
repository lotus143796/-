import json
import re
import traceback
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

# 尝试从项目根目录导入
try:
    from utils.logger import logger
    from agent.prompts import SYSTEM_PROMPT, get_review_prompt
    from agent.memory import AgentMemory
    from tools import (
        run_linter, run_security_scan, analyze_dependencies,
        analyze_project, search_code, apply_fix
    )
    from scanners.project_scanner import scan_project
    from utils.concurrent import run_parallel
    from utils.cache import get_global_cache
    from tqdm import tqdm
except ImportError:
    # 如果在独立目录中运行，创建模拟导入
    import sys
    import os

    # 添加项目根目录到路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    from utils.logger import logger
    from agent.prompts import SYSTEM_PROMPT, get_review_prompt
    from agent.memory import AgentMemory
    from tools import (
        run_linter, run_security_scan, analyze_dependencies,
        analyze_project, search_code, apply_fix
    )
    from scanners.project_scanner import scan_project
    from utils.concurrent import run_parallel
    from utils.cache import get_global_cache
    from tqdm import tqdm

# 导入我们定义的模式
try:
    from schemas import ReviewReport, Issue, ISSUE_TYPES, SEVERITY_LEVELS
except ImportError:
    # 如果在项目根目录运行，需要不同的导入路径
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from schemas import ReviewReport, Issue, ISSUE_TYPES, SEVERITY_LEVELS


class CodeReviewAgentWithValidation:
    """带有输出约束和自验证的代码审查 Agent"""

    def __init__(self, api_key: str, model: str = "deepseek-chat", max_steps: int = 5):
        logger.info(f"初始化 CodeReviewAgentWithValidation，模型: {model}, 最大步数: {max_steps}")
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model=model,
            temperature=0.2,
        )
        self.max_steps = max_steps
        self.memory = AgentMemory()
        self.steps_log = []

        # 创建输出解析器
        self.output_parser = PydanticOutputParser(pydantic_object=ReviewReport)

        # 修改系统提示词，包含输出格式说明
        self.system_prompt = self._get_system_prompt_with_format()

        logger.debug("CodeReviewAgentWithValidation 初始化完成")

    def _get_system_prompt_with_format(self) -> str:
        """返回包含输出格式约束的系统提示词"""
        format_instructions = self.output_parser.get_format_instructions()

        return f"""
你是一个智能代码审查 Agent，支持多语言（Python, Java, JS, Go, Rust 等）。
你可以使用以下工具：

1. run_linter(file_path, code) - 静态分析（支持多语言）
2. run_security_scan(code) - 安全漏洞扫描
3. analyze_dependencies(code) - 单文件依赖分析
4. analyze_project(repo_path) - 整个项目分析（结构、循环依赖等）
5. search_code(code, pattern) - 正则搜索代码
6. apply_fix(code, issue) - 生成修复补丁

工作流程：
- 先调用 run_linter 获取静态问题
- 调用 run_security_scan 检查安全
- 如果是项目审查，调用 analyze_project
- 综合信息输出 Final Answer（必须严格按照指定 JSON 格式）

输出格式要求：
{format_instructions}

问题类型必须是以下之一：{sorted(ISSUE_TYPES)}
严重程度必须是以下之一：{sorted(SEVERITY_LEVELS)}

每次响应格式：
Thought: ...
Action: tool_name({{"param": "value"}})

或者：
Final Answer: <严格按照上述格式的 JSON>
"""

    def _get_review_prompt_with_format(self, code: str, file_path: str = None) -> str:
        """返回包含格式说明的审查提示词"""
        context = f"文件: {file_path or '未知'}\n\n```\n{code}\n```\n"
        context += "请按顺序使用工具：run_linter → run_security_scan → 输出 Final Answer\n"
        context += "注意：Final Answer 必须严格按照指定的 JSON 格式输出。"
        return context

    # ---------- 单文件审查 ----------
    def run(self, code: str, file_path: str = None, repo_path: str = None) -> Dict[str, Any]:
        logger.info(f"开始单文件审查（带验证），文件: {file_path}, 代码长度: {len(code)} 字符")

        # 检查缓存
        cache = get_global_cache()
        cached = cache.get(code)
        if cached is not None:
            logger.info(f"命中缓存，跳过审查")
            return cached

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self._get_review_prompt_with_format(code, file_path))
        ]
        self.steps_log = []

        try:
            for step in range(self.max_steps):
                logger.debug(f"第 {step+1}/{self.max_steps} 步")
                response = self.llm.invoke(messages)
                response_text = response.content
                self.steps_log.append({"step": step+1, "response": response_text})

                if "Final Answer:" in response_text:
                    logger.info(f"在第 {step+1} 步收到最终答案")

                    # 解析并验证最终答案
                    result = self._parse_and_validate_final_answer(response_text)

                    # 如果验证失败，重试或返回错误
                    if "error" in result:
                        logger.error(f"最终答案验证失败: {result['error']}")
                        # 可以尝试修复或使用默认报告
                        result = self._fallback_report(result['error'])

                    cache.set(code, result)
                    logger.info(f"单文件审查完成，发现问题数: {len(result.get('report', {}).get('issues', []))}")
                    return result

                action = self._parse_action(response_text)
                if not action:
                    messages.append(AIMessage(content=response_text))
                    messages.append(HumanMessage(content="请按照格式继续。"))
                    continue

                logger.debug(f"执行工具: {action['tool']}, 参数: {action.get('params', {})}")
                obs = self._execute_tool(action, code, file_path, repo_path)
                self.memory.add_step(action["tool"], action["params"], obs)
                messages.append(AIMessage(content=response_text))
                messages.append(HumanMessage(content=f"Observation: {obs}"))

            result = self._force_report("达到最大步数")
            cache.set(code, result)
            logger.warning(f"达到最大步数 {self.max_steps}，强制结束")
            return result

        except Exception as e:
            logger.error(f"单文件审查过程中发生异常: {str(e)}")
            logger.error(traceback.format_exc())
            result = self._force_report(f"异常: {str(e)}")
            cache.set(code, result)
            return result

    def _parse_and_validate_final_answer(self, response: str) -> Dict[str, Any]:
        """解析并验证最终答案，确保符合模式"""
        try:
            # 提取 JSON 部分
            json_match = re.search(r'Final Answer:\s*(.*?)$', response, re.DOTALL)
            if not json_match:
                # 尝试直接查找 JSON
                json_match = re.search(r'({.*})', response, re.DOTALL)

            if json_match:
                answer_text = json_match.group(1)

                # 清理可能的代码块标记
                answer_text = re.sub(r'```json\s*', '', answer_text)
                answer_text = re.sub(r'```\s*', '', answer_text)
                answer_text = answer_text.strip()

                # 尝试解析为 JSON
                try:
                    json_data = json.loads(answer_text)
                except json.JSONDecodeError as e:
                    # 尝试修复常见的 JSON 问题
                    logger.warning(f"JSON 解析失败，尝试修复: {e}")
                    answer_text = self._fix_json_format(answer_text)
                    json_data = json.loads(answer_text)

                # 使用 Pydantic 模型验证
                try:
                    report = ReviewReport(**json_data)

                    # 额外验证：确保 issue_type 和 severity 是有效值
                    self._validate_issues(report.issues)

                    logger.info(f"最终答案验证成功，发现 {len(report.issues)} 个问题")

                    return {
                        "report": report.model_dump(),
                        "steps": self.steps_log,
                        "memory": self.memory.get_summary(),
                        "validated": True
                    }

                except Exception as e:
                    logger.error(f"Pydantic 验证失败: {str(e)}")
                    # 尝试修复数据
                    return self._try_fix_and_validate(json_data, str(e))

            # 如果没有找到有效的 JSON，尝试从文本提取
            return self._extract_report_from_text(response)

        except Exception as e:
            logger.error(f"最终答案解析验证过程中异常: {str(e)}")
            return {
                "report": {"summary": f"解析失败: {str(e)}", "issues": []},
                "steps": self.steps_log,
                "memory": self.memory.get_summary(),
                "error": str(e),
                "validated": False
            }

    def _validate_issues(self, issues: List[Issue]) -> None:
        """验证问题列表中的字段值"""
        for i, issue in enumerate(issues):
            # issue_type 验证
            if issue.issue_type not in ISSUE_TYPES:
                logger.warning(f"问题 {i}: issue_type '{issue.issue_type}' 不在允许的集合中")

            # severity 验证
            if issue.severity not in SEVERITY_LEVELS:
                logger.warning(f"问题 {i}: severity '{issue.severity}' 不在允许的集合中")

    def _fix_json_format(self, text: str) -> str:
        """尝试修复常见的 JSON 格式问题"""
        # 修复单引号
        text = text.replace("'", '"')

        # 修复未转义的控制字符
        text = text.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')

        # 修复尾部逗号
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        # 修复缺少引号的属性名
        text = re.sub(r'(\s*)(\w+)(\s*):', r'\1"\2"\3:', text)

        return text

    def _try_fix_and_validate(self, json_data: Dict, error_msg: str) -> Dict[str, Any]:
        """尝试修复数据并重新验证"""
        logger.info(f"尝试修复数据并重新验证: {error_msg}")

        try:
            # 尝试修复常见问题
            if "issues" in json_data and isinstance(json_data["issues"], list):
                for issue in json_data["issues"]:
                    # 确保 issue_type 和 severity 是小写
                    if "issue_type" in issue and isinstance(issue["issue_type"], str):
                        issue["issue_type"] = issue["issue_type"].lower()
                    if "severity" in issue and isinstance(issue["severity"], str):
                        issue["severity"] = issue["severity"].lower()

            # 尝试重新验证
            report = ReviewReport(**json_data)
            self._validate_issues(report.issues)

            return {
                "report": report.model_dump(),
                "steps": self.steps_log,
                "memory": self.memory.get_summary(),
                "validated": True,
                "fixed": True
            }

        except Exception as e:
            logger.error(f"修复后验证仍然失败: {str(e)}")
            # 返回一个基本的有效报告
            return self._fallback_report(f"验证失败，使用默认报告: {str(e)}")

    def _extract_report_from_text(self, response: str) -> Dict[str, Any]:
        """从文本响应中提取报告信息"""
        logger.warning("无法从响应中解析 JSON，尝试从文本提取")

        # 这里可以实现从自然语言文本中提取结构化信息的逻辑
        # 目前返回一个默认的报告
        return self._fallback_report("无法解析 JSON 响应")

    def _fallback_report(self, reason: str) -> Dict[str, Any]:
        """返回一个有效的默认报告"""
        default_report = ReviewReport(
            summary=f"分析完成（{reason}）",
            issues=[],
            overall_risk="low"
        )

        return {
            "report": default_report.model_dump(),
            "steps": self.steps_log,
            "memory": self.memory.get_summary(),
            "validated": True,
            "fallback": True,
            "fallback_reason": reason
        }

    # ---------- 批量项目审查 ----------
    def run_on_project(self, project_path: str, extensions: List[str] = None) -> Dict[str, Any]:
        """审查整个文件夹，返回汇总报告（带验证）"""
        logger.info(f"开始项目审查（带验证），路径: {project_path}, 扩展名: {extensions}")

        # 检查缓存
        cache = get_global_cache()
        ext_key = json.dumps(extensions) if extensions else ""
        key_data = f"{project_path}:{ext_key}"
        cached = cache.get(key_data)
        if cached is not None:
            logger.info(f"项目缓存命中，跳过审查")
            return cached

        try:
            files = scan_project(project_path, extensions)
            if not files:
                logger.warning(f"未找到任何代码文件: {project_path}")
                return {"error": "未找到任何代码文件"}

            logger.info(f"找到 {len(files)} 个文件，开始并发分析")

            # 并发分析每个文件
            def analyze_one(file_info):
                file_path = file_info["path"]
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    result = self.run(code, file_path=file_path, repo_path=project_path)
                    return {"file": file_path, "result": result}
                except Exception as e:
                    logger.error(f"分析文件失败: {file_path}, 错误: {str(e)}")
                    return {"file": file_path, "error": str(e)}

            results = run_parallel(analyze_one, files, max_workers=4, desc="分析文件中")

            # 汇总报告（带验证）
            all_issues = []
            success_count = 0
            error_count = 0
            validated_count = 0

            for r in results:
                if "error" in r:
                    error_count += 1
                    continue

                success_count += 1
                result_data = r.get("result", {})
                report = result_data.get("report", {})
                issues = report.get("issues", [])

                # 标记已验证的报告
                if result_data.get("validated", False):
                    validated_count += 1

                for issue in issues:
                    issue["file"] = r["file"]
                    all_issues.append(issue)

            # 额外执行项目级分析
            project_analysis = analyze_project(project_path)

            result = {
                "summary": f"审查完成，共 {len(files)} 个文件，成功分析 {success_count} 个（{validated_count} 个已验证），失败 {error_count} 个，发现 {len(all_issues)} 个问题",
                "files_analyzed": len(files),
                "success_count": success_count,
                "validated_count": validated_count,
                "error_count": error_count,
                "issues": all_issues,
                "project_analysis": project_analysis,
                "per_file_results": results
            }

            cache.set(key_data, result)
            logger.info(f"项目审查完成: {result['summary']}")
            return result

        except Exception as e:
            logger.error(f"项目审查过程中发生异常: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"项目审查失败: {str(e)}", "traceback": traceback.format_exc()}

    # ---------- 辅助方法（从原版继承）----------
    def _parse_action(self, response: str) -> Optional[Dict]:
        pattern = r'Action:\s*(\w+)\s*\(\s*({.*?})\s*\)'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            tool_name = match.group(1)
            try:
                params = json.loads(match.group(2))
            except:
                try:
                    params = eval(match.group(2))
                except:
                    params = {}
            return {"tool": tool_name, "params": params}
        return None

    def _execute_tool(self, action: Dict, code: str, file_path: str, repo_path: str) -> str:
        tool_name = action["tool"]
        params = action.get("params", {})

        logger.debug(f"_execute_tool: {tool_name} with params {params}")

        tools_map = {
            "run_linter": lambda: run_linter(params.get("file_path", file_path), code),
            "run_security_scan": lambda: run_security_scan(code),
            "analyze_dependencies": lambda: analyze_dependencies(code),
            "analyze_project": lambda: analyze_project(repo_path or "."),
            "search_code": lambda: search_code(code, params.get("pattern", "")),
            "apply_fix": lambda: apply_fix(code, params.get("issue", {})),
        }

        if tool_name in tools_map:
            try:
                result = tools_map[tool_name]()
                logger.debug(f"工具 {tool_name} 执行成功，结果长度: {len(result)} 字符")
                return result
            except Exception as e:
                error_msg = f"工具执行失败: {str(e)}"
                logger.error(f"工具 {tool_name} 执行失败: {str(e)}")
                logger.error(traceback.format_exc())
                return error_msg
        else:
            error_msg = f"未知工具: {tool_name}"
            logger.warning(f"未知工具: {tool_name}")
            return error_msg

    def _force_report(self, reason: str) -> Dict[str, Any]:
        logger.warning(f"强制生成报告: {reason}")

        # 使用有效的默认报告
        default_report = ReviewReport(
            summary=f"分析未完成：{reason}",
            issues=[],
            overall_risk="medium"
        )

        return {
            "report": default_report.model_dump(),
            "steps": self.steps_log,
            "error": reason,
            "validated": True,
            "forced": True
        }

    def visualize_steps(self) -> str:
        output = []
        for step in self.steps_log:
            output.append(f"## Step {step['step']}\n{step['response']}\n" + "-"*40)
        return "\n".join(output)
# 在文件末尾添加别名
CodeReviewAgent = CodeReviewAgentWithValidation