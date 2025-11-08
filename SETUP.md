# 🚀 빠른 시작 가이드

## 1단계: 환경 설정 (5분)

### Python 가상환경 생성
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 패키지 설치
```bash
pip install -r requirements.txt
```

## 2단계: OpenAI API 키 설정 (2분)

### API 키 발급
1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. 키 복사

### 환경변수 설정
`.env` 파일 생성 (프로젝트 루트에):
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
```

또는 `.env.example`을 복사:
```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

그 다음 `.env` 파일을 열어서 실제 API 키 입력

## 3단계: 앱 실행 (1분)

### Streamlit 앱 실행 (추천)
```bash
streamlit run frontend/streamlit_app.py
```

브라우저가 자동으로 열리면서 http://localhost:8501 접속됨

### FastAPI 서버 실행 (선택사항)
```bash
uvicorn app.main:app --reload
```

API 문서: http://localhost:8000/docs

## 4단계: 테스트 (2분)

### 텍스트로 테스트
1. "📝 텍스트 입력" 탭 선택
2. 다음 텍스트 복사 붙여넣기:
```
[Web발신]
택배가 도착했습니다.
확인: https://bit.ly/xxxxx
```
3. "검사하기" 버튼 클릭
4. 높은 위험도가 나오면 성공!

### 스크린샷으로 테스트
1. "📸 스크린샷 업로드" 탭 선택
2. 테스트용 스미싱 이미지 업로드
3. "검사하기" 버튼 클릭

## 트러블슈팅

### OpenAI API 오류
- ❌ "Error: Incorrect API key"
  - ✅ `.env` 파일에 올바른 API 키가 있는지 확인
  - ✅ API 키 앞뒤 공백 제거
  - ✅ Streamlit 앱 재시작 (Ctrl+C 후 다시 실행)

### 패키지 설치 오류
- ❌ "No module named 'openai'"
  - ✅ 가상환경이 활성화되어 있는지 확인
  - ✅ `pip install -r requirements.txt` 다시 실행

### 포트 충돌
- ❌ "Port 8501 is already in use"
  - ✅ 다른 Streamlit 앱 종료
  - ✅ 또는 다른 포트 사용: `streamlit run frontend/streamlit_app.py --server.port 8502`

## VSCode 추천 설정

### 확장 프로그램
- Python (Microsoft)
- Pylance
- Python Debugger

### launch.json (디버깅용)
`.vscode/launch.json` 생성:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Streamlit App",
      "type": "python",
      "request": "launch",
      "module": "streamlit",
      "args": ["run", "frontend/streamlit_app.py"]
    },
    {
      "name": "FastAPI Server",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"]
    }
  ]
}
```

## 해커톤 발표용 팁

### 데모 시나리오
1. **문제 제시** (30초): "작년 스미싱 피해 500억 원"
2. **솔루션 소개** (30초): "AI가 자동으로 탐지"
3. **실시간 데모** (2분):
   - 스미싱 예시 → 높은 위험도
   - 정상 문자 → 낮은 위험도
4. **차별화 포인트** (1분): "한국어 특화, 스크린샷 지원"
5. **확장 가능성** (30초): "API로 다른 앱에 통합 가능"

### 주의사항
- 데모 전 인터넷 연결 확인 (OpenAI API 필요)
- 테스트 케이스 미리 준비 (즉석에서 타이핑 X)
- 스크린샷 2-3개 미리 준비
- API 크레딧 충분한지 확인 (최소 $5)

## 비용 추정

- GPT-4 Vision API: 이미지당 약 $0.01-0.02
- GPT-4 Turbo (텍스트): 요청당 약 $0.003
- 해커톤 데모 30회 테스트: 약 $0.50

## 다음 단계

- [ ] 테스트 케이스 10개 준비
- [ ] 발표 자료 작성
- [ ] 데모 리허설
- [ ] GitHub 레포지토리 생성 (README 정리)
