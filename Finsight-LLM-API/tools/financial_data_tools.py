"""
재무 및 주식 데이터 조회 도구들 - pykrx 기반
에이전트 워크플로우에 최적화된 도구 설계
"""

import os
from langchain_core.tools import tool
from datetime import datetime, timedelta
from pykrx import stock
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any

# ============================================================================
# 1. 기본 재무지표 도구 (Consensus Analyst, Corporate Analyst용)
# ============================================================================

@tool
def get_financial_statements(stock_code: str) -> str:
    """
    종목의 기본 재무지표 조회 (PER, PBR, EPS, BPS, 배당수익률, 시가총액 등)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        재무지표 정보를 포함한 마크다운 형식의 문자열
        
    사용 예시:
        - Consensus Analyst: 컨센서스 분석 시 기업 가치 평가
        - Corporate Analyst: 기업 펀더멘털 분석
    """
    try:
        result = []
        result.append(f"## {stock_code} 재무지표 정보")
        
        # 기업명 조회
        try:
            company_name = stock.get_market_ticker_name(stock_code)
            result.append(f"**회사명:** {company_name}")
        except Exception as e:
            result.append(f"**회사명:** 조회 실패 ({str(e)})")
            return "\n".join(result)
        
        # 영업일만 확인하여 재무지표 데이터 조회
        fundamental_data = None
        market_cap_data = None
        valid_date = None
        
        result.append("**영업일 데이터 검색 중...**")
        
        for i in range(30):
            check_date = (datetime.now() - timedelta(days=i))
            
            # 주말 제외 (토요일=5, 일요일=6)
            if check_date.weekday() >= 5:
                continue
                
            check_date_str = check_date.strftime('%Y%m%d')
            
            try:
                # 1. PER, PBR, EPS, BPS, DIV, DPS 조회
                fundamental = stock.get_market_fundamental(check_date_str, market='KOSPI')
                if not fundamental.empty and stock_code in fundamental.index:
                    fundamental_data = fundamental.loc[stock_code]
                    valid_date = check_date_str
                    result.append(f"**{check_date_str}** 재무지표 데이터 발견")
                    
                    # 2. 시가총액, 거래량, 상장주식수 조회
                    market_cap = stock.get_market_cap(check_date_str, market='KOSPI')
                    if not market_cap.empty and stock_code in market_cap.index:
                        market_cap_data = market_cap.loc[stock_code]
                        
                        # 데이터 유효성 검사 (0이 아닌 값이 있는지)
                        if market_cap_data['시가총액'] > 0:
                            result.append(f"**{check_date_str}** 유효한 시가총액 데이터 발견")
                        else:
                            result.append(f"**{check_date_str}** 시가총액 데이터는 있지만 값이 0")
                            continue  # 다음 영업일 시도
                    else:
                        result.append(f"**{check_date_str}** 시가총액 데이터 없음")
                        continue
                    break
                else:
                    result.append(f"**{check_date_str}** 재무지표 데이터 없음")
            except Exception as e:
                result.append(f"**{check_date_str}** 오류: {str(e)}")
                continue
        
        if fundamental_data is not None and market_cap_data is not None:
            result.append("")
            result.append(f"**기준일:** {valid_date}")
            result.append("")
            
            # 3. 시가총액 정보
            result.append("### 시가총액 정보")
            result.append(f"- **시가총액:** {market_cap_data['시가총액']:,.0f}원")
            result.append(f"- **상장주식수:** {market_cap_data['상장주식수']:,}주")
            result.append(f"- **거래량:** {market_cap_data['거래량']:,}주")
            result.append(f"- **거래대금:** {market_cap_data['거래대금']:,}원")
            result.append("")
            
            # 4. 밸류에이션 지표
            result.append("### 💰 밸류에이션 지표")
            indicators = {
                'PER': {'format': 'ratio', 'unit': '배', 'desc': '주가수익비율'},
                'PBR': {'format': 'ratio', 'unit': '배', 'desc': '주가순자산비율'},
                'EPS': {'format': 'currency', 'unit': '원', 'desc': '주당순이익'},
                'BPS': {'format': 'currency', 'unit': '원', 'desc': '주당순자산'},
                'DIV': {'format': 'percentage', 'unit': '%', 'desc': '배당수익률'},
                'DPS': {'format': 'currency', 'unit': '원', 'desc': '주당배당금'}
            }
            
            for indicator, config in indicators.items():
                if indicator in fundamental_data.index:
                    value = fundamental_data[indicator]
                    if pd.notna(value) and value != 0:
                        if config['format'] == 'currency':
                            result.append(f"- **{config['desc']} ({indicator}):** {value:,.0f}{config['unit']}")
                        elif config['format'] == 'ratio':
                            result.append(f"- **{config['desc']} ({indicator}):** {value:.2f}{config['unit']}")
                        elif config['format'] == 'percentage':
                            result.append(f"- **{config['desc']} ({indicator}):** {value:.2f}{config['unit']}")
                    else:
                        result.append(f"- **{config['desc']} ({indicator}):** 데이터 없음 또는 0")
                else:
                    result.append(f"- **{config['desc']} ({indicator}):** 키가 존재하지 않음")
        else:
            result.append("**최근 30일간 유효한 재무지표 데이터를 찾을 수 없습니다.**")
        
        return "\n".join(result)
    except Exception as e:
        return f"**재무정보 조회 실패:** {str(e)}"

