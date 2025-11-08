@echo off
REM 스미싱 지킴이 Streamlit 앱 실행 스크립트

echo ====================================
echo   스미싱 지킴이 앱 실행 중...
echo ====================================
echo.

REM 가상환경 확인
if not exist "venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 없습니다.
    echo 먼저 setup.bat을 실행하세요.
    pause
    exit /b 1
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM .env 파일 확인
if not exist ".env" (
    echo [경고] .env 파일이 없습니다.
    echo .env.example을 복사하여 .env 파일을 만들고 API 키를 입력하세요.
    pause
)

echo Streamlit 앱 시작...
echo 브라우저에서 http://localhost:8501 이 자동으로 열립니다.
echo.
echo [종료하려면 Ctrl+C를 누르세요]
echo.

streamlit run frontend/streamlit_app.py

pause
