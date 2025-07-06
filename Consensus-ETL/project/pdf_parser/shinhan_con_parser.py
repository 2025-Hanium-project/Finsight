#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
신한투자증권 PDF 리포트 파서 (개선 버전)
하나증권 파서의 구조를 참고하여 모듈화 및 안정성 개선
"""

import pdfplumber
import pandas as pd
import re
import uuid
from datetime import datetime
import os
import logging
import traceback
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# PDFMiner의 불필요한 로깅을 억제
logging.getLogger("pdfminer").setLevel(logging.ERROR)


@dataclass
class ParsedReportData:
    """파싱된 리포트 데이터 구조"""

    report_id: str
    file_name: str
    securities_company: str
    stock_name: str
    stock_code: str
    report_title: str
    report_date: str
    rating: str
    opinion_change: str
    target_price: Optional[int]
    current_price: Optional[int]
    analysts: List[str]
    parsing_date: str

    def __post_init__(self):
        """데이터 검증"""
        if not self.stock_name or len(self.stock_name.strip()) == 0:
            self.stock_name = "Unknown"

        if not self.stock_code or len(self.stock_code) != 6:
            self.stock_code = "000000"


class ShinhanParsingPatterns:
    """신한투자증권 파싱 패턴 관리 클래스"""

    # 종목 정보 패턴
    STOCK_PATTERNS = [
        r"([가-힣A-Za-z\s&]+)\s*\((\d{6})\)",  # "LG이노텍 (011070)" 형태
        r"\((\d{6})\)\s*([가-힣A-Za-z\s&]+)",  # "(011070) LG이노텍" 형태
        r"([가-힣A-Za-z\s&]+)\s*\(\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*\)",  # "LG이노텍 (0 1 1 0 7 0)" 형태
    ]

    # 종목명 후보 키워드
    STOCK_NAME_KEYWORDS = [
        "LG이노텍",
        "LG 이노텍",
        "삼성전자",
        "삼성 전자",
        "SK하이닉스",
        "SK 하이닉스",
        "현대차",
        "현대 차",
        "NAVER",
        "네이버",
        "LG화학",
        "LG 화학",
    ]

    # 가격 패턴
    TARGET_PRICE_PATTERNS = [
        r"목표주가[:\s]*([0-9,]+)원?",
        r"Target Price[:\s]*([0-9,]+)원?",
        r"목표가[:\s]*([0-9,]+)원?",
        r"(\d{1,3}(?:,\d{3})*)\s*원\s*\([^)]*하향[^)]*\)",
        r"(\d{1,3}(?:,\d{3})*)\s*원\s*\([^)]*상향[^)]*\)",
        r"(\d{1,3}(?:,\d{3})*)\s*원\s*\([^)]*유지[^)]*\)",
    ]

    CURRENT_PRICE_PATTERNS = [
        r"현재주가[:\s]*\([^)]*\)[:\s]*([0-9,]+)원?",
        r"현재가[:\s]*([0-9,]+)원?",
        r"기준가[:\s]*([0-9,]+)원?",
        r"주가[:\s]*([0-9,]+)원?(?!.*목표)",
        r"(\d{1,3}(?:,\d{3})*)\s*원\s*오강호",
    ]

    # 애널리스트 패턴
    ANALYST_PATTERNS = [
        r"([가-힣]{2,4})\s*연구위원",
        r"([가-힣]{2,4})\s*연구원",
        r"연구위원[:\s]*([가-힣]{2,4})",
        r"연구원[:\s]*([가-힣]{2,4})",
        r"Analyst[:\s]*([가-힣]{2,4})",
        r"애널리스트[:\s]*([가-힣]{2,4})",
        r"작성자[:\s]*([가-힣]{2,4})",
        r"([가-힣]{2,4})\s*애널리스트",
    ]

    # 필터링용 키워드
    ANALYST_EXCLUDE_KEYWORDS = [
        "신한생각",
        "신한투자",
        "신한증권",
        "컨센서스",
        "리포트",
        "분석",
        "투자",
        "매수",
        "매도",
        "중립",
        "상향",
        "하향",
        "유지",
        "목표",
        "주가",
        "수익성",
        "개선",
        "필요",
        "전기전자",
        "실적",
        "부진",
        "지속",
        "방향성",
    ]

    # 투자의견 매핑
    RATING_KEYWORDS = {
        "매수": "매수",
        "BUY": "매수",
        "Buy": "매수",
        "매도": "매도",
        "SELL": "매도",
        "Sell": "매도",
        "중립": "중립",
        "HOLD": "중립",
        "Hold": "중립",
        "Trading BUY": "중립",
        "축소": "매도",
        "비중확대": "매수",
        "비중축소": "매도",
    }

    # 의견변화 매핑
    OPINION_CHANGE_KEYWORDS = {
        "유지": "유지",
        "Maintain": "유지",
        "상향": "상향",
        "UP": "상향",
        "Upgrade": "상향",
        "하향": "하향",
        "DOWN": "하향",
        "Downgrade": "하향",
        "신규": "신규",
        "NEW": "신규",
        "Initiate": "신규",
    }

    # 날짜 패턴
    DATE_PATTERNS = [
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})",
        r"(\d{1,2})월\s*(\d{1,2})일",
        r"(\d{1,2})/(\d{1,2})",
    ]


class BaseParser:
    """파서 기본 클래스"""

    def __init__(self, log_level=logging.INFO):
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


class ShinhanConsensusParser(BaseParser):
    """신한투자증권 PDF 리포트 파서 (개선 버전)"""

    def __init__(self, log_level=logging.INFO):
        super().__init__(log_level)
        self.data_list: List[Dict[str, Any]] = []

    def parse_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """PDF 파일을 파싱하여 주요 정보 추출"""

        self.logger.info(f"PDF 파싱 시작: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    raise ValueError("PDF에 페이지가 없습니다")

                # 첫 번째 페이지에서 주요 정보 추출
                first_page = pdf.pages[0]

                # 텍스트 추출
                text = first_page.extract_text()
                if not text:
                    raise ValueError("페이지에서 텍스트를 추출할 수 없습니다")

                filename = os.path.basename(pdf_path)

                # 각 정보 추출
                stock_name, stock_code = self._parse_stock_info(text, filename)
                target_price = self._extract_target_price(text)
                current_price = self._extract_current_price(text)
                rating = self._extract_rating(text)
                opinion_change = self._extract_opinion_change(text)
                analysts = self._extract_analysts(text)
                report_title = self._extract_report_title(text, filename)
                report_date = self._extract_report_date(text)

                # 데이터 구성
                data = {
                    "report_id": str(uuid.uuid4()),
                    "file_name": filename,
                    "securities_company": "신한투자증권",
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "report_title": report_title,
                    "report_date": report_date,
                    "rating": rating,
                    "opinion_change": opinion_change,
                    "target_price": target_price,
                    "current_price": current_price,
                    "analysts": analysts,
                    "parsing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # 데이터 검증
                try:
                    parsed_data = ParsedReportData(**data)
                    self.data_list.append(data)
                    self.logger.info(f"파싱 완료: {stock_name} ({stock_code})")
                    return data
                except Exception as e:
                    self.logger.error(f"데이터 검증 오류: {e}")
                    return None

        except Exception as e:
            self.logger.error(f"PDF 파싱 중 오류 발생: {e}")
            return None

    def _parse_stock_info(self, text: str, filename: str) -> Tuple[str, str]:
        """종목 정보 추출"""

        # 파일명에서 우선 추출 시도
        for stock_name in ShinhanParsingPatterns.STOCK_NAME_KEYWORDS:
            if stock_name in filename:
                clean_name = stock_name.replace(" ", "")
                self.logger.info(f"파일명에서 종목명 추출: {clean_name}")

                # 텍스트에서 종목코드 찾기
                code_match = re.search(r"(\d{6})", text)
                if code_match:
                    return clean_name, code_match.group(1)
                return clean_name, "000000"

        # 텍스트에서 패턴 매칭
        for pattern in ShinhanParsingPatterns.STOCK_PATTERNS:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()

                if len(groups) == 2:
                    if groups[1].isdigit() and len(groups[1]) == 6:
                        name = groups[0].strip()
                        code = groups[1]
                        self.logger.info(f"텍스트에서 종목 정보 추출: {name} ({code})")
                        return name, code
                    elif groups[0].isdigit() and len(groups[0]) == 6:
                        code = groups[0]
                        name = groups[1].strip()
                        self.logger.info(f"텍스트에서 종목 정보 추출: {name} ({code})")
                        return name, code

        # 기본값 반환
        return "Unknown", "000000"

    def _extract_target_price(self, text: str) -> Optional[int]:
        """목표주가 추출"""

        for pattern in ShinhanParsingPatterns.TARGET_PRICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(",", "")
                    price = int(price_str)
                    self.logger.info(f"목표주가 추출: {price:,}원")
                    return price
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_current_price(self, text: str) -> Optional[int]:
        """현재주가 추출"""

        for pattern in ShinhanParsingPatterns.CURRENT_PRICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(",", "")
                    price = int(price_str)
                    self.logger.info(f"현재주가 추출: {price:,}원")
                    return price
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_rating(self, text: str) -> str:
        """투자의견 추출"""

        for keyword, rating in ShinhanParsingPatterns.RATING_KEYWORDS.items():
            if keyword in text:
                self.logger.info(f"투자의견 추출: {rating}")
                return rating
        return "Not Rated"

    def _extract_opinion_change(self, text: str) -> str:
        """의견 변화 추출"""

        for keyword, change in ShinhanParsingPatterns.OPINION_CHANGE_KEYWORDS.items():
            if keyword in text:
                self.logger.info(f"의견변화 추출: {change}")
                return change
        return "유지"

    def _extract_analysts(self, text: str) -> List[str]:
        """애널리스트 이름 추출"""

        analysts = []
        for pattern in ShinhanParsingPatterns.ANALYST_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    analyst_name = match[0]
                else:
                    analyst_name = match

                # 필터링
                if (
                    analyst_name
                    and len(analyst_name) >= 2
                    and analyst_name not in ShinhanParsingPatterns.ANALYST_EXCLUDE_KEYWORDS
                    and not any(keyword in analyst_name for keyword in ShinhanParsingPatterns.ANALYST_EXCLUDE_KEYWORDS)
                ):
                    analysts.append(analyst_name)

        # 중복 제거
        unique_analysts = list(set(analysts))
        if unique_analysts:
            self.logger.info(f"애널리스트 추출: {', '.join(unique_analysts)}")
        return unique_analysts

    def _extract_report_title(self, text: str, filename: str) -> str:
        """리포트 제목 추출"""

        # 파일명에서 제목 추출 시도
        if "_" in filename:
            parts = filename.replace(".pdf", "").split("_")
            if len(parts) >= 2:
                potential_title = parts[1]
                if potential_title and len(potential_title) > 1:
                    self.logger.info(f"파일명에서 제목 추출: {potential_title}")
                    return potential_title

        # 텍스트에서 제목 찾기
        lines = text.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if (
                line
                and not any(
                    keyword in line
                    for keyword in ["COMPANY REPORT", "투자판단", "목표주가", "연구위원", "연구원", "년", "월", "일"]
                )
                and len(line) > 2
                and len(line) < 50
            ):
                self.logger.info(f"텍스트에서 제목 추출: {line}")
                return line

        return "분석리포트"

    def _extract_report_date(self, text: str) -> str:
        """리포트 날짜 추출"""

        for pattern in ShinhanParsingPatterns.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(0)
                self.logger.info(f"리포트 날짜 추출: {date_str}")
                return date_str

        # 기본값
        return datetime.now().strftime("%Y-%m-%d")

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
                    print(f"✅ {pdf_file} 파싱 완료")
                    print(self.get_summary(result))
                else:
                    error_count += 1
                    print(f"❌ {pdf_file} 파싱 실패")
            except Exception as e:
                error_count += 1
                self.logger.error(f"파일 처리 오류 {pdf_file}: {e}")
                print(f"❌ {pdf_file} 처리 중 오류: {e}")

        self.logger.info(f"처리 완료 - 성공: {success_count}개, 실패: {error_count}개")

    def save_to_csv(self, output_path: str) -> None:
        """CSV 파일로 저장"""

        if not self.data_list:
            self.logger.warning("저장할 데이터가 없습니다.")
            return

        try:
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # DataFrame 생성
            df = pd.DataFrame(self.data_list)

            # 컬럼 순서 정리
            columns_order = [
                "report_id",
                "file_name",
                "securities_company",
                "stock_name",
                "stock_code",
                "report_title",
                "report_date",
                "rating",
                "opinion_change",
                "target_price",
                "current_price",
                "analysts",
                "parsing_date",
            ]

            # analysts 컬럼을 문자열로 변환
            df["analysts"] = df["analysts"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))

            # 컬럼 순서 적용
            df = df[columns_order]

            # CSV 저장
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            self.logger.info(f"CSV 파일 저장 완료: {output_path}")
            self.logger.info(f"총 {len(self.data_list)}개 리포트 저장")

        except Exception as e:
            self.logger.error(f"CSV 저장 오류: {e}")
            raise

    def get_summary(self, data: Dict[str, Any]) -> str:
        """개별 파싱 결과 요약 반환"""

        summary = f"""
