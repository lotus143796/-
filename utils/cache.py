import os
import json
import hashlib
import time
from typing import Any, Optional, Union
from pathlib import Path

try:
    import diskcache
    HAS_DISKCACHE = True
except ImportError:
    diskcache = None
    HAS_DISKCACHE = False


class FileHashCache:
    """基于文件 SHA256 哈希的磁盘缓存，使用 diskcache 库，默认有效期 7 天"""

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None, default_ttl: int = 7 * 24 * 3600):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录，默认为 ~/.cache/code_review
            default_ttl: 默认缓存有效期（秒），默认 7 天
        """
        if not HAS_DISKCACHE:
            raise ImportError("diskcache 库未安装，请运行: pip install diskcache")

        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/code_review")

        self.cache_dir = str(cache_dir)
        self.default_ttl = default_ttl
        self._cache = diskcache.Cache(self.cache_dir)

    def _compute_key(self, data: str) -> str:
        """计算数据的 SHA256 哈希作为缓存键"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def get(self, key_data: str) -> Optional[Any]:
        """
        从缓存中获取数据

        Args:
            key_data: 用于生成缓存键的字符串数据（如文件内容）

        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        key = self._compute_key(key_data)
        try:
            cached = self._cache.get(key, default=None)
            if cached is not None:
                return json.loads(cached)
        except Exception:
            pass
        return None

    def set(self, key_data: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        将数据存入缓存

        Args:
            key_data: 用于生成缓存键的字符串数据
            value: 要缓存的值（必须可 JSON 序列化）
            ttl: 缓存有效期（秒），默认使用 default_ttl

        Returns:
            是否成功
        """
        key = self._compute_key(key_data)
        try:
            json_value = json.dumps(value)
            self._cache.set(key, json_value, expire=ttl or self.default_ttl)
            return True
        except Exception:
            return False

    def clear(self) -> int:
        """清除所有缓存，返回删除的条目数"""
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_or_compute(self, key_data: str, compute_func, ttl: Optional[int] = None) -> Any:
        """
        获取缓存数据，如果不存在则计算并缓存

        Args:
            key_data: 用于生成缓存键的字符串数据
            compute_func: 计算数据的函数（无参数）
            ttl: 缓存有效期（秒）

        Returns:
            缓存或新计算的数据
        """
        cached = self.get(key_data)
        if cached is not None:
            return cached

        result = compute_func()
        self.set(key_data, result, ttl=ttl)
        return result

    def __len__(self) -> int:
        """返回缓存条目数"""
        return len(self._cache)

    def __del__(self):
        """清理时关闭缓存"""
        if hasattr(self, '_cache'):
            self._cache.close()


# 全局缓存实例
_global_cache = None

def get_global_cache() -> FileHashCache:
    """获取全局缓存实例（单例）"""
    global _global_cache
    if _global_cache is None:
        _global_cache = FileHashCache()
    return _global_cache


def cache_result(key_data: str, ttl: Optional[int] = None):
    """
    装饰器：缓存函数结果

    Args:
        key_data: 缓存键的字符串数据（或可调用函数，接收函数参数）
        ttl: 缓存有效期（秒）

    Example:
        @cache_result(lambda code, file_path: f"{file_path}:{hashlib.sha256(code.encode()).hexdigest()}")
        def review_file(code, file_path):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_global_cache()

            # 生成缓存键
            if callable(key_data):
                actual_key = key_data(*args, **kwargs)
            else:
                actual_key = key_data

            # 尝试获取缓存
            cached = cache.get(actual_key)
            if cached is not None:
                return cached

            # 计算并缓存结果
            result = func(*args, **kwargs)
            cache.set(actual_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def hash_file_content(content: str) -> str:
    """计算文件内容的 SHA256 哈希"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def hash_project(project_path: str, extensions: Optional[list] = None) -> str:
    """
    计算项目的哈希（基于文件路径、大小和修改时间）
    用于项目级缓存的键
    """
    project_path = os.path.abspath(project_path)
    hash_data = []

    for root, dirs, files in os.walk(project_path):
        # 排除隐藏目录和虚拟环境
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', '.venv', 'venv', 'node_modules')]

        for file in sorted(files):
            if extensions:
                ext_ok = any(file.endswith(ext) for ext in extensions)
                if not ext_ok:
                    continue

            file_path = os.path.join(root, file)
            try:
                stat = os.stat(file_path)
                # 使用文件路径、大小和修改时间
                hash_data.append(f"{file_path}:{stat.st_size}:{stat.st_mtime}")
            except OSError:
                pass

    if not hash_data:
        return hashlib.sha256(project_path.encode()).hexdigest()

    return hashlib.sha256('\n'.join(hash_data).encode()).hexdigest()