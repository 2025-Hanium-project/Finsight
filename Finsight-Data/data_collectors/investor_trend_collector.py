import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.helpers import (
    logger, get_trading_date,
    log_data_collection, update_collection_time, save_to_csv
)
from config.settings import settings

class InvestorTrendCollector:
    """투자자별 매매동향 수집기"""
    
    def __init__(self):
        pass
    
    def collect_investor_trends(self) -> List[Dict]:
        """KOSPI 전체 시장 투자자별 매매동향 수집"""
        try:
            trends_data = []
            # 현재 날짜 기준으로 거래일 계산
            trading_date = get_trading_date()
            
            logger.info(f"투자자 동향 수집 시작 - 거래일: {trading_date}")
            
            # KOSPI 전체 투자자별 매매동향 (개별 종목별이 아닌 시장 전체)
            try:
                df = stock.get_market_trading_value_by_date(
                    fromdate=trading_date,
                    todate=trading_date,
                    ticker='KOSPI'
                )
                
                if df.empty:
                    # 현재 거래일 데이터가 없으면 이전 거래일로 시도
                    prev_date = None
                    for i in range(1, 8):
                        check_date = datetime.now() - timedelta(days=i)
                        if check_date.weekday() < 5:  # 평일
                            prev_date = check_date.strftime('%Y%m%d')
                            break
                    
                    if prev_date:
                        logger.info(f"이전 거래일 {prev_date}로 재시도")
                        df = stock.get_market_trading_value_by_date(
                            fromdate=prev_date,
                            todate=prev_date,
                            ticker='KOSPI'
                        )
                        if not df.empty:
                            trading_date = prev_date
                
                if not df.empty:
                    logger.info(f"투자자 동향 데이터 수집 완료: {len(df)}개 레코드")
                    latest = df.iloc[-1]
                    
                    # 컬럼명 확인
                    available_columns = latest.index.tolist()
                    logger.info(f"사용 가능한 컬럼: {available_columns}")
                    
                    # 기관 투자자
                    institution_cols = ['기관합계', '기관', '기관투자자']
                    institution_value = 0.0
                    for col in institution_cols:
                        if col in latest:
                            institution_value = float(latest[col])
                            break
                    
                    institution_data = {
                        'market': 'KOSPI',
                        'investor_type': '기관',
                        'net_buy_amount': institution_value,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    }
                    trends_data.append(institution_data)
                    
                    # 외국인 투자자
                    foreign_cols = ['외국인합계', '외국인', '외국인투자자']
                    foreign_value = 0.0
                    for col in foreign_cols:
                        if col in latest:
                            foreign_value = float(latest[col])
                            break
                    
                    foreign_data = {
                        'market': 'KOSPI',
                        'investor_type': '외국인',
                        'net_buy_amount': foreign_value,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    }
                    trends_data.append(foreign_data)
                    
                    # 개인 투자자
                    individual_cols = ['개인', '개인투자자']
                    individual_value = 0.0
                    for col in individual_cols:
                        if col in latest:
                            individual_value = float(latest[col])
                            break
                    
                    individual_data = {
                        'market': 'KOSPI',
                        'investor_type': '개인',
                        'net_buy_amount': individual_value,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    }
                    trends_data.append(individual_data)
                    
                    # 기타법인
                    other_corp_cols = ['기타법인', '기타']
                    other_corp_value = 0.0
                    for col in other_corp_cols:
                        if col in latest:
                            other_corp_value = float(latest[col])
                            break
                    
                    other_corp_data = {
                        'market': 'KOSPI',
                        'investor_type': '기타법인',
                        'net_buy_amount': other_corp_value,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    }
                    trends_data.append(other_corp_data)
                    
                    logger.info(f"KOSPI 시장 투자자 동향 수집 완료: 기관={institution_value:,.0f}, 외국인={foreign_value:,.0f}, 개인={individual_value:,.0f}, 기타법인={other_corp_value:,.0f}")
                else:
                    logger.warning("투자자 동향 데이터를 가져올 수 없음")
                    
            except Exception as e:
                logger.error(f"투자자 동향 데이터 수집 중 오류: {str(e)}")
                # 대체 방법: 개별 종목들의 투자자 동향을 합산
                logger.info("대체 방법으로 개별 종목 투자자 동향 수집 시도")
                trends_data = self._collect_individual_stock_trends(trading_date)
            
            return trends_data
            
        except Exception as e:
            logger.error(f"collect_investor_trends 오류: {str(e)}")
            return []
    
    def _collect_individual_stock_trends(self, trading_date: str) -> List[Dict]:
        """개별 종목들의 투자자 동향을 합산하는 대체 방법"""
        try:
            # 대표 종목들로 투자자 동향 추정
            top_stocks = ['005930', '000660', '207940', '373220', '012450']  # 삼성전자, SK하이닉스 등
            
            total_institution = 0.0
            total_foreign = 0.0
            total_individual = 0.0
            total_other = 0.0
            valid_stocks = 0
            
            for stock_code in top_stocks:
                try:
                    df = stock.get_market_trading_value_by_date(
                        fromdate=trading_date,
                        todate=trading_date,
                        ticker=stock_code
                    )
                    
                    if not df.empty:
                        latest = df.iloc[-1]
                        
                        # 각 투자자 유형별 매매금액 합산
                        for col in ['기관합계', '기관']:
                            if col in latest:
                                total_institution += float(latest[col])
                                break
                        
                        for col in ['외국인합계', '외국인']:
                            if col in latest:
                                total_foreign += float(latest[col])
                                break
                        
                        for col in ['개인']:
                            if col in latest:
                                total_individual += float(latest[col])
                                break
                        
                        for col in ['기타법인', '기타']:
                            if col in latest:
                                total_other += float(latest[col])
                                break
                        
                        valid_stocks += 1
                        
                except Exception as e:
                    logger.debug(f"종목 {stock_code} 투자자 동향 수집 실패: {str(e)}")
                    continue
            
            if valid_stocks > 0:
                trends_data = [
                    {
                        'market': 'KOSPI',
                        'investor_type': '기관',
                        'net_buy_amount': total_institution,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    },
                    {
                        'market': 'KOSPI',
                        'investor_type': '외국인',
                        'net_buy_amount': total_foreign,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    },
                    {
                        'market': 'KOSPI',
                        'investor_type': '개인',
                        'net_buy_amount': total_individual,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    },
                    {
                        'market': 'KOSPI',
                        'investor_type': '기타법인',
                        'net_buy_amount': total_other,
                        'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'collected_at': datetime.now()
                    }
                ]
                
                logger.info(f"개별 종목 기반 투자자 동향 수집 완료: {valid_stocks}개 종목")
                return trends_data
            
            return []
            
        except Exception as e:
            logger.error(f"개별 종목 투자자 동향 수집 오류: {str(e)}")
            return []
    
    def save_to_csv(self, data: List[Dict]):
        """CSV 파일로 저장"""
        try:
            if data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(data, f'investor_trend_data_{timestamp}.csv')
                logger.info(f"Saved {len(data)} investor trend records to CSV")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def collect_all(self):
        """투자자별 매매동향 수집 및 저장"""
        try:
            logger.info("Starting investor trend collection...")
            
            # 투자자별 매매동향 수집
            investor_data = self.collect_investor_trends()
            log_data_collection("investor_trends", len(investor_data))
            
            # CSV 파일로 저장
            if investor_data:
                self.save_to_csv(investor_data)
                update_collection_time("investor_trends")
            
            logger.info(f"Investor trend collection completed. Total: {len(investor_data)} records")
            
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    """메인 실행 함수"""
    collector = InvestorTrendCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 