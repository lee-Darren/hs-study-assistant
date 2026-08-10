import streamlit as st
from google import genai
from google.genai import types
import pypdf
import io

# 1. 頁面配置
try:
    st.set_page_config(page_title="Gemini + NotebookLM 高中 10 科全能 AI 助理", icon="📚", layout="wide")
except Exception:
    pass

st.title("📚 Gemini + NotebookLM 高中 10 科全能 AI 助理")

# 2. API Key 設定
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("請輸入 Gemini API Key：", type="password")
    st.sidebar.markdown("👉 [免費申請 Google Gemini API Key](https://aistudio.google.com/)")

# 3. 側邊欄：10 科選單與 NotebookLM 知識庫上傳
st.sidebar.header("⚙️ 學習設定")

subject = st.sidebar.selectbox(
    "選擇科目：",
    ["國文", "英文", "數學", "物理", "化學", "地球科學", "生物", "地理", "歷史", "公民"]
)

st.sidebar.subheader("📖 NotebookLM 個人知識庫")
uploaded_docs = st.sidebar.file_uploader(
    f"上傳【{subject}】參考講義/筆記 (支援 PDF, TXT)：", 
    type=["pdf", "txt"],
    accept_multiple_files=True,
    help="上傳後，AI 將扮演 NotebookLM 嚴格依據講義回答並標註引註！"
)

# 讀取並解析文字/PDF 檔案
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
    st.sidebar.success(f"已載入 {len(uploaded_docs)} 份【{subject}】參考資料！")

st.sidebar.subheader("🔍 Gemini 功能設定")
enable_web_search = st.sidebar.checkbox("開啟 Google 即時聯網搜尋", value=False)

# 4. 10 科 Prompt 設定
prompts = {
    "國文": "你是一位高中國文老師。解析課文主旨、古文註釋、修辭技巧或國寫作文，提供深入且白話的說明。",
    "英文": "你是一位高中英文老師。解析文法結構、單字用法（標註 Level 5-6 詞彙與例句），並指出常見易錯點。",
    "數學": "你是一位高中數學家教。請勿直接給出答案！先說明核心公式，分步驟引導解題，最後提供一題同類型練習題。",
    "物理": "你是一位高中物理家教。說明物理現象原理、公式推導與單位轉換，協助建立物理直覺。",
    "化學": "你是一位高中化學家教。解析化学反應式、實驗步驟、沉澱表與分子結構，並提醒記憶口訣。",
    "地球科學": "你是一位高中地科老師。結合圖表觀念（板塊、天文、大氣、海洋）說明自然現象背後的因果關係。",
    "生物": "你是一位高中生物老師。詳細說明生理機制、細胞運作流程與專有名詞，並建議結構圖輔助。",
    "地理": "你是一位高中地理老師。分析自然地理（地形、氣候）與人文地理（經濟、產業）的因果脈絡與空間概念。",
    "歷史": "你是一位高中歷史老師。使用時間軸與因果關係鏈（條列式）梳理歷史事件背景、經過與影響。",
    "公民": "你是一位高中公民老師。解析法律、政治、經濟與社會學的核心概念，並結合時事案例。"
}

# 5. 初始化對話歷史
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("🧹 清除當前對話紀錄"):
    st.session_state.messages = []
    st.rerun()

# 渲染歷史對話
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 6. 主對話區：支援文字 + 圖片/照片 上傳
st.markdown("### 💬 請輸入問題或上傳題目照片")
user_image = st.file_uploader("📷 上傳題目照片/考卷截圖 (選填)：", type=["png", "jpg", "jpeg"])

if user_input := st.chat_input(f"請輸入關於【{subject}】的問題..."):
    if not api_key:
        st.error("⚠️ 請先在左側邊欄輸入你的 Gemini API Key！")
    else:
        # 顯示使用者訊息
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
            if user_image:
                st.image(user_image, caption="已上傳題目照片", width=300)

        # 組合 System Instruction（結合 NotebookLM 知識庫指示）
        system_instruction = prompts[subject]
        if knowledge_base:
            system_instruction += (
                "\n\n【NotebookLM 模式開啟】\n"
                "學生上傳了以下參考講義內容。回答時請遵循以下原則：\n"
                "1. 優先依據參考資料回答問題。\n"
                "2. 請在回答中明確標註引用來源（例如：[引自 歷史講義.pdf 第 3 頁]）。\n"
                "3. 若參考資料未提及，請明確指出，再補充通用知識。\n\n"
                f"【參考資料內容】：\n{knowledge_base}"
            )

        # 準備 API 請求內容
        contents = []
        if user_image:
            image_bytes = user_image.read()
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=user_image.type))
        contents.append(user_input)

        # 設定 Config (搜尋與 System Instruction)
        tools = []
        if enable_web_search:
            tools.append({"google_search": {}})

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2 if knowledge_base else 0.4,
            tools=tools if tools else None
        )

        # 呼叫 Gemini 2.5 API
        with st.chat_message("assistant"):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                    config=config
                )
                reply = response.text
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Gemini API 連線失敗：{e}")
