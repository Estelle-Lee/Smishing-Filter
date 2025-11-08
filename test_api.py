import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("🧪 OpenAI API 테스트 중...")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Hello!"}
        ],
        max_tokens=50
    )
    
    print("✅ 성공!")
    print(f"응답: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ 에러: {e}")
