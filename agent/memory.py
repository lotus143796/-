import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

class AgentMemory:
    def __init__(self):
        self.analyzed_functions: Dict[str, Dict] = {}
        self.common_patterns: List[Dict] = []
        self.prev_decisions: List[Dict] = []
        self.session_start = datetime.now()

    def _get_code_hash(self, code: str) -> str:
        return hashlib.md5(code.encode()).hexdigest()[:16]

    def add_analysis(self, code: str, analysis: Dict) -> None:
        code_hash = self._get_code_hash(code)
        self.analyzed_functions[code_hash] = {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "code_preview": code[:100]
        }

    def get_cached_analysis(self, code: str) -> Optional[Dict]:
        code_hash = self._get_code_hash(code)
        if code_hash in self.analyzed_functions:
            return self.analyzed_functions[code_hash]["analysis"]
        return None

    def add_step(self, tool: str, params: Dict, result: str) -> None:
        self.prev_decisions.append({
            "tool": tool,
            "params": params,
            "result_preview": result[:200],
            "timestamp": datetime.now().isoformat()
        })

    def add_pattern(self, pattern: str, context: str) -> None:
        self.common_patterns.append({
            "pattern": pattern,
            "context": context,
            "occurrence_count": 1
        })

    def get_summary(self) -> Dict:
        return {
            "analyzed_functions": len(self.analyzed_functions),
            "patterns_found": len(self.common_patterns),
            "decisions_made": len(self.prev_decisions),
            "session_duration_seconds": (datetime.now() - self.session_start).seconds
        }

    def find_similar_pattern(self, code: str) -> Optional[str]:
        import re
        imports = re.findall(r'^(?:import|from)\s+(\w+)', code, re.MULTILINE)
        for pattern in self.common_patterns:
            if any(imp in pattern["pattern"] for imp in imports):
                return pattern["context"]
        return None