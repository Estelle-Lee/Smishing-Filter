# 🛡️ 스미싱 지킴이 (Smishing Detector)

AI 기반 스미싱 문자 탐지 API & 데모 앱

## 📋 프로젝트 개요
문자 메시지 스크린샷 또는 텍스트를 분석하여 스미싱(피싱 문자) 여부를 자동으로 판별하는 서비스입니다.

## 🎯 주요 기능
- 📸 스크린샷 업로드를 통한 자동 분석 (OCR + AI)
- 📝 텍스트 직접 입력 분석
- 🎨 위험도 시각화 (0-100% 점수)
- 💡 의심 이유 상세 설명
- ✅ 안전 행동 가이드 제공

## 🛠️ 기술 스택
- **Backend**: FastAPI (Python 3.9+)
- **AI**: OpenAI GPT-4 Vision API
- **Frontend**: Streamlit
- **Image Processing**: Pillow

## 📁 프로젝트 구조
```
smishing-detector/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 서버
│   ├── analyzer.py          # 스미싱 분석 로직
│   └── prompts.py           # AI 프롬프트 템플릿
├── frontend/
│   └── streamlit_app.py     # Streamlit UI
├── tests/
│   ├── sample_images/       # 테스트용 스크린샷
│   └── test_analyzer.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚀 시작하기

### 1. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
`.env` 파일 생성 후 OpenAI API 키 입력:
```
OPENAI_API_KEY=your_api_key_here
```

### 4. 실행

#### API 서버 (선택사항)
```bash
uvicorn app.main:app --reload
```

#### Streamlit 앱
```bash
streamlit run frontend/streamlit_app.py
```

## 📊 API 문서
서버 실행 후 http://localhost:8000/docs 에서 확인

## 🔒 보안 주의사항
- API 키는 절대 커밋하지 마세요
- `.env` 파일은 `.gitignore`에 포함되어 있습니다

## 📝 라이선스
MIT License
