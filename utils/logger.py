"""
日志配置模块
基于 loguru 的日志配置，支持轮转和分级输出。
"""

import sys
from pathlib import Path
from loguru import logger

# 项目根目录（向上四级：utils -> code_review_improvements -> code_review_improvements -> project_root）
project_root = Path(__file__).parent.parent.parent.parent
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

# 日志文件路径
log_file = log_dir / "code_review.log"

# 移除默认配置
logger.remove()

# 控制台输出（仅 INFO 及以上级别）
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# 文件输出（DEBUG 及以上级别，轮转配置）
logger.add(
    log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="DEBUG",
    rotation="10 MB",          # 每个日志文件最大 10MB
    retention=5,               # 保留最近 5 个文件
    compression="zip",         # 压缩旧日志
    encoding="utf-8",
    backtrace=True,            # 记录异常堆栈
    diagnose=True,             # 诊断信息
)

# 记录配置信息
logger.info(f"日志系统已配置，日志文件: {log_file}")
logger.debug(f"项目根目录: {project_root}")

# 导出 logger 实例
__all__ = ["logger"]