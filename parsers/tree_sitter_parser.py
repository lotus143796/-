from tree_sitter import Language, Parser
import tree_sitter_languages

class MultiLanguageParser:
    def __init__(self):
        self.parsers = {}
        for lang in ["python", "java", "javascript", "go", "rust"]:
            try:
                parser = Parser()
                parser.set_language(tree_sitter_languages.get_language(lang))
                self.parsers[lang] = parser
            except:
                pass

    def parse(self, code: str, extension: str) -> dict:
        lang_map = {".py": "python", ".java": "java", ".js": "javascript", ".go": "go", ".rs": "rust"}
        lang = lang_map.get(extension)
        if lang and lang in self.parsers:
            tree = self.parsers[lang].parse(bytes(code, "utf8"))
            return {"success": True, "root": tree.root_node, "language": lang}
        return {"success": False, "error": "Unsupported language"}

# 全局实例
parser = MultiLanguageParser()