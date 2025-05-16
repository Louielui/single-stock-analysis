import streamlit as st
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="單股即時分析系統", layout="centered")

# --- 股票清單 ---
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

stock_name = st.selectbox("請選擇股票：", list(stock_list.keys()))
ticker = stock_list[stock_name]

# --- 技術強度排行 ---
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

st.markdown("### 🧱 功能區塊預覽")

# --- 即時報價 ---
with st.container():
    st.subheader("📈 即時報價")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="股價", value=f"${price:.2f}", delta=f"{change_percent}%")
        st.write(f"成交量：{volume:,}")
    with col2:
        st.write(f"開盤：${open_price:.2f}")
        st.write(f"昨收：${prev_close:.2f}")

# --- 技術圖表 ---
with st.container():
    st.subheader("📊 技術指標圖：MACD + Bollinger Band + RSI")
    ma20 = hist['Close'].rolling(20).mean()
    bb_upper = ma20 + 2 * hist['Close'].rolling(20).std()
    bb_lower = ma20 - 2 * hist['Close'].rolling(20).std()
    exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
    exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    rsi_delta = hist['Close'].diff()
    up = rsi_delta.clip(lower=0)
    down = -1 * rsi_delta.clip(upper=0)
    avg_gain = up.rolling(14).mean()
    avg_loss = down.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    ax1.plot(hist.index, hist['Close'], label='收盤價', color='black')
    ax1.plot(hist.index, ma20, label='MA20', linestyle='--')
    ax1.plot(hist.index, bb_upper, label='BB上軌', alpha=0.3)
    ax1.plot(hist.index, bb_lower, label='BB下軌', alpha=0.3)
    ax1.fill_between(hist.index, bb_lower, bb_upper, alpha=0.1)
    ax1.legend()
    ax1.set_title(f'{ticker} 價格與布林通道')

    ax2.plot(macd.index, macd, label='MACD', color='blue')
    ax2.plot(signal.index, signal, label='Signal', color='orange')
    ax2.bar(macd.index, macd - signal, label='Histogram', color='gray')
    for i in range(1, len(macd)):
        if macd.iloc[i] > signal.iloc[i] and macd.iloc[i-1] < signal.iloc[i-1]:
            ax2.annotate('⬆️', xy=(macd.index[i], macd.iloc[i]), color='green', fontsize=12, ha='center')
        elif macd.iloc[i] < signal.iloc[i] and macd.iloc[i-1] > signal.iloc[i-1]:
            ax2.annotate('⬇️', xy=(macd.index[i], macd.iloc[i]), color='red', fontsize=12, ha='center')
    ax2.legend()
    ax2.set_title('MACD 指標')

    ax3.plot(rsi.index, rsi, label='RSI', color='purple')
    ax3.axhline(70, linestyle='--', color='red', alpha=0.5)
    ax3.axhline(30, linestyle='--', color='green', alpha=0.5)
    ax3.set_title('RSI 指標')
    ax3.legend()

    st.pyplot(fig)

# --- 期權模擬 ---
data_option = data
try:
    options_dates = data_option.options
    if options_dates:
        selected_date = st.selectbox("選擇到期日：", options_dates)
        option_chain = data_option.option_chain(selected_date)
        puts = option_chain.puts

        puts = puts.sort_values(by='strike')
        st.write("可用 Put 權：", puts[['contractSymbol', 'strike', 'lastPrice', 'bid', 'ask', 'volume']].reset_index(drop=True))

        selected_strike = st.selectbox("選擇履約價：", puts['strike'].values)
        selected_put = puts[puts['strike'] == selected_strike].iloc[0]

        premium = selected_put['bid']
        contracts = 5
        income = premium * 100 * contracts
        margin = selected_strike * 100 * contracts * 0.5
        roi = income / margin * 100

        st.markdown("---")
        st.write(f"✔️ 選擇履約價：${selected_strike:.2f}")
        st.write(f"權利金（Bid）：${premium:.2f}")
        st.write(f"總收入（{contracts}口）：${income:,.0f}")
        st.write(f"保證金需求：${margin:,.0f}")
        st.write(f"報酬率：{roi:.1f}%")

        st.success(f"🔍 技術趨勢：{trend}｜股價位置：{ma_bias}｜建議：{suggestion}")
    else:
        st.warning("⚠️ 此股票目前無期權資料可用。")
except Exception as e:
    st.error(f"期權資料載入錯誤：{str(e)}")

with st.container():
    st.subheader("🤖 AI 建議（模擬）")
    trend = "多頭" if macd.iloc[-1] > signal.iloc[-1] else "空頭"
    ma_bias = "高於 MA20" if price > ma20.iloc[-1] else "低於 MA20"

    if trend == "多頭" and price < ma20.iloc[-1]:
        suggestion = "短線拉回支撐區，可考慮低接 Sell Put 策略。"
    elif trend == "空頭" and price > ma20.iloc[-1]:
        suggestion = "偏空反彈，建議觀望，避免追高。"
    else:
        suggestion = "盤整區間，可留意支撐壓力區的突破情況。"

    # 黃金交叉判斷
    latest_cross = None
    for i in range(1, len(macd)):
        if macd.iloc[i] > signal.iloc[i] and macd.iloc[i-1] < signal.iloc[i-1]:
            latest_cross = macd.index[i]

    signal_text = f"\\n最近黃金交叉發生於 {latest_cross.date()}，可視為轉強訊號。" if latest_cross else ""

    # RSI 計算與判斷
    rsi_delta = hist['Close'].diff()
    up = rsi_delta.clip(lower=0)
    down = -1 * rsi_delta.clip(upper=0)
    avg_gain = up.rolling(14).mean()
    avg_loss = down.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    rsi_latest = rsi_series.dropna().iloc[-1]
    rsi_note = "⚠️ RSI 過熱，注意短線拉回。" if rsi_latest > 70 else ("🔻 RSI 過冷，有機會反彈。" if rsi_latest < 30 else "")

    stop_loss = price * 0.95
    strategy_label = 'Buy ⬆️' if price > ma20.iloc[-1] and macd.iloc[-1] > signal.iloc[-1] else ('Hold ➡️' if abs(price - ma20.iloc[-1]) < 1 and abs(macd.iloc[-1] - signal.iloc[-1]) < 0.1 else 'Reduce ⬇️')
    color = '#d4edda' if strategy_label.startswith('Buy') else '#fff3cd' if strategy_label.startswith('Hold') else '#f8d7da'
    text_color = '#155724' if strategy_label.startswith('Buy') else '#856404' if strategy_label.startswith('Hold') else '#721c24'

    st.markdown(f"""
    技術趨勢：{trend}，股價位置：{ma_bias}。

    💡 策略建議：{suggestion}  
    建議買入區間：{ma20.iloc[-1]*0.98:.2f}～{ma20.iloc[-1]:.2f}  
    建議賣出目標：{bb_upper.iloc[-1]:.2f}  
    建議止損參考：{stop_loss:.2f}  
    推薦策略：<span style='background-color:{color}; color:{text_color}; padding:4px 8px; border-radius:4px;'>{strategy_label}</span>  
    {rsi_note}{signal_text}
    """, unsafe_allow_html=True)

# --- 期權模擬 ---
