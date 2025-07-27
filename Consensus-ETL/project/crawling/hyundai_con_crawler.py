import os
import re
import time
import base64
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 다운로드 경로 설정 (다른 크롤링 코드와 일치)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DOWNLOAD_DIR = os.path.join(PARENT_DIR, "consensus", "hyundai")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class EnhancedPrintDownloader:
    def __init__(self, download_dir=None):
        """
        PDF 다운로더 초기화

        Args:
            download_dir (str): PDF 파일을 저장할 디렉토리 (기본값: project/consensus/hyundai)
        """
        self.base_url = "https://www.hmsec.com/mobile/research/research01_list.do?Menu_category=2"

        if download_dir is None:
            download_dir = DOWNLOAD_DIR

        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)
        self.driver = None

    def setup_driver(self):
        """Chrome 드라이버 설정 (DevTools Protocol 활성화)"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--run-all-compositor-stages-before-draw")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")

        # 다운로드 설정 (다른 크롤러와 일치)
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True,
        }
        options.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # DevTools Protocol 활성화
        driver.execute_cdp_cmd("Page.enable", {})

        return driver

    def get_report_list(self):
        """
        리포트 목록을 가져옵니다.

        Returns:
            list: 리포트 정보 리스트
        """
        if not self.driver:
            self.driver = self.setup_driver()

        logger.info("리포트 목록을 가져오는 중...")
        self.driver.get(self.base_url)
        time.sleep(3)

        reports = []
        seen_titles = set()  # 중복 제거를 위한 제목 집합

        try:
            report_elements = self.driver.find_elements(By.CSS_SELECTOR, "li")

            for element in report_elements:
                try:
                    text = element.text.strip()
                    if not text or ("Industry Report" not in text and "Conmpany Report" not in text):
                        continue

                    lines = text.split("\n")
                    if len(lines) >= 2:
                        title = lines[0].strip()
                        info = lines[1].strip()

                        # 중복 제목 체크
                        if title in seen_titles:
                            continue

                        if "|" in info:
                            report_type, date = info.split("|")
                            report_type = report_type.strip()
                            date = date.strip()
                        else:
                            report_type = info
                            date = ""

                        if element.is_enabled():
                            report_info = {"title": title, "type": report_type, "date": date}
                            reports.append(report_info)
                            seen_titles.add(title)  # 제목을 집합에 추가
                            logger.info(f"리포트 발견: {title} ({date})")

                except Exception as e:
                    logger.debug(f"리포트 정보 추출 중 오류: {e}")
                    continue

        except Exception as e:
            logger.error(f"리포트 목록 가져오기 실패: {e}")

        logger.info(f"총 {len(reports)}개의 리포트를 찾았습니다.")
        return reports

    def print_to_pdf(self, url, filename):
        """
        Chrome DevTools Protocol을 사용하여 페이지를 PDF로 저장합니다.

        Args:
            url (str): PDF로 저장할 페이지 URL
            filename (str): 저장할 파일명

        Returns:
            str: 저장된 파일 경로 또는 None
        """
        try:
            if not self.driver:
                self.driver = self.setup_driver()

            logger.info(f"페이지 로딩 중: {url}")
            self.driver.get(url)

            # 페이지 완전 로딩 대기
            time.sleep(10)

            # 스크롤하여 모든 콘텐츠 로드
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            logger.info(f"PDF 생성 중: {filename}")

            # Chrome DevTools Protocol을 사용하여 PDF 생성
            pdf_options = {
                "landscape": False,
                "displayHeaderFooter": False,
                "printBackground": True,
                "preferCSSPageSize": True,
                "paperWidth": 8.27,  # A4 width in inches
                "paperHeight": 11.69,  # A4 height in inches
                "marginTop": 0.4,
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4,
            }

            # PDF 생성 명령 실행
            result = self.driver.execute_cdp_cmd("Page.printToPDF", pdf_options)

            if "data" in result:
                # Base64 디코딩하여 PDF 파일 저장
                pdf_data = base64.b64decode(result["data"])

                filepath = os.path.join(self.download_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(pdf_data)

                logger.info(f"PDF 저장 완료: {filepath}")
                return filepath
            else:
                logger.error("PDF 생성 실패: 데이터가 없습니다.")
                return None

        except Exception as e:
            logger.error(f"PDF 생성 중 오류: {e}")
            return None

    def get_pdf_key_from_report(self, report_element):
        """리포트 요소에서 PDF key를 추출합니다."""
        try:
            if not self.driver:
                self.driver = self.setup_driver()

            # 리포트 클릭
            self.driver.execute_script("arguments[0].click();", report_element)
            time.sleep(3)

            # PDF 보기 버튼 클릭
            pdf_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'PDF 보기')]"))
            )

            self.driver.execute_script("arguments[0].click();", pdf_button)
            time.sleep(5)

            # PDF 뷰어 URL에서 key 추출
            current_url = self.driver.current_url
            if "key=" in current_url:
                key_match = re.search(r"key=([^&]+)", current_url)
                if key_match:
                    key = key_match.group(1)
                    logger.info(f"PDF key 추출 성공: {key}")
                    return key

            logger.warning("PDF key를 찾을 수 없습니다.")
            return None

        except Exception as e:
            logger.error(f"PDF key 추출 중 오류: {e}")
            return None

    def download_report_pdf(self, report_info):
        """개별 리포트를 PDF로 다운로드합니다."""
        try:
            # 새로운 드라이버 세션으로 리포트 목록 페이지 접근
            if not self.driver:
                self.driver = self.setup_driver()

            self.driver.get(self.base_url)
            time.sleep(3)

            # 리포트 목록에서 해당 리포트 찾기
            report_elements = self.driver.find_elements(By.CSS_SELECTOR, "li")
            target_element = None

            for element in report_elements:
                try:
                    text = element.text.strip()
                    if text and report_info["title"] in text:
                        target_element = element
                        break
                except:
                    continue

            if not target_element:
                logger.error(f"리포트 요소를 찾을 수 없음: {report_info['title']}")
                return None

            # PDF key 추출
            key = self.get_pdf_key_from_report(target_element)

            if not key:
                return None

            # PDF 뷰어 URL 생성
            viewer_url = f"https://docs.hmsec.com/SynapDocViewServer/viewer/doc.html?key={key}&convType=img&convLocale=ko_KR&contextPath=/SynapDocViewServer"

            # 파일명 생성
            safe_title = re.sub(r'[<>:"/\\|?*]', "", report_info["title"])
            safe_title = re.sub(r"\s+", "_", safe_title)[:50]
            filename = f"{report_info['date']}_{safe_title}_{key[:8]}.pdf"

            # PDF로 인쇄
            saved_file = self.print_to_pdf(viewer_url, filename)

            if saved_file:
                return {
                    "title": report_info["title"],
                    "type": report_info["type"],
                    "date": report_info["date"],
                    "file": saved_file,
                    "key": key,
                }

            return None

        except Exception as e:
            logger.error(f"리포트 다운로드 중 오류: {e}")
            return None

    def download_all_reports(self):
        """모든 리포트를 PDF로 다운로드합니다."""
        try:
            # 리포트 목록 가져오기
            reports = self.get_report_list()

            if not reports:
                logger.warning("다운로드할 리포트가 없습니다.")
                return []

            success_count = 0
            results = []

            for i, report in enumerate(reports, 1):
                logger.info(f"[{i}/{len(reports)}] 처리 중: {report['title']}")

                try:
                    # 각 리포트마다 새로운 드라이버 세션 사용
                    if self.driver:
                        self.driver.quit()
                        self.driver = None

                    result = self.download_report_pdf(report)

                    if result:
                        success_count += 1
                        results.append(result)
                        logger.info(f"✅ 다운로드 성공: {result['file']}")
                    else:
                        logger.warning(f"❌ 다운로드 실패: {report['title']}")

                except Exception as e:
                    logger.error(f"리포트 처리 중 오류 ({report['title']}): {e}")
                    # 드라이버 재설정
                    if self.driver:
                        self.driver.quit()
                        self.driver = None

            # 결과 요약
            logger.info(f"다운로드 완료: {success_count}/{len(reports)}개 성공")

            # 결과를 JSON 파일로 저장
            if results:
                result_file = os.path.join(
                    self.download_dir, f"download_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                logger.info(f"다운로드 결과 저장: {result_file}")

            return results

        except Exception as e:
            logger.error(f"다운로드 중 오류 발생: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()


def main():
    """메인 함수"""
    print("🚀 현대증권 PDF 다운로더")
    print("=" * 60)

    # 기본 다운로드 디렉토리 사용
    download_dir = DOWNLOAD_DIR

    print(f"🔄 모든 리포트를 {download_dir}에 다운로드합니다...")
    print("⏳ 잠시만 기다려주세요...\n")

    # 다운로더 실행
    downloader = EnhancedPrintDownloader(download_dir)

    try:
        results = downloader.download_all_reports()

        print("\n" + "=" * 60)
        print("📋 다운로드 결과")
        print("=" * 60)

        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   📅 날짜: {result['date']}")
                print(f"   📄 파일: {os.path.basename(result['file'])}")
                print(f"   🔑 키: {result['key'][:16]}...")
                print()

            print(f"✅ 총 {len(results)}개의 PDF 파일이 성공적으로 다운로드되었습니다!")
            print(f"📂 저장 위치: {os.path.abspath(download_dir)}")
        else:
            print("❌ 다운로드된 파일이 없습니다.")

    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()
