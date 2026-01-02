# RoutePick

실시간 웹 검색과 Google Maps API의 경로 최적화 로직을 결합하여, 사용자의 니즈에 최적화된 여행/데이트 코스를 설계하는 멀티 에이전트 시스템.

## 프로젝트 구조

```
RoutePick/
├── agents/                 # Agent 클래스들
│   ├── __init__.py
│   ├── base_agent.py      # Base Agent 인터페이스
│   ├── search_agent.py    # Search Agent (Tavily 검색)
│   ├── planning_agent.py  # Planning Agent (코스 제작)
│   └── routing_agent.py   # Routing Agent (경로 최적화)
│
├── tools/                  # Tool 클래스들
│   ├── __init__.py
│   ├── base_tool.py            # Base Tool 인터페이스
│   ├── tavily_search_tool.py   # Tavily 검색 Tool
│   ├── google_maps_tool.py     # Google Maps 경로 최적화 Tool
│   └── course_creation_tool.py # 코스 제작 Tool
│
├── config/                 # 설정 파일
│   └── config.py          # 전역 설정
│
├── utils/                  # 유틸리티 함수
│   └── __init__.py
│
├── requirements.txt        # Python 패키지 의존성
└── README.md              # 프로젝트 문서
```

## 시스템 아키텍처

### Agent 구성

1. **Search Agent** (`agents/search_agent.py`)
   - Tavily 검색 Tool을 사용하여 테마 기반 장소 후보군 확보
   - 최신성 및 평점 필터링

2. **Planning Agent** (`agents/planning_agent.py`)
   - 코스 제작 Tool을 사용하여 최적의 코스 생성
   - 사용자 선호도 및 시간대 고려

3. **Routing Agent** (`agents/routing_agent.py`)
   - Google Maps Tool을 사용하여 경로 최적화
   - 이동 효율성 극대화

### Tool 구성

1. **TavilySearchTool** (`tools/tavily_search_tool.py`)
   - 실시간 웹 검색을 통한 장소 검색
   - 평점 및 최신성 필터링

2. **GoogleMapsTool** (`tools/google_maps_tool.py`)
   - 장소들 간의 최적 경로 계산
   - 경유지 순서 최적화

3. **CourseCreationTool** (`tools/course_creation_tool.py`)
   - LLM을 사용한 맞춤형 코스 제작
   - 장소 조합 및 순서 최적화

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 API 키들을 설정하세요:

```env
TAVILY_API_KEY=your_tavily_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4
```

또는 환경 변수로 직접 설정:

```bash
export TAVILY_API_KEY=your_tavily_api_key
export GOOGLE_MAPS_API_KEY=your_google_maps_api_key
export OPENAI_API_KEY=your_openai_api_key
```

## 사용 예시

### Agent 사용 예시

```python
from agents import SearchAgent, PlanningAgent, RoutingAgent
from config.config import Config

# 설정 로드
config = Config.get_agent_config()

# Search Agent 실행
search_agent = SearchAgent(config=config)
search_result = await search_agent.execute({
    "theme": "비 오는 날 서울 실내 데이트",
    "location": "서울",
    "max_results": 20,
    "min_rating": 4.0
})

# Planning Agent 실행
planning_agent = PlanningAgent(config=config)
course_result = await planning_agent.execute({
    "places": search_result["places"],
    "user_preferences": {
        "theme": "비 오는 날 서울 실내 데이트",
        "group_size": 2,
        "visit_date": "2024-01-20",
        "visit_time": "오후",
        "transportation": "지하철"
    }
})

# Routing Agent 실행
routing_agent = RoutingAgent(config=config)
route_result = await routing_agent.execute({
    "places": course_result["course"]["places"],
    "mode": "transit",
    "optimize_waypoints": True
})
```

### Tool 직접 사용 예시

```python
from tools import TavilySearchTool, GoogleMapsTool, CourseCreationTool

# Tavily 검색 Tool
search_tool = TavilySearchTool(config={"api_key": "your_key"})
result = await search_tool.execute(
    query="비 오는 날 서울 실내 데이트",
    location="서울",
    max_results=20
)

# Google Maps Tool
maps_tool = GoogleMapsTool(config={"api_key": "your_key"})
route = await maps_tool.execute(
    places=places_list,
    mode="transit",
    optimize_waypoints=True
)

# 코스 제작 Tool
course_tool = CourseCreationTool(config={"api_key": "your_key"})
course = await course_tool.execute(
    places=places_list,
    user_preferences=preferences
)
```

## 협업 가이드

### 개발 규칙

1. **Agent 개발**
   - 모든 Agent는 `BaseAgent`를 상속받아야 합니다
   - `execute()` 메서드를 구현하여 주요 로직을 처리합니다
   - `validate_input()` 메서드를 구현하여 입력 검증을 수행합니다

2. **Tool 개발**
   - 모든 Tool은 `BaseTool`를 상속받아야 합니다
   - `execute()` 메서드를 구현하여 Tool의 기능을 수행합니다
   - `get_schema()` 메서드를 구현하여 입력 파라미터를 정의합니다

3. **에러 처리**
   - 모든 Agent와 Tool은 에러 발생 시 `success: False`와 `error` 메시지를 반환해야 합니다
   - 예외는 내부에서 처리하고, 사용자에게는 에러 메시지만 반환합니다

4. **비동기 처리**
   - 모든 Agent와 Tool의 `execute()` 메서드는 `async`로 정의되어 있습니다
   - API 호출 시 비동기 처리를 사용합니다

### TODO 항목

각 Tool 파일에는 실제 구현이 필요한 부분에 `TODO` 주석이 표시되어 있습니다:

- **TavilySearchTool**: Tavily API 클라이언트 초기화 및 호출, 검색 결과 파싱
- **GoogleMapsTool**: Google Maps API 클라이언트 초기화, 경로 계산, 경유지 최적화 알고리즘
- **CourseCreationTool**: LLM 프롬프트 구성 및 호출, 결과 파싱

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

