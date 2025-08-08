"""
컨센서스 분석 에이전트 테스트
"""

import os
import sys
import sqlite3
import json
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.consensus_analyst_agent import create_consensus_analyst_agent
from tools.stock_tools import get_current_stock_price

# 환경변수 로드
load_dotenv()

# 테스트용 설정
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "consensus_local.db")

# =====================================
# 테스트용 로컬 DB 도구들
# =====================================

@tool
def query_consensus_data(stock_code: str) -> str:
    """
    로컬 테스트 DB에서 컨센서스 메타데이터 조회 (정량 분석용)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        조회된 컨센서스 메타데이터 분석 결과
    """
    try:
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 모든 데이터 조회
        query = """
        SELECT * FROM consensus_reports 
        WHERE stock_code = ?
        ORDER BY report_date DESC
        """
        
        cursor.execute(query, (stock_code,))
        results = cursor.fetchall()
        
        if not results:
            conn.close()
            return f"종목코드 {stock_code}에 대한 데이터가 없습니다."
        
        # 데이터 분석
        total_reports = len(results)
        target_prices = [row['target_price'] for row in results if row['target_price']]
        ratings = [row['rating'] for row in results if row['rating']]
        companies = [row['company_name'] for row in results if row['company_name']]
        
        # 통계 계산
        avg_target_price = sum(target_prices) / len(target_prices) if target_prices else 0
        max_target_price = max(target_prices) if target_prices else 0
        min_target_price = min(target_prices) if target_prices else 0
        
        # 투자의견 분포
        rating_counts = {}
        for rating in ratings:
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        # 결과 포맷팅
        result = f"""[로컬 테스트 DB 조회 결과]
종목: {results[0]['stock_name']} ({stock_code})
총 리포트: {total_reports}개
평균 목표주가: {avg_target_price:,.0f}원
최고 목표주가: {max_target_price:,.0f}원
최저 목표주가: {min_target_price:,.0f}원
참여 증권사: {len(set(companies))}개사

[투자의견 분포]"""
        
        for rating, count in rating_counts.items():
            percentage = (count / total_reports) * 100
            result += f"\n- {rating}: {count}개 ({percentage:.1f}%)"
            
        result += f"\n\n[참여 증권사]\n{', '.join(set(companies))}"
        
        conn.close()
        return result
        
    except Exception as e:
        return f"로컬 DB 조회 오류: {str(e)}"

@tool
def query_consensus_summaries(stock_code: str) -> str:
    """
    로컬 테스트 DB에서 컨센서스 요약 조회 (질적 분석용)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        조회된 컨센서스 요약 분석 결과
    """
    try:
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 요약이 있는 데이터 조회
        query = """
        SELECT * FROM consensus_reports 
        WHERE stock_code = ?
        AND summary IS NOT NULL
        AND length(summary) > 10
        ORDER BY report_date DESC
        """
        
        cursor.execute(query, (stock_code,))
        results = cursor.fetchall()
        
        if not results:
            conn.close()
            return f"종목코드 {stock_code}에 대한 요약 데이터가 없습니다."
        
        # 결과 포맷팅
        result = f"""[로컬 테스트 DB 요약 조회 결과]
종목정보: {results[0]['stock_name']} ({stock_code})
총 요약 수: {len(results)}건

[증권사별 주요 요약 분석]"""
        
        # 증권사별 그룹핑
        company_reports = {}
        for row in results:
            company = row['company_name']
            if company not in company_reports:
                company_reports[company] = []
            company_reports[company].append(row)
        
        for company, reports in company_reports.items():
            result += f"\n■ {company} ({len(reports)}건)"
            for i, report in enumerate(reports, 1):
                summary_preview = report['summary'][:200] + "..." if len(report['summary']) > 200 else report['summary']
                result += f"\n  {i}. [{report['report_date']}] {report['rating']} {report['target_price']:,}원"
                result += f"\n     요약: {summary_preview}"
        
        conn.close()
        return result
        
    except Exception as e:
        return f"로컬 DB 요약 조회 오류: {str(e)}"

