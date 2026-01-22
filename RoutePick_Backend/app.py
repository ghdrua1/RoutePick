import asyncio
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from chatbot import get_chatbot_response  # chatbot.py가 course 객체를 인자로 받도록 수정 필요
from agents import SearchAgent, PlanningAgent
from config.config import Config
import uuid

app = Flask(__name__)
app.secret_key = 'string_secret_key'
CORS(app)

# 여러 사용자의 작업 상태와 결과를 저장하는 '개인 사물함'
agent_tasks = {}

async def execute_Agents(task_id, input_data):
    global agent_tasks
    config = Config.get_agent_config()

    try:
        search_agent = SearchAgent(config=config)
        search_input = {
            "theme": input_data["theme"],
            "location": input_data["location"]
        }
        # if not search_agent.validate_input(search_input):
        #     print("❌ 필수 정보가 누락되었습니다.")
        #     missing_info = []
            
        #     if not search_input.get("theme"):
        #         missing_info.append("테마")
        #     if not search_input.get("location"):
        #         missing_info.append("지역")
            
        #     if missing_info:
        #         print(f"⚠️  다음 정보를 입력해주세요: {', '.join(missing_info)}")
        #         print()
                
        #         # 누락된 정보 재입력 받기
        #         if not search_input.get("theme"):
        #             search_input["theme"] = get_user_input("📌 여행 테마", required=True)
        #         if not search_input.get("location"):
        #             search_input["location"] = get_user_input("📍 지역", required=True)
                
        #         # 재검증
        #         if not search_agent.validate_input(search_input):
        #             print("❌ 검증 실패: 필수 정보가 여전히 누락되었습니다.")
        #             return
        
        search_result = await search_agent.execute(search_input)
        
        if not search_result.get("success"):
            raise Exception(f"장소 검색 실패: {search_result.get('error', '알 수 없는 오류')}")

        places = search_result.get("candidate_pool", [])
        if not places:
            raise Exception("검색된 장소가 없습니다. 다른 테마나 지역으로 시도해주세요.")
        
        print(f"\n✅ 검색 완료: {len(places)}개의 장소를 찾았습니다.\n")
        # yield f"\n✅ 검색 완료: {len(places)}개의 장소를 찾았습니다."
        """
        TODO
        html page에 동적으로 중간 과정 메세지 출력.
        queue, yield 사용.
        """

        # 검색된 장소 미리보기
        print("📍 검색된 장소 미리보기 (상위 5개):")
        for i, place in enumerate(places[:5], 1):
            print(f"  {i}. {place.get('name')} ({place.get('category')}) - 평점: {place.get('rating', 'N/A')}")
        print()
        
        # ============================================================
        # Step 2: PlanningAgent 실행 (코스 제작)
        # ============================================================
        print("🧠 [Step 2] PlanningAgent: 코스 제작 중...")
        print()
        
        planning_agent = PlanningAgent(config=config)
        
        # 사용자 선호도 구성
        user_preferences = {
            "theme": input_data["theme"],
            "group_size": input_data.get("group_size", "1명"),
            "visit_date": input_data.get("visit_date") or "오늘",
            "visit_time": input_data.get("visit_time") or "오후",
            "transportation": input_data.get("transportation") or "도보"
        }
        
        # 시간 제약 (선택사항)
        time_constraints = None
        if input_data.get("visit_time"):
            time_constraints = {
                "start_time": "14:00" if "오후" in input_data["visit_time"] else "10:00",
                "end_time": "20:00",
                "total_duration": 360  # 6시간
            }
        
        planning_input = {
            "places": places,
            "user_preferences": user_preferences,
            "time_constraints": time_constraints
        }
        
        # PlanningAgent 입력 검증 및 누락 정보 확인
        # if not planning_agent.validate_input(planning_input):
        #     print("❌ 필수 정보가 누락되었습니다.")
        #     missing_info = []
            
        #     if not planning_input.get("places"):
        #         missing_info.append("장소 리스트")
        #     if not planning_input.get("user_preferences", {}).get("theme"):
        #         missing_info.append("테마")
            
        #     if missing_info:
        #         print(f"⚠️  다음 정보가 누락되었습니다: {', '.join(missing_info)}")
                
        #         # 장소가 없으면 검색 단계로 돌아가기
        #         if not planning_input.get("places"):
        #             print("❌ 장소 검색 결과가 없습니다. 코스를 제작할 수 없습니다.")
        #             return
                
        #         # 테마가 없으면 재입력
        #         if not planning_input.get("user_preferences", {}).get("theme"):
        #             print()
        #             theme = get_user_input("📌 여행 테마 (필수)", required=True)
        #             planning_input["user_preferences"]["theme"] = theme
                
        #         # 재검증
        #         if not planning_agent.validate_input(planning_input):
        #             print("❌ 검증 실패: 필수 정보가 여전히 누락되었습니다.")
        #             return
        
        course_result = await planning_agent.execute(planning_input)
        
        if not course_result.get("success"):
            raise Exception(f"코스 제작 실패: {course_result.get('error', '알 수 없는 오류')}")
        
        # ============================================================
        # 결과 출력
        # ============================================================
        final_course = course_result.get("course", {})
        if input_data.get("location"):
            final_course["location"] = input_data["location"]
        if course_result.get("reasoning"):
            final_course["reasoning"] = course_result.get("reasoning")
        
        print(f"\n✨ [{task_id}] 코스 제작 완료! 터미널에서 결과 확인:")
        print("=" * 70)
        
        # 코스 설명
        if final_course.get("course_description"):
            print("📝 코스 설명")
            print("-" * 70)
            print(final_course["course_description"])
            print()
        
        # 방문 순서
        sequence = final_course.get("sequence", [])
        places_list = final_course.get("places", [])
        estimated_duration = final_course.get("estimated_duration", {})
        
        if sequence and places_list:
            print("📍 방문 순서")
            print("-" * 70)
            
            for idx, place_idx in enumerate(sequence, 1):
                if place_idx < len(places_list):
                    place = places_list[place_idx]
                    duration = estimated_duration.get(str(place_idx), "정보 없음")
                    
                    print(f"\n{idx}. {place.get('name', '알 수 없음')}")
                    print(f"   - 카테고리: {place.get('category', 'N/A')}")
                    print(f"   - 체류 시간: {duration}분")
                    
            print()

        # 선정 이유
        reasoning = course_result.get("reasoning")
        if reasoning:
            print("💡 선정 이유")
            print("-" * 70)
            print(reasoning)
            print()
            
        print("=" * 70)

        # 최종 결과를 사용자 사물함에 저장
        agent_tasks[task_id].update({"done": True, "success": True, "course": final_course})

    except Exception as e:
        print(f"\n❌ [{task_id}] 에이전트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        agent_tasks[task_id].update({"done": True, "success": False, "error": str(e)})

def run_agent_task_with_id(task_id, input_data):
    asyncio.run(execute_Agents(task_id, input_data))

@app.route('/api/create-trip', methods=['POST'])
def create_trip():
    data = request.json
    task_id = str(uuid.uuid4())
    
    input_data_from_react = {
        "theme": data.get("theme"), "location": data.get("location"),
        "group_size": data.get("groupSize"),
        "visit_date": f"{data.get('startDate')} ~ {data.get('endDate')}" if data.get('endDate') and data.get('startDate') != data.get('endDate') else data.get('startDate'),
        "visit_time": data.get("visitTime"),
        "transportation": ", ".join(data.get("transportation", []) + ([data.get("customTransport")] if data.get("customTransport") else []))
    }
    
    agent_tasks[task_id] = {"done": False, "success": False, "course": None}
    threading.Thread(target=run_agent_task_with_id, args=(task_id, input_data_from_react)).start()
    
    print(f"🚀 [{task_id}] 신규 작업 시작.")
    return jsonify({"taskId": task_id, "status": "processing"})

@app.route("/status/<task_id>")
def status(task_id):
    task_status = agent_tasks.get(task_id, {})
    # course 데이터는 용량이 크므로 상태 체크 시에는 제외하고 보냄
    return jsonify({
        "done": task_status.get("done", False),
        "success": task_status.get("success", False),
        "error": task_status.get("error")
    })

@app.route('/chat-map/<task_id>')
def chat_page(task_id):
    task = agent_tasks.get(task_id)
    if task and task.get('success'):
        course_data = task.get('course')
        return render_template('chat.html', course=course_data, google_maps_api_key=Config.GOOGLE_MAPS_API_KEY)
    else:
        error_message = task.get('error', '알 수 없는 오류') if task else '유효하지 않은 접근입니다.'
        # TODO: 더 나은 에러 페이지를 보여줄 수 있음
        return f"여행 경로 생성에 실패했습니다: {error_message}", 404

# --- 채팅 API: 이제 task_id를 받아 해당 코스에 대해 채팅하도록 수정 ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message")
    task_id = data.get("taskId") # 프론트엔드에서 taskId를 함께 보내줘야 함

    if not all([user_message, task_id]):
        return jsonify({"response": "메시지 또는 taskId가 누락되었습니다."}), 400
    
    task = agent_tasks.get(task_id)
    if not task or not task.get('success'):
        return jsonify({"response": "유효하지 않은 taskId입니다."}), 400

    current_course = task.get('course')
    bot_response = get_chatbot_response(user_message, current_course)
    
    return jsonify({"response": bot_response})

# --- 기타 API (필요 시 수정) ---
@app.route('/api/locations/<task_id>', methods=['GET'])
def get_locations(task_id):
    task = agent_tasks.get(task_id)
    if not task or not task.get('success'):
        return jsonify({"error": "유효하지 않은 taskId입니다."}), 404
    return jsonify(task.get('course', {}))

# 기존의 단계별 입력 방식은 이제 사용되지 않으므로 주석 처리하거나 삭제 가능
# @app.route('/', methods=['GET', 'POST']) ...

if __name__ == '__main__':
    app.run(debug=True, port=5000)