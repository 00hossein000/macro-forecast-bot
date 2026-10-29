import os
import requests
import yfinance as yf
from fredapi import Fred

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FRED_API_KEY = os.getenv("FRED_API_KEY")

def send_telegram_msg(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

def fetch_all_macro_data():
    data = {}
    try:
        tickers = yf.Tickers('DX-Y.NYB ^TNX GC=F CL=F ^VIX')
        data['dxy'] = tickers.tickers['DX-Y.NYB'].history(period='1d')['Close'].iloc[-1]
        data['us10y'] = tickers.tickers['^TNX'].history(period='1d')['Close'].iloc[-1]
        data['gold'] = tickers.tickers['GC=F'].history(period='1d')['Close'].iloc[-1]
        data['oil'] = tickers.tickers['CL=F'].history(period='1d')['Close'].iloc[-1]
        data['vix'] = tickers.tickers['^VIX'].history(period='1d')['Close'].iloc[-1]
    except Exception as e:
        print(f"Yahoo error: {e}")

    try:
        nobitex_res = requests.get('https://api.nobitex.ir/v2/orderbook/USDTIRT', timeout=10).json()
        data['usdt'] = int(nobitex_res['bids'][0][0]) / 10
    except:
        data['usdt'] = 0

    if FRED_API_KEY:
        try:
            fred = Fred(api_key=FRED_API_KEY)
            data['real_yield'] = fred.get_series('DFII10').dropna().iloc[-1]
            data['inflation_exp'] = fred.get_series('T10YIE').dropna().iloc[-1]
            data['t10y2y'] = fred.get_series('T10Y2Y').dropna().iloc[-1]
            data['m2'] = fred.get_series('M2SL').dropna().iloc[-1]
            data['pce'] = fred.get_series('PCEPI').dropna().iloc[-1]
            data['fed_funds'] = fred.get_series('FEDFUNDS').dropna().iloc[-1]
        except Exception as e:
            print(f"FRED error: {e}")
            
    return data

def generate_comprehensive_analysis(d):
    dxy = d.get('dxy', 0)
    us10y = d.get('us10y', 0)
    real_yield = d.get('real_yield', 0)
    vix = d.get('vix', 0)
    oil = d.get('oil', 0)
    inflation_exp = d.get('inflation_exp', 0)
    yield_spread = d.get('t10y2y', 0)
    usdt = d.get('usdt', 0)

    gold_drivers = []
    if real_yield < 1.5:
        gold_drivers.append("🟢 بازده واقعی پایین (سوخت اصلی صعود انس)")
    else:
        gold_drivers.append("🔻 بازده واقعی بالا (فشار روی انس)")

    if vix > 20:
        gold_drivers.append("⚠️ جهش شاخص ترس/VIX (تقاضای پناهگاه امن)")
    else:
        gold_drivers.append("⚖️ آرامش نسبی بازارهای مالی (VIX نرمال)")

    if oil > 80:
        gold_drivers.append("🔥 نفت گران (فشار تورمی و حامی طلا)")

    short_term = "روند خنثی / نوسانی"
    if dxy > 104 and us10y > 4.2:
        short_term = "🔻 فشرده‌سازی نزولی (دلار و اوراق قوی)"
    elif dxy < 102 or real_yield < 1.5:
        short_term = "🚀 پتانسیل صعودی قوی برای طلا"

    usdt_text = f"`{usdt:,.0f} تومان`" if usdt > 0 else "نامشخص"

    report = (
        "🌐 **سیستم هوشمند جامع تحلیل اقتصاد کلان و بازار**\n\n"
        "📊 **قیمت‌های لحظه‌ای بازار جهانی:**\n"
        f"• انس طلا: `${d.get('gold', 0):.2f}`\n"
        f"• شاخص دلار (DXY): `{dxy:.2f}`\n"
        f"• اوراق ۱۰ ساله آمریکا: `{us10y:.2f}%`\n"
        f"• نفت خام (WTI): `${oil:.2f}`\n"
        f"• شاخص ترس (VIX): `{vix:.2f}`\n"
        f"• تتر در بازار ایران: {usdt_text}\n\n"
        "⚙️ **پیش‌شاخص‌ها و عوامل بنیادین کلان (FRED):**\n"
        f"• **بازده واقعی اوراق (DFII10):** `{real_yield:.2f}%`\n"
        f"• **انتظارات تورمی (T10YIE):** `{inflation_exp:.2f}%`\n"
        f"• **شکاف اوراق ۱۰ و ۲ ساله:** `{yield_spread:.2f}`\n"
        f"• **نرخ بهره مؤثر فدز:** `{d.get('fed_funds', 0):.2f}%`\n"
        f"• **شاخص تورم فدز (PCE):** `{d.get('pce', 0):.1f}`\n\n"
        "🧠 **برآیند هوش مصنوعی و مدل وزن‌دهی:**\n"
        f"⚡️ **پیش‌بینی جهت کوتاه‌مدت:** {short_term}\n\n"
        "🔍 **تحلیل عوامل نامرئی و کلیدی:**\n" +
        "\n".join([f"• {item}" for item in gold_drivers])
    )
    return report

if __name__ == "__main__":
    market_data = fetch_all_macro_data()
    final_report = generate_comprehensive_analysis(market_data)
    print(final_report)
    send_telegram_msg(final_report)