class ConsensusAnalysisTest:
    """컨센서스 분석 에이전트 직접 테스트 클래스"""
    
    def __init__(self):
        self.agent = None
        
    def setup_agent(self):
        """에이전트 설정"""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("Google API Key가 설정되지 않았습니다.")
        
        # LLM 초기화
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0
        )
        
        # 컨센서스 분석 에이전트 생성 (테스트용 도구 사용)
        from langgraph.prebuilt import create_react_agent
        from agents.consensus_analyst_agent import CONSENSUS_ANALYST_PROMPT
        
        tools = [query_consensus_data, query_consensus_summaries, get_current_stock_price]
        self.agent = create_react_agent(llm, tools, state_modifier=CONSENSUS_ANALYST_PROMPT)
        
        print("✅ 컨센서스 분석 에이전트 초기화 완료")
    
    def test_consensus_analysis(self, stock_code: str = "005930", question: str = None):
        """
        컨센서스 분석 에이전트 테스트
        
        Args:
            stock_code: 분석할 종목코드 (기본값: 삼성전자)
            question: 분석 질문 (기본값: 종합 분석)
        """
        if not self.agent:
            self.setup_agent()
        
        if not question:
            question = f"""
{stock_code} 종목에 대한 컨센서스 데이터를 종합 분석해주세요.

분석 요구사항:
1. **정량 분석**: query_consensus_data 도구를 사용하여 목표주가, 투자의견 분포 등 메타데이터 분석
2. **질적 분석**: query_consensus_summaries 도구를 사용하여 증권사별 애널리스트 요약 내용 분석  
3. **현재 주가 대비 분석**: get_current_stock_price 도구로 현재 주가를 조회하여 목표주가와 비교 분석
4. **종합 평가**: 정량/질적 분석을 통합하여 컨센서스의 신뢰성과 일관성 평가

특히 다음 관점에서 분석해주세요:
- 목표주가 분석: 평균, 최고, 최저 목표주가 및 현재가 대비 상승여력
- 투자의견 분포: 매수/중립/매도 비율 및 일치도  
- 애널리스트 합의도: 의견 일치 정도와 이견 부분
- 증권사별 핵심 논리와 근거 비교
- KOSPI200 대형주 관점에서의 투자 의미
- 현재 주가 수준의 적정성 평가
"""
        
        print(f"\n{'='*80}")
        print(f"🧪 컨센서스 분석 에이전트 테스트: {stock_code}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            print("🔄 분석 진행 중...")
            print("-" * 80)
            
            # 에이전트 실행
            result = self.agent.invoke({"messages": [("user", question)]})
            
            print("📋 분석 결과:")
            print("=" * 80)
            
            # 결과 출력
            if 'messages' in result and result['messages']:
                final_message = result['messages'][-1]
                if hasattr(final_message, 'content'):
                    print(final_message.content)
                else:
                    print(final_message)
            else:
                print("결과를 찾을 수 없습니다.")
                print(f"전체 결과: {result}")
                
        except Exception as e:
            print(f"❌ 분석 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n⏱️ 분석 시간: {elapsed_time:.2f}초")
        
        if elapsed_time < 60:
            print("✅ 성능 테스트 통과 (60초 이내)")
        else:
            print("⚠️ 성능 개선 필요 (60초 초과)")

def verify_test_environment():
    """테스트 환경 검증"""
    print("🔍 테스트 환경 검증 중...")
    
    # 로컬 DB 존재 확인
    if not os.path.exists(TEST_DB_PATH):
        print(f"❌ 테스트 DB 파일이 없습니다: {TEST_DB_PATH}")
        print("consensus_local.db 파일을 tests 폴더에 복사해주세요.")
        return False
    
    # DB 내용 확인
    try:
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.cursor()
        
        # 테이블 존재 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='consensus_reports'")
        if not cursor.fetchone():
            print("❌ consensus_reports 테이블이 없습니다.")
            conn.close()
            return False
            
        # 삼성전자 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM consensus_reports WHERE stock_code = '005930'")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("❌ 삼성전자(005930) 테스트 데이터가 없습니다.")
            conn.close()
            return False
            
        print(f"✅ 삼성전자 테스트 데이터: {count}개")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ DB 검증 중 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 컨센서스 분석 에이전트 직접 테스트 시작")
    print("=" * 80)
    
    # 환경 검증
    if not verify_test_environment():
        return
    
    # Google API 키 확인
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Google API Key가 설정되지 않았습니다.")
        print(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")
        return
    
    print("✅ 테스트 환경 검증 완료")
    
    # 테스트 실행
    test = ConsensusAnalysisTest()
    
    # 삼성전자 컨센서스 종합 분석 테스트
    test.test_consensus_analysis("005930")
    
    print(f"\n{'='*80}")
    print("🎉 컨센서스 분석 에이전트 테스트 완료")
    print("=" * 80)
    print("\n💡 테스트 요약:")
    print("- 에이전트가 직접 정량 분석(메타데이터) 수행")
    print("- 에이전트가 직접 질적 분석(요약 내용) 수행") 
    print("- 실제 주가 데이터를 사용한 현재가 대비 분석")
    print("- 에이전트가 종합 평가 및 투자 의견 제시")

if __name__ == "__main__":
    main() 