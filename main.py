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
        # ارسال پیام به صورت بخش‌بندی شده اگر طولانی بود
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"})
        else:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})

def fetch_tether_price():
    # تلاش اول: صرافی نوبیتکس
    try:
        res = requests.get('https://api.nobitex.ir/v2/orderbook/USDTIRT', timeout=5).json()
        if 'bids' in res and len(res['bids']) > 0:
            return int(float(res['bids'][0][0])) / 10 # تبدیل ریال به تومان
    except:
        pass
    
    # تلاش دوم (پشتیبان): صرافی والکس در صورت خطای نوبیتکس
    try:
        res = requests.get('https://api.wallex.ir/v1/markets', timeout=5).json()
        price = res['result']['symbols']['USDTIRT']['stats']['lastPrice']
        return int(float(price)) / 10
    except:
        pass
        
    return 0

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

    # دریافت قیمت تتر با متد اصلاح‌شده و ایمن
    data['usdt'] = fetch_tether_price()

    if FRED_API_KEY:
        try:
            fred = Fred(api_key=FRED_API_KEY)
            data['real_yield'] = fred.get_series('DFII10').dropna().iloc[-1]
            data['inflation_exp'] = fred.get_series('T10YIE').dropna().iloc[-1]
            data['t10y2y'] = fred.get_series('T10Y2Y').dropna().iloc[-1]
            data['fed_funds'] = fred.get_series('FEDFUNDS').dropna().iloc[-1]
            data['pce'] = fred.get_series('PCEPI').dropna().iloc[-1]
        except Exception as e:
            print(f"FRED error: {e}")
            
    return data

def generate_geopolitical_analysis(d):
    dxy = d.get('dxy', 0)
    us10y = d.get('us10y', 0)
    real_yield = d.get('real_yield', 0)
    vix = d.get('vix', 0)
    oil = d.get('oil', 0)
    inflation_exp = d.get('inflation_exp', 0)
    usdt = d.get('usdt', 0)
    gold = d.get('gold', 0)

    usdt_text = f"`{usdt:,.0f} تومان`" if usdt > 0 else "نامشخص"

    report = (
        "🌐 **سیستم جامع تحلیل اقتصاد کلان، ژئوپلیتیک و بازار**\n\n"
        "📊 **۱. قیمت‌های لحظه‌ای بازار جهانی و داخلی:**\n"
        f"• انس طلا: `${gold:.2f}`\n"
        f"• شاخص دلار (DXY): `{dxy:.2f}`\n"
        f"• اوراق ۱۰ ساله آمریکا: `{us10y:.2f}%`\n"
        f"• نفت خام (WTI): `${oil:.2f}`\n"
        f"• شاخص ترس (VIX): `{vix:.2f}`\n"
        f"• تتر / دلار بازار ایران: {usdt_text}\n\n"
        "⚙️ **۲. پیش‌شاخص‌های بنیادین آمریکا (FRED):**\n"
        f"• بازده واقعی اوراق (DFII10): `{real_yield:.2f}%`\n"
        f"• انتظارات تورمی (T10YIE): `{inflation_exp:.2f}%`\n"
        f"• نرخ بهره فدز: `{d.get('fed_funds', 0):.2f}%`\n"
        f"• شاخص تورم PCE: `{d.get('pce', 0):.1f}`\n\n"
        "🌍 **۳. تحلیل ژئوپلیتیک کلان (تأثیر بر انس، دلار و تتر):**\n"
        "• *الان کجاست؟* تنش‌های منطقه‌ای و رقابت‌های تجاری قدرت‌های بزرگ، ریسک سیستمیک را در سطح بالا نگه داشته و تقاضا برای دارایی‌های امن را تقویت کرده است.\n"
        "• *چه بود؟* در دهه‌های گذشته شوک‌های عرضه‌ای و جنگ‌ها معمولاً موجب فرار سرمایه از بورس‌ها به سمت طلا و دلار می‌شدند.\n"
        "• *چه می‌شود؟* با بالا ماندن شاخص ترس (VIX) و تنش‌ها، هرگونه بحران ژئوپلیتیک جدید مستقیماً به عنوان سوخت فوری برای جهش **انس جهانی** و افزایش تقاضای پناهگاه امن برای **تتر و دلار داخلی** عمل می‌کند.\n\n"
        "🔍 **۴. بررسی تفکیکی گذاره‌ها (الان، گذشته، آینده):**\n\n"
        "🟡 **الف) انس جهانی طلا:**\n"
        "  • *الان چقدره؟* تحت تأثیر تقاضای بانک‌های مرکزی و تنش‌ها در محدوده‌های بالا نوسان دارد، اما بازده واقعی مثبت تا حدودی جلوی رشد بی‌منطق آن را گرفته است.\n"
        "  • *چه بود؟* در دوره‌های افت شدید نرخ بهره یا بحران‌های بزرگ بانکی، رشد انفجاری را تجربه کرد.\n"
        "  • *چه می‌شود؟* با شروع چرخه‌های کاهش نرخ بهره توسط فدز و تداوم ریسک‌های ژئوپلیتیک، پتانسیل شکستن سقف‌های تاریخی را دارد.\n\n"
        "💵 **ب) تتر و دلار در بازار ایران:**\n"
        "  • *الان چقدره؟* تابع مستقیم انتظارات تورمی داخلی، نوسانات نرخ ارز آزاد و قیمت انس جهانی است.\n"
        "  • *چه بود؟* همواره به عنوان ابزار پوشش ریسک (Hedge) در برابر افت ارزش ریال عمل کرده است.\n"
        "  • *چه می‌شود؟* با توجه به همبستگی مثبت با تورم داخلی و پتانسیل رشد انس، هرگونه تنش خارجی یا داخلی به سرعت روی قیمت تتر تأثیر صعودی می‌گذارد.\n\n"
        "📉 **ج) بازده واقعی اوراق و سیاست فدز (آمریکا):**\n"
        "  • *الان چقدره؟* بازده واقعی مثبت است که هزینه فرصت نگهداری طلا را بالا نگه داشته است.\n"
        "  • *چه بود؟* در دوران کرونا بازده واقعی عمیقاً منفی بود و طلا را به شدت بالا کشید.\n"
        "  • *چه می‌شود؟* اگر تورم چسبنده باقی بماند، فدز مجبور به حفظ نرخ‌های بالاست که به نفع دلار (DXY) و به ضرر مقطعی طلا خواهد بود."
    )
    return report

if __name__ == "__main__":
    market_data = fetch_all_macro_data()
    final_report = generate_geopolitical_analysis(market_data)
    print(final_report)
    send_telegram_msg(final_report)
