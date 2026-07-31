"""교보 크롤러의 다운로드 판정 로직 자체 점검.

브라우저를 띄우지 않도록 save_dir/download_dir만 가진 가짜 self로 메서드를 호출한다.
    python crawling/test_kyobo_download.py
"""
import os
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kyobo_con_crawler import KyoboSecuritiesReportCrawler as K


def test_target_path():
    fake = SimpleNamespace(save_dir="/tmp/kyobo")

    # 종목명이 있으면 종목명_제목_날짜
    p = K.target_path(fake, title="1분기 실적", date="2026/07/30", stock_name="삼성전자")
    assert os.path.basename(p) == "삼성전자_1분기 실적_20260730.pdf", p

    # 파일명에 쓸 수 없는 문자는 제거
    p = K.target_path(fake, title="A/B:C?", date="2026-07-30", stock_name="")
    assert os.path.basename(p) == "A_BC_20260730.pdf", p

    # crawl_reports가 report_info를 통째로 넘겨도 받아야 한다
    info = {"title": "T", "date": "2026/07/30", "stock_name": "S",
            "analyst": "K", "category": "기업"}
    assert K.target_path(fake, **info) == "/tmp/kyobo/S_T_20260730.pdf"


def test_wait_for_download():
    with tempfile.TemporaryDirectory() as d:
        fake = SimpleNamespace(download_dir=d)

        # 클릭 전부터 있던 파일은 새 다운로드로 오해하면 안 된다
        old = os.path.join(d, "이전리포트.pdf")
        open(old, "w").close()
        before = set(os.listdir(d))
        assert K.wait_for_download(fake, before, timeout=1) is None

        # .crdownload가 사라지고 PDF가 생기면 그 파일을 집는다
        part = os.path.join(d, "새리포트.pdf.crdownload")
        open(part, "w").close()

        def finish():
            time.sleep(0.6)
            os.rename(part, os.path.join(d, "새리포트.pdf"))

        t = threading.Thread(target=finish)
        t.start()
        got = K.wait_for_download(fake, before, timeout=5)
        t.join()
        assert got == os.path.join(d, "새리포트.pdf"), got

        # 받는 중(.crdownload만 존재)에는 기다리다 포기한다
        open(os.path.join(d, "받는중.pdf.crdownload"), "w").close()
        before2 = {"이전리포트.pdf", "새리포트.pdf"}
        assert K.wait_for_download(fake, before2, timeout=1) is None


def test_stale_crdownload_not_stolen():
    """앞 리포트가 타임아웃으로 남긴 .crdownload가 뒤늦게 완성되어도
    다음 리포트의 다운로드로 착각하면 안 된다."""
    with tempfile.TemporaryDirectory() as d:
        fake = SimpleNamespace(download_dir=d)

        # A가 타임아웃되어 .crdownload를 남긴 상태에서 B를 클릭한다
        stale = os.path.join(d, "A리포트.pdf.crdownload")
        open(stale, "w").close()
        before = set(os.listdir(d))  # .crdownload가 before에 포함된다

        # A가 뒤늦게 완성되면 A.pdf는 '새 파일'로 보인다
        os.rename(stale, os.path.join(d, "A리포트.pdf"))

        # B의 다운로드가 아니므로 집으면 안 된다 -> B는 실패로 끝나야 한다
        assert K.wait_for_download(fake, before, timeout=1) is None


def test_ambiguous_multiple_new_pdfs():
    """새 PDF가 여러 개면 특정할 수 없으므로 아무거나 저장하지 않는다."""
    with tempfile.TemporaryDirectory() as d:
        fake = SimpleNamespace(download_dir=d)
        before = set()
        open(os.path.join(d, "하나.pdf"), "w").close()
        open(os.path.join(d, "둘.pdf"), "w").close()
        assert K.wait_for_download(fake, before, timeout=1) is None


if __name__ == "__main__":
    test_target_path()
    test_wait_for_download()
    test_stale_crdownload_not_stolen()
    test_ambiguous_multiple_new_pdfs()
    print("OK")
