import os
import time
import schedule
from google import genai
from google.genai import types

# 1. 初始化 Gemini Client
# 請確保已在環境變數設定 GEMINI_API_KEY 或直接填入
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "你的_GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. 定義學習 agent 的核心任務 (Task)

def generate_daily_review():
    """
    Agent 任務一：自動讀取近期學習紀錄，並請 Gemini 生成【每日考前 3 分鐘複習考卷】
    """
    print("🤖 [龍蝦 Agent] 正在為你準備今天的自動複習考卷...")

    # 模擬從你的 Streamlit 或資料庫讀取的累積弱點觀念
    weak_points = ["高中化學：沉澱表與顏色變化", "高中物理：斜面平拋運動公式", "高中歷史：冷戰時期的美蘇對峙"]
    
    prompt = f"""
    你是一位高中全科頂尖家教。
    請根據學生目前的弱點觀念：{weak_points}
    為學生設計一份「每日 3 分鐘精準練習題」：
    1. 針對每個弱點各出一題精選單選題（包含選項 A, B, C, D）。
    2. 在考卷最後附上【答案與白話觀念解析】。
    3. 排版請使用乾淨 Markdown 格式，方便閱讀。
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3)
        )
        
        quiz_content = response.text
        
        # 3. Agent 自動化動作：將生成的考卷儲存成每日筆記檔
        filename = f"daily_quiz_{time.strftime('%Y%m%d')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 📚 每日專屬複習考卷 ({time.strftime('%Y-%m-%d')})\n\n")
            f.write(quiz_content)
            
        print(f"✅ [龍蝦 Agent] 考卷已自動生成並儲存至：{filename}")
        
    except Exception as e:
        print(f"❌ [龍蝦 Agent] 執行失敗：{e}")

def fetch_current_events_quiz():
    """
    Agent 任務二：自動結合即時搜尋，將最新時事轉換為【公民/歷史/地理考點題】
    """
    print("🌐 [龍蝦 Agent] 正在搜尋最新新聞並轉換為高中公民/歷史考題...")

    prompt = """
    請使用 Google 搜尋搜尋近期台灣或國際的 1 則重大新聞時事。
    然後將這則新聞轉換為 1 題「高中公民與社會」或「高中地理」的學測情境題：
    1. 引述新聞背景文本（簡短 100 字）。
    2. 結合高中課本觀念設計 1 個題目與選項。
    3. 附上詳細答案與對應課本章節重點解析。
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}], # 開啟即時聯網搜尋
                temperature=0.3
            )
        )
        
        news_quiz = response.text
        filename = f"news_quiz_{time.strftime('%Y%m%d')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(news_quiz)
            
        print(f"✅ [龍蝦 Agent] 時事考題已生成至：{filename}")
        
    except Exception as e:
        print(f"❌ [龍蝦 Agent] 執行失敗：{e}")

# 3. Agent 自動化排程設定 (Automated Scheduler)

# 設定每日固定時間自動執行任務
schedule.every().day.at("07:00").do(generate_daily_review)      # 每天早上 7 點自動做複習卷
schedule.every().day.at("18:00").do(fetch_current_events_quiz)   # 每天下午 6 點自動產生時事題

print("🚀 龍蝦學習 Agent 已啟動，背景自動化監控中...")
print("按 Ctrl + C 可結束程式。\n")

# 手動立即測試一次
generate_daily_review()

# 保持背景排程持續運作
while True:
    schedule.run_pending()
    time.sleep(60)
