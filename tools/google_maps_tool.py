"""
Google Maps 경로 최적화 Tool
선택된 장소들의 동선을 최적화하고 경로를 계산합니다.
"""

from typing import Any, Dict, List, Optional, Tuple
import os
from .base_tool import BaseTool


class GoogleMapsTool(BaseTool):
    """Google Maps API를 사용한 경로 최적화 Tool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Tool 설정 (api_key 등)
        """
        super().__init__(
            name="google_maps_routing",
            description="장소들 간의 최적 경로를 계산하고 동선을 최적화합니다.",
            config=config or {}
        )
        self.api_key = self.config.get("api_key") or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY가 설정되지 않았습니다.")
        
        # Google Maps 클라이언트 초기화 (실제 구현 시 사용)
        # self.client = googlemaps.Client(key=self.api_key)
    
    async def execute(
        self,
        places: List[Dict[str, Any]],
        origin: Optional[Dict[str, Any]] = None,
        destination: Optional[Dict[str, Any]] = None,
        mode: str = "transit",  # 'driving', 'walking', 'transit', 'bicycling'
        optimize_waypoints: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        경로 최적화 실행
        
        Args:
            places: 장소 정보 리스트 (각 장소는 name, address, coordinates 등을 포함)
            origin: 출발지 (선택사항, 없으면 places의 첫 번째 항목)
            destination: 도착지 (선택사항, 없으면 places의 마지막 항목)
            mode: 이동 수단 ('driving', 'walking', 'transit', 'bicycling')
            optimize_waypoints: 경유지 순서 최적화 여부
            
        Returns:
            {
                "success": bool,
                "optimized_route": List[Dict],  # 최적화된 경로
                "total_duration": int,  # 총 소요 시간 (초)
                "total_distance": int,  # 총 거리 (미터)
                "directions": List[Dict],  # 각 구간별 경로 정보
                "error": Optional[str]
            }
        """
        try:
            if not self.validate_params(places=places):
                return {
                    "success": False,
                    "optimized_route": [],
                    "total_duration": 0,
                    "total_distance": 0,
                    "directions": [],
                    "error": "필수 파라미터가 누락되었습니다."
                }
            
            if not places:
                return {
                    "success": False,
                    "optimized_route": [],
                    "total_duration": 0,
                    "total_distance": 0,
                    "directions": [],
                    "error": "장소 리스트가 비어있습니다."
                }
            
            # 좌표 추출
            coordinates = self._extract_coordinates(places)
            
            if optimize_waypoints and len(coordinates) > 2:
                # 경유지 최적화 (TSP 알고리즘 또는 Google Directions API 사용)
                optimized_order = await self._optimize_waypoint_order(
                    coordinates, origin, destination, mode
                )
            else:
                optimized_order = list(range(len(places)))
            
            # 최적화된 순서로 장소 재배열
            optimized_places = [places[i] for i in optimized_order]
            
            # 각 구간별 경로 계산
            directions = await self._calculate_directions(
                optimized_places, origin, destination, mode
            )
            
            # 총 소요 시간 및 거리 계산
            total_duration = sum(d.get("duration", 0) for d in directions)
            total_distance = sum(d.get("distance", 0) for d in directions)
            
            return {
                "success": True,
                "optimized_route": optimized_places,
                "total_duration": total_duration,
                "total_distance": total_distance,
                "directions": directions,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "optimized_route": [],
                "total_duration": 0,
                "total_distance": 0,
                "directions": [],
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
                    "description": "장소 정보 리스트 (각 장소는 name, address, coordinates 포함)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"},
                            "coordinates": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number"},
                                    "lng": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "origin": {
                    "type": "object",
                    "description": "출발지 (선택사항)"
                },
                "destination": {
                    "type": "object",
                    "description": "도착지 (선택사항)"
                },
                "mode": {
                    "type": "string",
                    "enum": ["driving", "walking", "transit", "bicycling"],
                    "description": "이동 수단",
                    "default": "transit"
                },
                "optimize_waypoints": {
                    "type": "boolean",
                    "description": "경유지 순서 최적화 여부",
                    "default": True
                }
            },
            "required": ["places"]
        }
    
    def _extract_coordinates(self, places: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """
        장소 리스트에서 좌표 추출
        
        Args:
            places: 장소 정보 리스트
            
        Returns:
            (lat, lng) 튜플 리스트
        """
        coordinates = []
        for place in places:
            coords = place.get("coordinates")
            if coords:
                coordinates.append((coords.get("lat"), coords.get("lng")))
            else:
                # 주소를 좌표로 변환 (Geocoding API 사용)
                # TODO: 실제 구현 필요
                coordinates.append((0.0, 0.0))
        return coordinates
    
    async def _optimize_waypoint_order(
        self,
        coordinates: List[Tuple[float, float]],
        origin: Optional[Dict[str, Any]],
        destination: Optional[Dict[str, Any]],
        mode: str
    ) -> List[int]:
        """
        경유지 순서 최적화 (TSP 문제 해결)
        
        Args:
            coordinates: 좌표 리스트
            origin: 출발지
            destination: 도착지
            mode: 이동 수단
            
        Returns:
            최적화된 순서의 인덱스 리스트
        """
        # TODO: 실제 최적화 알고리즘 구현
        # 방법 1: Google Directions API의 optimize_waypoints 옵션 사용
        # 방법 2: 자체 TSP 알고리즘 구현 (Nearest Neighbor, 2-opt 등)
        
        # 임시로 원본 순서 반환
        return list(range(len(coordinates)))
    
    async def _calculate_directions(
        self,
        places: List[Dict[str, Any]],
        origin: Optional[Dict[str, Any]],
        destination: Optional[Dict[str, Any]],
        mode: str
    ) -> List[Dict[str, Any]]:
        """
        각 구간별 경로 정보 계산
        
        Args:
            places: 장소 리스트
            origin: 출발지
            destination: 도착지
            mode: 이동 수단
            
        Returns:
            구간별 경로 정보 리스트
        """
        directions = []
        
        # TODO: Google Directions API 호출 구현
        # for i in range(len(places) - 1):
        #     from_place = places[i]
        #     to_place = places[i + 1]
        #     
        #     result = await self.client.directions(
        #         origin=from_place["address"],
        #         destination=to_place["address"],
        #         mode=mode
        #     )
        #     
        #     leg = result[0]["legs"][0]
        #     directions.append({
        #         "from": from_place["name"],
        #         "to": to_place["name"],
        #         "duration": leg["duration"]["value"],
        #         "distance": leg["distance"]["value"],
        #         "steps": leg["steps"],
        #         "mode": mode
        #     })
        
        return directions

