import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, date
from typing import Dict, List
from utils.helpers import (
    logger, save_to_csv,
    log_data_collection, update_collection_time
)
from config.settings import settings
import requests
from urllib.parse import quote

class EconomicCalendarCollector:
    """경제 캘린더 수집기 - 한경 경제캘린더 API를 통한 경제 일정 수집"""
    
    def __init__(self):
        pass
    
    def collect_economic_calendar(self) -> List[Dict]:
        """경제 캘린더 데이터 수집"""
        try:
            calendar_data = []
            
            # 한경 경제캘린더 API 수집
            try:
                hk_events = self._collect_hankyung_calendar()
                calendar_data.extend(hk_events)
                logger.info(f"Collected {len(hk_events)} events from Hankyung")
            except Exception as e:
                logger.error(f"Error collecting Hankyung calendar: {str(e)}")
            
            logger.info(f"Total collected {len(calendar_data)} economic calendar events")
            return calendar_data
            
        except Exception as e:
            logger.error(f"Error in collect_economic_calendar: {str(e)}")
            return []
    
    def _collect_hankyung_calendar(self) -> List[Dict]:
        """한경 경제캘린더 데이터 수집 (API 직접 호출)"""
        all_events = []
        seen_events = set()

        # 날짜 범위 설정 (오늘 하루)
        start_date = date.today()
        end_date = start_date  # 오늘 하루만
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # API 파라미터 준비
        str_nation = quote('China|중국|South Korea|대한민국|United Kingdom|영국|United States|미국|')
        str_natcd = quote('cn|kr|gb|us|')
        str_importance = quote('3|2|1|')
        api_url = (
            f"https://asp.zeroin.co.kr/eco/includes/wei/module/json_getData.php?"
            f"start_date={start_date_str}&end_date={end_date_str}&sort_code=0&"
            f"str_nation={str_nation}&str_natcd={str_natcd}&str_importance={str_importance}"
        )
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://datacenter.hankyung.com/economic-calendar'
        }
        logger.info(f"Requesting API: {api_url}")
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            logger.error(f"API 요청 실패: status_code={response.status_code}")
            return []
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"JSON 파싱 실패: {e}\n본문: {response.text[:500]}")
            return []

        n = len(data.get('date_temp', []))
        logger.info(f"API에서 {n}개 이벤트 수신")
        for i in range(n):
            try:
                event_date = data['date_temp'][i][:10] if 'date_temp' in data else ''
                event_time = data['time'][i].strip() if 'time' in data else ''
                country = data['nat_hname'][i] if 'nat_hname' in data else ''
                event_name = data['kevent'][i] if 'kevent' in data else ''
                actual = data['actual'][i] if 'actual' in data else ''
                forecast = data['forecast'][i] if 'forecast' in data else ''
                previous = data['previous'][i] if 'previous' in data else ''
                importance = data['importance'][i] if 'importance' in data else ''
                
                # 중복 체크
                event_key = f"{event_date}_{event_time}_{event_name}_{country}"
                if event_key in seen_events:
                    continue
                seen_events.add(event_key)

                event_data = {
                    'event_date': event_date,
                    'event_time': event_time,
                    'country': country,
                    'event_name': event_name,
                    'actual': actual,
                    'forecast': forecast,
                    'previous': previous,
                    'importance': importance,
                    'source': '한경 경제캘린더',
                    'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                all_events.append(event_data)
            except Exception as e:
                logger.error(f"행 변환 오류: {e}")
                continue
        logger.info(f"최종 {len(all_events)}개 이벤트 수집 완료 (중복 제거 후)")
        return all_events
    
    def save_to_csv(self, calendar_data: List[Dict]):
        """CSV 파일로 저장"""
        try:
            if calendar_data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(calendar_data, f'economic_calendar_data_{timestamp}.csv')
                logger.info(f"Saved {len(calendar_data)} calendar records to CSV")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def collect_all(self):
        """모든 경제 캘린더 데이터 수집"""
        try:
            logger.info("Starting economic calendar collection...")
            
            # 경제 캘린더 데이터 수집
            calendar_data = self.collect_economic_calendar()
            log_data_collection("economic_calendar", len(calendar_data))
            
            # CSV에 저장
            if calendar_data:
                self.save_to_csv(calendar_data)
                update_collection_time("economic_calendar")
            
            logger.info(f"Economic calendar collection completed. Total: {len(calendar_data)} events")
            
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    """메인 실행 함수"""
    collector = EconomicCalendarCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 