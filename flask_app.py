from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime
import xlwings as xw
import pythoncom
import webbrowser
import threading
import time

app = Flask(__name__)

# --- Black-Scholes Hesaplama (r=0) ---
def black_scholes_r0(S, K, T, sigma, option_type='call'):
    if T <= 0: 
        return max(0, S - K) if option_type == 'call' else max(0, K - S)
    
    d1 = (np.log(S / K) + (0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        return S * norm.cdf(d1) - K * norm.cdf(d2)
    else:
        return K * norm.cdf(-d2) - S * norm.cdf(-d1)

def load_csv_data():
    try:
        cols = ['ad', 'dayanak', 'strike', 'vol', 'vade', 'carpan', 'tip']
        df = pd.read_csv('1.csv', names=cols, header=None)
        df['vade'] = pd.to_datetime(df['vade'], format='%d.%m.%Y')
        return df
    except Exception as e:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    # Flask sunucusu thread içinde çalıştığı için COM başlatma gerekebilir
    pythoncom.CoInitialize()
    
    try:
        # CSV Yükle
        df_opsiyon = load_csv_data()
        if df_opsiyon is None:
            return jsonify({'error': '1.csv dosyası okunamadı veya format hatalı.'})

        # Excel'den Veri Çek
        try:
            # Aktif Excel instance'ına bağlan
            wb = xw.Book('fiyat.xlsx')
            sheet = wb.sheets[0]
            # A1:D100 aralığını al
            raw_data = sheet.range("A1:D100").value 
        except Exception as e:
            return jsonify({'error': f"Excel'e bağlanılamadı. 'fiyat.xlsx' açık mı? ({str(e)})"})

        # Veriyi sözlüğe çevir
        fiyat_dict = {}
        for row in raw_data:
            if row[0] and row[3] is not None:
                fiyat_dict[str(row[0]).strip().lower()] = float(row[3])
        
        usdtry = fiyat_dict.get('usdtry', 1.0)
        now = datetime.now()
        results = []

        for _, row in df_opsiyon.iterrows():
            dayanak_adi = str(row['dayanak']).strip().lower()
            S = fiyat_dict.get(dayanak_adi, 0.0)
            K = row['strike']
            sigma = row['vol']
            carpan = row['carpan']
            opt_type = 'call' if str(row['tip']).strip().lower() == 'c' else 'put'
            
            T = (row['vade'] - now).days / 365
            if T < 0: T = 0
            
            fiyat_usd = black_scholes_r0(S, K, T, sigma, opt_type)
            toplam_trl = fiyat_usd * usdtry * carpan
            
            results.append({
                "Opsiyon": row['ad'],
                "Dayanak": row['dayanak'],
                "Tip": "Call" if opt_type == 'call' else "Put",
                "Spot Fiyat": f"{S:.4f}",
                "Vade": row['vade'].strftime('%d.%m.%Y'),
                "Volatilite": f"{sigma*100:.2f}%",
                "VolatiliteRaw": sigma,
                "Fiyat": f"{toplam_trl:.2f} ₺",
                "FiyatRaw": toplam_trl,
                "Strike": K,
                "Carpan": carpan,
                "Kur": usdtry,
                "T": T
            })
            
        return jsonify({
            'timestamp': now.strftime('%H:%M:%S'),
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)})

def open_browser():
    time.sleep(1) # Sunucunun başlaması için kısa bir bekleme
    webbrowser.open("http://localhost:8000")

if __name__ == '__main__':
    # Tarayıcıyı ayrı bir thread'de aç
    threading.Thread(target=open_browser).start()
    # Debug modu kapalı, port 8000
    app.run(debug=False, port=8000)