import json
import asyncio
import os
from typing import Any, Dict, Optional, List
from openai import AsyncOpenAI
import googlemaps
from .base_agent import BaseAgent
from tools.tavily_search_tool import TavilySearchTool

class SearchAgent(BaseAgent):
    """
    사용자의 테마를 [행동 단위]로 분석하여 [코스 구조]를 먼저 설계하고,
    그 설계를 채울 최적의 장소를 발굴 및 검증하는 전략가 에이전트.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="SearchAgent", config=config)
        self.search_tool = TavilySearchTool(config=config)
        
        # 1. config에서 먼저 찾고, 없으면 os.environ에서 직접 찾음
        self.openai_api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        self.google_maps_api_key = self.config.get("google_maps_api_key") or os.getenv("GOOGLE_MAPS_API_KEY")
        self.llm_model = self.config.get("llm_model", "gpt-4o-mini")
        
        # 2. 키가 여전히 없으면 명확한 에러 메시지 출력
        if not self.google_maps_api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY가 설정되지 않았습니다. .env 파일이나 환경변수를 확인하세요.")
        
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        self.gmaps = googlemaps.Client(key=self.google_maps_api_key)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """전략 수립 -> 행동 분해 -> 검색 -> 구글 검증 -> 후보 풀 반환"""
        if not self.validate_input(input_data):
            return {"success": False, "error": "입력 데이터가 유효하지 않습니다."}

        theme = input_data.get("theme")
        location = input_data.get("location")
        
        # 1. 전략 수립 (행동 분석 및 카테고리 설계)
        print(f"\n🧠 [Step 1] 테마 분석 및 코스 설계 중...")
        
        strategy = await self._generate_strategy(theme, location)
        if not strategy:
            return {"success": False, "error": "LLM 전략 수립 실패"}
        

        # 2. Tavily 멀티 검색 (본문 데이터 확보)
        print(f"📡 [Step 2] Tavily를 통해 실시간 데이터 수집 중...")

        tasks = [
            self.search_tool.execute(query=step['search_query'], max_results=5) 
            for step in strategy['course_structure']
        ]
        search_results = await asyncio.gather(*tasks)
        
        # ⭐ [여기서부터 추가/수정] 3. LLM 엔티티 추출 단계 (핵심 기획)
        print(f"📝 [Step 3] LLM이 검색 결과에서 진짜 장소명만 추출 중...")
        all_raw_data = []
        for res in search_results:
            if res["success"]:
                # 제목과 본문을 합쳐서 LLM에게 읽힙니다.
                all_raw_data.extend([f"제목: {p['name']}, 본문: {p['description']}" for p in res["places"]])
        
        # GPT에게 "진짜 이름"만 뽑으라고 시킴
        refined_names = await self._extract_place_entities(all_raw_data, location)
        
        # 4. Google Maps 기반 검증
        candidate_pool = []
        seen_names = set() # 중복 제거용

        for name in refined_names:
            # 구글 검색 전 '청소기'로 한 번 더 다듬기 (안전장치)
            clean_name = self._clean_place_name(name)
            google_info = self._get_google_data(clean_name, location)
            
            if google_info and google_info['rating'] >= 4.0:
                if google_info['name'] in seen_names: continue
                
                # 🔗 [추가] Tavily 원본 결과에서 해당 장소의 근거 URL 찾기
                matched_url = f"https://www.google.com/maps/search/?api=1&query={google_info['name']}+{location}".replace(" ", "+")
                for res in search_results:
                    if not res["success"]: continue
                    for p in res["places"]:
                        # 추출된 이름이나 구글이 찾은 이름이 블로그 제목에 포함되어 있는지 확인
                        if clean_name in p['name'] or google_info['name'] in p['name']:
                            matched_url = p['source_url']
                            break


                trust_score = self._calculate_trust_score(
                    google_info['rating'], google_info['reviews_count'], ""
                )
                
                print(f"   - [Keep] {google_info['name']} (평점: {google_info['rating']})")
                candidate_pool.append({
                    "name": google_info['name'],
                    "category": "추천 장소",
                    "rating": google_info['rating'],
                    "trust_score": trust_score,
                    "address": google_info['address'],
                    "source_url": matched_url  # ❗ 매칭된 블로그 URL 저장
                })
                seen_names.add(google_info['name'])


        # 신뢰도 점수(Trust Score) 순으로 정렬하여 가장 쌈뽕한 곳을 위로
        candidate_pool.sort(key=lambda x: x['trust_score'], reverse=True)
        
        return {
            "success": True,
            "action_analysis": strategy['action_analysis'],
            "candidate_pool": candidate_pool,
        }

    async def _extract_place_entities(self, raw_texts: List[str], location: str) -> List[str]:
        """지저분한 검색 결과 텍스트에서 실제 가게 이름만 추출"""
        if not raw_texts: return []

        prompt = f"""
        당신은 정보 정제 전문가입니다. 아래의 검색 결과(제목 및 본문)를 분석하여 {location} 지역에 위치한 구체적인 '장소 이름(가게명, 카페명, 전시장명 등)'만 추출하세요.
        - 일반 명사(맛집, 데이트 코스)는 무시하세요.
        - 수식어(분위기 좋은 등)를 제거하고 오직 고유 명칭만 남기세요.
        - 결과는 JSON 배열로만 응답하세요.

        [데이터]
        {raw_texts[:15]}  # 토큰 절약을 위해 상위 15개만

        응답 형식: {{"places": ["이름1", "이름2"]}}
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("places", [])
        except Exception:
            return [] # 실패 시 빈 리스트 (그러면 fallback으로 넘어감)
        

    async def _generate_strategy(self, theme: str, location: str) -> Optional[Dict]:
        """
        [핵심 페르소나 반영]
        테마를 행동 타입으로 분해하고 검색 전략을 수립하는 프롬프트
        """
        prompt = f"""
        당신은 베테랑 여행 설계자입니다. 사용자의 테마를 분석하여 최적의 '코스 구조'를 설계하고, 각 구조를 채울 검색 쿼리를 생성하세요.

        [사용자 입력]
        - 테마: {theme}
        - 지역: {location}

        [임무]
        1. 이 테마에 필요한 '행동 타입(Action Types)'을 3가지 분석하세요. (예: 대화 중심, 활동 중심, 휴식 중심)
        2. 각 행동에 맞는 '장소 카테고리'를 결정하세요. (예: 조용한 카페, 실내 전시장, 분위기 있는 식당)
        3. 각 카테고리별로 Tavily 검색을 위한 최적화된 '검색 쿼리'를 1개씩, 총 3개 생성하세요.

        [응답 형식 (JSON 고정)]
        {{
          "action_analysis": "행동 타입 분석 요약",
          "course_structure": [
            {{
              "step": 1,
              "category": "카테고리명",
              "search_query": "Tavily 검색용 최적화 쿼리"
            }},
            {{
              "step": 2,
              "category": "카테고리명",
              "search_query": "Tavily 검색용 최적화 쿼리"
            }},
            {{
              "step": 3,
              "category": "카테고리명",
              "search_query": "Tavily 검색용 최적화 쿼리"
            }}
          ]
        }}
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        #이게 원래 exception        
        # except Exception as e:
        #     print(f"Strategy Generation Error: {e}")
        #     return None

        #돈 없는 api 거지버전
        except Exception as e:
            # ❗ 429 에러(돈 없음) 발생 시 가짜 전략으로 우회해서 다음 단계 진행
            print(f"⚠️ LLM 호출 실패(쿼터 초과 등): {e}")
            print("🚀 임시 Mock 전략을 사용하여 Tavily/Google 검색을 계속합니다.")
            
            return {
                "action_analysis": f"{theme}을(를) 위한 실내외 혼합 활동 및 동선 최적화 전략",
                "course_structure": [
                    {"step": 1, "category": "카페", "search_query": f"{location} {theme} 분위기 좋은 카페"},
                    {"step": 2, "category": "활동", "search_query": f"{location} {theme} 팝업스토어 전시회"},
                    {"step": 3, "category": "식사", "search_query": f"{location} {theme} 맛집 추천"}
                ]
            }

    ## 한번 추가해보는 청소기
    def _clean_place_name(self, raw_name: str) -> str:
        """
        블로그 제목 등에서 실제 가게 이름만 남기기 위한 청소기
        예: '성수동 카페 베이크모굴 실내 놀거리 - 네이버 블로그' -> '베이크모굴'
        """
        # 1. 흔한 수식어 및 플랫폼 이름 제거
        junk_words = [
            '네이버 블로그', '네이버 포스트', '티스토리', '인스타그램', 'Instagram',
            '유튜브', 'YouTube', '트립닷컴', '나무위키', '총정리', '추천', 'BEST', 'TOP'
        ]
        
        clean_name = raw_name
        for word in junk_words:
            clean_name = clean_name.replace(word, "")
        
        # 2. 특수기호 제거 및 다듬기
        import re
        clean_name = re.sub(r'[\-\|\:\[\]\(\)]', ' ', clean_name) # 기호를 공백으로
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()     # 연속 공백 제거
        
        # 3. 너무 길면 앞의 2~3단어만 사용 (보통 앞에 가게 이름이 나옴)
        parts = clean_name.split()
        if len(parts) > 3:
            return " ".join(parts[:2]) # '성수동 베이크모굴' 정도로 압축
            
        return clean_name
    
    def _get_google_data(self, name: str, location: str) -> Optional[Dict]:
        """Google Places API 검증 (이름 정제 로직 포함)"""
        try:
            # [수정] 지저분한 이름을 청소하고 검색
            search_name = self._clean_place_name(name)
            query = f"{location} {search_name}"
            
            print(f"   🔎 구글 검색 시도: '{query}'") # 어떤 키워드로 구글에 물어보는지 확인용
            
            res = self.gmaps.places(query=query)
            if res.get('results'):
                place = res['results'][0]
                return {
                    "name": place.get("name"), # 구글이 확인해준 진짜 가게 이름
                    "rating": place.get("rating", 0.0),
                    "reviews_count": place.get("user_ratings_total", 0),
                    "address": place.get("formatted_address")
                }
        except Exception as e:
            print(f"      ⚠️ 구글 API 에러: {e}")
            return None
        return None
    
    def _calculate_trust_score(self, rating: float, reviews: int, content: str) -> float:
        """구글 평점 기반 + 보조 지표 가산점 로직"""
        score = rating
        # 보조 지표 1: 리뷰 수 (데이터가 많을수록 신뢰도 +)
        if reviews > 500: score += 0.2
        elif reviews > 100: score += 0.1
        
        # 보조 지표 2: 최신성 및 신뢰 키워드 (내돈내산 등)
        trust_keywords = ['내돈내산', '솔직후기', '분위기', '친절']
        for kw in trust_keywords:
            if kw in content:
                score += 0.05
        return round(min(score, 5.0), 2)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """BaseAgent의 필수 구현 추상 메서드"""
        if not isinstance(input_data, dict):
            return False
        return bool(input_data.get("theme") and input_data.get("location"))