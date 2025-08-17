"""
뉴스 및 시장 환경 분석 도구들 - Tavily API 기반
"""

from langchain_core.tools import tool
from tavily import TavilyClient
from datetime import datetime, timedelta
import os
from typing import List, Dict
import json
from pykrx import stock

def get_tavily_client():
    """Tavily 클라이언트 초기화"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY가 설정되지 않았습니다.")
    return TavilyClient(api_key=api_key)

@tool
def search_company_news(stock_code: str, days_back: int = 7) -> str:
    """
    특정 기업 관련 최신 뉴스 검색 (자기 기업용)
    
    Args:
        stock_code: 종목코드
        days_back: 검색 기간 (일)
    """
    try:
        # 종목코드를 회사명으로 변환
        try:
            company_name = stock.get_market_ticker_name(stock_code)
        except:
            company_name = stock_code
        
        client = get_tavily_client()
        
        # 검색 쿼리 생성 (자기 기업 뉴스)
        query = f"{company_name} 주가 실적 뉴스"
        
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            days=days_back
        )
        
        if not response.get('results'):
            return f"❌ {company_name}({stock_code}) 관련 뉴스를 찾을 수 없습니다."
        
        result = [f"## {company_name}({stock_code}) 관련 뉴스"]
        result.append(f"*검색 기간: 최근 {days_back}일*")
        result.append("")
        
        for i, item in enumerate(response['results'][:5], 1):
            title = item.get('title', '제목 없음')
            content = item.get('content', '내용 없음')[:200] + "..."
            url = item.get('url', '')
            
            result.append(f"### {i}. {title}")
            result.append(f"**요약**: {content}")
            result.append(f"**출처**: {url}")
            result.append("")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"뉴스 검색 실패: {str(e)}"

@tool
def search_competitor_news(stock_code: str, days_back: int = 7) -> str:
    """
    경쟁사 관련 뉴스 검색 (경쟁사 분석용)
    
    Args:
        stock_code: 종목코드
        days_back: 검색 기간 (일)
    """
    try:
        # 종목코드를 회사명으로 변환 (동일한 메커니즘)
        try:
            company_name = stock.get_market_ticker_name(stock_code)
        except:
            company_name = stock_code
        
        client = get_tavily_client()
        
        # 검색 쿼리 생성 (경쟁사 뉴스) - query만 다름
        query = f"{company_name} 경쟁사 주가 실적 뉴스"
        
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            days=days_back
        )
        
        if not response.get('results'):
            return f"❌ {company_name}({stock_code}) 경쟁사 관련 뉴스를 찾을 수 없습니다."
        
        result = [f"## {company_name}({stock_code}) 경쟁사 관련 뉴스"]
        result.append(f"*검색 기간: 최근 {days_back}일*")
        result.append("")
        
        for i, item in enumerate(response['results'][:5], 1):
            title = item.get('title', '제목 없음')
            content = item.get('content', '내용 없음')[:200] + "..."
            url = item.get('url', '')
            
            result.append(f"### {i}. {title}")
            result.append(f"**요약**: {content}")
            result.append(f"**출처**: {url}")
            result.append("")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"경쟁사 뉴스 검색 실패: {str(e)}"

@tool
def search_industry_news(industry_keyword: str) -> str:
    """
    산업 동향 뉴스 검색
    """
    try:
        client = get_tavily_client()
        
        query = f"{industry_keyword} 산업 동향 전망"
        
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            days=14
        )
        
        if not response.get('results'):
            return f"❌ {industry_keyword} 산업 관련 뉴스를 찾을 수 없습니다."
        
        result = [f"## {industry_keyword} 산업 동향 뉴스"]
        result.append("*검색 기간: 최근 2주*")
        result.append("")
        
        for i, item in enumerate(response['results'][:5], 1):
            title = item.get('title', '제목 없음')
            content = item.get('content', '내용 없음')[:200] + "..."
            
            result.append(f"### {i}. {title}")
            result.append(f"**요약**: {content}")
            result.append("")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"산업 뉴스 검색 실패: {str(e)}"

@tool
def search_financial_news(keyword: str = "금리 환율 인플레이션") -> str:
    """
    금융/경제 뉴스 검색
    """
    try:
        client = get_tavily_client()
        
        query = f"한국 {keyword} 경제 전망"
        
        response = client.search(
            query=query,
            search_depth="basic", 
            max_results=5,
            days=7
        )
        
        if not response.get('results'):
            return f"❌ {keyword} 관련 경제 뉴스를 찾을 수 없습니다."
        
        result = [f"## {keyword} 관련 경제 뉴스"]
        result.append("*검색 기간: 최근 1주*")
        result.append("")
        
        for i, item in enumerate(response['results'][:5], 1):
            title = item.get('title', '제목 없음')
            content = item.get('content', '내용 없음')[:200] + "..."
            
            result.append(f"### {i}. {title}")
            result.append(f"**요약**: {content}")
            result.append("")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"경제 뉴스 검색 실패: {str(e)}"

@tool
def get_market_indicators() -> str:
    """
    주요 시장 지표 조회 (지수, 환율 등)
    """
    try:
        result = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        result.append("## 주요 시장 지표")
        result.append(f"*조회일: {current_date}*")
        result.append("")
        
        # 한국 주요 지수
        result.append("### 🇰🇷 한국 주요 지수")
        try:
            today = datetime.now().strftime('%Y%m%d')
            yesterday = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            
            # KOSPI
            kospi = stock.get_index_ohlcv_by_date(yesterday, today, "1001")
            if not kospi.empty:
                latest_kospi = kospi.iloc[-1]
                result.append(f"KOSPI: {latest_kospi['종가']:,.2f}")
                
                if len(kospi) > 1:
                    prev_kospi = kospi.iloc[-2]['종가']
                    change = latest_kospi['종가'] - prev_kospi
                    change_rate = (change / prev_kospi) * 100
                    result.append(f"전일대비: {change:+,.2f} ({change_rate:+.2f}%)")
            
            # KOSDAQ
            kosdaq = stock.get_index_ohlcv_by_date(yesterday, today, "2001")
            if not kosdaq.empty:
                latest_kosdaq = kosdaq.iloc[-1]
                result.append(f"KOSDAQ: {latest_kosdaq['종가']:,.2f}")
                
        except Exception as e:
            result.append(f"한국 지수 조회 실패: {str(e)}")
        
        # 환율 정보 (USD/KRW)
        result.append("\n### 💱 환율")
        try:
            client = get_tavily_client()
            usd_response = client.search(
                query="USD KRW 환율 오늘",
                search_depth="basic",
                max_results=2
            )
            
            if usd_response.get('results'):
                result.append("USD/KRW 환율 정보:")
                content = usd_response['results'][0].get('content', '')
                result.append(content[:100] + "...")
        except:
            result.append("환율 정보 조회 실패")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"시장 지표 조회 실패: {str(e)}"
