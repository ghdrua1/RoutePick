"""
Routing Agent
Google Maps Tool을 사용하여 경로를 최적화합니다.
"""

from typing import Any, Dict, Optional
from .base_agent import BaseAgent
from tools.google_maps_tool import GoogleMapsTool


class RoutingAgent(BaseAgent):
    """경로 최적화 Agent - Google Maps Tool을 사용하여 동선 최적화"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Agent 설정
        """
        super().__init__(name="RoutingAgent", config=config)
        self.maps_tool = GoogleMapsTool(config=config)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        경로 최적화 실행
        
        Args:
            input_data: {
                "places": List[Dict],  # 코스에 포함된 장소 리스트
                "origin": Optional[Dict],  # 출발지
                "destination": Optional[Dict],  # 도착지
                "mode": str,  # 이동 수단
                "optimize_waypoints": bool  # 경유지 최적화 여부
            }
            
        Returns:
            {
                "success": bool,
                "optimized_route": List[Dict],  # 최적화된 경로
                "total_duration": int,  # 총 소요 시간 (초)
                "total_distance": int,  # 총 거리 (미터)
                "directions": List[Dict],  # 각 구간별 경로 정보
                "agent_name": str,
                "error": Optional[str]
            }
        """
        if not self.validate_input(input_data):
            return {
                "success": False,
                "optimized_route": [],
                "total_duration": 0,
                "total_distance": 0,
                "directions": [],
                "agent_name": self.name,
                "error": "입력 데이터가 유효하지 않습니다."
            }
        
        places = input_data.get("places", [])
        origin = input_data.get("origin")
        destination = input_data.get("destination")
        mode = input_data.get("mode", "transit")
        optimize_waypoints = input_data.get("optimize_waypoints", True)
        
        # 경로 최적화 실행
        result = await self.maps_tool.execute(
            places=places,
            origin=origin,
            destination=destination,
            mode=mode,
            optimize_waypoints=optimize_waypoints
        )
        
        return {
            "success": result.get("success", False),
            "optimized_route": result.get("optimized_route", []),
            "total_duration": result.get("total_duration", 0),
            "total_distance": result.get("total_distance", 0),
            "directions": result.get("directions", []),
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
        
        mode = input_data.get("mode", "transit")
        valid_modes = ["driving", "walking", "transit", "bicycling"]
        if mode not in valid_modes:
            return False
        
        return True

