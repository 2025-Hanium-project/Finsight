#!/usr/bin/env python3
"""
Finsight Data - 메인 실행 파일
모든 데이터 수집기를 실행합니다.
"""

import sys
import os
from datetime import datetime
from data_collectors.stock_collector import StockCollector
from data_collectors.market_index_collector import MarketIndexCollector
from data_collectors.exchange_rate_collector import ExchangeRateCollector
from data_collectors.news_collector import NewsCollector
from data_collectors.interest_rate_collector import InterestRateCollector
from data_collectors.sector_trend_collector import SectorTrendCollector
from data_collectors.economic_indicator_collector import EconomicIndicatorCollector
from data_collectors.economic_calendar_collector import EconomicCalendarCollector
from data_collectors.commodity_collector import CommodityCollector
from data_collectors.financial_collector import FinancialCollector
from data_collectors.investor_trend_collector import InvestorTrendCollector
from utils.helpers import logger

def run_all_collectors():
    """모든 데이터 수집기 실행"""
    try:
        logger.info("=" * 50)
        logger.info("Finsight Data 수집 시작")
        logger.info(f"시작 시간: {datetime.now()}")
        logger.info("=" * 50)
        
        # 1. 시장 지수 수집
        logger.info("\n📈 시장 지수 수집 시작...")
        index_collector = MarketIndexCollector()
        index_collector.collect_all()
        
        # 2. 환율 정보 수집
        logger.info("\n💱 환율 정보 수집 시작...")
        rate_collector = ExchangeRateCollector()
        rate_collector.collect_all()
        
        # 3. 금리 정보 수집
        logger.info("\n💰 금리 정보 수집 시작...")
        interest_collector = InterestRateCollector()
        interest_collector.collect_all()
        
        # 4. 주식 데이터 수집
        logger.info("\n📊 주식 데이터 수집 시작...")
        stock_collector = StockCollector()
        stock_collector.collect_all()
        
        # 5. 섹터 동향 분석 수집
        logger.info("\n📈 섹터 동향 분석 수집 시작...")
        trend_collector = SectorTrendCollector()
        trend_collector.collect_all()
        
        # 6. 경제 지표 수집
        logger.info("\n📊 경제 지표 수집 시작...")
        economic_collector = EconomicIndicatorCollector()
        economic_collector.collect_all()
        
        # 7. 경제 캘린더 수집
        logger.info("\n📅 경제 캘린더 수집 시작...")
        calendar_collector = EconomicCalendarCollector()
        calendar_collector.collect_all()
        
        # 8. 원자재 가격 수집
        logger.info("\n🛢️ 원자재 가격 수집 시작...")
        commodity_collector = CommodityCollector()
        commodity_collector.collect_all()
        
        # 9. 재무 정보 수집
        logger.info("\n📋 재무 정보 수집 시작...")
        financial_collector = FinancialCollector()
        financial_collector.collect_all()
        
        # 10. 투자자 동향 수집
        logger.info("\n👥 투자자 동향 수집 시작...")
        investor_collector = InvestorTrendCollector()
        investor_collector.collect_all()
        
        # 11. 뉴스 수집
        logger.info("\n📰 뉴스 수집 시작...")
        news_collector = NewsCollector()
        news_collector.collect_all()
        
        logger.info("\n" + "=" * 50)
        logger.info("모든 데이터 수집 완료!")
        logger.info(f"완료 시간: {datetime.now()}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"데이터 수집 중 오류 발생: {str(e)}")
        raise

def run_specific_collector(collector_name: str):
    """특정 수집기만 실행"""
    try:
        logger.info(f"{collector_name} 수집기 실행 시작...")
        
        if collector_name.lower() == 'market_index':
            collector = MarketIndexCollector()
        elif collector_name.lower() == 'exchange_rate':
            collector = ExchangeRateCollector()
        elif collector_name.lower() == 'interest_rate':
            collector = InterestRateCollector()
        elif collector_name.lower() == 'stock':
            collector = StockCollector()
        elif collector_name.lower() == 'sector_trend':
            collector = SectorTrendCollector()
        elif collector_name.lower() == 'economic_indicator':
            collector = EconomicIndicatorCollector()
        elif collector_name.lower() == 'economic_calendar':
            collector = EconomicCalendarCollector()
        elif collector_name.lower() == 'commodity':
            collector = CommodityCollector()
        elif collector_name.lower() == 'financial':
            collector = FinancialCollector()
        elif collector_name.lower() == 'investor_trend':
            collector = InvestorTrendCollector()
        elif collector_name.lower() == 'news':
            collector = NewsCollector()
        else:
            logger.error(f"알 수 없는 수집기: {collector_name}")
            return
        
        collector.collect_all()
        logger.info(f"{collector_name} 수집 완료!")
        
    except Exception as e:
        logger.error(f"{collector_name} 수집 중 오류: {str(e)}")
        raise

def main():
    """메인 함수"""
    # 명령행 인수 확인
    if len(sys.argv) > 1:
        collector_name = sys.argv[1]
        run_specific_collector(collector_name)
    else:
        # 모든 수집기 실행
        run_all_collectors()

if __name__ == "__main__":
    main() 