# ============================================================================
# 2. 주가 및 거래 데이터 도구 (Quantitative Analyst용)
# ============================================================================

@tool
def get_stock_price_data(stock_code: str, days: int = 10) -> str:
    """
    종목의 주가 및 거래 정보 조회 (OHLCV, 거래량, 변동률 등)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        days: 조회할 일수 (기본값: 10일)
        
    Returns:
        주가 및 거래 정보를 포함한 마크다운 형식의 문자열
        
    사용 예시:
        - Quantitative Analyst: 기술적 분석 및 시장 심리 파악
        - Market Context Analyst: 시장 동향 분석
    """
    try:
        result = []
        result.append(f"## {stock_code} 주가 및 거래 정보")
        
        # 기업명 조회
        try:
            company_name = stock.get_market_ticker_name(stock_code)
            result.append(f"**종목명:** {company_name}")
        except:
            result.append(f"**종목명:** 조회 실패")
            return "\n".join(result)
        
        # 최근 영업일 주가 데이터 조회
        today = datetime.now()
        ohlcv_data = None
        valid_date = None
        
        for i in range(days):
            end_date = (today - timedelta(days=i)).strftime('%Y%m%d')
            start_date = (today - timedelta(days=i+7)).strftime('%Y%m%d')
            
            try:
                temp_data = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
                if not temp_data.empty:
                    ohlcv_data = temp_data
                    valid_date = end_date
                    break
            except:
                continue
        
        if ohlcv_data is not None:
            latest = ohlcv_data.iloc[-1]
            result.append(f"**기준일:** {valid_date}")
            result.append("")
            
            # 기본 OHLCV 정보
            result.append("### 기본 주가 정보")
            result.append(f"- **현재가:** {latest['종가']:,}원")
            result.append(f"- **시가:** {latest['시가']:,}원")
            result.append(f"- **고가:** {latest['고가']:,}원")
            result.append(f"- **저가:** {latest['저가']:,}원")
            result.append(f"- **거래량:** {latest['거래량']:,}주")
            
            # 거래대금 계산
            trade_value = latest['종가'] * latest['거래량']
            result.append(f"- **거래대금:** {trade_value:,}원")
            
            # 전일 대비 변동률
            if len(ohlcv_data) > 1:
                prev_close = ohlcv_data.iloc[-2]['종가']
                change_amount = latest['종가'] - prev_close
                change_rate = (change_amount / prev_close) * 100
                
                result.append("")
                result.append("### 📈 전일 대비 변동")
                result.append(f"- **변동금액:** {change_amount:+,}원")
                result.append(f"- **변동률:** {change_rate:+.2f}%")
                
                # 변동 방향 표시
                if change_amount > 0:
                    result.append("- **방향:** 📈 상승")
                elif change_amount < 0:
                    result.append("- **방향:** 📉 하락")
                else:
                    result.append("- **방향:** ➡️ 보합")
        else:
            result.append(f"**최근 {days}일간 유효한 주가 데이터를 찾을 수 없습니다.**")
        
        return "\n".join(result)
    except Exception as e:
        return f"**주가 정보 조회 실패:** {str(e)}"

# ============================================================================
# 3. 기술적 분석 도구 (Quantitative Analyst 전용)
# ============================================================================

