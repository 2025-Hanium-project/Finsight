import os
import re
import requests
from datetime import datetime
from config import BASE_DOWNLOAD_PATH, USER_AGENT, DEFAULT_TIMEOUT

def safe_filename(stock, company):
    """
    파일명에 사용할 수 없는 문자를 _로 치환하고, 길이를 제한합니다.
    """
    name = f"{stock}_{company}"
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return name[:150]

def get_save_dir(date_str, company, base_download_path=None):
    """
    날짜와 증권사명을 받아 저장 폴더 경로를 생성합니다.
    base_download_path가 없으면 config의 BASE_DOWNLOAD_PATH를 사용합니다.
    """
    date_str = date_str.replace('.', '/').replace('-', '/').replace(' ', '')
    parts = date_str.split('/')
    if len(parts) == 3:
        year, month, day = parts
    else:
        now = datetime.now()
        year, month, day = now.strftime('%Y'), now.strftime('%m'), now.strftime('%d')
    if base_download_path is None:
        base_download_path = BASE_DOWNLOAD_PATH
    save_dir = os.path.join(base_download_path, year, month, day, company.upper())
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def download_file(url, save_path, headers=None, chunk_size=8192, timeout=None):
    """
    주어진 URL에서 파일을 다운로드하여 save_path에 저장합니다.
    """
    if headers is None:
        headers = {'User-Agent': USER_AGENT}
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    resp = requests.get(url, headers=headers, stream=True, timeout=timeout)
    resp.raise_for_status()
    with open(save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
    return save_path

def date_str_now(fmt='%Y%m%d'):
    """
    오늘 날짜를 문자열로 반환합니다. (기본: YYYYMMDD)
    """
    return datetime.now().strftime(fmt) 