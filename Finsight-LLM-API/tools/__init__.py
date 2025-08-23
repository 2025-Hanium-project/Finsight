"""
Finsight LLM API Tools Package
재무 분석을 위한 도구들
"""

# 핵심 재무 도구들
from .financial_data_tools import (
    get_financial_statements,
    get_stock_price_data, 
    get_technical_analysis,
    get_current_trading_date
)

# 외부 데이터 도구들 (실제로 존재하는 것들만)
from .external_data_tools import (
    search_company_news,
    search_industry_news,
    search_financial_news,
    get_market_indicators
)

# 컨센서스 도구들 (실제로 존재하는 것들만)
from .consensus_tools import (
    query_consensus_data,
    query_consensus_summaries,
    get_previous_day_investment_reports
)

# 문서 처리 도구들 (실제로 존재하는 것만)
from .document_tools import (
    extract_pdf  # parse_pdf_document가 아님!
)

__all__ = [
    # 재무 도구들
    'get_financial_statements',
    'get_stock_price_data',
    'get_technical_analysis', 
    'get_current_trading_date',
    
    # 외부 데이터 도구들
    'search_company_news',
    'search_industry_news',
    'search_financial_news',
    'get_market_indicators',
    
    # 컨센서스 도구들
    'query_consensus_data',
    'query_consensus_summaries',
    'get_previous_day_investment_reports',
    
    # 문서 처리 도구들
    'extract_pdf'  # 실제로 존재하는 함수
]
