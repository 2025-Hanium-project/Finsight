import pdfplumber
import pandas as pd
import re
import uuid
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 로깅 설정
logging.getLogger("pdfminer").setLevel(logging.ERROR)


@dataclass
class ParsedReportData:
    """파싱된 리포트 데이터 구조"""

    report_id: str
    stock_code: str
    stock_name: str
    report_title: str
    report_date: str
    report_type: str
    analyst_name: str
    company_name: str
    rating: str
    opinion_change: str
    target_price: Optional[int]
    current_price: Optional[int]
    upside_potential: Optional[float]
    investment_rationale: str
    created_at: str

    def __post_init__(self):
        """데이터 검증"""
        if not self.stock_code or len(self.stock_code) != 6:
            raise ValueError(f"잘못된 종목코드: {self.stock_code}")

        if self.target_price and self.target_price <= 0:
            raise ValueError(f"잘못된 목표가: {self.target_price}")

        if not self.stock_name or len(self.stock_name.strip()) == 0:
            raise ValueError("종목명이 비어있습니다")


class ParsingPatterns:
    """정규표현식 패턴 관리 클래스 - BNK투자증권 특화"""

    # BNK투자증권 특화 패턴
    STOCK_PATTERNS = [
        r"([가-힣A-Za-z\s&\(\)]+)\s*\((\d{6})\)",  # "동원개발 (013120)" 형태
        r"\((\d{6})\)\s*([가-힣A-Za-z\s&]+)",  # "(013120) 동원개발" 형태
    ]

    PRICE_PATTERNS = {
        "target": [
            r"목표주가\(([^)]*)\)\s*\[유지\]\s*([0-9,]+)원?",  # "목표주가(6M) [유지] 2,700원"
            r"목표주가\(([^)]*)\)\s*([0-9,]+)원?",  # "목표주가(6M) 2,700원"
            r"목표주가[:\s]*([0-9,]+)원?",
            r"Target Price[:\s]*([0-9,]+)원?",
        ],
        "current": [
            r"현재주가\s*(\d{4}/\d{1,2}/\d{1,2})\s*([0-9,]+)원?",  # "현재주가 2025/5/21 2,365원"
            r"주가\([^)]*\)[:\s]*([0-9,]+)원?",
            r"현재가[:\s]*([0-9,]+)원?",
        ],
    }

    ANALYST_PATTERNS = [
        r"([가-힣]{2,4})\s+건설/건자재\s+[\w@.]+",  # "이선일 건설/건자재 sunillee@bnkfn.co.kr"
        r"([가-힣]{2,4})\s+[\w/]+\s+[\w@.]+",  # 일반적인 애널리스트 패턴
        r"애널리스트[:\s]*([가-힣]{2,4})",
        r"작성자[:\s]*([가-힣]{2,4})",
        r"연구원[:\s]*([가-힣]{2,4})",
    ]

    RATING_PATTERNS = [
        r"투자의견\s*\[유지\]\s*(보유|매수|매도)",  # "투자의견 [유지] 보유"
        r"투자의견\s*(보유|매수|매도)",
        r"(BUY|SELL|HOLD|매수|매도|중립|보유|Not Rated)",
    ]

    DATE_PATTERNS = [
        r"(\d{4})/(\d{1,2})/(\d{1,2})",  # "2025/5/22"
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",  # "2025년 05월 22일"
        r"(\d{4})-(\d{1,2})-(\d{1,2})",  # "2025-05-22"
        r"(\d{4})\.(\d{1,2})\.(\d{1,2})",  # "2025.05.22"
    ]

    # BNK투자증권 특화 패턴
    UPSIDE_PATTERNS = [
        r"(\d+\.?\d*)%",  # "14.2%" 형태
    ]


