from typing import Optional, List
from pydantic import BaseModel, validator, Field


# 问题类型允许的值
ISSUE_TYPES = {"security", "style", "performance", "bug"}

# 严重程度允许的值
SEVERITY_LEVELS = {"critical", "high", "medium", "low"}


class Issue(BaseModel):
    """代码审查问题模型"""
    issue_type: str = Field(..., description="问题类型：security/style/performance/bug")
    severity: str = Field(..., description="严重程度：critical/high/medium/low")
    line_number: Optional[int] = Field(None, description="行号（可选）")
    description: str = Field(..., description="问题描述")
    suggestion: str = Field(..., description="修复建议")

    @validator('issue_type')
    def validate_issue_type(cls, v):
        if v not in ISSUE_TYPES:
            raise ValueError(f"问题类型必须是 {sorted(ISSUE_TYPES)} 之一")
        return v

    @validator('severity')
    def validate_severity(cls, v):
        if v not in SEVERITY_LEVELS:
            raise ValueError(f"严重程度必须是 {sorted(SEVERITY_LEVELS)} 之一")
        return v


class ReviewReport(BaseModel):
    """代码审查报告模型"""
    summary: str = Field(..., description="总结")
    issues: List[Issue] = Field(..., description="问题列表")
    overall_risk: str = Field(..., description="整体风险等级")

    @validator('overall_risk')
    def validate_overall_risk(cls, v):
        if v not in SEVERITY_LEVELS:
            raise ValueError(f"整体风险等级必须是 {sorted(SEVERITY_LEVELS)} 之一")
        return v