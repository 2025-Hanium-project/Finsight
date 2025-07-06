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
    """정규표현식 패턴 관리 클래스"""

    # 하나증권 특화 패턴
    STOCK_PATTERNS = [
        r"([가-힣A-Za-z\s&\(\)]+)\s*\((\d{6})\)",  # "화신 (010690)" 형태
        r"\((\d{6})\)\s*([가-힣A-Za-z\s&]+)",  # "(010690) 화신" 형태
    ]

    PRICE_PATTERNS = {
        "target": [
            r"목표주가\([^)]*\)\s*([0-9,]+)원?",  # "목표주가(12M) 15,000원"
            r"목표주가\([^)]*\)\s*([A-Z/]+)",  # "목표주가(12M) N/A"
            r"목표주가[:\s]*([0-9,]+)원?",
            r"Target Price[:\s]*([0-9,]+)원?",
        ],
        "current": [
            r"현재주가\([^)]*\)\s*([0-9,]+)원?",  # "현재주가(05.16) 8,100원"
            r"주가\([^)]*\)[:\s]*([0-9,]+)원?",
            r"현재가[:\s]*([0-9,]+)원?",
        ],
    }

    ANALYST_PATTERNS = [
        r"Analyst\s+([가-힣]{2,4})",  # "Analyst 송선재"
        r"애널리스트[:\s]*([가-힣]{2,4})",
        r"작성자[:\s]*([가-힣]{2,4})",
        r"연구원[:\s]*([가-힣]{2,4})",
    ]

    RATING_PATTERNS = [
        r"(BUY|SELL|HOLD|매수|매도|중립|Not Rated)",
        r"투자의견[:\s]*(BUY|SELL|HOLD|매수|매도|중립)",
    ]

    DATE_PATTERNS = [
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",  # "2025년 05월 19일"
        r"(\d{4})-(\d{1,2})-(\d{1,2})",  # "2025-05-19"
        r"(\d{4})\.(\d{1,2})\.(\d{1,2})",  # "2025.05.19"
    ]


class ParserConfig:
    """파서 설정 클래스"""

    # 기본 경로 설정
    DEFAULT_PDF_FOLDER = "../consensus/hana"
    DEFAULT_OUTPUT_PATH = "../consensus_parsed/hana_consensus_reports.csv"

    # 하나증권 고정 정보
    COMPANY_NAME = "하나증권"

    # 로깅 레벨
    LOG_LEVEL = logging.INFO

    # 투자 근거 추출 영역 (하나증권 리포트 기준)
    RATIONALE_START_KEYWORDS = ["Review:", "전망:", "투자포인트", "투자의견", "분석", "요약"]


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
                price_str = matches[0].replace(",", "")
                if price_str.isdigit():
                    price = int(price_str)
                    self.logger.info(f"현재가 발견: {price:,}원")
                    return price
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
        company_name = ParserConfig.COMPANY_NAME  # 하나증권 고정

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

        rating = self._extract_rating(text)
        opinion_change = self._extract_opinion_change(text)

        self.logger.info(f"투자등급 정보 파싱 완료: {rating} ({opinion_change})")
        return rating, opinion_change

    def _extract_rating(self, text: str) -> str:
        """투자등급 추출"""
        for pattern in ParsingPatterns.RATING_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rating_text = match.group(1).upper()

                # 등급 정규화
                if rating_text in ["BUY", "매수"]:
                    return "매수"
                elif rating_text in ["SELL", "매도"]:
                    return "매도"
                elif rating_text in ["HOLD", "중립"]:
                    return "중립"
                elif rating_text == "NOT RATED":
                    return "Not Rated"
                else:
                    return rating_text

        return "Not Rated"  # 기본값

    def _extract_opinion_change(self, text: str) -> str:
        """의견변경 추출"""
        change_patterns = [
            r"(Maintain|유지|상향|하향|신규|New)",
            r"\((Maintain|유지|상향|하향|신규|New)\)",
        ]

        for pattern in change_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                change_text = match.group(1).lower()
                if change_text in ["maintain", "유지"]:
                    return "유지"
                elif change_text in ["new", "신규"]:
                    return "신규"
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

        # 종목명 다음 줄을 제목으로 추정
        for i, line in enumerate(lines):
            if re.search(r"\(\d{6}\)", line):  # 종목코드가 있는 줄 찾기
                if i + 1 < len(lines):
                    title = lines[i + 1].strip()
                    if title and len(title) >= 3:
                        return title

        return "분석리포트"

    def _extract_report_date(self, text: str, filename: str) -> str:
        """리포트 날짜 추출"""
        # 텍스트에서 날짜 추출 시도
        for pattern in ParsingPatterns.DATE_PATTERNS:
            match = re.search(pattern, text)
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

        # 하나증권 리포트의 주요 분석 내용 추출
        rationale_sections = []

        # Review 섹션 추출
        review_match = re.search(r"(Review:.*?)(?=\n\n|\n[A-Z]|$)", text, re.DOTALL)
        if review_match:
            rationale_sections.append(review_match.group(1))

        # 기타 분석 내용 추출 (첫 번째 단락들)
        lines = text.split("\n")
        meaningful_lines = []

        for line in lines[:50]:  # 처음 50줄만 검토
            line = line.strip()
            if line and self._is_meaningful_line(line):
                meaningful_lines.append(line)

        if meaningful_lines:
            combined_text = " ".join(meaningful_lines)
            rationale_sections.append(combined_text)

        # 결합 및 정리
        if rationale_sections:
            combined_rationale = " ".join(rationale_sections)
            cleaned_rationale = self._clean_rationale_text(combined_rationale)
            self.logger.info(f"투자 근거 추출 완료: {len(cleaned_rationale)}자")
            return cleaned_rationale

        return "투자 근거 정보 없음"

    def _is_meaningful_line(self, line: str) -> bool:
        """의미 있는 라인인지 판단"""
        if len(line) < 20:
            return False

        # 제외할 라인들
        exclude_patterns = [
            r"^\d{4}년\s+\d{1,2}월\s+\d{1,2}일",  # 날짜
            r"^Analyst\s+",  # 애널리스트 정보
            r"^목표주가",  # 목표주가 정보
            r"^현재주가",  # 현재주가 정보
            r"^Not Rated",  # 등급 정보
            r"하나증권•\d+",  # 페이지 정보
        ]

        for pattern in exclude_patterns:
            if re.search(pattern, line):
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
        ]

        return any(keyword in line for keyword in include_keywords)

    def _clean_rationale_text(self, text: str) -> str:
        """투자 근거 텍스트 정리"""
        if not text:
            return "투자 근거 정보 없음"

        # 기본 정리
        text = re.sub(r"\s+", " ", text)  # 연속된 공백 정리
        text = re.sub(r"[\r\n]+", " ", text)  # 줄바꿈 정리

        # 불필요한 정보 제거
        unwanted_patterns = [
            r"Analyst\s+[가-힣]+\s+[\w@.]+",  # 애널리스트 정보
            r"RA\s+[가-힣]+\s+[\w@.]+",  # RA 정보
            r"\d{4}년\s+\d{1,2}월\s+\d{1,2}일",  # 날짜 정보
            r"하나증권•\d+",  # 페이지 정보
        ]

        for pattern in unwanted_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # 최종 정리
        text = re.sub(r"\s+", " ", text).strip()

        return text if len(text) >= 30 else "투자 근거 정보 없음"


