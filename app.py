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
    
    # 提供下載該科重點筆記功能
    st.sidebar.download_button(
        label=f"📥 下載【{subject}】複習筆記 (.txt)",
        data=f"=== 【{subject}】對話重點總結庫 ===\n\n" + db_text,
        file_name=f"{subject}_複習重點.txt",
        mime="text/plain"
    )
else:
    st.sidebar.info("目前尚無重點紀錄，發問後 AI 會自動整理加入！")

# 📖 NotebookLM 講義上傳區
st.sidebar.subheader("📖 NotebookLM 講義上傳")
uploaded_docs = st.sidebar.file_uploader(
    f"上傳【{subject}】講義/筆記 (PDF, TXT)：", 
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

enable_web_search = st.sidebar.checkbox("開啟 Google 即時聯網搜尋", value=False)

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

# 清除當前科目歷史紀錄按鈕
if st.sidebar.button(f"🧹 清除【{subject}】的對話與重點庫"):
    st.session_state.messages[subject] = []
    st.session_state.subjects_db[subject] = []
    st.rerun()

# 6. 渲染目前選定科目的歷史對話
for msg in st.session_state.messages[subject]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 7. 主對話區
st.markdown(f"### 💬 【{subject}】AI 學習助理")
user_image = st.file_uploader("📷 上傳題目照片/考卷截圖 (選填)：", type=["png", "jpg", "jpeg"])

if user_input := st.chat_input(f"請輸入關於【{subject}】的問題..."):
    if not api_key:
        st.error("⚠️ 請先在左側邊欄輸入你的 Gemini API Key！")
    else:
        # 紀錄使用者對話
        st.session_state.messages[subject].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
            if user_image:
                st.image(user_image, caption="已上傳題目照片", width=300)

        # 組合 System Instruction
        system_instruction = prompts[subject]
        if knowledge_base:
            system_instruction += f"\n\n【講義資料】：\n{knowledge_base}"

        # 準備 API 內容
        contents = []
        if user_image:
            image_bytes = user_image.read()
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=user_image.type))
        contents.append(user_input)

        tools = [{"google_search": {}}] if enable_web_search else []

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            tools=tools if tools else None
        )

        with st.chat_message("assistant"):
            try:
                client = genai.Client(api_key=api_key)
                
                # 1. 產生主要解答
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                    config=config
                )
                reply = response.text
                st.write(reply)
                st.session_state.messages[subject].append({"role": "assistant", "content": reply})

                # 2. 自動總結重點並存入【專屬資料庫】
                summary_prompt = (
                    f"請針對以下這段【{subject}】的對話內容，用最簡短的 1 到 2 句話總結一個關鍵學習重點或公式（不需包含廢話與解答過程）：\n"
                    f"問：{user_input}\n答：{reply}"
                )
                summary_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=summary_prompt
                )
                new_key_point = summary_response.text.strip()
                
                # 追加寫入該科資料庫
                st.session_state.subjects_db[subject].append(new_key_point)
                st.rerun() # 重新載入頁面更新側邊欄重點庫

            except Exception as e:
                st.error(f"Gemini API 連線失敗：{e}")
import re
import urllib.request

st.sidebar.subheader("🔗 Google Drive 連結載入")
gdrive_url = st.sidebar.text_input("貼上 Google Drive 檔案共用連結：")

if gdrive_url:
    # 使用正則表達式抓取 Google Drive 檔案 ID
    file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', gdrive_url) or re.search(r'id=([a-zA-Z0-9_-]+)', gdrive_url)
    if file_id_match:
        file_id = file_id_match.group(1)
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        try:
            # 自動下載檔案內容
            with urllib.request.urlopen(download_url) as response:
                content = response.read().decode('utf-8', errors='ignore')
                knowledge_base += f"\n=== 雲端硬碟檔案 (ID: {file_id}) ===\n" + content
            st.sidebar.success("✅ 成功從 Google Drive 載入講義！")
        except Exception as e:
            st.sidebar.error(f"下載失敗，請確認檔案已設定為「知道連結的人皆可檢視」：{e}")
