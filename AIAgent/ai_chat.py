from google import genai
from google.genai import types
import openai

import datetime

def generate_chat_response(config, user_message, context_schedules, history=None, active_focus=None):
    provider = config.get('ai_provider', 'gemini')
    gemini_key = config.get('api_key')
    openai_key = config.get('openai_api_key')
    xai_key = config.get('xai_api_key')
    
    if history is None:
        history = []

    current_time = datetime.datetime.now().strftime("%I:%M %p, %A %d/%m/%Y")
    focus_context = ""
    if active_focus:
        focus_context = f"\n[CẢNH BÁO THỜI GIAN THỰC: Người dùng đang trong phiên Học tập Tập trung (Bị Khóa Game/Web). Nhiệm vụ hiện tại: {active_focus['task']}. Thời gian còn lại phải chịu đựng: {active_focus['time_left_mins']} phút.]"

    system_instructions = (
        "Bạn là trợ lý AI (Study Agent) chạy trực tiếp trên máy tính Windows, nhiệm vụ của bạn là giám sát, hỗ trợ và thúc đẩy người dùng học tập.\n"
        "Bạn có khả năng can thiệp vào Lịch học của người dùng. Khi người dùng yêu cầu, hãy sử dụng các Thẻ Lệnh bí mật sau ở CUỐI câu trả lời của bạn:\n"
        "1. Tạo lịch: [[CREATE_SCHEDULE: Tên_Nhiệm_Vụ, HH:MM, Số_Phút]] -> Ví dụ: [[CREATE_SCHEDULE: Học Toán, 08:00, 45]]. Luôn mặc định chặn ứng dụng (Strict Mode) cho lịch này.\n"
        "2. Xóa lịch: [[DELETE_SCHEDULE: Tên_Nhiệm_Vụ]] -> Ví dụ: [[DELETE_SCHEDULE: Học Toán]].\n\n"
        "QUY TẮC QUAN TRỌNG:\n"
        "- Trước khi XÓA bất kỳ lịch nào, bạn PHẢI hỏi lại xác nhận: 'Cậu có chắc chắn muốn xóa lịch [Tên] không?'. Chỉ khi người dùng đồng ý mới được xuất lệnh [[DELETE_SCHEDULE]].\n"
        "- Bạn có khả năng chặn các ứng dụng/trang web giải trí. Hãy trả lời ngắn gọn, thẳng thắn, đôi khi có thể nghiêm khắc nếu người dùng lười biếng, nhưng vẫn mang tính động viên.\n"
        f"\nTHỜI GIAN HỆ THỐNG: {current_time}"
        f"{focus_context}\n"
        f"Lịch học hiện tại của người dùng: {context_schedules}"
    )

    try:
        if provider == 'openai' or provider == 'xai':
            api_key = openai_key if provider == 'openai' else xai_key
            if not api_key:
                return f"Vui lòng nhập API Key cho {provider.upper()} ở mục Cài đặt!"
            
            kwargs = {'api_key': api_key}
            if provider == 'xai':
                kwargs['base_url'] = "https://api.x.ai/v1"
            
            client = openai.OpenAI(**kwargs)
            model_name = "gpt-4o-mini" if provider == 'openai' else "grok-beta"
            
            # Xây dựng Messages Payload với Lịch sử
            messages = [{"role": "system", "content": system_instructions}]
            for h in history[-10:]: # Pass only last 10 messages context
                role = "assistant" if h['role'] == "ai" else "user"
                messages.append({"role": role, "content": h['content']})
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content

        else: # Default to gemini
            if not gemini_key:
                return "Vui lòng nhập Gemini API Key ở mục Cài đặt!"
            client = genai.Client(api_key=gemini_key)
            
            # Xây dựng Gemini Contents Payload với Lịch sử
            contents = []
            for h in history[-10:]:
                role = "model" if h['role'] == "ai" else "user"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h["content"])]))
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instructions,
                    temperature=0.7
                )
            )
            return response.text

    except Exception as e:
        return f"Đã có lỗi xảy ra khi kết nối với AI ({provider}): {str(e)}"
