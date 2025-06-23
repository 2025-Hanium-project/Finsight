import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd
from config.settings import settings
import os
import json
from functools import wraps

def load_config():
    """설정 로드"""
    return settings

# 로그 디렉토리 생성
log_dir = settings.LOGS_DIR
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 파일 핸들러 (DEBUG 이상)
file_handler = logging.FileHandler(f'{settings.LOGS_DIR}/data_collector.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 콘솔 핸들러 (DEBUG만)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# 기존 핸들러 제거 후 새로 추가
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def retry_request(func, max_retries: int = None, delay: float = 1.0):
    """요청 재시도 데코레이터"""
    if max_retries is None:
        max_retries = settings.MAX_RETRIES
    
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))  # 지수 백오프
                else:
                    logger.error(f"All {max_retries} attempts failed")
                    raise
    return wrapper

@retry_request
def make_api_request(url: str, params: Dict = None, headers: Dict = None, timeout: int = None) -> requests.Response:
    """API 요청 함수"""
    if timeout is None:
        timeout = settings.TIMEOUT
    
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response

def is_market_open(now: Optional[datetime] = None) -> bool:
    """장이 열려있는지 확인 (한국 시간 기준)"""
    if now is None:
        now = datetime.now()
    
    # 주말 체크
    if now.weekday() >= 5:  # 토요일(5), 일요일(6)
        return False
    
    # 장 시간 체크 (9:00-15:30)
    market_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_start <= now <= market_end

def get_trading_date() -> str:
    """거래일 반환 (장이 닫혀있으면 전 거래일)"""
    now = datetime.now()
    
    if is_market_open():
        return now.strftime('%Y%m%d')
    
    # 장이 닫혀있으면 전 거래일 계산
    days_back = 1
    while days_back <= 7:  # 최대 7일 전까지 확인
        check_date = now - timedelta(days=days_back)
        if check_date.weekday() < 5:  # 평일
            return check_date.strftime('%Y%m%d')
        days_back += 1
    
    return now.strftime('%Y%m%d')

def calculate_change_rate(current: float, previous: float) -> Optional[float]:
    """변화율 계산"""
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100

def format_number(value: float, decimal_places: int = 2) -> str:
    """숫자 포맷팅"""
    if value is None:
        return "N/A"
    
    if abs(value) >= 1e12:
        return f"{value/1e12:.{decimal_places}f}T"
    elif abs(value) >= 1e9:
        return f"{value/1e9:.{decimal_places}f}B"
    elif abs(value) >= 1e6:
        return f"{value/1e6:.{decimal_places}f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.{decimal_places}f}K"
    else:
        return f"{value:.{decimal_places}f}"

def parse_date_string(date_str: str, format_str: str = '%Y%m%d') -> datetime:
    """날짜 문자열을 datetime 객체로 변환"""
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        logger.error(f"Invalid date format: {date_str}")
        return datetime.now()

def clean_text(text: str) -> str:
    """텍스트 정리 (특수문자 제거, 공백 정리)"""
    if not text:
        return ""
    
    import re
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 특수문자 제거 (한글, 영문, 숫자, 기본 문장부호만 유지)
    text = re.sub(r'[^\w\s가-힣.,!?()]', '', text)
    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_stock_codes(text: str) -> List[str]:
    """텍스트에서 종목 코드 추출"""
    import re
    # 6자리 숫자 패턴 (한국 주식 코드)
    pattern = r'\b\d{6}\b'
    return re.findall(pattern, text)

def save_to_csv(data: List[Dict], filename: str, directory: str = None):
    """데이터를 CSV 파일로 저장"""
    if directory is None:
        directory = settings.DATA_DIR
    
    import os
    os.makedirs(directory, exist_ok=True)
    
    df = pd.DataFrame(data)
    filepath = os.path.join(directory, filename)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    logger.info(f"Data saved to {filepath}")

def load_from_csv(filename: str, directory: str = None) -> pd.DataFrame:
    """CSV 파일에서 데이터 로드"""
    if directory is None:
        directory = settings.DATA_DIR
    
    import os
    filepath = os.path.join(directory, filename)
    
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return pd.DataFrame()
    
    return pd.read_csv(filepath, encoding='utf-8-sig')

def get_sector_by_stock_code(stock_code: str) -> Optional[str]:
    """종목 코드로 섹터 반환"""
    for sector, codes in settings.SECTORS.items():
        if stock_code in codes:
            return sector
    return None

def validate_stock_code(stock_code: str) -> bool:
    """종목 코드 유효성 검사"""
    if not stock_code or len(stock_code) != 6:
        return False
    
    try:
        int(stock_code)
        return True
    except ValueError:
        return False

def get_importance_score(keywords: List[str], text: str) -> str:
    """텍스트의 중요도 점수 계산"""
    if not text:
        return "낮음"
    
    text_lower = text.lower()
    score = 0
    
    # 중요 키워드별 점수
    importance_keywords = {
        '긴급': 10, '중요': 8, '주의': 6, '경고': 5,
        '상승': 3, '하락': 3, '급등': 4, '급락': 4,
        '실적': 3, '배당': 2, '합병': 5, '분할': 5
    }
    
    for keyword, points in importance_keywords.items():
        if keyword in text_lower:
            score += points
    
    if score >= 8:
        return "높음"
    elif score >= 4:
        return "보통"
    else:
        return "낮음"

def create_directory_if_not_exists(directory: str):
    """디렉토리가 없으면 생성"""
    import os
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def log_data_collection(data_type: str, count: int, status: str = "success"):
    """데이터 수집 로그 기록"""
    logger.info(f"Data collection - Type: {data_type}, Count: {count}, Status: {status}")

def get_last_collection_time(data_type: str) -> Optional[datetime]:
    """마지막 수집 시간 조회"""
    # 실제 구현에서는 데이터베이스에서 조회
    # 여기서는 간단히 파일 기반으로 구현
    import os
    import json
    
    filepath = os.path.join(settings.LOGS_DIR, 'collection_times.json')
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            times = json.load(f)
            if data_type in times:
                return datetime.fromisoformat(times[data_type])
    except Exception as e:
        logger.error(f"Error reading collection times: {e}")
    
    return None

def update_collection_time(data_type: str):
    """수집 시간 업데이트"""
    import os
    import json
    
    filepath = os.path.join(settings.LOGS_DIR, 'collection_times.json')
    
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                times = json.load(f)
        else:
            times = {}
        
        times[data_type] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(times, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"Error updating collection time: {e}") 