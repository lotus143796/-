LANGUAGE_CONFIG = {
    ".py": {
        "name": "Python",
        "linter": "pylint",
        "comment": "#",
        "tree_sitter": "python"
    },
    ".java": {
        "name": "Java",
        "linter": "checkstyle",
        "comment": "//",
        "tree_sitter": "java"
    },
    ".js": {
        "name": "JavaScript",
        "linter": "eslint",
        "comment": "//",
        "tree_sitter": "javascript"
    },
    ".go": {
        "name": "Go",
        "linter": "golint",
        "comment": "//",
        "tree_sitter": "go"
    },
    ".rs": {
        "name": "Rust",
        "linter": "clippy",
        "comment": "//",
        "tree_sitter": "rust"
    }
}

def get_language(ext: str):
    return LANGUAGE_CONFIG.get(ext, {"name": "Unknown", "linter": None, "comment": "#", "tree_sitter": None})