"""
FinsightAI Agent 모듈
협업 기반 에이전트 시스템
"""

# 데이터 소스별 에이전트
from .financial_statement_agent import analyze_financial_statement, financial_statement_agent
from .news_analysis_agent import analyze_news, news_analysis_agent
from .securities_report_agent import analyze_securities_report, securities_report_agent
from .market_data_agent import analyze_market_data, market_data_agent

# 분석 유형별 에이전트
from .risk_assessment_agent import analyze_risk, risk_assessment_agent
from .growth_analysis_agent import analyze_growth, growth_analysis_agent
from .valuation_agent import analyze_valuation, valuation_agent
from .peer_comparison_agent import compare_peers, peer_comparison_agent

# 보고서 작성 에이전트
from .dday_report_agent import generate_dday_report, dday_report_agent
from .dplus1_report_agent import generate_dplus1_report, dplus1_report_agent

# 지원 에이전트
from .document_processing_agent import process_document, document_processing_agent
from .data_quality_agent import assess_data_quality, data_quality_agent
from .supervisor_agent import supervise_analysis, supervisor_agent

# 모든 에이전트 인스턴스
ALL_AGENTS = {
    "financial_statement_agent": financial_statement_agent,
    "news_analysis_agent": news_analysis_agent,
    "securities_report_agent": securities_report_agent,
    "market_data_agent": market_data_agent,
    "risk_assessment_agent": risk_assessment_agent,
    "growth_analysis_agent": growth_analysis_agent,
    "valuation_agent": valuation_agent,
    "peer_comparison_agent": peer_comparison_agent,
    "dday_report_agent": dday_report_agent,
    "dplus1_report_agent": dplus1_report_agent,
    "document_processing_agent": document_processing_agent,
    "data_quality_agent": data_quality_agent,
    "supervisor_agent": supervisor_agent
}

# 새로운 Agent 구조 함수들
__all__ = [
    # 데이터 소스별 에이전트
    'analyze_financial_statement',
    'analyze_news',
    'analyze_securities_report',
    'analyze_market_data',
    
    # 분석 유형별 에이전트
    'analyze_risk',
    'analyze_growth',
    'analyze_valuation',
    'compare_peers',
    
    # 보고서 작성 에이전트
    'generate_dday_report',
    'generate_dplus1_report',
    
    # 지원 에이전트
    'process_document',
    'assess_data_quality',
    'supervise_analysis',
    
    # 모든 에이전트 인스턴스
    'ALL_AGENTS'
]
