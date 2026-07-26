import streamlit as st
import pandas as pd

st.set_page_config(page_title="Last Execution Dashboard", layout="wide")

st.title("🚀 Last Execution Monitoring")
st.write("Data log real-time dari Google Sheets")

# Ganti link CSV Google Sheets kamu di bawah ini (Pastikan sheet sudah di-publish to web as CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSxudsJuAdIH9LyEL-hYQK4CNOkulrtUaYUMMSdAxaoURF4aVBBlaMHsA4bJRffBTl9c677YgkTDu-s/pub?gid=1057472349&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    return df

try:
    df = load_data()
    
    # Tampilkan metric/tabel ringkas
    st.subheader("Data Eksekusi Terakhir")
    st.dataframe(df.tail(1), use_container_width=True)
    
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
