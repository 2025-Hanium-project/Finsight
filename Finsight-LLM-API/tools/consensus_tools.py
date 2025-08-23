"""
데이터베이스 조회 도구들 - 컨센서스 데이터 및 요약 전용
Private Cloud MySQL DB 사용
"""

import pymysql
import pandas as pd
import os
from langchain_core.tools import tool
from typing import List, Dict, Any
from datetime import datetime, timedelta

# MySQL DB 연결 설정
DB_CONFIG = {
    'host': 'finsight.kro.kr',
    'port': 32503,
    'user': 'etluser',
    'password': 'data123!',
    'db': 'finsight_database',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """MySQL DB 연결 생성"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise ConnectionError(f"MySQL 연결 실패: {str(e)}")

@tool
def query_consensus_data(stock_code: str) -> str:
    """
    컨센서스 메타데이터 조회 (목표주가, 투자의견 등)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        컨센서스 메타데이터 정보
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # MySQL용 쿼리 (report_metadata 테이블 사용)
        query = """
        SELECT s.stock_code, s.stock_name, rm.report_date, rm.analyst_name, rm.company_name,
               rm.rating, rm.opinion_change, rm.target_price, rm.target_price_change
        FROM report_metadata rm
        JOIN Stock s ON rm.Stock_id = s.Stock_id
        WHERE s.stock_code = %s
        ORDER BY rm.report_date DESC
        """
        
        cursor.execute(query, (stock_code,))
        results = cursor.fetchall()
        
        if not results:
            return f"종목코드 {stock_code}에 대한 컨센서스 데이터가 없습니다."
        
        # 결과 포맷팅
        output = []
        output.append(f"## 종목코드 {stock_code} 컨센서스 메타데이터")
        output.append(f"총 {len(results)}개 리포트")
        output.append("")
        
        for row in results:
            stock_code_val = row['stock_code']
            stock_name = row['stock_name']
            report_date = row['report_date']
            analyst_name = row['analyst_name']
            company_name = row['company_name']
            rating = row['rating']
            opinion_change = row['opinion_change']
            target_price = row['target_price']
            target_price_change = row['target_price_change']
            
            output.append(f"### {company_name} - {analyst_name}")
            output.append(f"- 보고서 날짜: {report_date}")
            output.append(f"- 투자의견: {rating} ({opinion_change})")
            if target_price:
                output.append(f"- 목표주가: {target_price:,}원 ({target_price_change})")
            output.append("")
        
        cursor.close()
        conn.close()
        
        return "\n".join(output)
        
    except Exception as e:
        return f"DB 조회 중 오류 발생: {str(e)}"

@tool  
def query_consensus_summaries(stock_code: str) -> str:
    """
    컨센서스 요약 정보 조회 (요약문 포함)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        컨센서스 요약 정보 (summary 필드 사용)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # MySQL용 쿼리 - summary 필드 사용
        query = """
        SELECT s.stock_code, s.stock_name, rm.report_date, rm.analyst_name, rm.company_name,
               rc.summary
        FROM report_metadata rm
        JOIN Stock s ON rm.Stock_id = s.Stock_id
        LEFT JOIN report_content rc ON rm.report_id = rc.report_id
        WHERE s.stock_code = %s AND rc.summary IS NOT NULL AND rc.summary != ''
        ORDER BY rm.report_date DESC
        """
        
        cursor.execute(query, (stock_code,))
        results = cursor.fetchall()
        
        if not results:
            return f"종목코드 {stock_code}에 대한 컨센서스 요약 데이터가 없습니다."
        
        # 결과 포맷팅
        output = []
        output.append(f"## 종목코드 {stock_code} 컨센서스 요약 분석")
        output.append(f"총 {len(results)}개 리포트 요약")
        output.append("")
        
        for row in results:
            stock_code_val = row['stock_code']
            stock_name = row['stock_name']
            report_date = row['report_date']
            analyst_name = row['analyst_name']
            company_name = row['company_name']
            summary = row['summary']
            
            output.append(f"### {company_name} - {analyst_name} ({report_date})")
            output.append(f"**요약:** {summary}")
            output.append("")
        
        cursor.close()
        conn.close()
        
        return "\n".join(output)
        
    except Exception as e:
        return f"DB 조회 중 오류 발생: {str(e)}"

@tool
def get_previous_day_investment_reports(stock_code: str) -> str:
    """
    전날 투자 보고서 조회 (D+1 성과 분석용)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        전날 투자 보고서 정보 (투자의견, 목표주가, 요약 포함)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 전날 날짜 계산 (영업일 기준)
        today = datetime.now()
        previous_day = today - timedelta(days=1)
        
        # 주말인 경우 금요일로 조정
        while previous_day.weekday() >= 5:  # 5=토요일, 6=일요일
            previous_day = previous_day - timedelta(days=1)
        
        previous_day_str = previous_day.strftime('%Y-%m-%d')
        
        # MySQL용 쿼리 - 실제 테이블 구조에 맞춤
        query = """
        SELECT s.stock_code, s.stock_name, rm.report_date, rm.analyst_name, rm.company_name,
               rm.rating, rm.opinion_change, rm.target_price, rm.target_price_change,
               rc.content_text, rc.summary
        FROM report_metadata rm
        JOIN Stock s ON rm.Stock_id = s.Stock_id
        LEFT JOIN report_content rc ON rm.report_id = rc.report_id
        WHERE s.stock_code = %s AND rm.report_date = %s
        ORDER BY rm.company_name, rm.analyst_name
        """
        
        cursor.execute(query, (stock_code, previous_day_str))
        results = cursor.fetchall()
        
        if not results:
            return f"종목코드 {stock_code}에 대한 {previous_day_str} 투자 보고서가 없습니다."
        
        # 결과 포맷팅
        output = []
        output.append(f"## {stock_code} 전날({previous_day_str}) 투자 보고서")
        output.append(f"총 {len(results)}개 리포트")
        output.append("")
        
        for row in results:
            stock_code_val = row['stock_code']
            stock_name = row['stock_name']
            report_date = row['report_date']
            analyst_name = row['analyst_name']
            company_name = row['company_name']
            rating = row['rating']
            opinion_change = row['opinion_change']
            target_price = row['target_price']
            target_price_change = row['target_price_change']
            content_text = row['content_text']
            summary = row['summary']
            
            output.append(f"### {company_name} - {analyst_name}")
            output.append(f"- **투자의견:** {rating} ({opinion_change})")
            if target_price:
                output.append(f"- **목표주가:** {target_price:,}원 ({target_price_change})")
            
            if summary:
                output.append(f"- **요약:** {summary}")
            
            if content_text:
                # 본문 텍스트는 첫 300자만 표시
                text_preview = content_text[:300] + "..." if len(content_text) > 300 else content_text
                output.append(f"- **본문:** {text_preview}")
            
            output.append("")
        
        cursor.close()
        conn.close()
        
        return "\n".join(output)
        
    except Exception as e:
        return f"전날 투자 보고서 조회 중 오류 발생: {str(e)}"