import sys
sys.path.insert(0, 'D:\\zhuomian\\code-review-agent')

from agent.schemas import Issue
from test_validation.core_test import CodeReviewAgent
from test_validation.prompts_test import SYSTEM_PROMPT

print('=== 测试1: 模型定义 ===')
issue = Issue(
    type='security',
    severity='critical',
    line=1,
    description='测试问题',
    recommendation='测试建议'
)
print(f'✅ Issue 创建成功: {issue.type}/{issue.severity}')

print('\n=== 测试2: 提示词加载 ===')
print(f'✅ SYSTEM_PROMPT 长度: {len(SYSTEM_PROMPT)} 字符')
if 'JSON' in SYSTEM_PROMPT or 'json' in SYSTEM_PROMPT:
    print('✅ 提示词包含 JSON 格式要求')
else:
    print('⚠️ 提示词可能缺少 JSON 格式要求')

print('\n=== 测试3: Agent 实例化 ===')
try:
    agent = CodeReviewAgent(api_key='test_key', model='deepseek-chat', max_steps=3)
    print('✅ Agent 实例化成功')
    print(f'   - 有 _validate_issue_line: {hasattr(agent, "_validate_issue_line")}')
    print(f'   - 有 _validate_issue_exists: {hasattr(agent, "_validate_issue_exists")}')
except Exception as e:
    print(f'❌ Agent 实例化失败: {e}')

print('\n=== 测试4: 验证方法功能 ===')
agent_temp = CodeReviewAgent(api_key='test', max_steps=1)
code = 'line1\nline2\nline3'
result1 = agent_temp._validate_issue_line({'line': 2}, code)
result2 = agent_temp._validate_issue_line({'line': 10}, code)
print(f'   有效行号(2): {result1}')
print(f'   无效行号(10): {result2}')

if result1 and not result2:
    print('✅ 行号验证方法正常')
else:
    print('⚠️ 行号验证方法可能有问题')

print('\n=== 所有测试完成 ===')