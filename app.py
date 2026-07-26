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

# Styling CSS tambahan
st.markdown("""
    <style>
        .main {
            background-color: #f4f6f9;
        }
        .metric-box {
            background-color: #ffeb99;
            padding: 15px;
            border-radius: 8px;
            color: #333;
            font-family: monospace;
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

    # --- BARIS ATAS: KARTU METRIK TOTAL ---
    total_interaction = len(df)
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns([1, 2, 2])
    with m1:
        st.metric(label="Total Interaction", value=f"{total_interaction:,}")

    st.markdown("---")

    # --- BARIS 1: 3 KOLOM UTAMA SEBELUMNYA ---
    col1, col2, col3 = st.columns(3)

    # 1. Distribusi Jenis Input User
    with col1:
        st.markdown("### Distribusi Jenis Input User")
        if 'Input_Type' in df.columns:
            input_counts = df['Input_Type'].value_counts().reset_index()
            input_counts.columns = ['Input_Type', 'Count']
            chart_input = alt.Chart(input_counts).mark_bar(color='#2b7de9').encode(
                x=alt.X('Count:Q', title='Jumlah'),
                y=alt.Y('Input_Type:N', sort='-x', title='Jenis Input')
            ).properties(height=280)
            st.altair_chart(chart_input, use_container_width=True)
        else:
            st.info("Kolom 'Input_Type' tidak ditemukan.")

    # 2. Top User Actions
    with col2:
        st.markdown("### Top User Actions")
        if 'User_Action' in df.columns:
            action_counts = df['User_Action'].value_counts().head(10).reset_index()
            action_counts.columns = ['User_Action', 'Count']
            chart_action = alt.Chart(action_counts).mark_bar(color='#8c6239').encode(
                x=alt.X('Count:Q', title='Jumlah'),
                y=alt.Y('User_Action:N', sort='-x', title='User Action')
            ).properties(height=280)
            st.altair_chart(chart_action, use_container_width=True)
        else:
            st.info("Kolom 'User_Action' tidak ditemukan.")

    # 3. Top Unrecognized Queries
    with col3:
        st.markdown("### Top Unrecognized Queries")
        if 'User_Action' in df.columns:
            unrecognized = df[df['User_Action'].str.contains("UNRESOLVED|EMOJI|STICKER|UNRECOGNIZED", case=False, na=False)]
            if not unrecognized.empty:
                summary_unrec = unrecognized['User_Action'].value_counts().reset_index()
                summary_unrec.columns = ['User_Action', 'Record Count']
                st.dataframe(summary_unrec, use_container_width=True, height=280, hide_index=True)
            else:
                st.dataframe(df.tail(3)[['User_Action']], use_container_width=True, height=280, hide_index=True)
        else:
            st.dataframe(df.tail(3), use_container_width=True, height=280)

    st.markdown("---")

    # --- BARIS KEDUA (TAMBAHAN SESUAI REFERENSI BARU) ---
    st.markdown("### Analisis Performa & Eksekusi Lanjutan")
    b_col1, b_col2, b_col3 = st.columns([1.5, 1.5, 1])

    # 1. Avg. Response Time by User Action
    with b_col1:
        st.markdown("##### Avg. Response Time by User Action")
        if 'User_Action' in df.columns and 'Response_Time_MS' in df.columns:
            avg_resp = df.groupby('User_Action')['Response_Time_MS'].mean().reset_index()
            avg_resp = avg_resp.sort_values(by='Response_Time_MS', ascending=False).head(10)
            
            chart_resp = alt.Chart(avg_resp).mark_bar(color='#52b788').encode(
                x=alt.X('Response_Time_MS:Q', title='Response Time (ms)'),
                y=alt.Y('User_Action:N', sort='-x', title='')
            ).properties(height=300)
            st.altair_chart(chart_resp, use_container_width=True)
        else:
            st.info("Kolom waktu respons tidak lengkap.")

    # 2. Perbandingan FE vs BE Time (Simulasi/Kolom terkait)
    with b_col2:
        st.markdown("##### FE Time vs BE Time")
        # Mengecek apakah ada kolom latensi FE/BE, jika tidak pakai AI_Latency / Response_Time sebagai simulasi
        if 'AI_Latency_MS' in df.columns and 'Response_Time_MS' in df.columns:
            df['FE_Time'] = df['Response_Time_MS'] - df['AI_Latency_MS']
            df['BE_Time'] = df['AI_Latency_MS']
            
            lat_summary = df.tail(10)[['FE_Time', 'BE_Time']].reset_index()
            lat_melted = lat_summary.melt(id_vars=['index'], value_vars=['FE_Time', 'BE_Time'], var_name='Type', value_name='Time')
            
            chart_lat = alt.Chart(lat_melted).mark_bar().encode(
                x=alt.X('Time:Q', title='ms'),
                y=alt.Y('index:O', title='Record'),
                color=alt.Color('Type:N', scale=alt.Scale(domain=['FE_Time', 'BE_Time'], range=['#3b82f6', '#22c55e']))
            ).properties(height=300)
            st.altair_chart(chart_lat, use_container_width=True)
        else:
            st.info("Data FE/BE Latency belum tersedia.")

    # 3. Last Execution Card (Kotak Kuning Ringkas)
    with b_col3:
        st.markdown("##### Last Execution")
        latest = df.tail(1).iloc[0]
        
        # Ambil nilai aman dari row terakhir
        lat_menu = latest.get('Query_Menu', '-')
        lat_resp = latest.get('Response_Time_MS', 0)
        lat_ai = latest.get('AI_Latency_MS', 0)
        
        st.markdown(f"""
            <div class="metric-box">
                <b>Jumlah :</b> {total_interaction} Menu<br>
                <b>Waktu :</b> {datetime.datetime.now().strftime('%d %b %Y, %H:%M')}<br>
                <b>FE (ms) :</b> {lat_resp}<br>
                <b>BE (ms) :</b> {lat_ai}
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Gagal memuat atau memproses data: {e}")
