"""
스미싱 분석 로직 (고급 보안 기능 추가)
OpenAI GPT-4 Vision API + 보안 룰 엔진
"""

import os
import base64
import json
import re
from typing import Dict, Any, Optional, List
from io import BytesIO
from PIL import Image
import openai
from dotenv import load_dotenv
from urllib.parse import urlparse
from datetime import datetime

from app.prompts import SMISHING_ANALYSIS_PROMPT, TEXT_ANALYSIS_PROMPT

# 환경변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 모델 설정 (.env에서 읽기)
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class SecurityRuleEngine:
    """보안 룰 엔진 - 패턴 기반 탐지"""
    
    # 민감 행위 키워드
    SENSITIVE_ACTIONS = [
        "비밀번호", "password", "재설정", "reset",
        "결제", "payment", "환불", "refund",
        "주민등록", "주민번호", "신분증",
        "계좌", "account", "카드", "card",
        "인증", "본인확인", "verification",
        "로그인", "login", "접속"
    ]
    
    # 단축 URL 서비스
    SHORT_URL_DOMAINS = [
        "bit.ly", "tinyurl.com", "gg.gg", "han.gl",
        "me2.do", "goo.gl", "t.co", "ow.ly",
        "is.gd", "buff.ly", "adf.ly", "shorturl.at"
    ]
    
    # Homoglyph - 혼동되기 쉬운 문자
    HOMOGLYPH_PATTERNS = {
        # 라틴 vs 키릴
        'a': ['а', 'ɑ'],  # 키릴 а
        'e': ['е', 'е'],  # 키릴 е
        'o': ['о', 'ο'],  # 키릴 о, 그리스 ο
        'p': ['р', 'ρ'],  # 키릴 р
        'c': ['с', 'ϲ'],  # 키릴 с
        'x': ['х', 'ⅹ'],  # 키릴 х
        'y': ['у', 'ү'],  # 키릴 у
    }
    
    # 의심 토큰
    SUSPICIOUS_TOKENS = [
        "verify", "secure", "update", "confirm",
        "urgent", "suspended", "limited", "restricted",
        "action-required", "click-here", "login-now"
    ]
    
    def __init__(self):
        self.message_history = []  # 발송 패턴 추적용
    
    def check_sensitive_link_abuse(self, text: str) -> Dict[str, Any]:
        """
        민감 행위를 링크로 유도하는지 검사
        
        Returns:
            is_violation: 위반 여부
            risk_score: 추가 위험 점수
            details: 상세 내용
        """
        violations = []
        risk_score = 0
        
        # URL 추출
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        
        if urls:
            # 민감 키워드 + URL 조합 확인
            text_lower = text.lower()
            for keyword in self.SENSITIVE_ACTIONS:
                if keyword in text_lower:
                    violations.append({
                        "type": "민감행위_링크유도",
                        "keyword": keyword,
                        "message": f"'{keyword}' 작업을 링크로 유도하고 있습니다"
                    })
                    risk_score += 35
        
        # "클릭", "바로", "즉시" 등 긴급성 + 민감 행위
        urgency_words = ["클릭", "바로", "즉시", "지금", "긴급", "오늘", "24시간"]
        has_urgency = any(word in text for word in urgency_words)
        has_sensitive = any(word in text.lower() for word in self.SENSITIVE_ACTIONS)
        
        if has_urgency and has_sensitive and urls:
            violations.append({
                "type": "긴급성_민감행위_조합",
                "message": "긴급성을 강조하며 민감한 작업을 링크로 유도"
            })
            risk_score += 30
        
        return {
            "is_violation": len(violations) > 0,
            "risk_score": min(risk_score, 100),
            "violations": violations,
            "recommendation": "앱을 직접 열어서 확인하세요. 문자 내 링크를 클릭하지 마세요." if violations else None
        }
    
    def check_url_safety(self, text: str) -> Dict[str, Any]:
        """
        단축 URL 및 Homoglyph 탐지
        
        Returns:
            suspicious_urls: 의심스러운 URL 목록
            risk_score: 추가 위험 점수
        """
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        
        suspicious_urls = []
        total_risk = 0
        
        for url in urls:
            risk = 0
            reasons = []
            
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                path = parsed.path.lower()
                
                # 1. 단축 URL 체크
                if any(short in domain for short in self.SHORT_URL_DOMAINS):
                    risk += 40
                    reasons.append("단축 URL 사용")
                
                # 2. Homoglyph 체크 (키릴 문자 등)
                has_homoglyph = False
                for char in domain:
                    if ord(char) > 127:  # 비ASCII 문자
                        # 키릴 문자 범위 (Cyrillic)
                        if 0x0400 <= ord(char) <= 0x04FF:
                            has_homoglyph = True
                            break
                
                if has_homoglyph:
                    risk += 50
                    reasons.append("위장 문자(Homoglyph) 사용 - 키릴/그리스 문자")
                
                # 3. 의심 토큰 체크
                for token in self.SUSPICIOUS_TOKENS:
                    if token in domain or token in path:
                        risk += 25
                        reasons.append(f"의심 키워드 '{token}' 포함")
                
                # 4. 이상한 TLD (Top Level Domain)
                suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work']
                if any(domain.endswith(tld) for tld in suspicious_tlds):
                    risk += 35
                    reasons.append("의심스러운 도메인 확장자")
                
                # 5. IP 주소 직접 사용
                if re.match(r'\d+\.\d+\.\d+\.\d+', domain):
                    risk += 40
                    reasons.append("IP 주소 직접 사용")
                
                # 6. 과도하게 긴 도메인
                if len(domain) > 30:
                    risk += 20
                    reasons.append("비정상적으로 긴 도메인")
                
                # 7. 하이픈 과다 사용
                if domain.count('-') > 3:
                    risk += 15
                    reasons.append("하이픈 과다 사용")
                
                if risk > 0:
                    suspicious_urls.append({
                        "url": url,
                        "domain": domain,
                        "risk_score": min(risk, 100),
                        "reasons": reasons
                    })
                    total_risk += risk
                    
            except Exception as e:
                suspicious_urls.append({
                    "url": url,
                    "risk_score": 30,
                    "reasons": [f"URL 파싱 실패: {str(e)}"]
                })
        
        return {
            "suspicious_urls": suspicious_urls,
            "risk_score": min(total_risk, 100),
            "url_count": len(urls)
        }
    
    def check_sending_pattern(self, text: str, sender: str = None, timestamp: datetime = None) -> Dict[str, Any]:
        """
        비정상 발송 패턴 탐지
        
        Args:
            text: 메시지 내용
            sender: 발신번호
            timestamp: 발송 시각
        
        Returns:
            anomalies: 이상 패턴 목록
            risk_score: 추가 위험 점수
        """
        anomalies = []
        risk_score = 0
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # 1. 새벽 시간대 발송 (00:00 - 06:00)
        hour = timestamp.hour
        if 0 <= hour < 6:
            anomalies.append({
                "type": "비정상_시간대",
                "detail": f"새벽 {hour}시 발송 - 정상 기업은 새벽에 문자를 보내지 않습니다"
            })
            risk_score += 25
        
        # 2. 발신번호 패턴 (개인번호에서 기업 사칭)
        if sender and sender.startswith('010'):
            company_keywords = ["쿠팡", "네이버", "카카오", "은행", "KB", "신한", "우리", "NH", "정부", "경찰", "국세청"]
            if any(keyword in text for keyword in company_keywords):
                anomalies.append({
                    "type": "발신번호_불일치",
                    "detail": "개인 휴대폰 번호에서 기업을 사칭하고 있습니다"
                })
                risk_score += 40
        
        # 3. 메시지 히스토리 분석 (동일 발신자의 패턴)
        if sender:
            # 최근 같은 발신자의 메시지 찾기
            recent_messages = [
                msg for msg in self.message_history[-50:]  # 최근 50개만
                if msg.get('sender') == sender
            ]
            
            # 단시간 대량 발송 (5분 내 10건 이상)
            if len(recent_messages) >= 10:
                time_diff = (timestamp - recent_messages[-10]['timestamp']).total_seconds()
                if time_diff < 300:  # 5분
                    anomalies.append({
                        "type": "대량_발송",
                        "detail": f"5분 내 {len(recent_messages)}건 발송 - 자동화 공격 의심"
                    })
                    risk_score += 35
        
        # 4. 메시지 길이 이상 (너무 짧거나 너무 김)
        if len(text) < 20:
            anomalies.append({
                "type": "비정상_길이",
                "detail": "메시지가 너무 짧습니다 - 정보 부족"
            })
            risk_score += 10
        elif len(text) > 500:
            anomalies.append({
                "type": "비정상_길이",
                "detail": "메시지가 너무 깁니다 - 과도한 정보"
            })
            risk_score += 15
        
        # 5. 특수문자 과다 사용
        special_chars = re.findall(r'[!@#$%^&*()_+=\[\]{};:\'",.<>?/\\|`~]', text)
        if len(special_chars) > 10:
            anomalies.append({
                "type": "특수문자_과다",
                "detail": f"특수문자 {len(special_chars)}개 사용 - 스팸 가능성"
            })
            risk_score += 20
        
        # 히스토리에 추가
        self.message_history.append({
            'sender': sender,
            'timestamp': timestamp,
            'text': text[:50]  # 앞 50자만 저장
        })
        
        # 히스토리 크기 제한 (메모리 관리)
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
        
        return {
            "anomalies": anomalies,
            "risk_score": min(risk_score, 100),
            "timestamp": timestamp.isoformat()
        }