class HanaConsensusParser(BaseParser):
    """하나증권 컨센서스 파서 메인 클래스"""

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
    print("하나증권 컨센서스 리포트 파서 시작")
    print("=" * 60)

    parser = HanaConsensusParser()

    # 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_folder_path = os.path.join(current_dir, "..", "consensus", "hana")
    output_path = os.path.join(current_dir, "..", "consensus_parsed", "hana_consensus_reports.csv")

    try:
        # PDF 처리
        parser.process_all_pdfs(pdf_folder_path)

        # 결과 저장
        if parser.data_list:
            parser.save_to_csv(output_path)

            # 결과 출력
            print(f"\n{'='*80}")
            print("하나증권 리포트 파싱 결과:")
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

                # 투자 근거 요약 출력 (처음 100자만)
                rationale = data["investment_rationale"]
                if len(rationale) > 100:
                    rationale_summary = rationale[:100] + "..."
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
        print("하나증권 컨센서스 리포트 파서 종료")


# 단일 파일 테스트용 함수
def test_single_pdf(pdf_path: str):
    """단일 PDF 파일 테스트"""
    print(f"단일 PDF 파일 테스트: {pdf_path}")
    print("=" * 60)

    parser = HanaConsensusParser()

    try:
        result = parser.parse_pdf(pdf_path)

        if result:
            print("파싱 성공!")
            print(f"종목: {result['stock_name']} ({result['stock_code']})")
            print(f"제목: {result['report_title']}")
            print(f"애널리스트: {result['analyst_name']}")
            print(f"투자의견: {result['rating']}")
            print(f"목표가: {result['target_price']}")
            print(f"현재가: {result['current_price']}")
            print(f"투자근거: {result['investment_rationale'][:200]}...")
        else:
            print("파싱 실패")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback

        traceback.print_exc()


# 스크립트 직접 실행 시
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 명령행 인수가 있으면 단일 파일 테스트
        pdf_file = sys.argv[1]
        test_single_pdf(pdf_file)
    else:
        # 기본 실행
        main()
