## Gereksinimler

- Python 3.8+
- Microsoft Excel (yuklu ve calisir durumda)
- Windows veya macOS (xlwings Excel baglantisi icin gerekli)

## Kurulum

```bash
pip install -r requirements.txt
```

## Dosya Yapisi

```
vol/
  flask_app.py          # Flask sunucusu + Black-Scholes backend
  templates/
    index.html          # Dashboard arayuzu (client-side BS, Greeks, spread)
  1.csv                 # Opsiyon tanimlari (statik)
  vol.csv               # Piyasa volatiliteleri (harici guncelleme gerekli)
  fiyat.xlsx            # Canli fiyat kaynagi (Excel'de acik olmali)
  requirements.txt      # Python bagimliliklari
```

## Calistirma

```bash
python flask_app.py
```

Sunucu `http://localhost:8000` adresinde baslar ve tarayici otomatik acilir.

## Veri Dosyalari

### fiyat.xlsx — Canli Fiyat Kaynagi

**Bu dosya uygulama calisirken Microsoft Excel'de acik olmalidir.** Uygulama xlwings kutuphanesi ile acik olan Excel instance'ina baglanir ve her saniye A1:D100 araligini okur. Excel kapatilirsa veya dosya acik degilse dashboard hata verir.

| Sutun | Icerik |
|-------|--------|
| A | Varlik adi (ornek: `eurusd`, `xauusd`, `usdtry`) |
| B-C | (kullanilmiyor, formul/yardimci veri icin serbest) |
| D | Guncel fiyat |

- `usdtry` satiri zorunludur (TRY donusumu icin)
- Varlik adlari `1.csv`'deki `dayanak` degerleri ile eslesmeli (kucuk harf, bosluksuz)
- **Excel'de kaydetmeye gerek yok** — uygulama acik dosyadan anlik okur

### 1.csv — Varant Tanimlari

Statik dosya. Header satiri yok. Yeni varant eklemek veya mevcut varantlarin parametrelerini degistirmek icin bu dosya duzenlenir.

```
VarantAdi,dayanak,strike,vol,vade,carpan,tip
```

