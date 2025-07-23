import base64
import io
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageOps, ImageEnhance
import numpy as np

class ImageFormat:
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    TIFF = "tiff"

class ImageProcessingResult:
    def __init__(self, success: bool, image_data: Optional[str] = None, error_message: Optional[str] = None, quality_score: float = 0.0, processing_time: float = 0.0, metadata: Dict[str, Any] = None):
        self.success = success
        self.image_data = image_data
        self.error_message = error_message
        self.quality_score = quality_score
        self.processing_time = processing_time
        self.metadata = metadata

class ImageProcessor:
    """이미지 전처리 및 최적화 클래스"""
    def __init__(self):
        self.max_image_size = 20 * 1024 * 1024  # 20MB
        self.max_dimension = 4096  # Gemini API 제한
        self.supported_formats = [ImageFormat.JPEG, ImageFormat.PNG, ImageFormat.WEBP]

    def validate_image(self, image_path: str) -> Tuple[bool, str]:
        try:
            with Image.open(image_path) as img:
                if img.format.lower() not in [fmt for fmt in self.supported_formats]:
                    return False, f"지원하지 않는 이미지 포맷: {img.format}"
                file_size = img.size[0] * img.size[1] * 3
                if file_size > self.max_image_size:
                    return False, f"이미지가 너무 큽니다: {file_size} bytes"
                return True, "이미지 검증 성공"
        except Exception as e:
            return False, f"이미지 읽기 실패: {str(e)}"

    def optimize_image(self, image_path: str) -> ImageProcessingResult:
        start_time = datetime.now()
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                if max(img.size) > self.max_dimension:
                    ratio = self.max_dimension / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                img = self._enhance_image_quality(img)
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
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
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)
        return img

    def _calculate_quality_score(self, img: Image.Image) -> float:
        resolution_score = min(1.0, (img.size[0] * img.size[1]) / (1920 * 1080))
        gray_img = img.convert('L')
        gray_array = np.array(gray_img)
        sharpness_score = np.std(gray_array) / 255.0
        quality_score = (resolution_score * 0.6 + sharpness_score * 0.4)
        return min(1.0, quality_score) 