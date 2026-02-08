import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime
import time
import xlwings as xw

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

# --- Sayfa Yapılandırması ---
st.set_page_config(page_title="Canlı Opsiyon Takip", layout="wide")
st.title("⚡ Excel'den Canlı Veri Akışı (Kaydetme Gerektirmez)")

# CSV verisini bir kez yükle
@st.cache_data
def load_csv_data():
    cols = ['ad', 'dayanak', 'strike', 'vol', 'vade', 'carpan', 'tip']
    df = pd.read_csv('1.csv', names=cols, header=None)
    df['vade'] = pd.to_datetime(df['vade'], format='%d.%m.%Y')
    return df

placeholder = st.empty()

# Excel'e bağlanma (Uygulama açık olmalı)
try:
    # fiyat.xlsx dosyasına bağlan. Dosya açıksa ona kancalanır.
    wb = xw.Book('fiyat.xlsx')
    sheet = wb.sheets[0] # İlk sayfayı al
except Exception as e:
    st.error(f"Excel dosyasına bağlanılamadı. Lütfen 'fiyat.xlsx' dosyasının açık olduğundan emin olun. Hata: {e}")
    st.stop()

while True:
    try:
        df_opsiyon = load_csv_data()
        
        # Excel'den A ve D sütunlarını "Canlı" oku (Max 100 satır tarar, ihtiyaca göre artırabilirsin)
        # A1:D100 aralığını alıp Python listesine çeviriyoruz
        raw_data = sheet.range("A1:D100").value 
        
        # Veriyi sözlüğe çevir (Hızlı arama için)
        fiyat_dict = {}
        for row in raw_data:
            if row[0] and row[3] is not None: # A sütunu dolu ve D sütunu sayıysa
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
            
            T = (row['vade'] - now).total_seconds() / (365.25 * 24 * 3600)
            if T < 0: T = 0
            
            fiyat_usd = black_scholes_r0(S, K, T, sigma, opt_type)
            toplam_trl = fiyat_usd * usdtry * carpan
            
            results.append({
                "Opsiyon": row['ad'],
                "Dayanak": row['dayanak'],
                "Spot Fiyat": f"{S:.4f}",
                "Vade": row['vade'].strftime('%d.%m.%Y'),
                "Birim USD": f"{fiyat_usd:.4f}",
                "Kur": f"{usdtry:.4f}",
                "Toplam Değer (TRL)": f"{toplam_trl:.2f} ₺"
            })

        with placeholder.container():
            st.success(f"Bağlantı Aktif | Son Güncelleme: {now.strftime('%H:%M:%S')}")
            st.table(pd.DataFrame(results))
            
        time.sleep(0.5) # Yarım saniyede bir güncelle
        
    except Exception as e:
        st.warning(f"Veri okunurken bir aksama oldu: {e}")
        time.sleep(1)