class SmishingAnalyzer:
    """스미싱 탐지 분석기 (고급 보안 기능 통합)"""

    def __init__(self, model: str = None):
        self.model = model or DEFAULT_MODEL
        self.security_engine = SecurityRuleEngine()

    def _encode_image(self, image_bytes: bytes) -> str:
        """이미지를 base64로 인코딩"""
        return base64.b64encode(image_bytes).decode('utf-8')

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """GPT 응답을 파싱하여 JSON으로 변환"""
        try:
            # JSON 블록 추출
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
            return {
                "risk_score": 50,
                "is_smishing": False,
                "risk_level": "medium",
                "reasons": ["분석 중 오류가 발생했습니다."],
                "safe_actions": ["전문가에게 문의하세요."],
                "error": str(e)
            }

    def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """이미지를 분석하여 스미싱 여부 판단"""
        try:
            # 이미지 크기 최적화
            img = Image.open(BytesIO(image_bytes))
            if img.width > 1024 or img.height > 1024:
                img.thumbnail((1024, 1024))
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()

            base64_image = self._encode_image(image_bytes)

            # GPT-4 Vision API 호출
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": SMISHING_ANALYSIS_PROMPT},
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

    def analyze_text(self, text: str, sender: str = None, timestamp: datetime = None) -> Dict[str, Any]:
        """
        텍스트를 분석하여 스미싱 여부 판단 (고급 보안 룰 적용)
        
        Args:
            text: 분석할 문자 텍스트
            sender: 발신번호 (선택)
            timestamp: 발송 시각 (선택)
        """
        try:
            # 1️⃣ 로컬 룰 기반 사전 리스크 계산
            local_risk = 0

            # (1) 민감행위 탐지
            precheck = self.security_engine.check_sensitive_link_abuse(text)
            local_risk += precheck['risk_score']

            # (2) URL 패턴 점검
            url_check = self.security_engine.check_url_safety(text)
            local_risk += url_check['risk_score']

            # (3) 발신자 이상 행위 (선택)
            if sender:
                sender_check = self.security_engine.check_sending_pattern(text, sender, timestamp)
                local_risk += sender_check['risk_score']


            # 2️⃣ 모델 자동 승격
            base_model = "gpt-4o" if local_risk >= 50 else self.model

            # 3️⃣ GPT-4 호출
            response = client.chat.completions.create(
                model=base_model,
                messages=[
                    {"role": "user", "content": TEXT_ANALYSIS_PROMPT.format(text=text)}
                ],
                max_tokens=800
            )

            response_text = response.choices[0].message.content
            result = self._parse_response(response_text)

            # 2. 보안 룰 엔진 적용
            # 2-1. 민감 행위 링크 체크
            sensitive_check = self.security_engine.check_sensitive_link_abuse(text)
            if sensitive_check['is_violation']:
                result['risk_score'] = min(result['risk_score'] + sensitive_check['risk_score'], 100)
                result['reasons'].extend([v['message'] for v in sensitive_check['violations']])
                if sensitive_check['recommendation']:
                    result['safe_actions'].insert(0, sensitive_check['recommendation'])
            
            # 2-2. URL 안전성 체크
            url_check = self.security_engine.check_url_safety(text)
            if url_check['suspicious_urls']:
                result['risk_score'] = min(result['risk_score'] + url_check['risk_score'], 100)
                for sus_url in url_check['suspicious_urls']:
                    result['reasons'].append(
                        f"의심스러운 URL: {sus_url['domain']} - {', '.join(sus_url['reasons'])}"
                    )
            
            # 2-3. 발송 패턴 체크
            pattern_check = self.security_engine.check_sending_pattern(text, sender, timestamp)
            if pattern_check['anomalies']:
                result['risk_score'] = min(result['risk_score'] + pattern_check['risk_score'], 100)
                for anomaly in pattern_check['anomalies']:
                    result['reasons'].append(f"{anomaly['type']}: {anomaly['detail']}")
            
            # 3. 위험도 재평가
            if result['risk_score'] >= 70:
                result['is_smishing'] = True
                result['risk_level'] = 'high'
            elif result['risk_score'] >= 50:
                result['risk_level'] = 'medium'
            else:
                result['risk_level'] = 'low'

            # 로컬 룰 점수 병합 (가중치 기반)
            result['risk_score'] = min(100, result['risk_score'] + int(local_risk * 0.3))
            result['risk_level'] = (
                "high" if result['risk_score'] >= 75
                else "medium" if result['risk_score'] >= 40
                else "low"
            )
            
            # 4. 보안 룰 결과 추가
            result['security_checks'] = {
                'sensitive_link_abuse': sensitive_check,
                'url_safety': url_check,
                'sending_pattern': pattern_check
            }

            result['used_model'] = base_model
            result['local_risk'] = local_risk

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