@tool
def get_technical_analysis(stock_code: str, days: int = 90) -> str:
    """
    종목의 기술적 분석 지표 조회 (이동평균, RSI, 볼린저 밴드 등)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        days: 분석 기간 (기본값: 90일)
        
    Returns:
        기술적 분석 결과를 포함한 마크다운 형식의 문자열
        
    사용 예시:
        - Quantitative Analyst: 기술적 지표 기반 매매 시점 분석
        - Market Context Analyst: 시장 트렌드 분석
    """
    try:
        result = []
        result.append(f"## {stock_code} 기술적 분석")
        
        # 기업명 조회
        try:
            company_name = stock.get_market_ticker_name(stock_code)
            result.append(f"**종목명:** {company_name}")
            result.append(f"**분석 기간:** {days}일")
            result.append("")
        except:
            result.append(f"**종목명:** 조회 실패")
            return "\n".join(result)
        
        # 영업일 기준으로 충분한 데이터 수집 (2배로 확장하여 영업일 확보)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')
        
        try:
            df = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
            
            # 영업일만 필터링 (주말 제외)
            df = df[df.index.weekday < 5]
            
            if len(df) < 60:
                result.append(f"**충분한 영업일 데이터가 없습니다.** (실제: {len(df)}일, 필요: 60일)")
                result.append("**해결 방법:** 더 긴 기간으로 분석하거나 다른 종목을 선택하세요.")
                return "\n".join(result)
            
            # 이동평균 계산
            df['MA5'] = df['종가'].rolling(window=5).mean()
            df['MA20'] = df['종가'].rolling(window=20).mean()
            df['MA60'] = df['종가'].rolling(window=60).mean()
            
            # RSI 계산
            delta = df['종가'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # 볼린저 밴드 계산
            df['BB_MIDDLE'] = df['종가'].rolling(window=20).mean()
            bb_std = df['종가'].rolling(window=20).std()
            df['BB_UPPER'] = df['BB_MIDDLE'] + (bb_std * 2)
            df['BB_LOWER'] = df['BB_MIDDLE'] - (bb_std * 2)
            
            latest = df.iloc[-1]
            current_price = latest['종가']
            
            result.append("### 이동평균 분석")
            result.append(f"- **현재가:** {current_price:,}원")
            result.append(f"- **5일 이평:** {latest['MA5']:.0f}원")
            result.append(f"- **20일 이평:** {latest['MA20']:.0f}원")
            result.append(f"- **60일 이평:** {latest['MA60']:.0f}원")
            result.append("")
            
            # 이동평균 배열 상태 확인
            if current_price > latest['MA20'] > latest['MA60']:
                result.append("**이동평균 배열:** 정배열 상태 (상승 추세)")
            elif current_price < latest['MA20'] < latest['MA60']:
                result.append("**이동평균 배열:** 역배열 상태 (하락 추세)")
            else:
                result.append("**이동평균 배열:** 혼조 상태")
            result.append("")
            
            # RSI 분석
            rsi = latest['RSI']
            if pd.notna(rsi):
                result.append("### 📈 RSI (상대강도지수)")
                result.append(f"- **현재 RSI:** {rsi:.2f}")
                
                if rsi > 70:
                    result.append("- **해석:** 과매수 구간 (70 이상) - 매도 고려")
                elif rsi < 30:
                    result.append("- **해석:** 과매도 구간 (30 이하) - 매수 고려")
                else:
                    result.append("- **해석:** 중립 구간 (30-70) - 관망")
                result.append("")
            
            # 볼린저 밴드 분석
            bb_upper = latest['BB_UPPER']
            bb_lower = latest['BB_LOWER']
            
            if pd.notna(bb_upper) and pd.notna(bb_lower):
                result.append("### 볼린저 밴드")
                result.append(f"- **상단 밴드:** {bb_upper:.0f}원")
                result.append(f"- **중간 밴드:** {latest['BB_MIDDLE']:.0f}원")
                result.append(f"- **하단 밴드:** {bb_lower:.0f}원")
                result.append("")
                
                # 밴드 위치 분석
                if current_price > bb_upper:
                    result.append("**밴드 위치:** 상단 밴드 돌파 (과매수 가능성)")
                elif current_price < bb_lower:
                    result.append("**밴드 위치:** 하단 밴드 돌파 (과매도 가능성)")
                else:
                    result.append("**밴드 위치:** 밴드 내 정상 범위")
                result.append("")
            
            # 거래량 분석
            if '거래량' in latest:
                volume = latest['거래량']
                avg_volume = df['거래량'].rolling(window=20).mean().iloc[-1]
                
                result.append("### 📈 거래량 분석")
                result.append(f"- **현재 거래량:** {volume:,}주")
                result.append(f"- **20일 평균 거래량:** {avg_volume:.0f}주")
                
                if volume > avg_volume * 1.5:
                    result.append("- **해석:** 거래량 급증 (관심 집중)")
                elif volume < avg_volume * 0.5:
                    result.append("- **해석:** 거래량 감소 (관심 감소)")
                else:
                    result.append("- **해석:** 평균적인 거래량")
                result.append("")
            
            result.append(f"**분석 완료:** {len(df)}일간의 영업일 데이터로 분석 수행")
            
        except Exception as e:
            result.append(f"**데이터 분석 실패:** {str(e)}")
            return "\n".join(result)
            
        return "\n".join(result)
        
    except Exception as e:
        return f"**기술적 분석 실패:** {str(e)}"

# ============================================================================
# 4. 종합 분석 도구 (Report Writer Agent용)
# ============================================================================

@tool
def get_comprehensive_analysis(stock_code: str) -> str:
    """
    종목의 종합 분석 (52주 성과, 수익률, 기술적 지표 통합)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        
    Returns:
        종합 분석 결과를 포함한 마크다운 형식의 문자열
        
    사용 예시:
        - Report Writer Agent: 최종 보고서 작성 시 종합 정보 제공
        - Supervisor Agent: 전체적인 종목 상황 파악
    """
    try:
        result = []
        result.append(f"## {stock_code} 종합 분석 리포트")
        result.append("=" * 60)
        
        # 기업명 조회
        try:
            company_name = stock.get_market_ticker_name(stock_code)
            result.append(f"**종목명:** {company_name}")
            result.append("")
        except:
            result.append(f"**종목명:** 조회 실패")
            return "\n".join(result)
        
        # 1. 52주 성과 분석
        result.append("### 📈 52주 성과 분석")
        try:
            today = datetime.now().strftime('%Y%m%d')
            year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            year_data = stock.get_market_ohlcv_by_date(year_ago, today, stock_code)
            if not year_data.empty:
                high_52 = year_data['고가'].max()
                low_52 = year_data['저가'].min()
                current_price = year_data.iloc[-1]['종가']
                
                high_ratio = (current_price / high_52) * 100
                range_position = ((current_price - low_52) / (high_52 - low_52)) * 100
                
                result.append(f"- **52주 최고가:** {high_52:,}원")
                result.append(f"- **52주 최저가:** {low_52:,}원")
                result.append(f"- **현재가:** {current_price:,}원")
                result.append(f"- **최고가 대비:** {high_ratio:.1f}%")
                result.append(f"- **52주 구간 위치:** {range_position:.1f}%")
                
                # 구간별 위치 해석
                if range_position > 80:
                    result.append("- **해석:** 52주 구간 상단 - 고점 근처")
                elif range_position < 20:
                    result.append("- **해석:** 52주 구간 하단 - 저점 근처")
                else:
                    result.append("- **해석:** 52주 구간 중간 - 중립적 위치")
            else:
                result.append("**52주 데이터 조회 실패**")
        except Exception as e:
            result.append(f"**52주 성과 분석 실패:** {str(e)}")
        
        result.append("")
        
        # 2. 기간별 수익률 분석
        result.append("### 📊 기간별 수익률 분석")
        try:
            today = datetime.now()
            periods = [("1개월", 30), ("3개월", 90), ("6개월", 180), ("1년", 365)]
            
            # 현재가 조회
            current_data = stock.get_market_ohlcv_by_date(
                (today - timedelta(days=7)).strftime('%Y%m%d'),
                today.strftime('%Y%m%d'),
                stock_code
            )
            
            if not current_data.empty:
                current_price = current_data.iloc[-1]['종가']
                
                for period_name, days in periods:
                    try:
                        past_date = (today - timedelta(days=days)).strftime('%Y%m%d')
                        past_data = stock.get_market_ohlcv_by_date(past_date, past_date, stock_code)
                        
                        if not past_data.empty:
                            past_price = past_data.iloc[0]['종가']
                            return_rate = ((current_price - past_price) / past_price) * 100
                            
                            # 수익률 방향 표시
                            if return_rate > 0:
                                result.append(f"- **{period_name}:** +{return_rate:.2f}%")
                            elif return_rate < 0:
                                result.append(f"- **{period_name}:** {return_rate:.2f}%")
                            else:
                                result.append(f"- **{period_name}:** ➡️ {return_rate:.2f}%")
                    except:
                        result.append(f"- **{period_name}:** 데이터 없음")
            else:
                result.append("**현재가 데이터 조회 실패**")
        except Exception as e:
            result.append(f"**수익률 분석 실패:** {str(e)}")
        
        result.append("")
        
        # 3. 간단한 기술적 분석 요약
        result.append("### 📈 기술적 분석 요약")
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
            df = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
            if not df.empty and len(df) >= 60:
                df['MA20'] = df['종가'].rolling(window=20).mean()
                df['MA60'] = df['종가'].rolling(window=60).mean()
                
                latest = df.iloc[-1]
                current_price = latest['종가']
                ma20 = latest['MA20']
                ma60 = latest['MA60']
                
                result.append(f"- **현재가:** {current_price:,}원")
                result.append(f"- **20일 이평:** {ma20:.0f}원")
                result.append(f"- **60일 이평:** {ma60:.0f}원")
                
                # 트렌드 해석
                if current_price > ma20 > ma60:
                    result.append("- **트렌드:** 상승 추세 (정배열)")
                elif current_price < ma20 < ma60:
                    result.append("- **트렌드:** 하락 추세 (역배열)")
                else:
                    result.append("- **트렌드:** 혼조 상태")
            else:
                result.append("**기술적 분석 데이터 부족**")
        except Exception as e:
            result.append(f"**기술적 분석 실패:** {str(e)}")
        
        return "\n".join(result)
    except Exception as e:
        return f"**종합 분석 실패:** {str(e)}"

# ============================================================================
# 5. 보조 도구들 (내부 사용)
# ============================================================================

@tool
def get_current_trading_date() -> str:
    """
    현재 날짜와 가장 가까운 영업일 조회
    
    Returns:
        영업일 문자열 (YYYY-MM-DD 형식)
        
    사용 예시:
        - 다른 도구들에서 날짜 계산 시 기준점으로 사용
    """
    try:
        now = datetime.now()
        
        # 2024-2025년 주요 공휴일
        holidays = {
            '2024-01-01', '2024-02-09', '2024-02-10', '2024-02-11', '2024-02-12',
            '2024-03-01', '2024-04-10', '2024-05-05', '2024-05-06', '2024-05-15',
            '2024-06-06', '2024-08-15', '2024-09-16', '2024-09-17', '2024-09-18',
            '2024-10-03', '2024-10-09', '2024-12-25',
            '2025-01-01', '2025-01-28', '2025-01-29', '2025-01-30',
            '2025-03-01', '2025-05-05', '2025-05-15', '2025-06-06', 
            '2025-08-15', '2025-10-03', '2025-10-09', '2025-12-25'
        }
        
        # 현재 시간이 16시 이후이고 평일이면서 공휴일이 아니면 오늘
        if (now.weekday() < 5 and now.hour >= 16 and 
            now.strftime('%Y-%m-%d') not in holidays):
            return now.strftime('%Y-%m-%d')
        
        # 가장 최근 영업일 찾기
        days_back = 1
        while days_back <= 10:
            check_date = now - timedelta(days=days_back)
            if (check_date.weekday() < 5 and 
                check_date.strftime('%Y-%m-%d') not in holidays):
                return check_date.strftime('%Y-%m-%d')
            days_back += 1
        
        return now.strftime('%Y-%m-%d')  # 실패시 오늘 반환
    except Exception as e:
        return datetime.now().strftime('%Y-%m-%d')

def calculate_technical_indicators(stock_code: str, days: int = 90) -> Optional[pd.DataFrame]:
    """
    기술적 지표 계산 (내부 함수)
    
    Args:
        stock_code: 종목코드
        days: 분석 기간
        
    Returns:
        기술적 지표가 추가된 DataFrame 또는 None
    """
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        df = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
        
        if not df.empty:
            # 이동평균
            df['MA5'] = df['종가'].rolling(window=5).mean()
            df['MA20'] = df['종가'].rolling(window=20).mean()
            df['MA60'] = df['종가'].rolling(window=60).mean()
            
            # RSI 계산
            delta = df['종가'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            return df
        return None
    except:
        return None

def get_institutional_trading(stock_code: str, days: int = 30) -> Optional[pd.DataFrame]:
    """
    기관/외국인 매매 동향 분석 (내부 함수)
    
    Args:
        stock_code: 종목코드
        days: 분석 기간
        
    Returns:
        기관/외국인 매매 데이터 DataFrame 또는 None
    """
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        df = stock.get_market_trading_value_by_date(start_date, end_date, stock_code)
        return df
    except:
        return None

@tool
def get_technical_indicators(stock_code: str, days: int = 60) -> str:
    """
    종목의 기술적 지표 조회 (이동평균선, RSI, 볼린저 밴드 등)
    
    Args:
        stock_code: 종목코드 (예: "005930")
        days: 조회할 일수 (기본값: 60일)
        
    Returns:
        기술적 지표를 포함한 마크다운 형식의 문자열
        
    사용 예시:
        - Quantitative Analyst: 기술적 분석 및 매매 타이밍
    """
    try:
        result = []
        result.append(f"## {stock_code} 기술적 지표 분석")
        
        # 기업명 조회
        try:
            company_name = stock.get_market_ticker_name(stock_code)
            result.append(f"**종목명:** {company_name}")
        except:
            result.append(f"**종목명:** 조회 실패")
            return "\n".join(result)
        
        # 최근 주가 데이터 조회
        today = datetime.now()
        end_date = today.strftime('%Y%m%d')
        start_date = (today - timedelta(days=days)).strftime('%Y%m%d')
        
        try:
            ohlcv_data = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
            if ohlcv_data.empty:
                return f"**최근 {days}일간 주가 데이터를 찾을 수 없습니다.**"
        except:
            return f"**주가 데이터 조회 실패**"
        
        # 기술적 지표 계산
        latest = ohlcv_data.iloc[-1]
        result.append(f"**기준일:** {end_date}")
        result.append("")
        
        # 이동평균선 계산
        result.append("### 이동평균선 분석")
        ma5 = ohlcv_data['종가'].rolling(window=5).mean().iloc[-1]
        ma20 = ohlcv_data['종가'].rolling(window=20).mean().iloc[-1]
        ma60 = ohlcv_data['종가'].rolling(window=60).mean().iloc[-1]
        
        result.append(f"- **5일 이동평균:** {ma5:,.0f}원")
        result.append(f"- **20일 이동평균:** {ma20:,.0f}원")
        result.append(f"- **60일 이동평균:** {ma60:,.0f}원")
        
        # 이동평균선 배열 상태
        if ma5 > ma20 > ma60:
            result.append("- **배열 상태:** 📈 정배열 (상승 추세)")
        elif ma5 < ma20 < ma60:
            result.append("- **배열 상태:** 📉 역배열 (하락 추세)")
        else:
            result.append("- **배열 상태:** ➡️ 혼재 (추세 불명확)")
        
        # RSI 계산
        result.append("")
        result.append("### 📈 RSI 분석")
        delta = ohlcv_data['종가'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        result.append(f"- **RSI (14일):** {rsi:.2f}")
        if rsi >= 70:
            result.append("- **상태:** 🔴 과매수 (매도 고려)")
        elif rsi <= 30:
            result.append("- **상태:** 🟢 과매도 (매수 고려)")
        else:
            result.append("- **상태:** 🟡 중립 (관망)")
        
        # 볼린저 밴드 계산
        result.append("")
        result.append("### 볼린저 밴드 분석")
        ma20 = ohlcv_data['종가'].rolling(window=20).mean().iloc[-1]
        std20 = ohlcv_data['종가'].rolling(window=20).std().iloc[-1]
        
        upper_band = ma20 + (2 * std20)
        lower_band = ma20 - (2 * std20)
        
        result.append(f"- **중간 밴드 (20일 이평):** {ma20:,.0f}원")
        result.append(f"- **상단 밴드:** {upper_band:,.0f}원")
        result.append(f"- **하단 밴드:** {lower_band:,.0f}원")
        
        current_price = latest['종가']
        bb_position = ((current_price - lower_band) / (upper_band - lower_band)) * 100
        
        result.append(f"- **밴드 내 위치:** {bb_position:.1f}%")
        if bb_position >= 80:
            result.append("- **상태:** 🔴 상단 밴드 근접 (과매수 가능성)")
        elif bb_position <= 20:
            result.append("- **상태:** 🟢 하단 밴드 근접 (과매도 가능성)")
        else:
            result.append("- **상태:** 🟡 중간 구간 (정상)")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"**기술적 지표 조회 실패:** {str(e)}"
