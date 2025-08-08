"""
데이터베이스 조회 도구들 - 컨센서스 데이터 및 요약 전용
"""

import pymysql
import pandas as pd
from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# DB 연결 설정
DB_CONFIG = {
    'host': 'finsight.kro.kr',
    'port': 32503,
    'user': 'etluser',
    'password': 'data123!',
    'db': 'finsight_database',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """DB 연결 생성"""
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor
    )

@tool
def query_consensus_data(stock_code: str) -> str:
    """
    컨센서스 데이터 조회 (메타데이터 - 정량 분석용)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        조회된 컨센서스 분석 결과
    """
    try:
        with get_db_connection() as connection:
            query = """
            SELECT 
                stock_name,
                company_name,
                rating,
                target_price,
                report_date,
                opinion_change,
                target_price_change
            FROM consensus_reports 
            WHERE stock_code = %s 
            AND report_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            ORDER BY report_date DESC
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, (stock_code,))
                results = cursor.fetchall()
                
                if not results:
                    return f"종목코드 {stock_code}에 대한 컨센서스 데이터가 없습니다."
                
                # 데이터 분석
                total_reports = len(results)
                stock_name = results[0]['stock_name']
                target_prices = [r['target_price'] for r in results if r['target_price']]
                ratings = [r['rating'] for r in results if r['rating']]
                companies = list(set([r['company_name'] for r in results if r['company_name']]))
                
                # 통계 계산
                avg_target_price = sum(target_prices) / len(target_prices) if target_prices else 0
                max_target_price = max(target_prices) if target_prices else 0
                min_target_price = min(target_prices) if target_prices else 0
                
                # 투자의견 분포
                rating_counts = {}
                for rating in ratings:
                    rating_counts[rating] = rating_counts.get(rating, 0) + 1
                
                # 결과 포맷팅
                result_text = f"""컨센서스 메타데이터 분석 결과:
종목: {stock_name} ({stock_code})
총 리포트: {total_reports}개
평균 목표주가: {avg_target_price:,.0f}원
최고 목표주가: {max_target_price:,.0f}원  
최저 목표주가: {min_target_price:,.0f}원
참여 증권사: {len(companies)}개사

투자의견 분포:"""
                
                for rating, count in rating_counts.items():
                    percentage = (count / total_reports) * 100
                    result_text += f"\n- {rating}: {count}개 ({percentage:.1f}%)"
                    
                result_text += f"\n\n참여 증권사:\n{', '.join(companies)}"
                
                return result_text
                
    except Exception as e:
        return f"DB 조회 중 오류 발생: {str(e)}"

@tool
def query_consensus_summaries(stock_code: str) -> str:
    """
    컨센서스 요약 데이터 조회 (질적 분석용)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        조회된 컨센서스 요약 분석 결과
    """
    try:
        with get_db_connection() as connection:
            query = """
            SELECT 
                stock_name,
                company_name,
                rating,
                target_price,
                report_date,
                summary
            FROM consensus_reports 
            WHERE stock_code = %s 
            AND summary IS NOT NULL 
            AND LENGTH(summary) > 50
            AND report_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            ORDER BY report_date DESC
            LIMIT 20
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, (stock_code,))
                results = cursor.fetchall()
                
                if not results:
                    return f"종목코드 {stock_code}에 대한 요약 데이터가 없습니다."
                
                # 결과 포맷팅
                stock_name = results[0]['stock_name']
                result_text = f"""컨센서스 요약 분석 결과:
종목: {stock_name} ({stock_code})
총 요약: {len(results)}건

증권사별 주요 분석 요약:"""
                
                # 증권사별 그룹핑
                company_reports = {}
                for result in results:
                    company = result['company_name']
                    if company not in company_reports:
                        company_reports[company] = []
                    company_reports[company].append(result)
                
                for company, reports in company_reports.items():
                    result_text += f"\n\n■ {company} ({len(reports)}건)"
                    for i, report in enumerate(reports, 1):
                        summary_preview = report['summary'][:300] + "..." if len(report['summary']) > 300 else report['summary']
                        result_text += f"\n  {i}. [{report['report_date']}] {report['rating']} {report['target_price']:,}원"
                        result_text += f"\n     {summary_preview}"
        
        return result_text
        
    except Exception as e:
        return f"DB 조회 중 오류 발생: {str(e)}" 