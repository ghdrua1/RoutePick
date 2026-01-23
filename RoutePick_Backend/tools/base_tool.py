"""
Base Tool 클래스
모든 Tool의 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTool(ABC):
    """모든 Tool의 기본 클래스"""
    
    def __init__(self, name: str, description: str, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            name: Tool 이름
            description: Tool 설명
            config: Tool 설정 딕셔너리
        """
        self.name = name
        self.description = description
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Tool 실행 메서드
        
        Args:
            **kwargs: Tool에 전달할 파라미터들
            
        Returns:
            Tool 실행 결과 딕셔너리
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Tool의 입력 스키마를 반환 (파라미터 정의)
        
        Returns:
            Tool 스키마 딕셔너리
        """
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """
        파라미터 유효성 검증
        
        Args:
            **kwargs: 검증할 파라미터들
            
        Returns:
            유효성 검증 결과
        """
        schema = self.get_schema()
        required_params = schema.get("required", [])
        
        for param in required_params:
            if param not in kwargs:
                return False
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        Tool 정보 반환
        
        Returns:
            Tool 정보 딕셔너리
        """
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.get_schema()
        }

