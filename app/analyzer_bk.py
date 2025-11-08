"""
스미싱 분석 로직 VERSION#1
OpenAI GPT-4 Vision API를 사용한 이미지 및 텍스트 분석
"""

import os
import base64
import json
from typing import Dict, Any, Optional
from io import BytesIO
from PIL import Image
import openai
from dotenv import load_dotenv

from app.prompts import SMISHING_ANALYSIS_PROMPT, TEXT_ANALYSIS_PROMPT

# 환경변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class SmishingAnalyzer:
    """스미싱 탐지 분석기"""

    def __init__(self, model: str = None):
        self.model = model or DEFAULT_MODEL

    def _encode_image(self, image_bytes: bytes) -> str:
        """이미지를 base64로 인코딩"""
        return base64.b64encode(image_bytes).decode('utf-8')

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """GPT 응답을 파싱하여 JSON으로 변환"""
        try:
            # JSON 블록 추출 (```json ... ``` 형식 처리)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            else:
                json_str = response_text.strip()

            result = json.loads(json_str)

            # 필수 필드 검증
            required_fields = ["risk_score", "is_smishing", "risk_level", "reasons", "safe_actions"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            # 파싱 실패시 기본값 반환
            return {
                "risk_score": 50,
                "is_smishing": False,
                "risk_level": "medium",
                "reasons": ["분석 중 오류가 발생했습니다."],
                "safe_actions": ["전문가에게 문의하세요."],
                "error": str(e)
            }

    def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        이미지를 분석하여 스미싱 여부 판단

        Args:
            image_bytes: 이미지 바이트 데이터

        Returns:
            분석 결과 딕셔너리
        """
        try:
            # 이미지 크기 최적화 (비용 절감)
            img = Image.open(BytesIO(image_bytes))
            if img.width > 1024 or img.height > 1024:
                img.thumbnail((1024, 1024))
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()

            # base64 인코딩
            base64_image = self._encode_image(image_bytes)

            # GPT-4 Vision API 호출
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": SMISHING_ANALYSIS_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            # 응답 파싱
            response_text = response.choices[0].message.content
            result = self._parse_response(response_text)

            return result

        except Exception as e:
            return {
                "risk_score": 0,
                "is_smishing": False,
                "risk_level": "error",
                "reasons": [f"분석 중 오류가 발생했습니다: {str(e)}"],
                "safe_actions": ["나중에 다시 시도해주세요."],
                "error": str(e)
            }

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        텍스트를 분석하여 스미싱 여부 판단

        Args:
            text: 분석할 문자 텍스트

        Returns:
            분석 결과 딕셔너리
        """
        try:
            # GPT-4 API 호출 (텍스트만)
            response = client.chat.completions.create(
                model=self.model,  # 텍스트 전용은 더 저렴한 모델 사용
                messages=[
                    {
                        "role": "user",
                        "content": TEXT_ANALYSIS_PROMPT.format(text=text)
                    }
                ],
                max_tokens=800
            )

            # 응답 파싱
            response_text = response.choices[0].message.content
            result = self._parse_response(response_text)

            return result

        except Exception as e:
            return {
                "risk_score": 0,
                "is_smishing": False,
                "risk_level": "error",
                "reasons": [f"분석 중 오류가 발생했습니다: {str(e)}"],
                "safe_actions": ["나중에 다시 시도해주세요."],
                "error": str(e)
            }


# 싱글톤 인스턴스
analyzer = SmishingAnalyzer()
