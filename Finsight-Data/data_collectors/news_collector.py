import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from typing import Dict, List
from utils.helpers import (
    logger, clean_text,
    log_data_collection, update_collection_time, make_api_request, save_to_csv
)
from config.settings import settings

class NewsCollector:
    """뉴스 수집기 - 네이버 뉴스 API를 통한 경제/투자 뉴스 수집"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def collect_naver_news(self, keywords: List[str] = None) -> List[Dict]:
        """네이버 뉴스 API를 통한 경제/투자 뉴스 수집"""
        try:
            if keywords is None:
                keywords = ['주식', '증시', '투자', '경제', '금융', '부동산']
            
            news_data = []
            
            # 네이버 API 키가 없는 경우 빈 리스트 반환
            if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
                logger.info("Naver API keys not configured, skipping Naver news collection")
                return news_data
            
            for keyword in keywords:
                try:
                    # 네이버 뉴스 검색 API
                    base_url = "https://openapi.naver.com/v1/search/news.json"
                    
                    params = {
                        'query': keyword,
                        'display': 100,
                        'start': 1,
                        'sort': 'date'  # 최신순
                    }
                    
                    headers = {
                        'X-Naver-Client-Id': settings.NAVER_CLIENT_ID,
                        'X-Naver-Client-Secret': settings.NAVER_CLIENT_SECRET
                    }
                    
                    # 실제 API 호출
                    response = make_api_request(base_url, params=params, headers=headers)
                    if response:
                        data = response.json()
                        
                        if 'items' in data:
                            for item in data['items']:
                                news_item = {
                                    'title': clean_text(item['title']),
                                    'content': clean_text(item['description']),
                                    'source': '네이버뉴스',
                                    'url': item['link'],
                                    'published_at': datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S %z'),
                                    'collected_at': datetime.now()
                                }
                                
                                news_data.append(news_item)
                    
                    logger.info(f"Collected {len(data.get('items', []))} news articles for keyword: {keyword}")
                    
                except Exception as e:
                    logger.error(f"Error collecting news for keyword {keyword}: {str(e)}")
                    continue
            
            return news_data
            
        except Exception as e:
            logger.error(f"Error in collect_naver_news: {str(e)}")
            return []
    
    def save_to_csv(self, news_data: List[Dict]):
        """뉴스 데이터를 CSV 파일로 저장"""
        try:
            if news_data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(news_data, f'news_data_{timestamp}.csv')
                logger.info(f"Saved {len(news_data)} news records to CSV")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def collect_all(self):
        """네이버 뉴스 수집 실행"""
        try:
            logger.info("Starting Naver news collection...")
            
            # 네이버 뉴스 수집
            naver_news = self.collect_naver_news()
            log_data_collection("naver_news", len(naver_news))
            
            # CSV에 저장
            if naver_news:
                self.save_to_csv(naver_news)
                update_collection_time("news_data")
            
            logger.info(f"News collection completed. Total: {len(naver_news)} articles")
            
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    """메인 실행 함수"""
    collector = NewsCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 