| Alan | Aciklama | Ornek |
|------|----------|-------|
| `ad` | Varant kodu | `AOIHC` |
| `dayanak` | Dayanak varlik (fiyat.xlsx'teki isimle eslesir) | `xagusd` |
| `strike` | Kullanim fiyati | `55` |
| `vol` | Volatilite (ondalik, 0.656 = %65.6) | `0.656` |
| `vade` | Vade tarihi (GG.AA.YYYY) | `27.02.2026` |
| `carpan` | Carpan (kontrat buyuklugu) | `0.02` |
| `tip` | `c` = Call, `p` = Put | `c` |

Ornek satir:
```
AOIHC,xagusd,55,0.656,27.02.2026,0.02,c
```

### vol.csv — Piyasa Volatiliteleri

**Bu dosya harici bir kaynak tarafindan duzenli araliklarla guncellenmelidir** . Uygulama her API cagrisinda bu dosyayi diskten yeniden okur, dolayisiyla dosya guncellendiginde dashboard otomatik olarak yeni verileri gosterir.

Format:
```
VarantAdi,MarketVol
```

- `VarantAdi` → `1.csv`'deki varant kodlari ile birebir eslesmeli
- `MarketVol` → Ondalik formatta (0.42389 = %42.39)
- Gruplar arasinda ayirici olarak tek `,` satiri kullanilabilir
- Dosya yoksa veya bos ise Market Vol sutunlari `-` gosterir

Ornek:
```
PPIEM,0.42389021
PPIEN,0.45331131
,
AAICY,0.85313113
AAICZ,0.67095215
```

## Dashboard Ozellikleri

### Tablo Sutunlari

| Sutun | Aciklama |
|-------|----------|
| Opsiyon | Varant kodu |
| Dayanak | Dayanak varlik |
| Strike | Kullanim fiyati |
| Tip | Call / Put |
| Spot Fiyat | Excel'den anlik okunan fiyat |
| Vade | Son kullanim tarihi |
| Volatilite | CSV'deki baz volatilite |
| Teorik Fiyat | Black-Scholes fiyati (TRY) |
| Spread (Kurus) | TL cinsinden spread ayari |
| Spread Vol (%) | Volatilite cinsinden spread ayari |
| Voldan Kr | Vol spread'in kurus karsiligi |
| Krden Vol | Kurus spread'in vol karsiligi |
| Ask IV | Nihai ask fiyatin zımni volatilitesi |
| Ask Fiyat | Spread eklenmiş nihai fiyat (TRY) |
| Market Vol | Piyasa volatilitesi (toggle ile acilir) |
| Vol Fark | Market Vol - Baz Vol farki, % puan (toggle ile acilir) |
| Delta | Varantin deltasi (toggle ile acilir) |
| Theta | Gunluk zaman kaybi, TRY/gun (toggle ile acilir) |

### Toggle Butonlari

- **Market Vol** → Market Vol ve Vol Fark sutunlarini acar/kapatir
- **Greeks** → Delta ve Theta sutunlarini acar/kapatir

### Vol Fark Renklendirme

- **Kirmizi (pozitif)**: Market vol > mevcut vol
- **Yesil (negatif)**: Market vol < mevcut vol

### Spread Sistemi

Her varant icin iki bagimsiz spread ayari vardir:

1. **Spread (Kurus)**: Teorik fiyata dogrudan TRY kurus ekleme/cikarma
2. **Spread Vol (%)**: Volatiliteye yuzde puan ekleme, fiyat yeniden hesaplanir

**Toplu Spread**: Filtre uygulandiktan sonra "Uygula" ile gorunen tum varantlara ayni spread verilir.

**Breakeven**: Market Vol > Baz Vol olan opsiyonlarda, farki otomatik olarak Spread Vol'e yazar. Opsiyonu piyasa fiyatina esitler.

### Siralama

Tum sutun basliklari tiklanabilir. Ayni sutuna tekrar tiklamak yonu tersine cevirir. Delta sutunu mutlak degere gore siralanir.

### Filtreler

- **Dayanak Varlik**: eurusd, xauusd, xagusd, spx, vb.
- **Tip**: Call / Put
- **Vade**: Vade tarihine gore

## Hesaplama Detaylari

### Black-Scholes (Generalized, r=0)

```
d1 = [ln(S/K) + (b + 0.5*sigma^2)*T] / (sigma*sqrt(T))
d2 = d1 - sigma*sqrt(T)

Call = S*exp((b-r)*T)*N(d1) - K*exp(-r*T)*N(d2)
Put  = K*exp(-r*T)*N(-d2) - S*exp((b-r)*T)*N(-d1)
```

- `r = 0` (risksiz faiz orani)
- `b = 0` (cogu varlik icin)
- `b = -rho * sigma * sigmaFX` (xauusd quanto icin, rho=-0.15, sigmaFX=0.4)

### Greeks

```
Delta Call = exp(b*T) * N(d1)
Delta Put  = exp(b*T) * (N(d1) - 1)

Theta (yillik) = -S*exp(b*T)*n(d1)*sigma/(2*sqrt(T)) -/+ b*S*exp(b*T)*N(d1)
Theta (gunluk TRY) = (Theta_yillik / 365) * kurCarpan
```

### Ask Fiyat Hesabi

1. Vol spread ekle: `newSigma = bazVol + (spreadVol / 100)`
2. Black-Scholes'u yeni sigma ile hesapla (USD)
3. TRY'ye cevir: `fiyatTRY = fiyatUSD * kur * carpan`
4. Kurus spread ekle: `askFiyat = fiyatTRY + (spreadKurus / 100)`

### Implied Volatility

Bisection metodu ile ters hesaplama. Aralik: %0-%500, tolerans: 0.0001, maks iterasyon: 20.

## Sik Karsilasilan Hatalar ve Cozumleri

### "Excel'e baglanamadi. 'fiyat.xlsx' acik mi?"

**Sebep**: `fiyat.xlsx` dosyasi Excel'de acik degil veya Excel yuklu degil.

**Cozum**:
- `fiyat.xlsx` dosyasini Microsoft Excel ile acin (LibreOffice/Google Sheets desteklenmez)
- Excel'in tamamen yuklenmesini bekleyin, sonra `python flask_app.py` calistirin
- Birden fazla Excel penceresi aciksa, `fiyat.xlsx`'in acik oldugu instance'i kontrol edin

### "1.csv dosyasi okunamadi veya format hatali"

**Sebep**: `1.csv` dosyasi bulunamadi veya format bozuk.

**Cozum**:
- `1.csv`'nin `flask_app.py` ile ayni klasorde oldugunu dogrulayin
- Dosyanin header satiri **olmamali** (ilk satir dogrudan veri)
- Vade formati `GG.AA.YYYY` olmali (ornek: `27.02.2026`)
- Virgullerden sonra bosluk **olmamali**

### "Sunucuyla baglanti kurulamadi"

**Sebep**: Flask sunucusu calismiyor veya port 8000 mesgul.

**Cozum**:
- Terminal'de `python flask_app.py` calistigini dogrulayin
- Port 8000 mesgulse, baska bir terminal'de calistirilmis eski bir instance olabilir — onu kapatin
- Windows Firewall uyarisi cikarsa "izin ver" secin

### Spot fiyat 0.0000 gorunuyor

**Sebep**: `fiyat.xlsx`'teki varlik adi ile `1.csv`'deki `dayanak` alani eslesmiyor.

**Cozum**:
- `fiyat.xlsx` A sutunundaki isimler kucuk harfle `1.csv`'deki dayanak degerlerine esmeli
- Ornek: CSV'de `eurusd` yaziyorsa Excel'de de `eurusd` olmali (bosluk/buyuk harf farki olmamali)
- Fiyatin D sutununda oldugunu kontrol edin (B veya C sutunu okunmaz)

### Market Vol sutunu hep "-" gosteriyor

**Sebep**: `vol.csv` dosyasi yok, bos veya varant kodlari eslesmiyor.

**Cozum**:
- `vol.csv`'nin proje klasorunde oldugunu dogrulayin
- Varant kodlarinin `1.csv`'deki `ad` alani ile **birebir ayni** oldugunu kontrol edin (buyuk/kucuk harf dahil)
- `vol.csv` harici bir surec tarafindan guncellenmeli — uygulama bu dosyayi kendisi **olusturmaz**

### Greeks degerleri 0 gosteriyor

**Sebep**: Opsiyon vadesi gecmis (T <= 0) veya volatilite 0.

**Cozum**:
- `1.csv`'deki vade tarihinin gelecekte oldugunu kontrol edin
- Volatilite degerinin 0'dan buyuk oldugunu dogrulayin

### Sayfa cok yavas / donuyor

**Sebep**: Cok fazla varant satiri (500+) ile her saniye DOM yenilenmesi.

**Cozum**:
- Filtreleri kullanarak gorunen satir sayisini azaltin (dayanak, tip veya vade filtresi)
- Tarayicinin gelistirici konsolunda hata olup olmadigini kontrol edin
