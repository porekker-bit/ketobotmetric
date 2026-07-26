import streamlit as st
import pandas as pd
import datetime

# Konfigurasi Halaman (Lebar & Judul)
st.set_page_config(
    page_title="KetoBot Dashboard",
    page_icon="📊",
    layout="wide"
)

# Styling CSS biar tampilannya clean ala dashboard profesional
st.markdown("""
    <style>
        .main {
            background-color: #f4f6f9;
        }
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# Ganti link CSV Google Sheets kamu di sini
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSxudsJuAdIH9LyEL-hYQK4CNOkulrtUaYUMMSdAxaoURF4aVBBlaMHsA4bJRffBTl9c677YgkTDu-s/pub?gid=1057472349&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    # Ubah kolom timestamp/tanggal ke format datetime jika ada (sesuaikan nama kolomnya)
    # Contoh kolom mengasumsikan ada 'Timestamp' atau 'Date'
    return df

try:
    df = load_data()

    # --- HEADER & FILTER TANGGAL DI SIDEBAR / ATAS ---
    st.title("KetoBot Dashboard")
    st.markdown("---")

    # Layout atas: Judul dan Filter Tanggal
    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.subheader("Overview Log Analitik")
    with col_head2:
        # Simulasi rentang tanggal (bisa disesuaikan jika kolom tanggal tersedia)
        date_range = st.date_input(
            "Filter Periode",
            value=(datetime.date.today() - datetime.timedelta(days=7), datetime.date.today())
        )

    # --- KARTU METRIK: Total Interaction ---
    total_interaction = len(df)
    
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns([1, 2, 2])
    with m1:
        st.metric(label="Total Interaction", value=f"{total_interaction:,}")

    st.markdown("---")

    # --- LAYOUT UTAMA: GRAFIK & TABEL (3 KOLOM SEPERTI REFERENSI) ---
    col1, col2, col3 = st.columns(3)

    # 1. Kolom Kiri: Distribusi Jenis Input User (Pie/Bar Chart)
    with col1:
        st.markdown("### Distribusi Jenis Input User")
        if 'Input_Type' in df.columns:
            input_counts = df['Input_Type'].value_counts()
            st.bar_chart(input_counts)  # Streamlit native chart yang super cepat & interaktif
        else:
            st.info("Kolom 'Input_Type' tidak ditemukan di Sheet.")

    # 2. Kolom Tengah: Top User Actions
    with col2:
        st.markdown("### Top User Actions")
        if 'User_Action' in df.columns:
            action_counts = df['User_Action'].value_counts().head(10)
            st.bar_chart(action_counts, horizontal=True)
        else:
            st.info("Kolom 'User_Action' tidak ditemukan di Sheet.")

    # 3. Kolom Kanan: Top Unrecognized Queries (Tabel)
    with col3:
        st.markdown("### Top Unrecognized Queries")
        # Contoh filter jika ada unhandled/unrecognized intent
        if 'User_Action' in df.columns:
            unrecognized = df[df['User_Action'].str.contains("UNRESOLVED|EMOJI|STICKER|UNRECOGNIZED", case=False, na=False)]
            if not unrecognized.empty:
                summary_unrec = unrecognized['User_Action'].value_counts().reset_index()
                summary_unrec.columns = ['User_Action', 'Record Count']
                st.dataframe(summary_unrec, use_container_width=True, hide_index=True)
            else:
                # Fallback data dummy/tabel ringkas jika data spesifik belum ada
                st.dataframe(df.tail(3)[['User_Action']], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df.tail(3), use_container_width=True)

except Exception as e:
    st.error(f"Gagal memuat atau memproses data: {e}")
