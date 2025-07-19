"""
FinsightAI Agent 모듈
협업 기반 에이전트 시스템
"""

# 데이터 에이전트들
from .data_agents import (
    FinancialStatementAgent,
    NewsAnalysisAgent,
    SecuritiesReportAgent,
    MarketDataAgent
)

# 분석 에이전트들
from .analysis_agents import (
    RiskAssessmentAgent,
    GrowthAnalysisAgent,
    ValuationAgent,
    PeerComparisonAgent
)

# 리포트 에이전트들
from .report_agents import (
    DDayReportAgent,
    DPlus1ReportAgent
)

# 지원 에이전트들
from .support_agents import (
    SupervisorAgent,
    DataQualityAgent,
    DocumentProcessingAgent
)

# 모든 에이전트 클래스
ALL_AGENT_CLASSES = {
    # 데이터 에이전트
    "financial_statement_agent": FinancialStatementAgent,
    "news_analysis_agent": NewsAnalysisAgent,
    "securities_report_agent": SecuritiesReportAgent,
    "market_data_agent": MarketDataAgent,
    
    # 분석 에이전트
    "risk_assessment_agent": RiskAssessmentAgent,
    "growth_analysis_agent": GrowthAnalysisAgent,
    "valuation_agent": ValuationAgent,
    "peer_comparison_agent": PeerComparisonAgent,
    
    # 리포트 에이전트
    "dday_report_agent": DDayReportAgent,
    "dplus1_report_agent": DPlus1ReportAgent,
    
    # 지원 에이전트
    "supervisor_agent": SupervisorAgent,
    "data_quality_agent": DataQualityAgent,
    "document_processing_agent": DocumentProcessingAgent
}

# 에이전트 카테고리별 그룹
DATA_AGENTS = {
    "financial_statement_agent": FinancialStatementAgent,
    "news_analysis_agent": NewsAnalysisAgent,
    "securities_report_agent": SecuritiesReportAgent,
    "market_data_agent": MarketDataAgent
}

ANALYSIS_AGENTS = {
    "risk_assessment_agent": RiskAssessmentAgent,
    "growth_analysis_agent": GrowthAnalysisAgent,
    "valuation_agent": ValuationAgent,
    "peer_comparison_agent": PeerComparisonAgent
}

REPORT_AGENTS = {
    "dday_report_agent": DDayReportAgent,
    "dplus1_report_agent": DPlus1ReportAgent
}

SUPPORT_AGENTS = {
    "supervisor_agent": SupervisorAgent,
    "data_quality_agent": DataQualityAgent,
    "document_processing_agent": DocumentProcessingAgent
}

__all__ = [
    # 데이터 에이전트
    'FinancialStatementAgent',
    'NewsAnalysisAgent',
    'SecuritiesReportAgent',
    'MarketDataAgent',
    
    # 분석 에이전트
    'RiskAssessmentAgent',
    'GrowthAnalysisAgent',
    'ValuationAgent',
    'PeerComparisonAgent',
    
    # 리포트 에이전트
    'DDayReportAgent',
    'DPlus1ReportAgent',
    
    # 지원 에이전트
    'SupervisorAgent',
    'DataQualityAgent',
    'DocumentProcessingAgent',
    
    # 에이전트 그룹
    'ALL_AGENT_CLASSES',
    'DATA_AGENTS',
    'ANALYSIS_AGENTS',
    'REPORT_AGENTS',
    'SUPPORT_AGENTS'
]
