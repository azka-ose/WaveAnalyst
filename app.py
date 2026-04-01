import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import plotly.graph_objects as go

# --- CONFIG & CUTE THEME ---
st.set_page_config(page_title="Oceanic Blue Processor", layout="wide", page_icon="🌊")

# CSS untuk gaya Biru Pastel & Putih (Perbaikan: unsafe_allow_html=True)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
    }
    .stApp {
        background-color: #F0F7FF;
    }
    .main-card {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 25px;
        box-shadow: 0 8px 30px rgba(173, 216, 230, 0.3);
        margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #A1C4FD 0%, #C2E9FB 100%);
        color: #4A4A4A;
        border: none;
        border-radius: 15px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(161, 196, 253, 0.4);
    }
    h1 { color: #5D9CEC; text-align: center; margin-bottom: 20px; }
    h3 { color: #7DBBE6; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI FILTER ---
def low_pass_filter(data, cutoff_hours, sampling_interval_minutes):
    fs = 1 / (sampling_interval_minutes * 60)
    cutoff_hz = 1 / (cutoff_hours * 3600)
    nyq = 0.5 * fs
    normal_cutoff = cutoff_hz / nyq
    
    if normal_cutoff >= 1: normal_cutoff = 0.99
    
    b, a = butter(2, normal_cutoff, btype='low', analog=False)
    data_clean = np.nan_to_num(data, nan=np.nanmean(data))
    return filtfilt(b, a, data_clean)

# --- UI CONTENT ---
st.markdown("<div class='main-card'>", unsafe_allow_html=True)
st.title("🌊 Ocean Wave Data Toolkit")
st.write("Dibuat khusus untuk pengolahan data water level Azka. Silakan drag file CSV kamu!")

uploaded_file = st.file_uploader("Upload file observasi (CSV/XLSX)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Menangani pemisah titik koma (;) sesuai file kamu
        df = pd.read_csv(uploaded_file, sep=';')
        if len(df.columns) < 2:
            df = pd.read_csv(uploaded_file)
    except:
        df = pd.read_excel(uploaded_file)

    # Bersihkan nama kolom jika ada string kosong atau Unnamed
    df.columns = [c if not c.startswith('Unnamed') else 'Datetime' for c in df.columns]

    st.success("Data berhasil masuk! ✨")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("⚙️ Settings")
        time_col = st.selectbox("Kolom Waktu:", df.columns)
        data_col = st.selectbox("Kolom Data:", [c for c in df.columns if c != time_col])
        
        try:
            df[time_col] = pd.to_datetime(df[time_col], dayfirst=True)
            diff = (df[time_col].iloc[1] - df[time_col].iloc[0]).total_seconds() / 60
            st.info(f"Interval: {diff:.0f} menit")
        except:
            diff = 1

        process_all = st.button("Proses Semua Filter ✨")

    if process_all:
        res_df = df.copy()
        data_values = df[data_col].values
        points_per_hour = int(60 / diff)

        # 1. Moving Average (1, 3, 12, 25h)
        for h in [1, 3, 12, 25]:
            win = h * points_per_hour
            res_df[f'MA_{h}h'] = df[data_col].rolling(window=win, center=True).mean()

        # 2. Averaging (1, 3, 12, 24h)
        for h in [1, 3, 12, 24]:
            win = h * points_per_hour
            res_df[f'AVG_{h}h'] = df[data_col].rolling(window=win).mean()

        # 3. Low Pass Filter (1, 3, 12, 25h)
        for h in [1, 3, 12, 25]:
            res_df[f'LPF_{h}h'] = low_pass_filter(data_values, h, diff)

        with col2:
            st.subheader("📊 Preview Grafik")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df[time_col], y=df[data_col], name="Asli", line=dict(color='#E0E0E0', width=1)))
            fig.add_trace(go.Scatter(x=df[time_col], y=res_df['LPF_25h'], name="LPF 25h (Bersih)", line=dict(color='#5D9CEC', width=2)))
            fig.update_layout(template="plotly_white", height=450)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📥 Hasil Akhir")
        st.dataframe(res_df.head(10))
        
        csv = res_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Terproses 📩", data=csv, file_name='processed_data_ocean.csv', mime='text/csv')

else:
    st.info("Upload file kamu dulu ya! 🌸")

st.markdown("</div>", unsafe_allow_html=True)