=== 신한투자증권 리포트 파싱 결과 ===
파일명: {data.get('file_name', 'N/A')}
종목명: {data.get('stock_name', 'N/A')} ({data.get('stock_code', 'N/A')})
리포트 제목: {data.get('report_title', 'N/A')}
리포트 날짜: {data.get('report_date', 'N/A')}
투자의견: {data.get('rating', 'N/A')} ({data.get('opinion_change', 'N/A')})
목표주가: {data.get('target_price', 'N/A')}원
현재주가: {data.get('current_price', 'N/A')}원
애널리스트: {', '.join(data.get('analysts', []))}
파싱일시: {data.get('parsing_date', 'N/A')}
"""
        return summary


def main():
    """메인 함수"""

    print("신한투자증권 컨센서스 리포트 파서 시작")
    print("=" * 60)

    parser = ShinhanConsensusParser()

    # 경로 설정
    pdf_folder_path = r"c:\hanium\Finsight-service\Consensus-ETL\project\consensus\shinhan"
    output_folder = r"c:\hanium\Finsight-service\Consensus-ETL\project\consensus_parsed"

    # 타임스탬프 포함한 출력 파일명
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"shinhan_consensus_result_{timestamp}.csv"
    output_path = os.path.join(output_folder, output_filename)

    try:
        # PDF 처리
        parser.process_all_pdfs(pdf_folder_path)

        # 결과 저장
        if parser.data_list:
            parser.save_to_csv(output_path)

            print(f"\n{'='*60}")
            print(f"전체 결과 CSV 파일 저장: {output_path}")
            print(f"총 {len(parser.data_list)}개 파일 파싱 완료")
            print("=" * 60)
        else:
            print("파싱된 결과가 없습니다.")

    except FileNotFoundError as e:
        print(f"오류: {e}")
        print(f"PDF 폴더를 확인해주세요: {pdf_folder_path}")

    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        traceback.print_exc()

    finally:
        print(f"\n{'='*60}")
        print("신한투자증권 컨센서스 리포트 파서 종료")


if __name__ == "__main__":
    main()
