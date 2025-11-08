"""
Streamlit 프론트엔드
스미싱 탐지 데모 웹 앱
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.analyzer import analyzer

# 페이지 설정
st.set_page_config(
    page_title="스미싱 필터",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .risk-critical {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .risk-high {
        background-color: #ff8800;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .risk-medium {
        background-color: #ffbb00;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .risk-low {
        background-color: #00aa00;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .risk-safe {
        background-color: #00cc00;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


def get_risk_color(risk_level: str) -> str:
    """위험도에 따른 색상 반환"""
    colors = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
        "safe": "✅"
    }
    return colors.get(risk_level, "⚪")


def display_result(result: dict):
    """분석 결과 표시"""
    risk_score = result.get("risk_score", 0)
    risk_level = result.get("risk_level", "unknown")
    is_smishing = result.get("is_smishing", False)
    reasons = result.get("reasons", [])
    safe_actions = result.get("safe_actions", [])

    # 위험도 게이지
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if risk_level == "critical":
            st.markdown(f'<div class="risk-critical">⚠️ 위험도: {risk_score}%</div>', unsafe_allow_html=True)
            st.error("**스미싱일 가능성이 매우 높습니다!**")
        elif risk_level == "high":
            st.markdown(f'<div class="risk-high">⚠️ 위험도: {risk_score}%</div>', unsafe_allow_html=True)
            st.warning("**스미싱일 가능성이 높습니다.**")
        elif risk_level == "medium":
            st.markdown(f'<div class="risk-medium">⚠️ 위험도: {risk_score}%</div>', unsafe_allow_html=True)
            st.warning("**주의가 필요합니다.**")
        elif risk_level == "low":
            st.markdown(f'<div class="risk-low">✓ 위험도: {risk_score}%</div>', unsafe_allow_html=True)
            st.info("**비교적 안전해 보입니다.**")
        else:
            st.markdown(f'<div class="risk-safe">✅ 위험도: {risk_score}%</div>', unsafe_allow_html=True)
            st.success("**안전한 문자입니다.**")

    # 진단 결과
    st.subheader("📋 진단 결과")
    if is_smishing:
        st.error("🚨 **이 문자는 스미싱으로 판단됩니다.**")
    else:
        st.success("✅ **이 문자는 안전해 보입니다.**")

    # 의심 이유
    if reasons:
        st.subheader("🔍 의심되는 이유")
        for i, reason in enumerate(reasons, 1):
            st.write(f"{i}. {reason}")

    # 안전 행동 가이드
    if safe_actions:
        st.subheader("💡 안전 행동 가이드")
        for i, action in enumerate(safe_actions, 1):
            st.write(f"{i}. {action}")


def main():
    """메인 앱"""

    # 헤더
    st.markdown('<div class="main-header">🛡️ 스미싱 필터<div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI가 의심스러운 문자를 분석해드립니다</div>', unsafe_allow_html=True)

    # 사이드바
    with st.sidebar:
        st.header("ℹ️ 사용 방법")
        st.markdown("""
        1. **스크린샷** 또는 **텍스트** 탭 선택
        2. 의심스러운 문자 입력
        3. **검사하기** 버튼 클릭
        4. AI 분석 결과 확인
        """)

        st.divider()

        st.header("⚠️ 스미싱 특징")
        st.markdown("""
        - 출처 불명 링크
        - 긴급성 강조
        - 금전/개인정보 요구
        - 공식 기관 사칭
        - 맞춤법 오류
        """)

        st.divider()

        st.header("📊 통계")
        if 'total_checks' not in st.session_state:
            st.session_state.total_checks = 0
        if 'smishing_detected' not in st.session_state:
            st.session_state.smishing_detected = 0

        # 초기화
        result=st.session_state.get("last_result",{})

        if 'security_checks' in result:
            st.subheader("보안 검사 결과")
            checks=result['security_checks']
            
            # 1. URL안전성
            if checks['url_safety']['suspicious_urls']:
                st.error("⚠️ 의심스러운 URL 발견")
                for url_info in checks['url_safety']['suspicious_urls']:
                    with st.expander(f"🔗 {url_info['domain']}"):
                        st.write(f"**위험도:** {url_info['risk_score']}/100")
                        st.write("**이유:**")
                        for reason in url_info['reasons']:
                            st.write(f"  • {reason}")

            # 발송 패턴
            if checks['sending_pattern']['anomalies']:
                st.warning("📊 비정상 발송 패턴 감지")
                for anomaly in checks['sending_pattern']['anomalies']:
                    st.write(f"• **{anomaly['type']}**: {anomaly['detail']}")
            
            # 민감 행위 링크
            if checks['sensitive_link_abuse']['is_violation']:
                st.error("🚨 민감한 작업을 링크로 유도")
                for violation in checks['sensitive_link_abuse']['violations']:
                    st.write(f"• {violation['message']}")


        st.metric("총 검사 횟수", st.session_state.total_checks)
        st.metric("스미싱 탐지", st.session_state.smishing_detected)

    # 메인 컨텐츠
    tab1, tab2 = st.tabs(["📸 스크린샷 업로드", "📝 텍스트 입력"])

    # 탭 1: 스크린샷 업로드
    with tab1:
        st.subheader("문자 스크린샷을 업로드하세요")

        uploaded_file = st.file_uploader(
            "이미지 선택 (PNG, JPG, JPEG)",
            type=['png', 'jpg', 'jpeg'],
            help="문자 메시지의 스크린샷을 업로드하세요"
        )

        if uploaded_file is not None:
            col1, col2 = st.columns([1, 1])

            with col1:
                st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)

            with col2:
                if st.button("🔍 검사하기", key="analyze_image", type="primary", use_container_width=True):
                    with st.spinner("AI가 분석 중입니다..."):
                        try:
                            # 이미지 바이트로 읽기
                            image_bytes = uploaded_file.getvalue()

                            # 분석 실행
                            result = analyzer.analyze_image(image_bytes)
                            st.session_state.last_result = result

                            # 통계 업데이트
                            st.session_state.total_checks += 1
                            if result.get("is_smishing"):
                                st.session_state.smishing_detected += 1

                            # 결과 표시
                            st.divider()
                            display_result(result)

                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {str(e)}")
                            st.info("OpenAI API 키가 설정되어 있는지 확인해주세요.")

    # 탭 2: 텍스트 입력
    with tab2:
        st.subheader("문자 내용을 직접 입력하세요")

        text_input = st.text_area(
            "문자 내용",
            height=200,
            placeholder="예시:\n[Web발신]\n택배가 도착했습니다.\n확인: https://bit.ly/xxxxx",
            help="의심스러운 문자 내용을 붙여넣으세요"
        )

        if st.button("🔍 검사하기", key="analyze_text", type="primary", use_container_width=True):
            if text_input.strip():
                with st.spinner("AI가 분석 중입니다..."):
                    try:
                        # 분석 실행
                        result = analyzer.analyze_text(text_input)
                        st.session_state.last_result = result

                        # 통계 업데이트
                        st.session_state.total_checks += 1
                        if result.get("is_smishing"):
                            st.session_state.smishing_detected += 1

                        # 결과 표시
                        st.divider()
                        display_result(result)

                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
                        st.info("OpenAI API 키가 설정되어 있는지 확인해주세요.")
            else:
                st.warning("텍스트를 입력해주세요.")

    # 푸터
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Made with ❤️ using OpenAI GPT-4 Vision |
        <a href="https://github.com" target="_blank">GitHub</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