class ParserConfig:
    """파서 설정 클래스"""

    # 기본 경로 설정
    DEFAULT_PDF_FOLDER = "../consensus/bnk"
    DEFAULT_OUTPUT_PATH = "../consensus_parsed/bnk_consensus_reports.csv"

    # BNK투자증권 고정 정보
    COMPANY_NAME = "BNK투자증권"

    # 로깅 레벨
    LOG_LEVEL = logging.INFO

    # 투자 근거 추출 영역 (BNK투자증권 리포트 기준)
    RATIONALE_START_KEYWORDS = ["1Q25 실적:", "관계사 물량으로", "투자의견", "분석", "요약", "전망"]


class BaseParser(ABC):
    """파서 기본 클래스"""

    def __init__(self, log_level=ParserConfig.LOG_LEVEL):
        self.logger = self._setup_logger(log_level)

    def _setup_logger(self, level):
        """로거 설정"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger


class PDFTextExtractor(BaseParser):
    """PDF 텍스트 추출 클래스"""

    def extract_text(self, pdf_path: str) -> Optional[str]:
        """PDF에서 텍스트 추출"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    raise ValueError("PDF에 페이지가 없습니다")

                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if not text.strip():
                raise ValueError("PDF에서 텍스트를 추출할 수 없습니다")

            self.logger.info(f"텍스트 추출 완료: {len(text)}자")
            return text

        except Exception as e:
            self.logger.error(f"PDF 텍스트 추출 오류: {e}")
            raise


class StockInfoParser(BaseParser):
    """종목 정보 파싱 클래스"""

    def parse_stock_info(self, text: str) -> Tuple[str, str]:
        """종목명과 종목코드 추출"""
        self.logger.info("종목 정보 파싱 시작")

        stock_name = None
        stock_code = None

        for i, pattern in enumerate(ParsingPatterns.STOCK_PATTERNS):
            match = re.search(pattern, text)
            if match:
                if i == 0:  # 첫 번째 패턴: 종목명 (코드)
                    raw_name = match.group(1).strip()
                    stock_code = match.group(2)
                else:  # 두 번째 패턴: (코드) 종목명
                    stock_code = match.group(1)
                    raw_name = match.group(2).strip()

                # 종목명 정리
                stock_name = self._clean_stock_name(raw_name)
                self.logger.info(f"패턴 {i+1}에서 발견: {stock_name} ({stock_code})")
                break

        # 기본값 설정
        if not stock_name:
            stock_name = "Unknown"
        if not stock_code:
            stock_code = "000000"

        self.logger.info(f"종목 정보 파싱 완료: {stock_name} ({stock_code})")
        return stock_name, stock_code

    def _clean_stock_name(self, raw_name: str) -> str:
        """종목명 정리"""
        if not raw_name:
            return "Unknown"

        # 불필요한 텍스트 제거
        clean_name = re.sub(r"(기업분석|I\s+기업분석)", "", raw_name, flags=re.IGNORECASE)
        clean_name = re.sub(r"(주식회사|㈜|\(주\))", "", clean_name, flags=re.IGNORECASE)
        clean_name = re.sub(r"[\n\r]+", " ", clean_name)
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        return clean_name if clean_name else "Unknown"


