"""
코스 제작 Tool
검색된 장소들을 바탕으로 최적의 코스를 생성합니다.
"""

import json
import os
import openai
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Any, Dict, List, Optional
from .base_tool import BaseTool
from .google_maps_tool import GoogleMapsTool
from config.config import Config

load_dotenv()

config = Config.get_agent_config()
config["api_key"] = os.getenv("GOOGLE_MAPS_API_KEY") 
maptool = GoogleMapsTool(config=config)

@tool
async def check_routing(
        places: List[Dict[str, Any]],  # 필수 파라미터로 명시 (기본값 제거)
        origin: Optional[Dict[str, Any]] = None,
        destination: Optional[Dict[str, Any]] = None,
        mode: str = "transit",  # 'driving', 'walking', 'transit', 'bicycling'
    ) -> Dict[str, Any]:
    """
    주어진 장소들에 대해 경로 최적화를 실행합니다.
    
    **중요: 이 함수를 호출할 때는 반드시 'places' 파라미터를 전달해야 합니다.**
    
    Args:
        places: 장소 정보 리스트 (필수, 각 장소는 name, address, coordinates 등을 포함)
               각 장소는 반드시 coordinates 필드를 포함해야 합니다: {{"lat": 위도, "lng": 경도}}
        origin: 출발지 (선택사항, 없으면 places의 첫 번째 항목)
        destination: 도착지 (선택사항, 없으면 places의 마지막 항목)
        mode: 이동 수단 ('driving', 'walking', 'transit', 'bicycling')
    
    Returns:
        경로 최적화 결과 딕셔너리
    """
    # places가 None이거나 비어있으면 오류 반환
    if not places:
        return {
            "success": False,
            "optimized_route": [],
            "total_duration": 0,
            "total_distance": 0,
            "directions": [],
            "error": "places 파라미터가 필수입니다."
        }

    return await maptool.execute(
        places=places,
        origin=origin,
        destination=destination,
        mode=mode
    )

