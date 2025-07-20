"""
증권사 리포트 분석 에이전트 (이미지 OCR 지원)
"""
import base64
import io
import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# 이미지 처리 라이브러리
from PIL import Image, ImageOps, ImageEnhance
import numpy as np

from utils.core.agent_base import AnalysisAgent, AgentType, create_standard_prompt_template
from utils.llm.llm_client import generate_multimodal_response

logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """지원하는 이미지 포맷"""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    TIFF = "tiff"


class ImageQuality(Enum):
    """이미지 품질 등급"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class ImageProcessingResult:
    """이미지 처리 결과"""
    success: bool
    image_data: Optional[str] = None  # Base64 인코딩된 이미지
    error_message: Optional[str] = None
    quality_score: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class OCRResult:
    """OCR 처리 결과"""
    success: bool
    extracted_text: str = ""
    structured_data: Dict[str, Any] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    error_message: Optional[str] = None


class ImageProcessor:
    """이미지 전처리 및 최적화 클래스"""
    
    def __init__(self):
        self.max_image_size = 20 * 1024 * 1024  # 20MB
        self.max_dimension = 4096  # Gemini API 제한
        self.supported_formats = [ImageFormat.JPEG, ImageFormat.PNG, ImageFormat.WEBP]
    
    def validate_image(self, image_path: str) -> Tuple[bool, str]:
        """이미지 유효성 검증"""
        try:
            with Image.open(image_path) as img:
                # 포맷 검증
                if img.format.lower() not in [fmt.value for fmt in self.supported_formats]:
                    return False, f"지원하지 않는 이미지 포맷: {img.format}"
                
                # 크기 검증
                file_size = img.size[0] * img.size[1] * 3  # 대략적인 파일 크기
                if file_size > self.max_image_size:
                    return False, f"이미지가 너무 큽니다: {file_size} bytes"
                
                return True, "이미지 검증 성공"
                
        except Exception as e:
            return False, f"이미지 읽기 실패: {str(e)}"
    
    def optimize_image(self, image_path: str) -> ImageProcessingResult:
        """이미지 최적화"""
        start_time = datetime.now()
        
        try:
            with Image.open(image_path) as img:
                # RGB 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 크기 조정
                if max(img.size) > self.max_dimension:
                    ratio = self.max_dimension / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 품질 향상
                img = self._enhance_image_quality(img)
                
                # Base64 인코딩
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # 품질 점수 계산
                quality_score = self._calculate_quality_score(img)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return ImageProcessingResult(
                    success=True,
                    image_data=image_data,
                    quality_score=quality_score,
                    processing_time=processing_time,
                    metadata={
                        "original_size": img.size,
                        "format": "jpeg",
                        "file_size": len(buffer.getvalue())
                    }
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return ImageProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def _enhance_image_quality(self, img: Image.Image) -> Image.Image:
        """이미지 품질 향상"""
        # 대비 향상
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # 선명도 향상
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        # 밝기 조정
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)
        
        return img
    
    def _calculate_quality_score(self, img: Image.Image) -> float:
        """이미지 품질 점수 계산"""
        # 해상도 점수
        resolution_score = min(1.0, (img.size[0] * img.size[1]) / (1920 * 1080))
        
        # 선명도 점수 (간단한 방법)
        gray_img = img.convert('L')
        gray_array = np.array(gray_img)
        sharpness_score = np.std(gray_array) / 255.0
        
        # 종합 점수
        quality_score = (resolution_score * 0.6 + sharpness_score * 0.4)
        return min(1.0, quality_score)


class SecuritiesReportOCR:
    """증권사 리포트 OCR 처리 클래스"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.required_fields = [
            "stock_code", "stock_name", "report_title", "report_date",
            "analyst_name", "company_name", "rating", "target_price"
        ]
    
    async def process_image_report(self, image_path: str) -> OCRResult:
        """이미지 리포트 처리"""
        start_time = datetime.now()
        
        try:
            # 1. 이미지 검증
            is_valid, message = self.image_processor.validate_image(image_path)
            if not is_valid:
                return OCRResult(
                    success=False,
                    error_message=message,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 2. 이미지 최적화
            processing_result = self.image_processor.optimize_image(image_path)
            if not processing_result.success:
                return OCRResult(
                    success=False,
                    error_message=processing_result.error_message,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 3. OCR 처리
            ocr_result = await self._perform_ocr(processing_result.image_data)
            
            # 4. 데이터 검증 및 후처리
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
        """Gemini 2.5 Flash를 사용한 OCR 처리"""
        try:
            # OCR 프롬프트 생성
            prompt = self._create_ocr_prompt()
            
            # Gemini 멀티모달 호출
            response = await generate_multimodal_response(
                prompt=prompt,
                image_data=image_data,
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                max_tokens=4096
            )
            
            # 응답 파싱
            try:
                structured_data = json.loads(response)
                return OCRResult(
                    success=True,
                    extracted_text=response,
                    structured_data=structured_data,
                    confidence_score=0.8  # 기본값
                )
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트에서 구조화된 데이터 추출
                structured_data = self._extract_structured_data_from_text(response)
                return OCRResult(
                    success=True,
                    extracted_text=response,
                    structured_data=structured_data,
                    confidence_score=0.6  # 낮은 신뢰도
                )
                
        except Exception as e:
            return OCRResult(
                success=False,
                error_message=str(e),
                processing_time=0.0
            )
    
    def _create_ocr_prompt(self) -> str:
        """OCR 프롬프트 생성"""
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
        """텍스트에서 구조화된 데이터 추출"""
        data = {}
        
        # 종목코드 패턴
        stock_code_pattern = r'종목코드[:\s]*(\d{6})'
        match = re.search(stock_code_pattern, text)
        if match:
            data['stock_code'] = match.group(1)
        
        # 종목명 패턴
        stock_name_pattern = r'종목명[:\s]*([가-힣A-Za-z]+)'
        match = re.search(stock_name_pattern, text)
        if match:
            data['stock_name'] = match.group(1)
        
        # 투자의견 패턴
        rating_pattern = r'투자의견[:\s]*(매수|중립|매도|BUY|HOLD|SELL)'
        match = re.search(rating_pattern, text, re.IGNORECASE)
        if match:
            data['rating'] = match.group(1)
        
        # 목표가 패턴
        target_price_pattern = r'목표가[:\s]*([\d,]+)'
        match = re.search(target_price_pattern, text)
        if match:
            data['target_price'] = int(match.group(1).replace(',', ''))
        
        return data
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 검증 및 정리"""
        if not data:
            return {}
        
        cleaned_data = {}
        
        # 필수 필드 검증
        for field in self.required_fields:
            if field in data and data[field]:
                cleaned_data[field] = data[field]
            else:
                cleaned_data[field] = None
        
        # 추가 필드
        optional_fields = ['opinion_change', 'upside_potential', 'content_text', 'summary']
        for field in optional_fields:
            if field in data:
                cleaned_data[field] = data[field]
        
        return cleaned_data
    
    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """신뢰도 점수 계산"""
        if not data:
            return 0.0
        
        # 필수 필드 채움 정도에 따른 점수
        filled_fields = sum(1 for field in self.required_fields if data.get(field))
        base_score = filled_fields / len(self.required_fields)
        
        # 데이터 품질에 따른 보정
        quality_bonus = 0.0
        if data.get('stock_code') and len(str(data['stock_code'])) == 6:
            quality_bonus += 0.1
        if data.get('rating'):
            quality_bonus += 0.1
        if data.get('target_price'):
            quality_bonus += 0.1
        
        return min(1.0, base_score + quality_bonus)


class BatchImageProcessor:
    """배치 이미지 처리 클래스"""
    
    def __init__(self):
        self.ocr_processor = SecuritiesReportOCR()
    
    async def process_batch(self, image_paths: List[str]) -> List[OCRResult]:
        """배치 이미지 처리"""
        results = []
        
        for image_path in image_paths:
            try:
                result = await self.ocr_processor.process_image_report(image_path)
                results.append(result)
            except Exception as e:
                results.append(OCRResult(
                    success=False,
                    error_message=str(e)
                ))
        
        return results
    
    def filter_successful_results(self, results: List[OCRResult]) -> List[OCRResult]:
        """성공한 결과만 필터링"""
        return [result for result in results if result.success]
    
    def get_quality_statistics(self, results: List[OCRResult]) -> Dict[str, Any]:
        """품질 통계 계산"""
        if not results:
            return {}
        
        successful_results = self.filter_successful_results(results)
        
        if not successful_results:
            return {
                "total_count": len(results),
                "success_count": 0,
                "success_rate": 0.0
            }
        
        avg_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)
        avg_processing_time = sum(r.processing_time for r in successful_results) / len(successful_results)
        
        return {
            "total_count": len(results),
            "success_count": len(successful_results),
            "success_rate": len(successful_results) / len(results),
            "avg_confidence": avg_confidence,
            "avg_processing_time": avg_processing_time
        }


class SecuritiesReportAgent(AnalysisAgent):
    """증권사 리포트 분석 에이전트 (이미지 OCR 지원)"""
    
    def __init__(self):
        from utils.core.agent_base import AgentConfig
        config = AgentConfig(
            name="securities_report_agent",
            agent_type=AgentType.SECURITIES_REPORT
        )
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.4  # 리포트 분석을 위한 중간 temperature
        
        # 이미지 처리 컴포넌트 초기화
        self.ocr_processor = SecuritiesReportOCR()
        self.image_processor = ImageProcessor()
        self.batch_processor = BatchImageProcessor()
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "market_data_agent",
            "valuation_agent",
            "peer_comparison_agent",
            "data_quality_agent",
            "document_processing_agent"
        ]
    
    def _create_image_analysis_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> str:
        """이미지 분석 프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        # 원하는 JSON 스키마 정의
        output_schema = {
            "report_id": "자동 생성되는 고유 ID (형식: REP_YYYYMMDD_HHMMSS)",
            "stock_code": "종목 코드 (예: 005930)",
            "stock_name": "종목명 (예: 삼성전자)",
            "report_title": "리포트 제목",
            "report_date": "리포트 발행일 (YYYY-MM-DD 형식)",
            "report_type": "리포트 유형 (기업 분석, 산업 분석, 섹터 분석, 시장 전망 등)",
            "analyst_name": "분석가명",
            "company_name": "증권사명",
            "rating": "투자 의견 (매수, 중립, 매도 등)",
            "opinion_change": "의견 변경 여부 (상향, 하향, 유지)",
            "target_price": "목표 주가 (숫자만)",
            "current_price": "현재 주가 (숫자만)",
            "upside_potential": "상승 여력 (퍼센트, 숫자만)",
            "content_text": "리포트 전문 텍스트",
            "summary": "핵심 요약 (3-5문장)",
            "created_at": "처리 시각 (자동 생성)"
        }
        
        template = create_standard_prompt_template(
            agent_name="증권사 리포트 이미지 분석 전문가",
            task_description="제공된 증권사 리포트 이미지를 직접 분석하여 구조화된 JSON 데이터를 추출합니다.",
            output_schema=output_schema,
            collaboration_info=collaboration_info
        )
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        
        # 이미지 분석 지침 추가
        image_analysis_guidance = """
        
이미지 분석 지침:
1. 이미지에서 모든 텍스트를 정확히 읽어서 추출하세요
2. 종목코드, 종목명, 리포트 제목, 분석가명, 증권사명을 정확히 식별하세요
3. 투자의견, 목표가, 현재가를 숫자로 추출하세요 (원화 기호, 쉼표 제거)
4. 날짜는 YYYY-MM-DD 형식으로 통일하세요
5. 없는 정보는 null로 표시하세요
6. JSON 형식으로만 응답하세요
7. 한글 텍스트는 그대로 유지하세요
8. 이미지에서 보이는 모든 정보를 최대한 활용하세요
9. report_id는 자동으로 생성하세요 (형식: REP_YYYYMMDD_HHMMSS)
10. created_at은 현재 시각으로 설정하세요
11. content_text에는 이미지의 모든 텍스트를 포함하세요
12. summary는 핵심 내용을 3-5문장으로 요약하세요

중요: 이미지의 모든 텍스트를 정확히 읽어서 분석하고, 요청된 JSON 형식으로만 응답하세요.
"""
        
        template = template.replace("{{target_type}}", target_type)
        template = template.replace("{{target_name}}", target_name)
        template = template.replace("{{input_data}}", image_analysis_guidance)
        
        return template
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무제표 분석: " + json.dumps(data.get("financial_analysis", {}), ensure_ascii=False))
            elif agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
            elif agent_name == "peer_comparison_agent":
                formatted.append("동종업계 비교: " + json.dumps(data.get("peer_analysis", {}), ensure_ascii=False))
            elif agent_name == "data_quality_agent":
                formatted.append("데이터 품질 검증: " + json.dumps(data.get("quality_metrics", {}), ensure_ascii=False))
            elif agent_name == "document_processing_agent":
                formatted.append("문서 처리 결과: " + json.dumps(data.get("processing_result", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""

    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> str:
        """프롬프트 생성 (추상 메서드 구현)"""
        # 이미지 분석용 프롬프트 생성
        return self._create_image_analysis_prompt(input_data, collaboration_data)
    
    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """증권사 리포트 분석 수행 (이미지만 지원)"""
        return await self._analyze_image_report(input_data)
    
    async def _analyze_image_report(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """이미지 리포트 분석"""
        try:
            start_time = datetime.now()
            
            # 이미지 경로 확인
            image_path = input_data.get("image_path")
            self.logger.info(f"이미지 경로 확인: {image_path}")
            self.logger.info(f"파일 존재 여부: {os.path.exists(image_path) if image_path else False}")
            
            if not image_path:
                return {
                    "error": "이미지 경로가 제공되지 않았습니다",
                    "agent_name": self.name,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
            
            if not os.path.exists(image_path):
                return {
                    "error": f"이미지 파일을 찾을 수 없습니다: {image_path}",
                    "agent_name": self.name,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 이미지를 직접 분석용 데이터로 변환
            analysis_input = {
                "data_source": "securities_report_image",
                "image_path": image_path,
                "target_type": input_data.get("target_type", ""),
                "target_name": input_data.get("target_name", ""),
                "data_type": "image"
            }
            
            # 이미지 직접 분석 수행
            analysis_result = await self._execute_image_analysis(analysis_input)
            
            # 결과에 메타데이터 추가
            analysis_result.update({
                "image_path": image_path,
                "data_type": "image"
            })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            analysis_result["total_execution_time"] = execution_time
            
            return analysis_result
            
        except Exception as e:
            return {
                "error": str(e),
                "agent_name": self.name,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_image_analysis(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """이미지 분석 실행"""
        try:
            start_time = datetime.now()
            
            # 이미지 파일 읽기
            image_path = input_data.get("image_path")
            if not image_path or not os.path.exists(image_path):
                return {
                    "error": f"이미지 파일을 찾을 수 없습니다: {image_path}",
                    "agent_name": self.name,
                    "status": "failed"
                }
            
            # 이미지 파일을 Base64로 인코딩
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Base64 인코딩
            import base64
            image_data = base64.b64encode(image_bytes).decode('utf-8')
            
            # 프롬프트 생성
            prompt = self._create_image_analysis_prompt(input_data, collaboration_data)
            
            # Gemini 멀티모달 호출
            response = await generate_multimodal_response(
                prompt=prompt,
                image_data=image_data,
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                max_tokens=4096
            )
            
            # JSON 블록 추출 (```json으로 감싸진 경우)
            json_text = self._extract_json_from_response(response)
            
            # JSON 파싱 시도
            try:
                parsed_data = json.loads(json_text)
                
                # 메타데이터 추가
                parsed_data["created_at"] = datetime.now().isoformat()
                if "report_id" not in parsed_data or not parsed_data["report_id"]:
                    parsed_data["report_id"] = f"REP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": True,
                    "agent_name": self.name,
                    "status": "completed",
                    "analysis_result": json_text,
                    "parsed_data": parsed_data,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
                
            except json.JSONDecodeError as e:
                # JSON 파싱 실패 시 원본 텍스트 반환
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": False,
                    "agent_name": self.name,
                    "status": "json_parse_error",
                    "analysis_result": response,
                    "error": f"JSON 파싱 실패: {str(e)}",
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "agent_name": self.name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_json_from_response(self, response: str) -> str:
        """응답에서 JSON 블록 추출"""
        # ```json으로 감싸진 JSON 블록 찾기
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # ```로 감싸진 블록 찾기
        json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # JSON 객체 패턴 찾기
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # JSON 배열 패턴 찾기
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return response
    
    async def process_batch_images(self, image_paths: List[str]) -> Dict[str, Any]:
        """배치 이미지 처리"""
        try:
            start_time = datetime.now()
            
            results = []
            for image_path in image_paths:
                input_data = {
                    "image_path": image_path,
                    "data_type": "image",
                    "target_type": "securities_report",
                    "target_name": "배치 분석"
                }
                
                result = await self.analyze(input_data)
                results.append({
                    "image_path": image_path,
                    "result": result
                })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "total_images": len(image_paths),
                "processed_results": results,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def validate_image_quality(self, image_path: str) -> Dict[str, Any]:
        """이미지 품질 검증"""
        try:
            start_time = datetime.now()
            
            # 이미지 검증
            is_valid, message = self.image_processor.validate_image(image_path)
            
            if not is_valid:
                return {
                    "success": False,
                    "error": message,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 이미지 최적화 (품질 점수 계산용)
            processing_result = self.image_processor.optimize_image(image_path)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "is_valid": is_valid,
                "quality_score": processing_result.quality_score,
                "processing_time": execution_time,
                "metadata": processing_result.metadata,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 편의 함수들
async def analyze_securities_report_image(image_path: str, target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """증권사 리포트 이미지 분석 (편의 함수)"""
    agent = SecuritiesReportAgent()
    input_data = {
        "image_path": image_path,
        "data_type": "image",
        "target_type": target_type,
        "target_name": target_name
    }
    return await agent.analyze(input_data)


async def process_batch_securities_reports(image_paths: List[str]) -> Dict[str, Any]:
    """배치 증권사 리포트 처리 (편의 함수)"""
    agent = SecuritiesReportAgent()
    return await agent.process_batch_images(image_paths)


async def validate_image_quality(image_path: str) -> Dict[str, Any]:
    """이미지 품질 검증 (편의 함수)"""
    agent = SecuritiesReportAgent()
    return await agent.validate_image_quality(image_path) 