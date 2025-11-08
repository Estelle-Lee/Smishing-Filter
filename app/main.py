"""
FastAPI 백엔드 서버
스미싱 탐지 API 엔드포인트
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from app.analyzer import analyzer

# FastAPI 앱 초기화
app = FastAPI(
    title="Smishing Detector API",
    description="AI 기반 스미싱 문자 탐지 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청/응답 모델
class TextAnalysisRequest(BaseModel):
    text: str

    class Config:
        json_schema_extra = {
            "example": {
                "text": "[Web발신]\n(광고)국민지원금 신청하세요\nhttps://bit.ly/xxxxx"
            }
        }


class AnalysisResponse(BaseModel):
    risk_score: int
    is_smishing: bool
    risk_level: str
    reasons: list[str]
    safe_actions: list[str]
    error: Optional[str] = None


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "스미싱 지킴이 API",
        "status": "running",
        "endpoints": {
            "POST /analyze/image": "이미지 분석",
            "POST /analyze/text": "텍스트 분석",
            "GET /docs": "API 문서"
        }
    }


@app.post("/analyze/image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    문자 스크린샷 이미지를 분석하여 스미싱 여부 판단

    Args:
        file: 이미지 파일 (PNG, JPG 등)

    Returns:
        분석 결과
    """
    try:
        # 이미지 파일 검증
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

        # 파일 읽기
        image_bytes = await file.read()

        # 분석 실행
        result = analyzer.analyze_image(image_bytes)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    문자 텍스트를 분석하여 스미싱 여부 판단

    Args:
        request: 분석할 텍스트

    Returns:
        분석 결과
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="텍스트를 입력해주세요.")

        # 분석 실행
        result = analyzer.analyze_text(request.text)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
