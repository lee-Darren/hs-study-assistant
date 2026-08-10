import streamlit as st
from groq import Groq
import pypdf
import io

# 1. 頁面配置
try:
    st.set_page_config(page_title="Groq 高中 10 科全能 AI 助理", icon="📚", layout="wide")
except Exception:
    pass

st.title("⚡ Groq 高中 10 科全能 AI 助理 (極速解答版)")

# 2. Groq API Key 設定
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("請輸入 Groq API Key (gsk_...)：", type="password")
    st.sidebar.markdown("👉 [免費申請 Groq API Key](https://console.groq.com/keys)")

# 3. 初始化各科專屬記憶庫與歷史紀錄
SUBJECTS = ["國文", "英文", "數學", "物理", "化學", "地球科學", "生物", "地理", "歷史", "公民"]

if "subjects_db" not in st.session_state:
    st.session_state.subjects_db = {sub: [] for sub in SUBJECTS}

if "messages" not in st.session_state:
    st.session_state.messages = {sub: [] for sub in SUBJECTS}

# 4. 側邊欄：10 科選擇與專屬學習重點庫
st.sidebar.header("⚙️ 學習設定")
subject = st.sidebar.selectbox("選擇科目：", SUBJECTS)

# 📖 專屬資料庫顯示區
st.sidebar.subheader(f"📌【{subject}】專屬學習重點庫")
current_db = st.session_state.subjects_db[subject]

if current_db:
    db_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(current_db)])
    st.sidebar.text_area("歷史學習筆記 (自動累積)：", value=db_text, height=200, disabled=True)
    
    st.sidebar.download_button(
        label=f"📥 下載【{subject}】複習筆記 (.txt)",
        data=f"=== 【{subject}】對話重點總結庫 ===\n\n" + db_text,
        file_name=f"{subject}_複習重點.txt",
        mime="text/plain"
    )
else:
    st.sidebar.info("目前尚無重點紀錄，發問後 AI 會自動整理加入！")

# 📖 講義上傳區
st.sidebar.subheader("📖 參考講義上傳 (TXT, PDF)")
uploaded_docs = st.sidebar.file_uploader(
    f"上傳【{subject}】講義/筆記：", 
    type=["pdf", "txt"],
    accept_multiple_files=True
)

knowledge_base = ""
if uploaded_docs:
    for doc in uploaded_docs:
        doc_text = ""
        if doc.name.endswith(".txt"):
            doc_text = doc.read().decode("utf-8")
        elif doc.name.endswith(".pdf"):
            pdf_reader = pypdf.PdfReader(io.BytesIO(doc.read()))
            for i, page in enumerate(pdf_reader.pages):
                extracted = page.extract_text()
                if extracted:
                    doc_text += f"\n[檔案: {doc.name} - 第 {i+1} 頁]\n" + extracted
        knowledge_base += f"\n=== 參考文件: {doc.name} ===\n{doc_text}\n"

# 5. 10 科 Prompt 設定
prompts = {
    "國文": "你是一位高中國文老師。解析課文主旨、古文註釋、修辭技巧或國寫作文，提供深入且白話的說明。",
    "英文": "你是一位高中英文老師。解析文法結構、單字用法（標註 Level 5-6 詞彙與例句），並指出常見易錯點。",
    "數學": "你是一位高中數學家教。請勿直接給出答案！先說明核心公式，分步驟引導解題，最後提供一題同類型練習題。",
    "物理": "你是一位高中物理家教。說明物理現象原理、公式推導與單位轉換，協助建立物理直覺。",
    "化學": "你是一位高中化學家教。解析化學反應式、實驗步驟、沉澱表與分子結構，並提醒記憶口訣。",
    "地球科學": "你是一位高中地科老師。結合圖表觀念（板塊、天文、大氣、海洋）說明自然現象背後的因果關係。",
    "生物": "你是一位高中生物老師。詳細說明生理機制、細胞運作流程與專有名詞，並建議結構圖輔助。",
    "地理": "你是一位高中地理老師。分析自然地理（地形、氣候）與人文地理（經濟、產業）的因果脈絡與空間概念。",
    "歷史": "你是一位高中歷史老師。使用時間軸與因果關係鏈（條列式）梳理歷史事件背景、經過與影響。",
    "公民": "你是一位高中公民老師。解析法律、政治、經濟與社會學的核心概念，並結合時事案例。"
}

if st.sidebar.button(f"🧹 清除【{subject}】的對話與重點庫"):
    st.session_state.messages[subject] = []
    st.session_state.subjects_db[subject] = []
    st.rerun()

# 6. 渲染目前科目的對話紀錄
for msg in st.session_state.messages[subject]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 7. 主對話區
if user_input := st.chat_input(f"請輸入關於【{subject}】的問題..."):
    if not api_key:
        st.error("⚠️ 請先在左側邊欄輸入你的 Groq API Key (gsk_...)！")
    else:
        st.session_state.messages[subject].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        system_prompt = prompts[subject]
        if knowledge_base:
            system_prompt += f"\n\n【參考講義資料】：\n{knowledge_base}\n回答時請盡可能參考上述資料並說明出處。"

        # 組成 Message 格式
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.messages[subject]:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=api_key)
                
                # 1. 呼叫 Groq API (選用目前最頂級的 Llama 3.3 70B 模型)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=api_messages,
                    temperature=0.3,
                )
                reply = completion.choices[0].message.content
                st.write(reply)
                st.session_state.messages[subject].append({"role": "assistant", "content": reply})

                # 2. 自動總結重點並存入【專屬資料庫】
                summary_messages = [
                    {"role": "system", "content": "你是一位精準的筆記整理助手。"},
                    {"role": "user", "content": f"請將以下【{subject}】的對話，用 1 到 2 句話總結為關鍵學習重點：\n問：{user_input}\n答：{reply}"}
                ]
                summary_res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=summary_messages,
                    temperature=0.2
                )
                new_key_point = summary_res.choices[0].message.content.strip()
                st.session_state.subjects_db[subject].append(new_key_point)
                
                st.rerun()

            except Exception as e:
                st.error(f"Groq API 連線失敗：{e}")
