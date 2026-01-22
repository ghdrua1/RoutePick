"""
Planning Agent
코스 제작 Tool을 사용하여 최적의 코스를 생성합니다.
"""

from typing import Any, Dict, Optional
from .base_agent import BaseAgent
from tools.course_creation_tool import CourseCreationTool


class PlanningAgent(BaseAgent):
    """계획 Agent - 코스 제작 Tool을 사용하여 최적 코스 생성"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Agent 설정
        """
        super().__init__(name="PlanningAgent", config=config)
        self.course_tool = CourseCreationTool(config=config)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        코스 계획 실행
        
        Args:
            input_data: {
                "places": List[Dict],  # 검색된 장소 리스트
                "user_preferences": Dict,  # 사용자 선호도
                "time_constraints": Optional[Dict]  # 시간 제약
            }
            
        Returns:
            {
                "success": bool,
                "course": Dict,  # 생성된 코스
                "reasoning": str,  # 코스 선정 이유
                "agent_name": str,
                "error": Optional[str]
            }
        """
        if not self.validate_input(input_data):
            return {
                "success": False,
                "course": None,
                "reasoning": "",
                "agent_name": self.name,
                "error": "입력 데이터가 유효하지 않습니다."
            }
        
        places = input_data.get("places", [])
        user_preferences = input_data.get("user_preferences", {})
        time_constraints = input_data.get("time_constraints")
        
        # 코스 제작 실행
        result = await self.course_tool.execute(
            places=places,
            user_preferences=user_preferences,
            time_constraints=time_constraints
        )
        
        return {
            "success": result.get("success", False),
            "course": result.get("course"),
            "reasoning": result.get("reasoning", ""),
            "agent_name": self.name,
            "error": result.get("error")
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        입력 데이터 유효성 검증
        
        Args:
            input_data: 검증할 입력 데이터
            
        Returns:
            유효성 검증 결과
        """
        if not isinstance(input_data, dict):
            return False
        
        places = input_data.get("places")
        if not places or not isinstance(places, list):
            return False
        
        user_preferences = input_data.get("user_preferences")
        if not user_preferences or not isinstance(user_preferences, dict):
            return False
        
        if not user_preferences.get("theme"):
            return False
        
        return True

