import streamlit as st
from groq import Groq

st.set_page_config(page_title="高中全科 AI 學習助理", icon="📚")
st.title("📚 高中全科 AI 學習助理")

# 從左側輸入 Groq API Key 或設定 secrets
api_key = st.sidebar.text_input("輸入 Groq API Key", type="password")

if api_key:
    client = Groq(api_key=api_key)

    subject = st.selectbox(
        "選擇要請教的科目：",
        ["數學/物理/化學", "英文", "國文/社會"]
    )

    prompts = {
        "數學/物理/化學": "你是一位高中數理家教。請勿直接給出答案！先說明核心公式或觀念，分步驟引導解題，最後提供一題同類型的練習題。",
        "英文": "你是一位高中英文老師。解析使用者輸入的句子或文章，分析文法結構、重要單字，並指出常見易錯點。",
        "國文/社會": "你是一位高中人文社科老師。請使用結構化心智圖（條列式）說明歷史脈絡、地理因果關係或課文主旨。"
    }

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("請輸入題目或想問的觀念..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompts[subject]},
                    {"role": "user", "content": user_input}
                ],
                model="llama-3.3-70b-versatile",
            )
            reply = chat_completion.choices[0].message.content
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