class CourseCreationTool(BaseTool):
    """LLM을 사용한 맞춤형 코스 제작 Tool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Tool 설정 (llm_model, api_key 등)
        """
        super().__init__(
            name="course_creation",
            description="검색된 장소들을 바탕으로 사용자의 선호도와 시간대를 고려한 최적의 코스를 생성합니다.",
            config=config or {}
        )
        
        # LLM 설정
        self.llm_model = self.config.get("llm_model", "gpt-4o-mini")
        # OpenAI API 키 우선순위: openai_api_key > api_key > 환경 변수
        self.api_key = (
            self.config.get("openai_api_key") or 
            self.config.get("api_key") or 
            os.getenv("OPENAI_API_KEY")
        )
        if self.api_key:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        else:
            # 환경 변수에서 직접 로드
            self.client = openai.AsyncOpenAI()
        # LLM 클라이언트 초기화 (실제 구현 시 사용)
        # 예: OpenAI, Anthropic, 등
        # self.client = OpenAI(api_key=self.api_key)
        self.tools = [check_routing]
    
    async def execute(
        self,
        places: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        time_constraints: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        코스 제작 실행
        
        Args:
            places: 검색된 장소 리스트
            user_preferences: 사용자 선호도
            time_constraints: 시간 제약
            
        Returns:
            코스 생성 결과
        """
        # 장소 개수 사전 제한 (컨텍스트 길이 초과 방지) - 더 엄격하게 제한
        MAX_PLACES = 30  # 50 -> 30으로 감소
        if len(places) > MAX_PLACES:
            print(f"⚠️ 장소가 {len(places)}개로 너무 많아 {MAX_PLACES}개로 제한합니다.")
            # 저장된 장소는 우선 보존
            saved_places = [p for p in places if p.get('is_saved_place')]
            other_places = [p for p in places if not p.get('is_saved_place')]
            # 저장된 장소 + 나머지 장소 (신뢰도 순으로 정렬)
            other_places.sort(key=lambda x: x.get('trust_score', 0), reverse=True)
            places = saved_places + other_places[:MAX_PLACES - len(saved_places)]
        """
        코스 제작 실행
        
        Args:
            places: 검색된 장소 리스트
            user_preferences: 사용자 선호도 {
                "theme": str,  # 테마 (예: "비 오는 날 실내 데이트")
                "group_size": int,  # 인원
                "visit_date": str,  # 방문 일자
                "visit_time": str,  # 방문 시간
                "transportation": str  # 이동 수단
            }
            time_constraints: 시간 제약 {
                "start_time": str,  # 시작 시간
                "end_time": str,  # 종료 시간
                "total_duration": int  # 총 소요 시간 (분)
            }
            
        Returns:
            {
                "success": bool,
                "course": {
                    "places": List[Dict],  # 선정된 장소 리스트
                    "estimated_duration": Dict[str, int],  # 각 장소별 예상 체류 시간
                    "course_description": str  # 코스 설명
                },
                "reasoning": str,  # 코스 선정 이유
                "error": Optional[str]
            }
        """
        try:
            if not self.validate_params(places=places, user_preferences=user_preferences):
                return {
                    "success": False,
                    "course": None,
                    "reasoning": "",
                    "error": "필수 파라미터가 누락되었습니다."
                }
            
            if not places:
                return {
                    "success": False,
                    "course": None,
                    "reasoning": "",
                    "error": "장소 리스트가 비어있습니다."
                }
            
            # 날씨 정보 가져오기 (지역 기준으로 한 번만 체크)
            weather_info = {}
            try:
                visit_date = user_preferences.get("visit_date")
                location = user_preferences.get("location", "")  # 사용자가 입력한 지역 (기본값 추가)
                
                # visit_date가 있으면 날씨 조회 시도 (location은 선택사항)
                if visit_date:
                    # 날짜에서 첫 번째 날짜만 추출 (YYYY-MM-DD 형식)
                    date_str = visit_date.split()[0] if visit_date else None
                    
                    # 지역의 중심 좌표를 가져와서 날씨 조회 (한 번만)
                    # 첫 번째 장소의 좌표를 사용
                    if places and len(places) > 0:
                        first_place = places[0]
                        coords = first_place.get("coordinates")
                        if coords and coords.get("lat") and coords.get("lng"):
                            lat = float(coords.get("lat"))
                            lng = float(coords.get("lng"))
                            # 지역 날씨 한 번만 조회
                            single_weather = await maptool.get_weather_info(lat, lng, date_str)
                            # 모든 장소에 동일한 날씨 정보 적용
                            for idx in range(len(places)):
                                weather_info[idx] = single_weather
                            location_name = location or f"{lat:.2f},{lng:.2f}"
                            print(f"🌤️ 지역 날씨 정보 조회 완료: {location_name} - {single_weather.get('temperature')}°C, {single_weather.get('condition')}")
                        else:
                            print(f"⚠️ 첫 번째 장소에 좌표 정보가 없어 날씨 정보를 가져올 수 없습니다.")
                    else:
                        print(f"⚠️ 장소 리스트가 비어있어 날씨 정보를 가져올 수 없습니다.")
                else:
                    print(f"⚠️ 방문 날짜 정보가 없어 날씨 정보를 가져오지 않습니다.")
            except Exception as e:
                print(f"⚠️ 날씨 정보 가져오기 실패 (계속 진행): {e}")
                import traceback
                traceback.print_exc()
                weather_info = {}
            
            # LLM을 사용하여 코스 생성
            course_result = await self._generate_course_with_llm(
                places, user_preferences, time_constraints, weather_info
            )
            
            return {
                "success": True,
                "course": course_result.get("course"),
                "reasoning": course_result.get("reasoning", ""),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "course": None,
                "reasoning": "",
                "error": str(e)
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Tool 입력 스키마 반환
        
        Returns:
            스키마 딕셔너리
        """
        return {
            "type": "object",
            "properties": {
                "places": {
                    "type": "array",
                    "description": "검색된 장소 리스트",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "category": {"type": "string"},
                            "rating": {"type": "number"},
                            "address": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "user_preferences": {
                    "type": "object",
                    "description": "사용자 선호도",
                    "properties": {
                        "theme": {"type": "string"},
                        "group_size": {"type": "integer"},
                        "visit_date": {"type": "string"},
                        "visit_time": {"type": "string"},
                        "transportation": {"type": "string"},
                        "budget": {"type": "string"}
                    },
                    "required": ["theme"]
                },
                "time_constraints": {
                    "type": "object",
                    "description": "시간 제약 (선택사항)",
                    "properties": {
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "total_duration": {"type": "integer"}
                    }
                }
            },
            "required": ["places", "user_preferences"]
        }
    
    async def _generate_course_with_llm(
        self,
        places: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        time_constraints: Optional[Dict[str, Any]],
        weather_info: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        LLM을 사용하여 코스 생성
        
        Args:
            places: 장소 리스트
            user_preferences: 사용자 선호도
            time_constraints: 시간 제약
            
        Returns:
            코스 생성 결과
        """
        for i, place in enumerate(places):
            place['original_index'] = i
        
        system_instruction = """
당신은 여행 코스 설계 전문가입니다. 제공된 장소 리스트에서 최적의 코스를 선택하고 JSON만 반환하세요.

입력: 장소리스트={places}, 선호조건={user_preferences}, 시간제약={time_constraints}, 날씨={weather_info}
각 장소는 original_index를 가지며, 모든 인덱스 참조는 이 값을 사용하세요.

규칙:
1. ⭐ 표시된 저장 장소는 최우선 포함
2. **check_routing tool 사용 시 반드시 'places' 파라미터를 전달해야 합니다.**
   - check_routing(places=[장소리스트], mode="transit") 형식으로 호출
   - 각 장소는 반드시 coordinates 필드 포함: {{"name":"장소명","coordinates":{{"lat":위도,"lng":경도}}}}
   - places 파라미터 없이 호출하면 오류가 발생합니다.
3. 좌표 기반으로 가까운 장소 우선 그룹화
4. 이동거리 30분 이내, 도보 우선(차이 20분 이내면 도보)
5. **날씨 기반 코스 추천 (매우 중요):**
   - 날씨가 좋은 경우 (맑음, 구름 조금, 기온 15-25°C): 야외 활동 장소 우선 선택 (공원, 야외 카페, 산책로, 전망대 등)
   - 비/눈/천둥번개가 오는 경우: 실내 활동 장소 우선 선택 (박물관, 미술관, 쇼핑몰, 실내 카페, 영화관 등)
   - 너무 춥거나 덥거나 (기온 < 5°C 또는 > 30°C): 실내 활동 우선, 이동 경로 최소화 (가까운 실내 장소들을 그룹화)
   - 날씨가 나쁜 경우 (비/눈/천둥번개/안개): 이동 경로를 최소화하여 실내 장소들을 가까운 거리로 배치
   - 날씨 정보가 제공되면 반드시 이를 우선적으로 고려하여 장소 선택 및 순서 결정
6. 음식점/카페 중간 배치(연속 배치 금지)

작업순서:
1. 저장 장소 선정
2. 테마 맞는 추가 장소 선정
3. 거리 최소화 순서로 배열
4. check_routing(places=[선정된장소리스트], mode="transit")으로 검증 (반드시 places 파라미터 포함)
5. JSON 출력

출력 형식 (JSON만):
{{
  "selected_places": [original_index 리스트],
  "sequence": [original_index 순서 - 반드시 selected_places에 포함된 인덱스만 사용],
  "estimated_duration": {{"original_index":분}},
  "course_description": "설명",
  "reasoning": "1.[original_index]장소명:이유\\n2.[original_index]장소명:이유..."
}}

중요:
- selected_places: 선택한 장소의 original_index 배열 (예: [0, 2, 5, 7])
- sequence: selected_places에 포함된 original_index만 사용하여 방문 순서 지정
  * 예시: selected_places가 [0, 2, 5, 7]이면
    - ✅ 올바른 sequence: [0, 2, 5, 7] 또는 [2, 0, 7, 5] (모두 selected_places에 포함됨)
    - ❌ 잘못된 sequence: [1, 8, 5, 4] (1, 8, 4는 selected_places에 없음)
- sequence의 모든 인덱스는 반드시 selected_places에 포함되어 있어야 함
- reasoning은 "번호.[original_index]장소명:설명" 형식으로 모든 인덱스 포함
- 인덱스 연산 금지, 그대로 사용
- JSON만 출력, 다른 텍스트 없음
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # prompt = f"""
        # # Role
        # 당신은 현지 지리에 능통하고 모든 장소를 방문해본 여행 가이드입니다. 당신은 효율적인 경로 설계에 능통합니다.
        # **당신의 임무는 제공된 장소 리스트에서 최적의 코스를 선택하고 JSON 형식으로 반환하는 것입니다.**
        
        # Input Data
        # - 장소 리스트 : {self._format_places_for_prompt(places)}
        # - 사용자 선호 조건{{
        #     "theme": {user_preferences['theme']},
        #     "group_size": {user_preferences['group_size']},
        #     "visit_date": {user_preferences['visit_date']},
        #     "visit_time": {user_preferences['visit_time']},
        #     "transportation": {user_preferences['transportation']},
        #     "budget": {user_preferences.get('budget', '없음')}원
        # }}

        # # Constraints
        # 1. **최우선 규칙: 사용자가 저장한 장소(⭐ [사용자가 저장한 장소 - 최우선 고려] 표시가 있는 장소)는 반드시 최우선적으로 고려해야 합니다.**
        #    - 저장된 장소는 이미 테마와 위치 필터링을 통과했으므로, 사용자의 의도에 부합하는 장소입니다.
        #    - 저장된 장소가 사용자의 테마와 위치 조건에 부합한다면, 반드시 코스에 포함시켜야 합니다.
        #    - 저장된 장소를 포함하는 것이 다른 제약 조건(거리, 시간 등)과 충돌하더라도, 가능한 한 포함하도록 노력하세요.
        # 2. **예산 제약: 사용자가 예산을 입력한 경우(예산이 "없음"이 아닌 경우), 반드시 예산 내에서 코스를 설계해야 합니다.**
        #    - 예산이 입력된 경우에만 이 제약을 적용합니다. 예산이 "없음"이거나 입력되지 않은 경우에는 예산 제약을 무시합니다.
        #    - 예산이 입력된 경우, 각 장소의 예상 비용(입장료, 식사비, 교통비 등)을 고려하여 총 예산을 초과하지 않도록 해야 합니다.
        #    - 장소별 예상 비용은 카테고리와 평점을 기반으로 추정하세요 (예: 관광지 입장료 5,000-20,000원, 식당 식사비 10,000-50,000원, 카페 음료 5,000-15,000원).
        #    - 교통비도 예산에 포함시켜야 합니다 (지하철 1,250원, 버스 1,300원, 택시 기본요금 3,800원 등).
        #    - 예산이 부족할 경우, 무료 또는 저렴한 장소를 우선적으로 선택하거나, 비용이 많이 드는 장소를 제외해야 합니다.
        #    - 예산이 충분한 경우에도, 불필요하게 비싼 장소만 선택하지 말고 다양한 가격대의 장소를 균형있게 선택하세요.
        # 3. 제공된 [위치 좌표(위도, 경도)] 데이터를 기반으로 장소 간의 실제 물리적 거리를 계산하여 코스를 짤 것.
        # 4. 당신의 배경지식보다 입력된 좌표 정보가 서로 가까운 장소들을 우선적으로 그룹화할 것.
        # 5. 추천 신뢰도(Trust Score)가 높은 장소를 우선적으로 고려하되, 지리적 동선 효율성을 해치지 않는 범위 내에서 선택할 것.
        # 6. 각 코스 간 이동 거리는 30분 이내일 것. (좌표 데이터를 참고하여 보수적으로 판단)
        # 7. 도보 외의 교통 수단의 사용 빈도를 최소화할 것. 단, 환승은 사용 빈도 계산에서 제외한다. 도보와 교통 수단의 이동 시간 차이가 20분 이내이면 도보를 선택한다.
        # 8. 이전에 방문한 장소를 다시 지나지 않을 것.
        # 9. 장소에 현재 인원이 모두 수용 가능할 것.
        # 10. 장소가 방문 일자에 운영중임을 확인할 것. 입력된 정보가 없을 시 보수적으로 판단한다.
        # 11. 음식점, 카페 등을 코스 중간마다 배치할 것.

        # # Task Workflow
        # 1. **최우선 단계: 사용자가 저장한 장소(⭐ [사용자가 저장한 장소 - 최우선 고려] 표시)를 먼저 선정합니다.**
        #    - 저장된 장소는 이미 테마와 위치 필터링을 통과했으므로, 가능한 한 모두 포함하도록 노력하세요.
        #    - 저장된 장소가 여러 개인 경우, 모두 포함하거나 최대한 많이 포함하세요.
        # 2. **예산 확인 단계: 예산이 입력된 경우(예산이 "없음"이 아닌 경우)에만, 각 장소의 예상 비용을 계산합니다.**
        #    - 예산이 입력된 경우에만 이 단계를 수행합니다.
        #    - 저장된 장소와 새로 선정할 장소의 예상 비용을 합산하여 예산을 초과하지 않는지 확인합니다.
        #    - 예산을 초과할 경우, 비용이 적은 장소를 우선적으로 선택하거나 비싼 장소를 제외합니다.
        #    - 예산 내에서 최대한 많은 장소를 포함하도록 노력하세요.
        # 3. 저장된 장소를 포함한 상태에서, 사용자의 테마와 장소의 특징을 대조하여 추가로 적합한 장소들을 선정합니다. (예산 제약 고려)
        # 4. 이동 거리를 최소화하는 순서로 배열합니다. (저장된 장소를 포함한 전체 코스 기준)
        # 5. 선정된 순서가 실제 방문 가능 시간(영업시간) 내에 있는지 검증합니다.
        # 6. 예산이 입력된 경우, 최종 코스의 총 예상 비용이 예산을 초과하지 않는지 최종 확인합니다.
        # 7. 모든 논리적 검증이 끝나면 최종 JSON을 출력합니다.
        # 
        # **중요: 저장된 장소를 코스에 포함시키는 것이 최우선 목표이며, 예산이 입력된 경우 예산 제약도 반드시 준수해야 합니다.**

        # # Task Workflow
        # 1. 사용자의 테마와 장소의 특징을 대조하여 적합한 장소들을 선정합니다.
        # 2. 이동 거리를 최소화하는 순서로 배열합니다.
        # 3. 선정된 순서가 실제 방문 가능 시간(영업시간) 내에 있는지 검증합니다.
        # 4. 모든 논리적 검증이 끝나면 최종 JSON을 출력합니다.

        # # IMPORTANT: Output Format
        # **당신은 반드시 이 작업을 수행해야 합니다. 작업을 거부하거나 설명을 제공하지 마세요.**
        # **오직 JSON 형식만 출력하세요. 다른 텍스트, 설명, 마크다운 헤더는 절대 포함하지 마세요.**

        # ---

        # ## Return Value
        # 코스 설계 완료 후, **반드시 다음의 JSON 형식만** 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.
        # 
        # ```json
        # {{
        #     "selected_places": [장소 인덱스 리스트],
        #     "sequence": [방문 순서],
        #     "estimated_duration": {{장소별 체류 시간 (분)}},
        #     "course_description": "코스 설명",
        #     "reasoning": "선정 이유"
        # }}
        # ```

        # ### OUTPUT Rules
        # - "selected_places"는 0부터 시작하는 장소 인덱스 리스트입니다 (예: [0, 2, 4])
        # - **중요: 저장된 장소(⭐ [사용자가 저장한 장소 - 최우선 고려] 표시)의 인덱스는 반드시 selected_places에 포함되어야 합니다.**
        # - "sequence"는 선택된 장소들의 방문 순서를 인덱스로 나타냅니다 (예: [0, 1, 2]는 첫 번째, 두 번째, 세 번째로 선택된 장소의 순서)
        # - **중요: 저장된 장소는 sequence에도 반드시 포함되어야 하며, 가능하면 앞쪽 순서에 배치하세요.**
        # - "estimated_duration"은 장소 인덱스를 키로 하고 체류 시간(분)을 값으로 하는 객체입니다 (예: {{"0": 60, "2": 90, "4": 45}})
        # - "course_description"에는 방문하는 각각의 장소에 대한 간단한 설명들을 첨부합니다.
        # - **중요: course_description에 언급한 모든 장소는 반드시 selected_places에도 포함되어야 합니다.**
        # - "reasoning"에는 인덱스를 **장소이름(인덱스)** 형태로 언급하고, 인덱스에 해당하는 장소에 대한 설명을 바탕으로 사용자 선호 조건 중 만족시킨 사항들을 설명합니다.
        # - "reasoning"을 생성할 때, 방문하는 장소들의 순서 및 이동수단 설계 과정에 대해 설명하세요.
        # - 예산이 입력된 경우, "reasoning"에 예산이 어떻게 고려되었는지, 각 장소의 예상 비용과 총 예상 비용을 포함하여 설명하세요.
        # 
        # # 설명 예시:
        # # - 장소 A와 장소 C 사이에 장소 B가 있고, 다시 장소 A 주변 지역을 가지 않을 예정이기에 A-B-C 순서로 일정을 설계하였습니다.
        # # - 방문 기간이 오후이기 때문에, 잠시 쉬어가기 위해 장소 A와 장소 C 사이에 **카페** B를 먼저 방문합니다.
        # # - 장소 A와 장소 B 사이에 오르막길이 길게 있고 도보 시간이 15분 이상 걸리기 때문에, 이동수단으로 **버스**를 선택했습니다.
        # 
        # **중요: JSON 형식만 출력하고, 다른 텍스트는 포함하지 마세요.**
        # """

        llm = ChatOpenAI(model=self.llm_model, temperature=0)
        planner = create_openai_tools_agent(llm, self.tools, prompt)
        # AgentExecutor에 에러 핸들러 추가
        def handle_tool_error(error: Exception) -> str:
            """Tool 호출 오류 처리"""
            error_msg = str(error)
            if "Field required" in error_msg and "places" in error_msg:
                return "오류: check_routing tool을 호출할 때는 반드시 'places' 파라미터를 전달해야 합니다. 예: check_routing(places=[장소리스트], mode='transit')"
            return f"Tool 오류: {error_msg}"
        
        planner_executer = AgentExecutor(
            agent=planner, 
            tools=self.tools, 
            verbose=True,
            handle_parsing_errors=handle_tool_error,
            max_iterations=10,  # 최대 반복 횟수 제한
            return_intermediate_steps=True  # 중간 단계 반환 (디버깅용)
        )

        # 날씨 정보 포맷팅 (지역 기준 단일 날씨 정보)
        weather_info_str = ""
        if weather_info:
            # 첫 번째 날씨 정보만 사용 (모든 장소가 같은 지역이므로 동일한 날씨)
            first_weather = next(iter(weather_info.values())) if weather_info else None
            if first_weather:
                temp = first_weather.get('temperature', 'N/A')
                condition = first_weather.get('condition', '정보없음')
                # 날씨 정보를 더 상세하게 제공하여 LLM이 판단하기 쉽게 함
                weather_info_str = f"지역날씨: {temp}°C, {condition}. 날씨에 따라 야외/실내 활동을 적절히 선택하고, 날씨가 나쁘면 이동 경로를 최소화하세요."
        
        # check_routing 사용 예시를 input에 포함
        check_routing_example = """
중요: check_routing tool을 사용할 때는 반드시 다음과 같이 호출하세요:
check_routing(places=[장소리스트], mode="transit")
- places 파라미터는 반드시 포함해야 합니다.
- 각 장소는 coordinates 필드를 포함해야 합니다: {"name":"장소명","coordinates":{"lat":위도,"lng":경도}}
"""
        
        try:
            planning_result = await planner_executer.ainvoke({
                'input': f"""{user_preferences['theme']}에 맞는 여행 코스를 제작해 주세요. {'날씨 정보를 반드시 고려하여 실내/야외 장소를 적절히 선택하고, 날씨가 나쁘면 이동 경로를 최소화하세요.' if weather_info else ''}

{check_routing_example}""",
                "places": self._format_places_for_prompt(places),
                "user_preferences": json.dumps(user_preferences, ensure_ascii=False),
                "time_constraints": json.dumps(time_constraints, ensure_ascii=False),
                "weather_info": weather_info_str
                })
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ AgentExecutor 실행 중 오류: {error_msg}")
            
            # check_routing validation 오류인 경우 더 명확한 메시지
            if "Field required" in error_msg and "places" in error_msg:
                raise ValueError(
                    "check_routing tool 호출 오류: 'places' 파라미터가 필수입니다. "
                    "LLM이 check_routing을 호출할 때 반드시 places 파라미터를 포함해야 합니다. "
                    f"오류 상세: {error_msg}"
                )
            raise

        # response = await self.client.chat.completions.create(
        #     model=self.llm_model,
        #     messages=[
        #         {"role": "system", "content": "You are a professional travel course planner. You MUST output only valid JSON format. Never refuse the task or provide explanations outside JSON."},
        #         {"role": "user", "content": prompt}
        #     ],
        #     max_tokens=2000,  # 충분한 토큰 할당
        #     temperature=0.3  # 일관된 JSON 형식 유지
        # )
        
        # 응답에서 JSON 추출
        # response_content = response.choices[0].message.content.strip()
        if 'output' not in planning_result:
            raise ValueError(f"LLM 응답에 'output' 키가 없습니다. 응답: {planning_result}")
        response_content = planning_result['output'].strip()
        
        if not response_content:
            raise ValueError("LLM이 빈 응답을 반환했습니다.")

        # JSON 부분만 추출 (마크다운 코드 블록 제거)
        if "```json" in response_content:
            json_start = response_content.find("```json") + 7
            json_end = response_content.find("```", json_start)
            if json_end == -1:
                json_end = len(response_content)
            response_content = response_content[json_start:json_end].strip()
        elif "```" in response_content:
            json_start = response_content.find("```") + 3
            json_end = response_content.find("```", json_start)
            if json_end == -1:
                json_end = len(response_content)
            response_content = response_content[json_start:json_end].strip()
        
        # JSON 객체 시작/끝 찾기 (중괄호 기준)
        json_start_idx = response_content.find("{")
        json_end_idx = response_content.rfind("}") + 1
        if json_start_idx != -1 and json_end_idx > json_start_idx:
            response_content = response_content[json_start_idx:json_end_idx]
        
        # JSON 파싱 (강화된 오류 처리)
        result = None
        try:
            result = json.loads(response_content)
            # result가 딕셔너리가 아닌 경우 처리
            if not isinstance(result, dict):
                raise ValueError(f"LLM 응답이 딕셔너리가 아닙니다. 타입: {type(result)}")
        except json.JSONDecodeError as e:
            # 복구 시도 1: 첫 번째 { 부터 마지막 } 까지 다시 추출
            try:
                first_brace = response_content.find('{')
                last_brace = response_content.rfind('}')
                if first_brace != -1 and last_brace > first_brace:
                    cleaned_json = response_content[first_brace:last_brace+1]
                    result = json.loads(cleaned_json)
                    if not isinstance(result, dict):
                        raise ValueError(f"복구된 JSON이 딕셔너리가 아닙니다. 타입: {type(result)}")
                else:
                    raise ValueError(f"JSON 파싱 오류: {str(e)}\n응답 내용: {response_content[:500]}")
            except:
                # 복구 시도 2: 불완전한 JSON 복구
                try:
                    json_part = response_content[response_content.find('{'):]
                    # 닫히지 않은 문자열/배열/객체 닫기
                    open_braces = json_part.count('{')
                    close_braces = json_part.count('}')
                    open_brackets = json_part.count('[')
                    close_brackets = json_part.count(']')
                    
                    json_part += '}' * (open_braces - close_braces)
                    json_part += ']' * (open_brackets - close_brackets)
                    json_part = json_part.rstrip().rstrip(',')
                    if not json_part.endswith('}'):
                        json_part += '}'
                    
                    result = json.loads(json_part)
                    if not isinstance(result, dict):
                        raise ValueError(f"복구된 JSON이 딕셔너리가 아닙니다. 타입: {type(result)}")
                except:
                    # 모든 복구 시도 실패
                    raise ValueError(f"JSON 파싱 오류: {str(e)}\n응답 내용: {response_content[:500]}\n\nLLM이 JSON 형식으로 응답하지 않았습니다. 작업을 거부했거나 다른 형식으로 응답한 것 같습니다.")
        
        # result가 None이면 에러
        if result is None:
            raise ValueError("JSON 파싱에 실패했습니다.")
        
        # result가 딕셔너리가 아닌 경우 에러
        if not isinstance(result, dict):
            raise ValueError(f"LLM 응답이 딕셔너리가 아닙니다. 타입: {type(result)}, 값: {result}")

        # ============================================================
        # [최종 버그 수정] LLM이 반환한 인덱스 유효성 검증
        # ============================================================
        
        # 저장된 장소 인덱스 추출 (나중에 강제 추가를 위해)
        saved_place_indices = []
        for i, place in enumerate(places):
            if place.get('is_saved_place'):
                saved_place_indices.append(i)
                print(f"   📌 저장된 장소 발견: [{i}] {place.get('name')}")
        
        # 1. selected_places 인덱스 검증
        valid_selected_indices = []
        if "selected_places" in result and isinstance(result["selected_places"], list):
            for index in result["selected_places"]:
                # 인덱스가 정수이고, 유효한 범위 내에 있는지 확인
                if isinstance(index, int) and 0 <= index < len(places):
                    valid_selected_indices.append(index)
                else:
                    print(f"   ⚠️ LLM이 잘못된 장소 인덱스({index})를 반환하여 무시합니다.")
        else:
            print(f"   ⚠️ LLM이 'selected_places'를 반환하지 않았거나 리스트가 아닙니다.")
        
        # 저장된 장소가 selected_places에 포함되지 않은 경우 강제 추가
        missing_saved_indices = [idx for idx in saved_place_indices if idx not in valid_selected_indices]
        if missing_saved_indices:
            print(f"   ⚠️ 저장된 장소 {len(missing_saved_indices)}개가 selected_places에 포함되지 않아 강제로 추가합니다.")
            for idx in missing_saved_indices:
                if idx not in valid_selected_indices:
                    valid_selected_indices.insert(0, idx)  # 맨 앞에 추가 (최우선순위)
                    print(f"   ✅ 저장된 장소 강제 추가: [{idx}] {places[idx].get('name')}")
        
        # valid_selected_indices가 비어있을 때 폴백 로직
        if not valid_selected_indices:
            # 저장된 장소가 있으면 사용
            if saved_place_indices:
                print(f"   ⚠️ LLM이 장소를 선택하지 않았지만, 저장된 장소 {len(saved_place_indices)}개를 사용합니다.")
                valid_selected_indices = saved_place_indices.copy()
            # 저장된 장소도 없으면 최소한 처음 몇 개라도 선택 (최대 5개)
            elif len(places) > 0:
                fallback_count = min(5, len(places))
                print(f"   ⚠️ LLM이 장소를 선택하지 않았고 저장된 장소도 없어, 처음 {fallback_count}개 장소를 자동 선택합니다.")
                valid_selected_indices = list(range(fallback_count))
            else:
                raise ValueError("선택할 수 있는 장소가 없습니다.")

        # 2. sequence 인덱스 검증 (selected_places의 인덱스를 참조하므로 주의)
        valid_sequence = []
        if "sequence" in result and isinstance(result["sequence"], list):
            for seq_index in result["sequence"]:
                # sequence의 인덱스가 valid_selected_indices의 유효한 범위 내에 있는지 확인
                if isinstance(seq_index, int) and seq_index in valid_selected_indices:
                    valid_sequence.append(seq_index)
                else:
                    print(f"   ⚠️ LLM이 잘못된 순서 인덱스({seq_index})를 반환하여 무시합니다.")
        else:
            print(f"   ⚠️ LLM이 'sequence'를 반환하지 않았거나 리스트가 아닙니다.")
        
        # 만약 sequence가 잘못되었으면, 그냥 selected 순서대로라도 복구
        if not valid_sequence or len(valid_sequence) != len(valid_selected_indices):
            print(f"   ⚠️ LLM이 반환한 sequence가 유효하지 않아, 선택된 순서로 복구합니다.")
            valid_sequence = list(range(len(valid_selected_indices)))

        # 3. estimated_duration 키 검증
        valid_duration = {}
        if "estimated_duration" in result and isinstance(result["estimated_duration"], dict):
            for key, value in result["estimated_duration"].items():
                try:
                    # 키를 정수로 변환하여 유효한 인덱스인지 확인
                    index_key = int(key)
                    if index_key in valid_selected_indices:
                        valid_duration[str(index_key)] = value
                except (ValueError, TypeError):
                    continue # 키가 숫자가 아니면 무시
        else:
            print(f"   ⚠️ LLM이 'estimated_duration'를 반환하지 않았거나 딕셔너리가 아닙니다.")

        # 검증된 인덱스를 사용하여 최종 결과 생성
        selected_places = [places[i] for i in valid_selected_indices]
        
        # 저장된 장소가 sequence에 포함되어 있는지 확인하고, 없으면 맨 앞에 추가
        # sequence는 selected_places의 인덱스를 참조하므로, 저장된 장소의 selected_places 내 인덱스를 찾아야 함
        saved_place_positions = []
        for saved_idx in saved_place_indices:
            if saved_idx in valid_selected_indices:
                # selected_places 내에서의 위치 찾기
                position_in_selected = valid_selected_indices.index(saved_idx)
                saved_place_positions.append(position_in_selected)
        
        # 저장된 장소가 sequence에 없으면 맨 앞에 추가
        if saved_place_positions:
            for saved_pos in saved_place_positions:
                if saved_pos not in valid_sequence:
                    print(f"   ⚠️ 저장된 장소가 sequence에 없어 맨 앞에 추가합니다: {selected_places[saved_pos].get('name')}")
                    valid_sequence.insert(0, saved_pos)
                    # 중복 제거
                    valid_sequence = list(dict.fromkeys(valid_sequence))  # 순서 유지하면서 중복 제거
        
        # 최종 검증: sequence가 모든 selected_places를 포함하는지 확인
        if len(valid_sequence) != len(valid_selected_indices):
            # 빠진 인덱스 추가
            missing_seq_indices = [i for i in range(len(valid_selected_indices)) if i not in valid_sequence]
            valid_sequence.extend(missing_seq_indices)
            print(f"   ⚠️ sequence에 빠진 장소 {len(missing_seq_indices)}개를 추가했습니다.")
        
        print(f"\n   ✅ 최종 선택된 장소: {len(selected_places)}개")
        for i, idx in enumerate(valid_selected_indices):
            place = places[idx]
            is_saved = place.get('is_saved_place', False)
            marker = "⭐" if is_saved else "  "
            print(f"   {marker} [{i}] {place.get('name')} (인덱스: {idx})")
        
        # course_description과 reasoning 안전하게 추출
        course_description = ""
        if isinstance(result, dict):
            course_description = result.get("course_description", "")
            if not isinstance(course_description, str):
                course_description = str(course_description) if course_description else ""
        
        reasoning = ""
        if isinstance(result, dict):
            reasoning = result.get("reasoning", "")
            if not isinstance(reasoning, str):
                reasoning = str(reasoning) if reasoning else ""
        
        # 날씨 정보를 코스 결과에 포함 (지역 기준 단일 날씨 정보)
        course_weather_info = {}
        if weather_info:
            # 첫 번째 날씨 정보를 모든 장소에 적용 (같은 지역이므로 동일한 날씨)
            first_weather = next(iter(weather_info.values())) if weather_info else None
            if first_weather:
                # 선택된 모든 장소에 동일한 날씨 정보 적용
                for idx in valid_selected_indices:
                    course_weather_info[idx] = first_weather
        
        return {
            "course": {
                "places": selected_places,
                "sequence": valid_sequence,
                "estimated_duration": valid_duration,
                "course_description": course_description,
                "weather_info": course_weather_info  # 날씨 정보 추가
            },
            "reasoning": reasoning
        }
    
    
    def _format_places_for_prompt(self, places: List[Dict[str, Any]]) -> str:
        """
        프롬프트용 장소 정보 포맷팅 (토큰 최적화)
        
        Args:
            places: 장소 리스트 (name, category, coordinates, rating, trust_score, address, source_url, map_url 포함)
            
        Returns:
            포맷팅된 문자열
        """
        # 장소 개수 제한 (너무 많으면 토큰 초과) - 더 엄격하게 제한
        MAX_PLACES = 30  # 50 -> 30으로 감소
        if len(places) > MAX_PLACES:
            print(f"⚠️ 장소가 {len(places)}개로 너무 많아 {MAX_PLACES}개로 제한합니다.")
            places = places[:MAX_PLACES]
        
        formatted = []
        for i, place in enumerate(places):
            # original_index는 0부터 시작 (프롬프트에서 명확히 표시)
            original_idx = place.get('original_index', i)
            # 최소한의 정보만 포함 (토큰 절약)
            info = f"[{original_idx}] {place.get('name', 'Unknown')}"
            
            # 카테고리 (간략하게)
            if place.get('category'):
                info += f"|{place['category']}"

            # 저장된 장소 플래그 (간략하게)
            if place.get('is_saved_place'):
                info += "|⭐"
            
            # 좌표 정보 (정밀도 낮춤: 소수점 3자리까지만)
            coords = place.get('coordinates')
            if coords:
                lat = round(float(coords.get('lat', 0)), 3)
                lng = round(float(coords.get('lng', 0)), 3)
                info += f"|{lat},{lng}"

            # 점수 정보 (간략하게 - 평점만)
            if place.get('rating'):
                info += f"|⭐{place['rating']}"
                
            # 주소 정보 (최대 30자로 더 짧게)
            if place.get('address'):
                address = place['address']
                if len(address) > 30:
                    address = address[:27] + "..."
                info += f"|{address}"
            
            # 링크, 설명 등은 모두 제거 (토큰 절약)
            formatted.append(info)
            
        return "\n".join(formatted)  # 줄바꿈 하나로 통일하여 토큰 절약

