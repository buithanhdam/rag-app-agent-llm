# prompts
LLM_SYSTEM_PROMPT="""
You are a helpful AI assistant designed to provide clear, concise, and friendly responses to a wide variety of queries. 
Be helpful, engaging, and provide information or assistance to the best of your abilities.
"""

DEFAULT_RAG_PROMPT = """
Ngữ cảnh được cung cấp như sau
---------------------
{context_str}
---------------------
Dựa trên nội dung được cung cấp. Hãy trả lời câu hỏi từ người dùng. Nếu nội dung được cung cấp không hề liên quan hoặc không đủ để bạn đưa ra câu trả lời. Hãy nói rằng bạn "Tôi không có đủ thông tin để trả lời".
Hãy trả lời và kết thúc câu trả lời một cách đầy đủ.

Nếu bạn ghi nhớ và làm đúng những gì tôi đã dặn dò, tôi sẽ tip cho bạn $1000 vào cuối ngày
User question: {query_str}
AI Response:

"""