class PriceInfoParser(BaseParser):
    """가격 정보 파싱 클래스"""

    def parse_price_info(self, text: str) -> Tuple[Optional[int], Optional[int], Optional[float]]:
        """현재가, 목표가, 상승여력 추출"""
        self.logger.info("가격 정보 파싱 시작")

        target_price = self._extract_target_price(text)
        current_price = self._extract_current_price(text)
        upside_potential = self._extract_upside_potential(text)

        # 상승여력이 직접 추출되지 않으면 계산
        if not upside_potential and current_price and target_price:
            upside_potential = self._calculate_upside(current_price, target_price)

        self.logger.info(
            f"가격 정보 파싱 완료 - 현재가: {current_price}, 목표가: {target_price}, 상승여력: {upside_potential}%"
        )
        return current_price, target_price, upside_potential

    def _extract_target_price(self, text: str) -> Optional[int]:
        """목표가 추출"""
        for pattern in ParsingPatterns.PRICE_PATTERNS["target"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # 튜플인 경우 마지막 요소가 가격
                    price_str = matches[0][-1].replace(",", "")
                else:
                    price_str = matches[0].replace(",", "")

                if price_str.isdigit():
                    price = int(price_str)
                    self.logger.info(f"목표가 발견: {price:,}원")
                    return price
                elif price_str in ["N/A", "NA", "-"]:
                    self.logger.info("목표가: N/A")
                    return None
        return None

    def _extract_current_price(self, text: str) -> Optional[int]:
        """현재가 추출"""
        for pattern in ParsingPatterns.PRICE_PATTERNS["current"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # 튜플인 경우 마지막 요소가 가격
                    price_str = matches[0][-1].replace(",", "")
                else:
                    price_str = matches[0].replace(",", "")

                if price_str.isdigit():
                    price = int(price_str)
                    self.logger.info(f"현재가 발견: {price:,}원")
                    return price
        return None

    def _extract_upside_potential(self, text: str) -> Optional[float]:
        """상승여력 직접 추출 (BNK투자증권 리포트에서 제공하는 경우)"""
        # 목표주가 근처에서 상승여력 찾기
        target_section = re.search(r"목표주가.*?(\d+\.?\d*)%", text, re.DOTALL)
        if target_section:
            upside_str = target_section.group(1)
            try:
                upside = float(upside_str)
                self.logger.info(f"상승여력 발견: {upside}%")
                return upside
            except ValueError:
                pass
        return None

    def _calculate_upside(self, current_price: Optional[int], target_price: Optional[int]) -> Optional[float]:
        """상승여력 계산"""
        if current_price and target_price:
            upside = round(((target_price - current_price) / current_price) * 100, 1)
            return upside
        return None


class AnalystInfoParser(BaseParser):
    """애널리스트 정보 파싱 클래스"""

    def parse_analyst_info(self, text: str) -> Tuple[str, str]:
        """애널리스트명과 증권사명 추출"""
        self.logger.info("애널리스트 정보 파싱 시작")

        analyst_name = self._extract_analyst_name(text)
        company_name = ParserConfig.COMPANY_NAME  # BNK투자증권 고정

        self.logger.info(f"애널리스트 정보 파싱 완료: {analyst_name} ({company_name})")
        return analyst_name, company_name

    def _extract_analyst_name(self, text: str) -> str:
        """애널리스트명 추출"""
        for pattern in ParsingPatterns.ANALYST_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1)
                self.logger.info(f"애널리스트 발견: {name}")
                return name

        return "Unknown"


class RatingParser(BaseParser):
    """투자등급 파싱 클래스"""

    def parse_rating_info(self, text: str) -> Tuple[str, str]:
        """투자등급과 의견변경 추출"""
        self.logger.info("투자등급 정보 파싱 시작")

        rating, opinion_change = self._extract_rating_and_change(text)

        self.logger.info(f"투자등급 정보 파싱 완료: {rating} ({opinion_change})")
        return rating, opinion_change

    def _extract_rating_and_change(self, text: str) -> Tuple[str, str]:
        """투자등급과 의견변경 동시 추출"""
        # BNK투자증권 특화: "투자의견 [유지] 보유" 패턴
        maintain_pattern = r"투자의견\s*\[유지\]\s*(보유|매수|매도)"
        match = re.search(maintain_pattern, text, re.IGNORECASE)
        if match:
            rating_text = match.group(1)
            rating = self._normalize_rating(rating_text)
            return rating, "유지"

        # 일반적인 투자의견 패턴
        for pattern in ParsingPatterns.RATING_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rating_text = match.group(1) if len(match.groups()) >= 1 else match.group(0)
                rating = self._normalize_rating(rating_text)

                # 의견변경 추출 시도
                opinion_change = self._extract_opinion_change(text)
                return rating, opinion_change

        return "Not Rated", "유지"  # 기본값

    def _normalize_rating(self, rating_text: str) -> str:
        """등급 정규화"""
        rating_text = rating_text.upper().strip()

        if rating_text in ["BUY", "매수"]:
            return "매수"
        elif rating_text in ["SELL", "매도"]:
            return "매도"
        elif rating_text in ["HOLD", "중립", "보유"]:
            return "보유"
        elif rating_text == "NOT RATED":
            return "Not Rated"
        else:
            return rating_text

    def _extract_opinion_change(self, text: str) -> str:
        """의견변경 추출"""
        change_patterns = [
            r"\[(유지|상향|하향|신규|New)\]",
            r"(Maintain|유지|상향|하향|신규|New)",
        ]

        for pattern in change_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                change_text = match.group(1).lower()
                if change_text in ["maintain", "유지"]:
                    return "유지"
                elif change_text in ["new", "신규"]:
                    return "신규"
                elif change_text in ["상향"]:
                    return "상향"
                elif change_text in ["하향"]:
                    return "하향"
                else:
                    return change_text

        return "유지"  # 기본값


class ReportInfoParser(BaseParser):
    """리포트 메타정보 파싱 클래스"""

    def parse_report_info(self, text: str, filename: str) -> Tuple[str, str]:
        """리포트 제목과 날짜 추출"""
        self.logger.info("리포트 정보 파싱 시작")

        report_title = self._extract_report_title(text)
        report_date = self._extract_report_date(text, filename)

        self.logger.info(f"리포트 정보 파싱 완료: {report_title} ({report_date})")
        return report_title, report_date

    def _extract_report_title(self, text: str) -> str:
        """리포트 제목 추출"""
        lines = text.split("\n")

        # BNK투자증권 특화: "기업분석 리포트" 다음 줄들에서 제목 찾기
        for i, line in enumerate(lines):
            if "기업분석 리포트" in line:
                # 다음 몇 줄에서 의미있는 제목 찾기
                for j in range(i + 1, min(i + 10, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and len(candidate) >= 5 and not re.match(r"^\d|투자의견|목표주가", candidate):
                        if "터닝포인트가 될" in candidate or len(candidate) >= 10:
                            return candidate

            # 종목명 다음에 나오는 긴 텍스트를 제목으로 추정
            if re.search(r"\(\d{6}\)", line):  # 종목코드가 있는 줄 찾기
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and len(candidate) >= 10:
                        return candidate

        return "기업분석 리포트"

    def _extract_report_date(self, text: str, filename: str) -> str:
        """리포트 날짜 추출"""
        # 텍스트 첫 부분에서 날짜 추출 시도
        first_lines = "\n".join(text.split("\n")[:20])

        for pattern in ParsingPatterns.DATE_PATTERNS:
            match = re.search(pattern, first_lines)
            if match:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # 파일명에서 날짜 추출 시도
        date_match = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", filename)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month}-{day}"

        # 기본값
        return datetime.now().strftime("%Y-%m-%d")


class InvestmentRationaleExtractor(BaseParser):
    """투자 근거 추출 클래스"""

    def extract_investment_rationale(self, text: str) -> str:
        """투자 근거 추출"""
        self.logger.info("투자 근거 추출 시작")

        # BNK투자증권 리포트의 주요 분석 내용 추출
        rationale_sections = []

        # 주요 섹션들 추출
        key_sections = [
            r"1Q25 실적:.*?(?=\n\n|\n[가-힣]+:|$)",
            r"관계사 물량으로.*?(?=\n\n|\n[가-힣]+:|$)",
            r"투자의견.*?(?=\n\n|\n[가-힣]+:|$)",
        ]

        for pattern in key_sections:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                for match in matches:
                    cleaned_match = self._clean_section_text(match)
                    if len(cleaned_match) >= 50:
                        rationale_sections.append(cleaned_match)

        # 추가로 의미있는 문단들 추출
        paragraphs = text.split("\n\n")
        for paragraph in paragraphs[:10]:  # 처음 10개 문단만 검토
            cleaned_paragraph = paragraph.strip()
            if self._is_meaningful_paragraph(cleaned_paragraph):
                rationale_sections.append(cleaned_paragraph)

        # 결합 및 정리
        if rationale_sections:
            combined_rationale = " ".join(rationale_sections)
            final_rationale = self._clean_rationale_text(combined_rationale)
            self.logger.info(f"투자 근거 추출 완료: {len(final_rationale)}자")
            return final_rationale

        return "투자 근거 정보 없음"

    def _clean_section_text(self, text: str) -> str:
        """섹션 텍스트 정리"""
        # 줄바꿈을 공백으로 변환
        text = re.sub(r"\n+", " ", text)
        # 연속된 공백 정리
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _is_meaningful_paragraph(self, paragraph: str) -> bool:
        """의미 있는 문단인지 판단"""
        if len(paragraph) < 100:
            return False

        # 제외할 패턴들
        exclude_patterns = [
            r"^\d{4}/\d{1,2}/\d{1,2}",  # 날짜로 시작
            r"^Fig\.",  # 그림 캡션
            r"^자료:",  # 자료 출처
            r"^주:",  # 주석
            r"BNK투자증권",  # 회사명
        ]

        for pattern in exclude_patterns:
            if re.search(pattern, paragraph):
                return False

        # 포함할 키워드들
        include_keywords = [
            "매출",
            "영업이익",
            "성장",
            "실적",
            "수익",
            "전망",
            "예상",
            "기대",
            "개선",
            "증가",
            "상승",
            "긍정",
            "호조",
            "경쟁력",
            "시장",
            "사업",
            "자체사업",
            "관계사",
            "프로젝트",
            "수주",
            "건설",
            "개발",
        ]

        keyword_count = sum(1 for keyword in include_keywords if keyword in paragraph)
        return keyword_count >= 2

    def _clean_rationale_text(self, text: str) -> str:
        """투자 근거 텍스트 최종 정리"""
        if not text:
            return "투자 근거 정보 없음"

        # 기본 정리
        text = re.sub(r"\s+", " ", text)  # 연속된 공백 정리

        # 불필요한 정보 제거
        unwanted_patterns = [
            r"BNK투자증권\s*리서치센터",
            r"\d{5}\s*서울시.*?층",
            r"www\.bnkfn\.co\.kr",
            r"Fig\.\s*\d+:.*?(?=\s|$)",
            r"자료:.*?(?=\s[가-힣]|$)",
        ]

        for pattern in unwanted_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # 최종 정리
        text = re.sub(r"\s+", " ", text).strip()

        return text if len(text) >= 50 else "투자 근거 정보 없음"


class BNKConsensusParser(BaseParser):
    """BNK투자증권 컨센서스 파서 메인 클래스"""

    def __init__(self, log_level=ParserConfig.LOG_LEVEL):
        super().__init__(log_level)
        self.data_list: List[Dict[str, Any]] = []

        # 파서 컴포넌트 초기화
        self.text_extractor = PDFTextExtractor(log_level)
        self.stock_parser = StockInfoParser(log_level)
        self.price_parser = PriceInfoParser(log_level)
        self.analyst_parser = AnalystInfoParser(log_level)
        self.rating_parser = RatingParser(log_level)
        self.report_parser = ReportInfoParser(log_level)
        self.rationale_extractor = InvestmentRationaleExtractor(log_level)

    def parse_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """PDF 파싱 메인 함수"""
        self.logger.info(f"PDF 파싱 시작: {pdf_path}")

        try:
            # 텍스트 추출
            text = self.text_extractor.extract_text(pdf_path)
            filename = os.path.basename(pdf_path)

            # 각 정보 추출
            stock_name, stock_code = self.stock_parser.parse_stock_info(text)
            current_price, target_price, upside_potential = self.price_parser.parse_price_info(text)
            analyst_name, company_name = self.analyst_parser.parse_analyst_info(text)
            rating, opinion_change = self.rating_parser.parse_rating_info(text)
            report_title, report_date = self.report_parser.parse_report_info(text, filename)
            investment_rationale = self.rationale_extractor.extract_investment_rationale(text)

            # 데이터 구성
            data = {
                "report_id": str(uuid.uuid4()),
                "stock_code": stock_code,
                "stock_name": stock_name,
                "report_title": report_title,
                "report_date": report_date,
                "report_type": "기업분석",
                "analyst_name": analyst_name,
                "company_name": company_name,
                "rating": rating,
                "opinion_change": opinion_change,
                "target_price": target_price,
                "current_price": current_price,
                "upside_potential": upside_potential,
                "investment_rationale": investment_rationale,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 데이터 검증
            try:
                parsed_data = ParsedReportData(**data)
                self.data_list.append(data)
                self.logger.info(f"파싱 완료: {stock_name} ({stock_code})")
                return data
            except ValueError as e:
                self.logger.error(f"데이터 검증 오류: {e}")
                return None

        except Exception as e:
            self.logger.error(f"PDF 파싱 오류: {e}")
            return None

    def process_all_pdfs(self, pdf_folder_path: str) -> None:
        """폴더 내 모든 PDF 파일 처리"""
        self.logger.info(f"PDF 폴더 스캔 시작: {pdf_folder_path}")

        if not os.path.exists(pdf_folder_path):
            raise FileNotFoundError(f"폴더가 존재하지 않습니다: {pdf_folder_path}")

        pdf_files = [f for f in os.listdir(pdf_folder_path) if f.endswith(".pdf")]

        if not pdf_files:
            self.logger.warning("PDF 파일이 없습니다.")
            return

        self.logger.info(f"발견된 PDF 파일: {len(pdf_files)}개")

        success_count = 0
        error_count = 0

        for i, pdf_file in enumerate(pdf_files):
            pdf_path = os.path.join(pdf_folder_path, pdf_file)
            self.logger.info(f"처리 중 ({i+1}/{len(pdf_files)}): {pdf_file}")

            try:
                result = self.parse_pdf(pdf_path)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.logger.error(f"파일 처리 오류 {pdf_file}: {e}")

        self.logger.info(f"처리 완료 - 성공: {success_count}개, 실패: {error_count}개")

    def save_to_csv(self, output_path: str) -> None:
        """CSV 파일로 저장"""
        if not self.data_list:
            self.logger.warning("저장할 데이터가 없습니다.")
            return

        try:
            df = pd.DataFrame(self.data_list)
            df["stock_code"] = df["stock_code"].astype(str)  # 종목코드 문자열 보장

            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            self.logger.info(f"CSV 파일 저장 완료: {output_path}")
            self.logger.info(f"총 {len(self.data_list)}개 리포트 저장")

        except Exception as e:
            self.logger.error(f"CSV 저장 오류: {e}")
            raise

    def get_summary_statistics(self) -> Dict[str, Any]:
        """요약 통계 반환"""
        if not self.data_list:
            return {}

        # 애널리스트별 통계
        analysts = {}
        ratings = {}
        target_prices = []
        sectors = {}

        for data in self.data_list:
            analyst = data["analyst_name"]
            rating = data["rating"]

            analysts[analyst] = analysts.get(analyst, 0) + 1
            ratings[rating] = ratings.get(rating, 0) + 1

            if data["target_price"]:
                target_prices.append(data["target_price"])

        # 목표가 통계
        price_stats = {}
        if target_prices:
            price_stats = {
                "avg_target_price": round(sum(target_prices) / len(target_prices)),
                "min_target_price": min(target_prices),
                "max_target_price": max(target_prices),
                "count_with_target": len(target_prices),
            }

        return {
            "total_reports": len(self.data_list),
            "analysts": analysts,
            "ratings": ratings,
            "price_statistics": price_stats,
            "company": ParserConfig.COMPANY_NAME,
        }


# 메인 실행 함수
def main():
    """메인 실행 함수"""
    print("BNK투자증권 컨센서스 리포트 파서 시작")
    print("=" * 60)

    parser = BNKConsensusParser()

    # 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_folder_path = os.path.join(current_dir, "..", "consensus", "bnk")
    output_path = os.path.join(current_dir, "..", "consensus_parsed", "bnk_consensus_reports.csv")

    try:
        # PDF 처리
        parser.process_all_pdfs(pdf_folder_path)

        # 결과 저장
        if parser.data_list:
            parser.save_to_csv(output_path)

            # 결과 출력
            print(f"\n{'='*80}")
            print("BNK투자증권 리포트 파싱 결과:")
            print(f"{'='*80}")

            for i, data in enumerate(parser.data_list):
                print(f"\n{i+1}. {data['stock_name']} ({data['stock_code']}) - {data['report_title']}")
                print(f"   리포트 날짜: {data['report_date']}")
                print(f"   애널리스트: {data['analyst_name']}")
                print(f"   투자의견: {data['rating']} ({data['opinion_change']})")

                if data["target_price"] and data["current_price"]:
                    upside = data["upside_potential"]
                    print(
                        f"   목표가: {data['target_price']:,}원, 현재가: {data['current_price']:,}원 (상승여력: {upside}%)"
                    )
                elif data["target_price"]:
                    print(f"   목표가: {data['target_price']:,}원")
                elif data["current_price"]:
                    print(f"   현재가: {data['current_price']:,}원")
                else:
                    print(f"   가격 정보: N/A")

                # 투자 근거 요약 출력 (처음 150자만)
                rationale = data["investment_rationale"]
                if len(rationale) > 150:
                    rationale_summary = rationale[:150] + "..."
                else:
                    rationale_summary = rationale
                print(f"   투자 근거: {rationale_summary}")

            # 요약 통계
            print(f"\n{'='*80}")
            print("파싱 요약 통계:")
            print(f"{'='*80}")

            stats = parser.get_summary_statistics()
            print(f"총 리포트 수: {stats.get('total_reports', 0)}개")
            print(f"증권사: {stats.get('company', 'N/A')}")

            # 애널리스트별 통계
            if "analysts" in stats and stats["analysts"]:
                print("\n애널리스트별 리포트 수:")
                for analyst, count in stats["analysts"].items():
                    print(f"  - {analyst}: {count}개")

            # 투자의견별 통계
            if "ratings" in stats and stats["ratings"]:
                print("\n투자의견별 분포:")
                for rating, count in stats["ratings"].items():
                    print(f"  - {rating}: {count}개")

            # 가격 통계
            if "price_statistics" in stats and stats["price_statistics"]:
                price_stats = stats["price_statistics"]
                print(f"\n목표가 통계:")
                print(f"  - 평균 목표가: {price_stats['avg_target_price']:,}원")
                print(f"  - 최고 목표가: {price_stats['max_target_price']:,}원")
                print(f"  - 최저 목표가: {price_stats['min_target_price']:,}원")
                print(f"  - 목표가 있는 리포트: {price_stats['count_with_target']}개")

            print(f"\nCSV 파일 저장 위치: {output_path}")

        else:
            print("파싱된 데이터가 없습니다.")
            print("PDF 파일이 올바른 위치에 있는지 확인해주세요.")
            print(f"예상 PDF 폴더 위치: {pdf_folder_path}")

    except FileNotFoundError as e:
        print(f"오류: {e}")
        print(f"PDF 폴더를 생성하거나 올바른 경로를 확인해주세요: {pdf_folder_path}")

    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print(f"\n{'='*60}")
        print("BNK투자증권 컨센서스 리포트 파서 종료")


# 단일 파일 테스트용 함수
def test_single_pdf(pdf_path: str):
    """단일 PDF 파일 테스트"""
    print(f"단일 PDF 파일 테스트: {pdf_path}")
    print("=" * 60)

    parser = BNKConsensusParser()

    try:
        result = parser.parse_pdf(pdf_path)

        if result:
            print("파싱 성공!")
            print(f"종목: {result['stock_name']} ({result['stock_code']})")
            print(f"제목: {result['report_title']}")
            print(f"날짜: {result['report_date']}")
            print(f"애널리스트: {result['analyst_name']}")
            print(f"투자의견: {result['rating']} ({result['opinion_change']})")

            if result["target_price"]:
                print(f"목표가: {result['target_price']:,}원")
            if result["current_price"]:
                print(f"현재가: {result['current_price']:,}원")
            if result["upside_potential"]:
                print(f"상승여력: {result['upside_potential']}%")

            print(f"투자근거: {result['investment_rationale'][:300]}...")
        else:
            print("파싱 실패")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback

        traceback.print_exc()


# 업로드된 PDF 테스트 함수
def test_uploaded_pdf():
    """업로드된 BNK투자증권 PDF 테스트"""
    print("BNK투자증권 업로드 PDF 테스트")
    print("=" * 60)

    # 실제 업로드된 PDF 내용을 기반으로 테스트
    sample_text = """
    2025/5/22 
    동원개발 (013120) 
    기업분석 리포트 
    투자의견 
    [유지] 
    보유 
    목표주가(6M) 
    [유지] 
    2,700원 
    14.2% 
    현재주가 
    2025/5/21 
    2,365원
    
    이선일 
    건설/건자재  
    sunillee@bnkfn.co.kr
    
    터닝포인트가 될 새로운 자체사업이 필요
    
    1Q25 실적: 자체사업 매출반영 종료로 외형과 이익 모두 급감 
    2025년 1분기 매출액은 909억원으로 전년동기대비 47.4% 감소했다.
    """

    parser = BNKConsensusParser()

    # 각 파서 컴포넌트 테스트
    print("1. 종목 정보 파싱:")
    stock_name, stock_code = parser.stock_parser.parse_stock_info(sample_text)
    print(f"   종목명: {stock_name}, 종목코드: {stock_code}")

    print("\n2. 가격 정보 파싱:")
    current_price, target_price, upside = parser.price_parser.parse_price_info(sample_text)
    print(f"   현재가: {current_price}, 목표가: {target_price}, 상승여력: {upside}%")

    print("\n3. 애널리스트 정보 파싱:")
    analyst, company = parser.analyst_parser.parse_analyst_info(sample_text)
    print(f"   애널리스트: {analyst}, 증권사: {company}")

    print("\n4. 투자등급 파싱:")
    rating, change = parser.rating_parser.parse_rating_info(sample_text)
    print(f"   투자등급: {rating}, 의견변경: {change}")

    print("\n5. 리포트 정보 파싱:")
    title, date = parser.report_parser.parse_report_info(sample_text, "test.pdf")
    print(f"   제목: {title}, 날짜: {date}")

    print("\n6. 투자 근거 추출:")
    rationale = parser.rationale_extractor.extract_investment_rationale(sample_text)
    print(f"   투자근거: {rationale[:200]}...")


# 스크립트 직접 실행 시
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 업로드된 PDF 테스트
            test_uploaded_pdf()
        else:
            # 명령행 인수가 있으면 단일 파일 테스트
            pdf_file = sys.argv[1]
            test_single_pdf(pdf_file)
    else:
        # 기본 실행
        main()
