# 🌊 WaveAnalyst

Web app berbasis **Python + Flask** untuk analisis sinyal data time series (water level, sensor, dll).

## ✨ Fitur
- **Moving Average**: 1 jam, 3 jam, 12 jam, 24 jam, 25 jam
- **Time Averaging** (resample): 1 jam, 3 jam, 12 jam, 24 jam
- **Low-Pass Filter** (Butterworth orde 4): 1 jam, 3 jam, 12 jam, 24 jam, 25 jam
- Drag & drop file upload (CSV, Excel, TXT)
- Visualisasi interaktif dengan Chart.js
- Export hasil ke CSV
- Tampilan biru pastel yang lucu 🎨

## 🚀 Cara Menjalankan

### 1. Clone & Install
```bash
git clone https://github.com/username/waveanalyst.git
cd waveanalyst
pip install -r requirements.txt
```

### 2. Jalankan
```bash
python app.py
```

### 3. Buka browser
```
http://localhost:5000
```

## 📁 Format File yang Didukung
- **CSV / TXT**: kolom pertama = datetime, kolom kedua = nilai. Separator bisa `;` `,` atau `\t`
- **Excel (.xlsx/.xls)**: sheet pertama, baris pertama = header

Contoh format CSV yang didukung:
```
13/02/2026 08:09;348.6
13/02/2026 08:10;343.2
```

## 🗂️ Struktur Project
```
waveanalyst/
├── app.py               # Flask backend
├── requirements.txt     # Dependencies
├── templates/
│   └── index.html       # Frontend (HTML + JS + CSS)
└── README.md
```

## 📦 Dependencies
- Flask
- Pandas
- NumPy
- SciPy
- OpenPyXL (untuk Excel)

## 📤 Deploy ke GitHub
```bash
git init
git add .
git commit -m "🌊 Initial commit: WaveAnalyst"
git branch -M main
git remote add origin https://github.com/username/waveanalyst.git
git push -u origin main
```

---
Made with 💙 Python + Flask + Chart.js
