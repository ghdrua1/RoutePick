"""
코스 제작 Tool
검색된 장소들을 바탕으로 최적의 코스를 생성합니다.
"""

from typing import Any, Dict, List, Optional
from .base_tool import BaseTool


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
        self.llm_model = self.config.get("llm_model", "gpt-4")
        self.api_key = self.config.get("api_key") or self.config.get("openai_api_key")
        
        # LLM 클라이언트 초기화 (실제 구현 시 사용)
        # 예: OpenAI, Anthropic, 등
        # self.client = OpenAI(api_key=self.api_key)
    
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
                    "sequence": List[int],  # 방문 순서
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
            
            # LLM을 사용하여 코스 생성
            course_result = await self._generate_course_with_llm(
                places, user_preferences, time_constraints
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
                        "transportation": {"type": "string"}
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
        time_constraints: Optional[Dict[str, Any]]
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
        # TODO: LLM 프롬프트 구성 및 호출 구현
        # 
        # 프롬프트 예시:
        # prompt = f"""
        # 다음 장소들 중에서 사용자의 선호도에 맞는 최적의 코스를 제안해주세요.
        # 
        # 사용자 선호도:
        # - 테마: {user_preferences['theme']}
        # - 인원: {user_preferences['group_size']}명
        # - 방문 일자: {user_preferences['visit_date']}
        # - 이동 수단: {user_preferences['transportation']}
        # 
        # 장소 리스트:
        # {self._format_places_for_prompt(places)}
        # 
        # 다음을 고려하여 코스를 생성해주세요:
        # 1. 테마에 맞는 장소 선택
        # 2. 식사-활동-카페 등의 자연스러운 순서
        # 3. 시간대 고려 (점심, 저녁 등)
        # 4. 인원수에 적합한 장소
        # 
        # JSON 형식으로 응답해주세요:
        # {{
        #   "selected_places": [장소 인덱스 리스트],
        #   "sequence": [방문 순서],
        #   "estimated_duration": {{장소별 체류 시간 (분)}},
        #   "course_description": "코스 설명",
        #   "reasoning": "선정 이유"
        # }}
        # """
        # 
        # response = await self.client.chat.completions.create(
        #     model=self.llm_model,
        #     messages=[{"role": "user", "content": prompt}],
        #     response_format={"type": "json_object"}
        # )
        # 
        # result = json.loads(response.choices[0].message.content)
        # 
        # # 선택된 장소만 필터링
        # selected_places = [places[i] for i in result["selected_places"]]
        # 
        # return {
        #     "course": {
        #         "places": selected_places,
        #         "sequence": result["sequence"],
        #         "estimated_duration": result["estimated_duration"],
        #         "course_description": result["course_description"]
        #     },
        #     "reasoning": result["reasoning"]
        # }
        
        # 임시 반환 구조
        return {
            "course": {
                "places": places[:3],  # 임시로 처음 3개 선택
                "sequence": [0, 1, 2],
                "estimated_duration": {0: 120, 1: 60, 2: 90},
                "course_description": "임시 코스 설명"
            },
            "reasoning": "임시 선정 이유"
        }
    
    def _format_places_for_prompt(self, places: List[Dict[str, Any]]) -> str:
        """
        프롬프트용 장소 정보 포맷팅
        
        Args:
            places: 장소 리스트
            
        Returns:
            포맷팅된 문자열
        """
        formatted = []
        for i, place in enumerate(places):
            info = f"[{i}] {place.get('name', 'Unknown')}"
            if place.get('category'):
                info += f" ({place['category']})"
            if place.get('rating'):
                info += f" - 평점: {place['rating']}"
            if place.get('description'):
                info += f"\n  설명: {place['description']}"
            formatted.append(info)
        return "\n".join(formatted)

