import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import plotly.graph_objects as go

# --- TEMA BIRU PASTEL & PUTIH ---
st.set_page_config(page_title="Oceanic Processor", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Quicksand', sans-serif; }
    .stApp { background-color: #F0F7FF; }
    .main-card { background-color: #FFFFFF; padding: 25px; border-radius: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    h1 { color: #5D9CEC; text-align: center; }
    .stButton>button { 
        background: linear-gradient(135deg, #A1C4FD 0%, #C2E9FB 100%); 
        border: none; border-radius: 10px; color: #444; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def low_pass_filter(data, cutoff_hours, sampling_interval_minutes):
    fs = 1 / (sampling_interval_minutes * 60)
    cutoff_hz = 1 / (cutoff_hours * 3600)
    nyq = 0.5 * fs
    normal_cutoff = cutoff_hz / nyq
    if normal_cutoff >= 1: normal_cutoff = 0.99
    b, a = butter(2, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, np.nan_to_num(data, nan=np.nanmean(data)))

st.markdown("<div class='main-card'>", unsafe_allow_html=True)
st.title("🌊 Ocean Data Processor")

uploaded_file = st.file_uploader("Drag & Drop File CSV/Excel di sini", type=["csv", "xlsx"])

if uploaded_file:
    # Mengakomodasi format titik koma (;) dari data observasi kamu
    try:
        df = pd.read_csv(uploaded_file, sep=';')
        if len(df.columns) < 2: df = pd.read_csv(uploaded_file)
    except:
        df = pd.read_excel(uploaded_file)

    st.success("Data berhasil masuk!")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        time_col = st.selectbox("Pilih Kolom Waktu", df.columns)
        data_col = st.selectbox("Pilih Kolom Data", [c for c in df.columns if c != time_col])
        
        # Hitung interval sampling otomatis
        try:
            df[time_col] = pd.to_datetime(df[time_col], dayfirst=True)
            diff = (df[time_col].iloc[1] - df[time_col].iloc[0]).total_seconds() / 60
        except:
            diff = 1 # Default 1 menit
            
        run = st.button("Proses Sekarang ✨")

    if run:
        res_df = df.copy()
        pts = int(60 / diff) # Baris per jam

        # Proses semua permintaan
        for h in [1, 3, 12, 25]: # Moving Average
            res_df[f'MA_{h}h'] = df[data_col].rolling(window=h*pts, center=True).mean()
        
        for h in [1, 3, 12, 24]: # Averaging
            res_df[f'AVG_{h}h'] = df[data_col].rolling(window=h*pts).mean()
            
        for h in [1, 3, 12, 25]: # Low Pass Filter
            res_df[f'LPF_{h}h'] = low_pass_filter(df[data_col].values, h, diff)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df[time_col], y=df[data_col], name="Asli", line=dict(color='#DDD')))
            fig.add_trace(go.Scatter(x=df[time_col], y=res_df['LPF_25h'], name="LPF 25h", line=dict(color='#5D9CEC')))
            st.plotly_chart(fig, use_container_width=True)

        st.download_button("Unduh Hasil (CSV)", res_df.to_csv(index=False).encode('utf-8'), "hasil_olahan.csv", "text/csv")
        st.dataframe(res_df.head())

st.markdown("</div>", unsafe_allow_html=True)
