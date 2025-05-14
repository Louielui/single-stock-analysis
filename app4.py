import streamlit as st
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import openai
import os

# --- Page Config ---
st.set_page_config(page_title="單股即時分析系統", layout="centered")

# --- OpenAI Key (建議設為環境變數或在 cloud secrets 設定) ---
openai.api_key = os.getenv("OPENAI_API_KEY")  # 或直接輸入 API Key (不建議硬編碼)

# --- 股票清單（含中文） ---
stock_list = {
    "道明銀行 (TD.TO) 🇨🇦": "TD.TO",
    "Fortis 公用 (FTS.TO) 🇨🇦": "FTS.TO",
    "RioCan REIT (REI-UN.TO) 🇨🇦": "REI-UN.TO",
    "騰訊控股 (0700.HK) 🇭🇰": "0700.HK",
    "阿里巴巴 (9988.HK) 🇭🇰": "9988.HK",
    "滙豐控股 (0005.HK) 🇭🇛": "0005.HK",
    "港交所 (0388.HK) 🇭🇰": "0388.HK",
    "建設銀行 (0939.HK) 🇭🇰": "0939.HK"
}

# --- Header ---
st.title("📊 多股即時分析系統")
st.caption(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 股票選單輸入 ---
stock_name = st.selectbox("請選擇股票：", list(stock_list.keys()))
ticker = stock_list[stock_name]

# --- 技術強度排行計算 ---
@st.cache_data
def get_strength_scores():
    scores = {}
    for name, code in stock_list.items():
        try:
            data = yf.Ticker(code).history(period="3mo")
            ma = data['Close'].rolling(20).mean()
            rsi_delta = data['Close'].diff()
            up = rsi_delta.clip(lower=0)
            down = -1 * rsi_delta.clip(upper=0)
            avg_gain = up.rolling(14).mean()
            avg_loss = down.rolling(14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            last_rsi = rsi.dropna().iloc[-1]
            last_price = data['Close'].iloc[-1]
            last_ma = ma.dropna().iloc[-1]
            score = 0
            score += 50 if last_rsi > 60 else 30 if last_rsi > 45 else 10
            score += 50 if last_price > last_ma else 20
            scores[name] = score
        except:
            scores[name] = 0
    return scores

# 技術強度排行區塊
with st.container():
    st.markdown("### 📋 技術強度排行（依 RSI + MA 計算）")
    strength_scores = get_strength_scores()
    sorted_scores = sorted(strength_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (name, score) in enumerate(sorted_scores, 1):
        st.write(f"{rank}. {name} —— 強度分數：{score}")

# --- 資料擷取 ---
data = yf.Ticker(ticker)
hist = data.history(period="6mo")
info = data.info

try:
    price = info['regularMarketPrice']
    prev_close = info['regularMarketPreviousClose']
    open_price = info['regularMarketOpen']
    volume = info['volume']
    change_percent = round(((price - prev_close) / prev_close) * 100, 2)
except:
    st.error("無法擷取資料，請確認代碼是否正確。")
    st.stop()

# --- Layout ---
st.markdown("""
### 🧱 功能區塊預覽
""")

# 即時報價區塊
with st.container():
    st.subheader("📈 即時報價")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="股價", value=f"${price:.2f}", delta=f"{change_percent}%")
        st.write(f"成交量：{volume:,}")
    with col2:
        st.write(f"開盤：${open_price:.2f}")
        st.write(f"昨收：${prev_close:.2f}")

# 技術指標區塊（略） ...（原有技術指標和圖表區塊保持不變）

# 保留原有期權模擬與 AI 建議區塊（略） ...