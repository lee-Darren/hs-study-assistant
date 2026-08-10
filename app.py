import streamlit as st

# 務必確保這是程式碼執行的最優先指令
try:
    st.set_page_config(page_title="高中全科 AI 學習助理", icon="📚")
except Exception:
    pass

from groq import Groq

st.title("📚 高中全科 AI 學習助理")

# 以下保持原本的邏輯...
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("請輸入 Groq API Key：", type="password")
    st.sidebar.markdown("👉 [免費申請 Groq API Key](https://console.groq.com/keys)")

subject = st.selectbox(
    "選擇要請教的科目：",
    ["數學/物理/化學", "英文", "國文/社會"]
)

prompts = {
    "數學/物理/化學": "你是一位高中數理家教。請勿直接給出答案！先說明核心公式或觀念，分步驟引導解題，最後提供一題同類型的練習題。",
    "英文": "你是一位高中英文老師。解析使用者輸入的句子或文章，分析文法結構、重要單字（標註 Level 5-6 詞彙與例句），並指出常見易錯點。",
    "國文/社會": "你是一位高中人文社科老師。請使用結構化心智圖（條列式）說明歷史脈絡、地理因果關係或課文主旨，幫助記憶。"
}

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("請輸入題目或想問的觀念..."):
    if not api_key:
        st.error("⚠️ 請先在左側邊欄輸入你的 Groq API Key 才能開始對話！")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=api_key)
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
            except Exception as e:
                st.error(f"連線失敗：{e}")
