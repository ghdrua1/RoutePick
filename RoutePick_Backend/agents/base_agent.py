"""
Base Agent 클래스
모든 Agent의 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAgent(ABC):
    """모든 Agent의 기본 클래스"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            name: Agent 이름
            config: Agent 설정 딕셔너리
        """
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent의 주요 실행 메서드
        
        Args:
            input_data: Agent에 전달할 입력 데이터
            
        Returns:
            Agent 실행 결과 딕셔너리
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        입력 데이터 유효성 검증
        
        Args:
            input_data: 검증할 입력 데이터
            
        Returns:
            유효성 검증 결과
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Agent의 현재 상태를 반환
        
        Returns:
            Agent 상태 정보
        """
        return {
            "name": self.name,
            "status": "ready",
            "config": self.config
        }

