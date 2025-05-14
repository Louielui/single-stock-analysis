import streamlit as st
import yfinance as yf
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="單股即時分析系統", layout="centered")

# --- Header ---
st.title("📊 單股即時分析系統 Prototype")
st.caption(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 股票代號輸入 ---
ticker = st.text_input("輸入股票代號 (如 TD.TO)", value="TD.TO")

data = yf.Ticker(ticker)
hist = data.history(period="5d")
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

# 技術指標區塊（簡易版）
with st.container():
    st.subheader("📊 技術指標")
    ma20 = hist['Close'].rolling(20).mean().iloc[-1]
    delta_rsi = hist['Close'].diff()
    up = delta_rsi.clip(lower=0)
    down = -1 * delta_rsi.clip(upper=0)
    avg_gain = up.rolling(14).mean()
    avg_loss = down.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    rsi_trend = "偏多" if current_rsi > 60 else "中性" if current_rsi > 40 else "偏空"
    with st.columns(2)[0]:
        st.write(f"MA20：${ma20:.2f}")
        st.write(f"RSI：{current_rsi:.1f}（{rsi_trend}）")
    with st.columns(2)[1]:
        st.write("MACD：多方趨勢（模擬）")

# 選擇權模擬區塊（靜態）
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

# AI 建議區塊（模擬）
with st.container():
    st.subheader("🤖 AI 建議")
    if current_rsi > 60:
        ai_msg = "此股處於上升通道，短線回測支撐。Put Sell 策略可考慮於 $77.5～$80 範圍佈局。"
    elif current_rsi < 40:
        ai_msg = "技術指標偏弱，建議暫緩進場，觀察是否有止穩訊號。"
    else:
        ai_msg = "股價整理中，可留意支撐壓力突破再行動。"
    st.info(ai_msg)
