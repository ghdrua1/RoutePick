"""
Search Agent
Tavily 검색 Tool을 사용하여 테마 기반 장소 후보군을 확보합니다.
"""

from typing import Any, Dict, Optional
from .base_agent import BaseAgent
from tools.tavily_search_tool import TavilySearchTool


class SearchAgent(BaseAgent):
    """검색 Agent - Tavily Tool을 사용하여 장소 검색"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Agent 설정
        """
        super().__init__(name="SearchAgent", config=config)
        self.search_tool = TavilySearchTool(config=config)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        검색 실행
        
        Args:
            input_data: {
                "theme": str,  # 테마 (예: "비 오는 날 서울 실내 데이트")
                "location": Optional[str],  # 검색 지역
                "max_results": Optional[int],  # 최대 결과 개수
                "min_rating": Optional[float]  # 최소 평점
            }
            
        Returns:
            {
                "success": bool,
                "places": List[Dict],  # 검색된 장소 리스트
                "total_count": int,
                "agent_name": str,
                "error": Optional[str]
            }
        """
        if not self.validate_input(input_data):
            return {
                "success": False,
                "places": [],
                "total_count": 0,
                "agent_name": self.name,
                "error": "입력 데이터가 유효하지 않습니다."
            }
        
        theme = input_data.get("theme", "")
        location = input_data.get("location")
        max_results = input_data.get("max_results")
        min_rating = input_data.get("min_rating")
        
        # 검색 쿼리 구성
        query = f"{theme}"
        if location:
            query = f"{theme} {location}"
        
        # Tavily 검색 실행
        result = await self.search_tool.execute(
            query=query,
            location=location,
            max_results=max_results,
            min_rating=min_rating
        )
        
        return {
            "success": result.get("success", False),
            "places": result.get("places", []),
            "total_count": result.get("total_count", 0),
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
        
        theme = input_data.get("theme")
        if not theme or not isinstance(theme, str):
            return False
        
        return True

