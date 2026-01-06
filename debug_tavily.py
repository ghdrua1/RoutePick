import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

from agents.search_agent import SearchAgent
from config.config import Config



async def main():
    print("🎨 [RoutePick] Search Agent 전략 검색 디버깅 시작...")
    
    # 1. 설정 로드
    config = Config.get_agent_config()
    agent = SearchAgent(config=config)
    
    # 2. 테스트 데이터 (예시)
    user_input = {
        "theme": "비 오는 날 성수동 실내 데이트",
        "location": "서울 성수동"
    }
    
    # 3. 실행
    result = await agent.execute(user_input)
    
    if result["success"]:
        print(f"\n🧠 [1/2단계] 행동 분석: {result.get('action_analysis', 'N/A')}")
        print("\n🏠 [3단계] 설계된 후보 풀 (Candidate Pool):")
        print("-" * 60)
        
        candidates = result.get("candidate_pool", [])
        if not candidates:
            print("검색 결과가 없거나 모든 장소가 필터링되었습니다.")
        
        for p in candidates:
            # .get(키, 기본값) 형식을 사용하여 데이터가 없어도 프로그램이 멈추지 않음
            category = p.get('category', '추천 장소')
            name = p.get('name', '이름 없음')
            rating = p.get('rating', 'N/A')
            trust_score = p.get('trust_score', 'N/A')
            address = p.get('address', '주소 정보 없음')
            url = p.get('source_url', '링크 없음')

            print(f"\n[{category}] {name}")
            print(f"    평점: {rating} | 신뢰도 점수: {trust_score}")
            print(f"    주소: {address}")
            print(f"    URL: {url}")
    else:
        print(f"❌ 에러 발생: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())