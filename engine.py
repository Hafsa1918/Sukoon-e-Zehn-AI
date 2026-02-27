import os
import asyncio
import edge_tts
from typing import TypedDict, List
from groq import Groq
from tempfile import NamedTemporaryFile
from langgraph.graph import StateGraph, END

client = Groq(api_key=os.getenv("GROQ_API_KEY_Health"))

class AgentState(TypedDict):
    messages: List[dict]
    is_crisis: bool
    final_response: str
    audio_path: str

def crisis_node(state: AgentState):
    user_msg = state['messages'][-1]['content'].lower()
    keywords = ["suicide", "khudkushi", "marna", "marne", "zindagi khatam", "jaan de", "hopeless"]
    is_crisis = any(word in user_msg for word in keywords)
    return {"is_crisis": is_crisis}

def support_node(state: AgentState):
    user_msg = state['messages'][-1]['content']

    system_prompt = (
        "You are Sukoon-e-Zehn AI. "
        "Respond ONLY in proper Urdu script (اردو). "
        "Be empathetic, natural, and supportive."
    )

    if state.get('is_crisis'):
        system_prompt += " EMERGENCY: Provide Umang Helpline 0311-7786264."

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    )

    resp = completion.choices[0].message.content
    tmp = NamedTemporaryFile(delete=False, suffix=".mp3")

    async def generate_audio(text, path):
        communicate = edge_tts.Communicate(
            text,
            voice="ur-PK-UzmaNeural",
            rate="+5%",
            pitch="+2Hz"
        )
        await communicate.save(path)

    asyncio.run(generate_audio(resp, tmp.name))

    return {
        "final_response": resp,
        "audio_path": tmp.name
    }

workflow = StateGraph(AgentState)
workflow.add_node("check", crisis_node)
workflow.add_node("chat", support_node)
workflow.set_entry_point("check")
workflow.add_edge("check", "chat")
workflow.add_edge("chat", END)

sukoon_app = workflow.compile()