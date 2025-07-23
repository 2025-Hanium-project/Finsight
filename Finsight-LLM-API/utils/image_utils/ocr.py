import re
import json
from datetime import datetime
from typing import Dict, Any
from .image_processor import ImageProcessor

class OCRResult:
    def __init__(self, success: bool, extracted_text: str = "", structured_data: Dict[str, Any] = None, confidence_score: float = 0.0, processing_time: float = 0.0, error_message: str = None):
        self.success = success
        self.extracted_text = extracted_text
        self.structured_data = structured_data
        self.confidence_score = confidence_score
        self.processing_time = processing_time
        self.error_message = error_message

class SecuritiesReportOCR:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.required_fields = [
            "stock_code", "stock_name", "report_title", "report_date",
            "analyst_name", "company_name", "rating", "target_price"
        ]

    async def process_image_report(self, image_path: str) -> OCRResult:
        start_time = datetime.now()
        try:
            is_valid, message = self.image_processor.validate_image(image_path)
            if not is_valid:
                return OCRResult(
                    success=False,
                    error_message=message,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            processing_result = self.image_processor.optimize_image(image_path)
            if not processing_result.success:
                return OCRResult(
                    success=False,
                    error_message=processing_result.error_message,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            from utils.llm.llm_client import generate_multimodal_response
            ocr_result = await self._perform_ocr(processing_result.image_data)
            if ocr_result.success:
                validated_data = self._validate_and_clean_data(ocr_result.structured_data)
                ocr_result.structured_data = validated_data
                ocr_result.confidence_score = self._calculate_confidence_score(validated_data)
            ocr_result.processing_time = (datetime.now() - start_time).total_seconds()
            return ocr_result
        except Exception as e:
            return OCRResult(
                success=False,
                error_message=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    async def _perform_ocr(self, image_data: str) -> OCRResult:
        try:
            prompt = self._create_ocr_prompt()
            from utils.llm.llm_client import generate_multimodal_response
            response = await generate_multimodal_response(
                prompt=prompt,
                image_data=image_data,
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                max_tokens=4096
            )
            try:
                structured_data = json.loads(response)
                return OCRResult(
                    success=True,
                    extracted_text=response,
                    structured_data=structured_data,
                    confidence_score=0.8
                )
            except json.JSONDecodeError:
                structured_data = self._extract_structured_data_from_text(response)
                return OCRResult(
                    success=True,
                    extracted_text=response,
                    structured_data=structured_data,
                    confidence_score=0.6
                )
        except Exception as e:
            return OCRResult(
                success=False,
                error_message=str(e),
                processing_time=0.0
            )

    def _create_ocr_prompt(self) -> str:
        return """
증권사 리포트 이미지를 분석하여 다음 정보를 JSON 형식으로 추출해주세요:

필수 추출 항목:
- stock_code: 종목코드 (예: 005930)
- stock_name: 종목명 (예: 삼성전자)
- report_title: 리포트 제목
- report_date: 리포트 발행일 (YYYY-MM-DD 형식)
- analyst_name: 분석가명
- company_name: 증권사명
- rating: 투자의견 (매수, 중립, 매도 등)
- target_price: 목표주가 (숫자만, 원화 기호 제거)
- current_price: 현재주가 (숫자만, 원화 기호 제거)

추가 정보 (가능한 경우):
- opinion_change: 의견 변경 (상향, 하향, 유지)
- upside_potential: 상승 여력 (퍼센트, 숫자만)
- content_text: 리포트 전문 텍스트
- summary: 핵심 요약

JSON 형식으로만 응답하고, 없는 정보는 null로 표시하세요.
"""

    def _extract_structured_data_from_text(self, text: str) -> Dict[str, Any]:
        data = {}
        stock_code_pattern = r'종목코드[:\s]*(\d{6})'
        match = re.search(stock_code_pattern, text)
        if match:
            data['stock_code'] = match.group(1)
        stock_name_pattern = r'종목명[:\s]*([가-힣A-Za-z]+)'
        match = re.search(stock_name_pattern, text)
        if match:
            data['stock_name'] = match.group(1)
        rating_pattern = r'투자의견[:\s]*(매수|중립|매도|BUY|HOLD|SELL)'
        match = re.search(rating_pattern, text, re.IGNORECASE)
        if match:
            data['rating'] = match.group(1)
        target_price_pattern = r'목표가[:\s]*([\d,]+)'
        match = re.search(target_price_pattern, text)
        if match:
            data['target_price'] = int(match.group(1).replace(',', ''))
        return data

    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data:
            return {}
        cleaned_data = {}
        for field in self.required_fields:
            if field in data and data[field]:
                cleaned_data[field] = data[field]
            else:
                cleaned_data[field] = None
        optional_fields = ['opinion_change', 'upside_potential', 'content_text', 'summary']
        for field in optional_fields:
            if field in data:
                cleaned_data[field] = data[field]
        return cleaned_data

    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        if not data:
            return 0.0
        filled_fields = sum(1 for field in self.required_fields if data.get(field))
        base_score = filled_fields / len(self.required_fields)
        quality_bonus = 0.0
        if data.get('stock_code') and len(str(data['stock_code'])) == 6:
            quality_bonus += 0.1
        if data.get('rating'):
            quality_bonus += 0.1
        if data.get('target_price'):
            quality_bonus += 0.1
        return min(1.0, base_score + quality_bonus) 