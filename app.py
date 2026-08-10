import streamlit as st
from groq import Groq

# 1. 頁面設定
try:
    st.set_page_config(page_title="高中 10 科全能 AI 學習助理", icon="📚", layout="wide")
except Exception:
    pass

from groq import Groq

st.title("📚 高中 10 科全能 AI 學習助理")

# 2. API Key 設定
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("請輸入 Groq API Key：", type="password")
    st.sidebar.markdown("👉 [免費申請 Groq API Key](https://console.groq.com/keys)")

# 3. 側邊栏：10 科選單與專屬檔案上傳
st.sidebar.header("⚙️ 學習設定")

subject = st.sidebar.selectbox(
    "選擇要請教的科目：",
    [
        "國文", "英文", "數學", 
        "物理", "化學", "地球科學", "生物", 
        "地理", "歷史", "公民"
    ]
)

# 檔案上傳器 (支援 txt，若要 pdf 需額外套件，建議先以 txt 或直接貼上文字為主)
uploaded_file = st.sidebar.file_uploader(
    f"上傳【{subject}】的講義/筆記 (.txt 檔)：", 
    type=["txt"],
    help="上傳後，AI 回答時會優先依據這份檔案的內容！"
)

# 讀取檔案內容
file_context = ""
if uploaded_file is not None:
    file_context = uploaded_file.read().decode("utf-8")
    st.sidebar.success(f"已載入【{subject}】參考資料！")

# 4. 10 大科目的 System Prompt 字典
prompts = {
    "國文": "你是一位高中國文老師。請針對課文主旨、古文註釋、修辭技巧或國寫作文提供深入且白話的解析。",
    "英文": "你是一位高中英文老師。請解析文法結構、單字用法（標註 Level 5-6 高中常見字彙與例句），並指出常見易錯點。",
    "數學": "你是一位高中數學家教。請勿直接給出答案！先說明核心公式或觀念，分步驟引導解題，最後提供一題同類型的練習題。",
    "物理": "你是一位高中物理家教。說明物理現象背後的原理、公式推導與單位轉換，協助學生建立物理直覺。",
    "化學": "你是一位高中化學家教。解析化學反應式、實驗步驟、沉澱表與分子結構，並提醒記憶口訣。",
    "地球科學": "你是一位高中地科老師。請結合圖表觀念（板塊、天文、大氣、海洋）說明自然現象背後的因果關係。",
    "生物": "你是一位高中生物老師。請詳細說明生理機制、細胞運作流程與專有名詞，並建議使用結構圖幫助記憶。",
    "地理": "你是一位高中地理老師。請分析自然地理（地形、氣候）與人文地理（經濟、產業）的因果脈絡與空間概念。",
    "歷史": "你是一位高中歷史老師。請使用時間軸與因果關係鏈（條列式）梳理歷史事件背景、經過與影響。",
    "公民": "你是一位高中公民老師。解析法律、政治、經濟與社會學的核心概念，並結合時事案例幫助理解。"
}

# 5. 初始化對話紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# 清除對話紀錄按鈕
if st.sidebar.button("🧹 清除當前對話紀錄"):
    st.session_state.messages = []
    st.rerun()

# 6. 渲染歷史對話
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 7. 對話處理邏輯
if user_input := st.chat_input(f"請輸入關於【{subject}】的題目或觀念..."):
    if not api_key:
        st.error("⚠️ 請先在左側邊欄輸入你的 Groq API Key 才能開始對話！")
    else:
        # 顯示使用者輸入
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # 組合 System Prompt + 個人資料庫內容
        base_prompt = prompts[subject]
        if file_context:
            system_instruction = f"{base_prompt}\n\n【重要參考資料】：學生上傳了以下【{subject}】講義內容，請優先根據以下資料來回答問題：\n{file_context}"
        else:
            system_instruction = base_prompt

        # 呼叫 AI
        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=api_key)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_input}
                    ],
                    model="llama-3.3-70b-versatile",
                )
                reply = chat_completion.choices[0].message.content
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"連線失敗：{e}")
