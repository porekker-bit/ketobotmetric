import streamlit as st
import pandas as pd
import altair as alt
import datetime

# Konfigurasi Halaman
st.set_page_config(
    page_title="KetoBot Dashboard",
    page_icon="📊",
    layout="wide"
)

# Styling CSS biar tampilannya clean
st.markdown("""
    <style>
        .main {
            background-color: #f4f6f9;
        }
    </style>
""", unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSxudsJuAdIH9LyEL-hYQK4CNOkulrtUaYUMMSdAxaoURF4aVBBlaMHsA4bJRffBTl9c677YgkTDu-s/pub?gid=1057472349&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    return df

try:
    df = load_data()

    # --- HEADER ---
    st.title("KetoBot Dashboard")
    st.markdown("---")

    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.subheader("Overview Log Analitik")
    with col_head2:
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

    # --- LAYOUT UTAMA: GRAFIK & TABEL (3 KOLOM) ---
    col1, col2, col3 = st.columns(3)

    # 1. Kolom Kiri: Distribusi Jenis Input User (Horizontal Bar Chart via Altair)
    with col1:
        st.markdown("### Distribusi Jenis Input User")
        if 'Input_Type' in df.columns:
            input_counts = df['Input_Type'].value_counts().reset_index()
            input_counts.columns = ['Input_Type', 'Count']
            
            # Buat grafik horizontal pakai Altair
            chart_input = alt.Chart(input_counts).mark_bar(color='#2b7de9').encode(
                x=alt.X('Count:Q', title='Jumlah'),
                y=alt.Y('Input_Type:N', sort='-x', title='Jenis Input')
            ).properties(height=300)
            
            st.altair_chart(chart_input, use_container_width=True)
        else:
            st.info("Kolom 'Input_Type' tidak ditemukan.")

    # 2. Kolom Tengah: Top User Actions (Horizontal Bar Chart)
    with col2:
        st.markdown("### Top User Actions")
        if 'User_Action' in df.columns:
            action_counts = df['User_Action'].value_counts().head(10).reset_index()
            action_counts.columns = ['User_Action', 'Count']
            
            chart_action = alt.Chart(action_counts).mark_bar(color='#8c6239').encode(
                x=alt.X('Count:Q', title='Jumlah'),
                y=alt.Y('User_Action:N', sort='-x', title='User Action')
            ).properties(height=300)
            
            st.altair_chart(chart_action, use_container_width=True)
        else:
            st.info("Kolom 'User_Action' tidak ditemukan.")

    # 3. Kolom Kanan: Top Unrecognized Queries (Tabel)
    with col3:
        st.markdown("### Top Unrecognized Queries")
        if 'User_Action' in df.columns:
            unrecognized = df[df['User_Action'].str.contains("UNRESOLVED|EMOJI|STICKER|UNRECOGNIZED", case=False, na=False)]
            if not unrecognized.empty:
                summary_unrec = unrecognized['User_Action'].value_counts().reset_index()
                summary_unrec.columns = ['User_Action', 'Record Count']
                st.dataframe(summary_unrec, use_container_width=True, hide_index=True)
            else:
                st.dataframe(df.tail(3)[['User_Action']], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df.tail(3), use_container_width=True)

except Exception as e:
    st.error(f"Gagal memuat atau memproses data: {e}")
