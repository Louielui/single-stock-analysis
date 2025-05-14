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

# 技術指標區塊
with st.container():
    st.subheader("📊 技術指標")

    ma20 = hist['Close'].rolling(20).mean()
    delta_rsi = hist['Close'].diff()
    up = delta_rsi.clip(lower=0)
    down = -1 * delta_rsi.clip(upper=0)
    avg_gain = up.rolling(14).mean()
    avg_loss = down.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    rsi_trend = "偏多" if current_rsi > 60 else "中性" if current_rsi > 40 else "偏空"

    exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
    exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    bb_upper = ma20 + 2 * hist['Close'].rolling(20).std()
    bb_lower = ma20 - 2 * hist['Close'].rolling(20).std()

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"MA20：${ma20.iloc[-1]:.2f}")
        st.write(f"RSI：{current_rsi:.1f}（{rsi_trend}）")
    with col2:
        st.write("MACD：多方趨勢" if macd.iloc[-1] > signal.iloc[-1] else "MACD：空方趨勢")

    # 圖表展示
    st.markdown("#### 📉 技術圖：MACD / Bollinger Band")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(hist.index, hist['Close'], label='收盤價', color='black')
    ax.plot(hist.index, ma20, label='MA20', color='blue', linestyle='--')
    ax.plot(hist.index, bb_upper, label='Bollinger 上軌', color='green', alpha=0.4)
    ax.plot(hist.index, bb_lower, label='Bollinger 下軌', color='red', alpha=0.4)
    ax.fill_between(hist.index, bb_lower, bb_upper, color='gray', alpha=0.1)
    ax.set_title(f'{ticker} 收盤價 + Bollinger Band')
    ax.legend()
    st.pyplot(fig)

    fig2, ax2 = plt.subplots(figsize=(10, 3))
    ax2.plot(macd.index, macd, label='MACD', color='blue')
    ax2.plot(signal.index, signal, label='Signal', color='orange')
    ax2.bar(macd.index, macd - signal, label='MACD Histogram', color='gray')
    ax2.set_title('MACD 指標')
    ax2.legend()
    st.pyplot(fig2)

# 判斷是否為港股，略過期權模擬
if not ticker.endswith(".HK"):
    with st.container():
        st.subheader("📉 期權模擬：賣出 Put @ $77.5")
        premium = 1.35
        contracts = 5
        income = premium * 100 * contracts
        margin = 77.5 * 100 * contracts * 0.5
        roi = income / margin * 100
        st.write(f"權利金：${premium:.2f}，{contracts}口總收入：${income:,.0f}")
        st.write(f"保證金需求：${margin:,.0f}")
        st.write(f"報酬率：{roi:.1f}%")
        st.success("✅ 建議：可建倉，風險偏低（進場價低於 MA60）")

# AI 建議區塊
with st.container():
    st.subheader("🤖 AI 建議")
    try:
        prompt = f"""
你是一位專業技術分析投資顧問。請根據以下條件撰寫一段簡短的盤前策略建議：
- 股票代號：{ticker}
- 今日開盤價：{open_price:.2f}
- RSI 指標：{current_rsi:.1f}
- MACD 狀況：{'多頭' if macd.iloc[-1] > signal.iloc[-1] else '空頭'}
- 均線位置：MA20 為 {ma20.iloc[-1]:.2f}，股價為 {price:.2f}
- 今日漲跌幅：{change_percent}%
語氣務實精簡，建議以「策略觀點」為導向，例如支撐壓力位、建議策略方向。
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_msg = response.choices[0].message.content
    except:
        ai_msg = "（無法取得 OpenAI 建議，請確認 API 金鑰或流量限制）"
    st.info(ai_msg)
