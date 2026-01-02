"""
Tavily 검색 Tool
실시간 웹 검색을 통해 추천 장소 후보군을 확보합니다.
"""

from typing import Any, Dict, List, Optional
import os
from .base_tool import BaseTool


class TavilySearchTool(BaseTool):
    """Tavily API를 사용한 실시간 검색 Tool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Tool 설정 (api_key, max_results 등)
        """
        super().__init__(
            name="tavily_search",
            description="테마 기반 장소 검색을 수행하여 추천 장소 후보군을 확보합니다.",
            config=config or {}
        )
        self.api_key = self.config.get("api_key") or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY가 설정되지 않았습니다.")
        
        # Tavily 클라이언트 초기화 (실제 구현 시 사용)
        # self.client = TavilyClient(api_key=self.api_key)
        self.max_results = self.config.get("max_results", 20)
        self.min_rating = self.config.get("min_rating", 4.0)
    
    async def execute(
        self,
        query: str,
        location: Optional[str] = None,
        max_results: Optional[int] = None,
        min_rating: Optional[float] = None,
        filter_by_date: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Tavily 검색 실행
        
        Args:
            query: 검색 쿼리 (예: "비 오는 날 서울 실내 데이트")
            location: 검색 지역 (예: "서울")
            max_results: 최대 결과 개수
            min_rating: 최소 평점 (필터링용)
            filter_by_date: 최신성 필터링 여부
            
        Returns:
            {
                "success": bool,
                "places": List[Dict],  # 장소 정보 리스트
                "total_count": int,
                "error": Optional[str]
            }
        """
        try:
            if not self.validate_params(query=query):
                return {
                    "success": False,
                    "places": [],
                    "total_count": 0,
                    "error": "필수 파라미터가 누락되었습니다."
                }
            
            max_results = max_results or self.max_results
            min_rating = min_rating or self.min_rating
            
            # TODO: 실제 Tavily API 호출 구현
            # 예시 구조:
            # search_results = await self.client.search(
            #     query=f"{query} {location}" if location else query,
            #     max_results=max_results,
            #     search_depth="advanced"
            # )
            
            # 검색 결과를 장소 정보로 변환 및 필터링
            # places = self._parse_search_results(search_results)
            # filtered_places = self._filter_places(places, min_rating, filter_by_date)
            
            # 임시 반환 구조 (실제 구현 시 교체)
            return {
                "success": True,
                "places": [],  # 실제 검색 결과로 교체
                "total_count": 0,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "places": [],
                "total_count": 0,
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
                "query": {
                    "type": "string",
                    "description": "검색 쿼리 (예: '비 오는 날 서울 실내 데이트')"
                },
                "location": {
                    "type": "string",
                    "description": "검색 지역 (선택사항)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "최대 결과 개수",
                    "default": 20
                },
                "min_rating": {
                    "type": "number",
                    "description": "최소 평점",
                    "default": 4.0
                },
                "filter_by_date": {
                    "type": "boolean",
                    "description": "최신성 필터링 여부",
                    "default": True
                }
            },
            "required": ["query"]
        }
    
    def _parse_search_results(self, search_results: Any) -> List[Dict[str, Any]]:
        """
        Tavily 검색 결과를 장소 정보 딕셔너리 리스트로 변환
        
        Args:
            search_results: Tavily API 응답
            
        Returns:
            장소 정보 리스트
        """
        # TODO: 실제 파싱 로직 구현
        # 각 결과에서 장소명, 주소, 평점, 설명 등을 추출
        places = []
        # 예시 구조:
        # for result in search_results.results:
        #     place = {
        #         "name": result.get("title"),
        #         "description": result.get("content"),
        #         "address": result.get("address"),
        #         "rating": result.get("rating"),
        #         "source_url": result.get("url"),
        #         "category": result.get("category"),
        #         "tags": result.get("tags", [])
        #     }
        #     places.append(place)
        return places
    
    def _filter_places(
        self,
        places: List[Dict[str, Any]],
        min_rating: float,
        filter_by_date: bool
    ) -> List[Dict[str, Any]]:
        """
        장소 리스트를 평점 및 최신성 기준으로 필터링
        
        Args:
            places: 장소 정보 리스트
            min_rating: 최소 평점
            filter_by_date: 최신성 필터링 여부
            
        Returns:
            필터링된 장소 리스트
        """
        filtered = []
        for place in places:
            rating = place.get("rating", 0)
            if rating >= min_rating:
                # 최신성 필터링 로직 추가 가능
                filtered.append(place)
        
        # 평점 기준으로 정렬
        filtered.sort(key=lambda x: x.get("rating", 0), reverse=True)
        return filtered

