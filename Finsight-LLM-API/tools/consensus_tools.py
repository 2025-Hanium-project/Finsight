"""
데이터베이스 조회 도구들 - 컨센서스 데이터 및 요약 전용
로컬 SQLite DB만 사용
"""

import sqlite3
import pandas as pd
import os
from langchain_core.tools import tool
from typing import List, Dict, Any
from datetime import datetime, timedelta

# 로컬 SQLite DB 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "consensus_local.db")

def get_db_connection():
    """로컬 SQLite DB 연결 생성"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다: {DB_PATH}")
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 테이블 존재 확인
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    if 'consensus_reports' not in tables:
        raise ValueError(f"consensus_reports 테이블이 존재하지 않습니다. 테이블 목록: {tables}")
    
    return conn

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
        
        query = """
        SELECT stock_code, stock_name, report_date, analyst_name, company_name,
               rating, opinion_change, target_price, target_price_change
        FROM consensus_reports 
        WHERE stock_code = ?
        ORDER BY report_date DESC
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
            stock_code_val, stock_name, report_date, analyst_name, company_name, rating, opinion_change, target_price, target_price_change = row
            output.append(f"### {company_name} - {analyst_name}")
            output.append(f"- 보고서 날짜: {report_date}")
            output.append(f"- 투자의견: {rating} ({opinion_change})")
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
    컨센서스 요약 정보 조회 (증권사별 간단 요약만)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        컨센서스 요약 정보 (summary 필드만)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT stock_code, stock_name, report_date, analyst_name, company_name, summary
        FROM consensus_reports 
        WHERE stock_code = ? AND summary IS NOT NULL AND summary != ''
        ORDER BY report_date DESC
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
            stock_code_val, stock_name, report_date, analyst_name, company_name, summary = row
            output.append(f"### {company_name} - {analyst_name} ({report_date})")
            output.append(f"**요약:** {summary}")
            output.append("")
        
        cursor.close()
        conn.close()
        
        return "\n".join(output)
        
    except Exception as e:
        return f"DB 조회 중 오류 발생: {str(e)}"

@tool
def query_consensus_details(stock_code: str) -> str:
    """
    컨센서스 상세 정보 조회 (전체 투자 근거 포함)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        컨센서스 상세 정보 (investment_rationale 포함)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT stock_code, stock_name, report_date, analyst_name, company_name,
               summary, investment_rationale
        FROM consensus_reports 
        WHERE stock_code = ?
        ORDER BY report_date DESC
        """
        
        cursor.execute(query, (stock_code,))
        results = cursor.fetchall()
        
        if not results:
            return f"종목코드 {stock_code}에 대한 컨센서스 상세 데이터가 없습니다."
        
        # 결과 포맷팅 (상위 5개 리포트만)
        output = []
        output.append(f"## 종목코드 {stock_code} 컨센서스 상세 분석")
        output.append(f"총 {len(results)}개 리포트 중 최신 5개 상세 분석")
        output.append("")
        
        for i, row in enumerate(results[:5]):  # 상위 5개만
            stock_code_val, stock_name, report_date, analyst_name, company_name, summary, investment_rationale = row
            output.append(f"### {company_name} - {analyst_name} ({report_date})")
            if summary:
                output.append(f"**요약:** {summary}")
            if investment_rationale:
                # 투자 근거는 첫 500자만 표시 (너무 길어지는 것 방지)
                rationale_preview = investment_rationale[:500] + "..." if len(investment_rationale) > 500 else investment_rationale
                output.append(f"**투자 근거:** {rationale_preview}")
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
        전날 투자 보고서 정보 (투자의견, 목표주가, 요약, 투자근거 포함)
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
        
        # 먼저 investment_reports 테이블에서 조회 시도
        try:
            query = """
            SELECT stock_code, stock_name, report_date, report_type, report_content
            FROM investment_reports 
            WHERE stock_code = ? AND report_date = ? AND report_type = 'report'
            ORDER BY created_at DESC
            """
            
            cursor.execute(query, (stock_code, previous_day_str))
            results = cursor.fetchall()
            
            if results:
                # investment_reports에서 찾은 경우
                output = []
                output.append(f"## {stock_code} 전날({previous_day_str}) 투자 보고서")
                output.append(f"총 {len(results)}개 리포트")
                output.append("")
                
                for row in results:
                    stock_code_val, stock_name, report_date, report_type, report_content = row
                    
                    output.append(f"### {stock_name} - {report_type} 보고서")
                    output.append(f"- **보고서 날짜:** {report_date}")
                    output.append(f"- **보고서 내용:**")
                    
                    # 보고서 내용이 너무 길면 요약
                    if len(report_content) > 500:
                        content_preview = report_content[:500] + "..."
                        output.append(f"{content_preview}")
                        output.append(f"**전체 길이:** {len(report_content)}자")
                    else:
                        output.append(f"{report_content}")
                    
                    output.append("")
                
                cursor.close()
                conn.close()
                return "\n".join(output)
                
        except Exception as e:
            # investment_reports 테이블이 없거나 오류가 발생한 경우
            pass
        
        # investment_reports에서 찾지 못한 경우 consensus_reports에서 조회 (기존 로직)
        query = """
        SELECT stock_code, stock_name, report_date, analyst_name, company_name,
               rating, opinion_change, target_price, target_price_change,
               summary, investment_rationale
        FROM consensus_reports 
        WHERE stock_code = ? AND report_date = ?
        ORDER BY company_name, analyst_name
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
            stock_code_val, stock_name, report_date, analyst_name, company_name, rating, opinion_change, target_price, target_price_change, summary, investment_rationale = row
            
            output.append(f"### {company_name} - {analyst_name}")
            output.append(f"- **투자의견:** {rating} ({opinion_change})")
            output.append(f"- **목표주가:** {target_price:,}원 ({target_price_change})")
            
            if summary:
                output.append(f"- **요약:** {summary}")
            
            if investment_rationale:
                # 투자 근거는 첫 300자만 표시
                rationale_preview = investment_rationale[:300] + "..." if len(investment_rationale) > 300 else investment_rationale
                output.append(f"- **투자 근거:** {rationale_preview}")
            
            output.append("")
        
        cursor.close()
        conn.close()
        
        return "\n".join(output)
        
    except Exception as e:
        return f"전날 투자 보고서 조회 중 오류 발생: {str(e)}"