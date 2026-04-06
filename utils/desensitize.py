import re

def desensitize_code(code: str) -> str:
    """
    对代码中的敏感信息进行脱敏处理。
    替换模式：
    - api_key = "xxx"
    - password = 'xxx'
    - token = "xxx"
    - secret = "xxx"
    - AWS_SECRET_KEY = "xxx"
    - PRIVATE_KEY = "xxx"
    - sk-xxxxxxxxx (OpenAI/DeepSeek API key)

    返回脱敏后的代码，敏感值替换为 [REDACTED]。
    """
    if not code or not isinstance(code, str):
        return code

    patterns = [
        # api_key = "xxx"
        (r'api_key\s*=\s*["\'][^"\']*["\']', 'api_key = "[REDACTED]"'),
        # password = "xxx"
        (r'password\s*=\s*["\'][^"\']*["\']', 'password = "[REDACTED]"'),
        # token = "xxx"
        (r'token\s*=\s*["\'][^"\']*["\']', 'token = "[REDACTED]"'),
        # secret = "xxx"
        (r'secret\s*=\s*["\'][^"\']*["\']', 'secret = "[REDACTED]"'),
        # AWS_SECRET_KEY = "xxx"
        (r'AWS_SECRET_KEY\s*=\s*["\'][^"\']*["\']', 'AWS_SECRET_KEY = "[REDACTED]"'),
        # PRIVATE_KEY = "xxx"
        (r'PRIVATE_KEY\s*=\s*["\'][^"\']*["\']', 'PRIVATE_KEY = "[REDACTED]"'),
        # sk-xxxxxxxxx (OpenAI/DeepSeek API key)
        (r'sk-[a-zA-Z0-9]+', '[REDACTED]'),
    ]

    result = code
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result

if __name__ == "__main__":
    # 测试用例
    test_code = '''
api_key = "sk-1234567890abcdef"
password = 'my_password'
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
secret = "my_secret_key"
AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"
PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----"
some_var = "should not be redacted"
sk-abcdef123456
'''
    print("原始代码:")
    print(test_code)
    print("脱敏后代码:")
    print(desensitize_code(test_code))