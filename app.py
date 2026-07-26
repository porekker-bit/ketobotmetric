import streamlit as st
import pandas as pd
import altair as alt
import datetime
import requests
import json
import re

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

# URL GIST yang benar (mengarah ke raw Gist langsung)
GIST_URL = "https://gist.githubusercontent.com/porekker-bit/af3570b588cf74d97e230b8c51c0a255/raw"

@st.cache_data(ttl=60)
def load_sheet_url_from_gist():
    try:
        response = requests.get(GIST_URL)
        if response.status_code == 200:
            config = response.json()
            return config.get("DS")
    except Exception:
        pass
    # Fallback default URL jika GIST gagal diakses
    return "https://docs.google.com/spreadsheets/d/e/2PACX-1vSxudsJuAdIH9LyEL-hYQK4CNoKu1rtUaYUMMSdAxaoURF4aVBBlaMHsA4bJRffBTl9c677YgkTDu-s/pub?gid=1057472349&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(sheet_url):
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()
    return df

try:
    # Ambil URL Sheet dinamis dari GIST (key: "DS")
    SHEET_URL = load_sheet_url_from_gist()
    df_raw = load_data(SHEET_URL)

    # --- HEADER & FILTER PERIODE ---
    st.title("KetoBot Dashboard")
    st.markdown("---")

    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.subheader("Overview Log Analitik")
    with col_head2:
        # Konversi kolom Timestamp ke datetime untuk keperluan filter
        if 'Timestamp' in df_raw.columns:
            df_raw['Parsed_Date'] = pd.to_datetime(df_raw['Timestamp'], format='mixed', errors='coerce')
            min_date = df_raw['Parsed_Date'].min().date() if not df_raw['Parsed_Date'].isna().all() else (datetime.date.today() - datetime.timedelta(days=30))
            max_date = df_raw['Parsed_Date'].max().date() if not df_raw['Parsed_Date'].isna().all() else datetime.date.today()
        else:
            min_date = datetime.date.today() - datetime.timedelta(days=7)
            max_date = datetime.date.today()

        date_range = st.date_input(
            "Filter Periode",
            value=(min_date, max_date)
        )

    # Filter DataFrame berdasarkan tanggal yang dipilih di widget
    df = df_raw.copy()
    if 'Parsed_Date' in df.columns and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['Parsed_Date'].dt.date >= start_date) & (df['Parsed_Date'].dt.date <= end_date)]

    # --- BARIS ATAS: KARTU METRIK TOTAL (Terfilter) ---
    total_interaction = len(df)
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns([1, 2, 2])
    with m1:
        st.metric(label="Total Interaction", value=f"{total_interaction:,}")

    st.markdown("---")

    # --- BARIS 1: 3 KOLOM UTAMA ---
    col1, col2, col3 = st.columns(3)

    # 1. Distribusi Jenis Input User
    with col1:
        st.markdown("### Distribusi Jenis Input User")
        if 'Input_Type' in df.columns and not df.empty:
            input_counts = df['Input_Type'].value_counts().reset_index()
            input_counts.columns = ['Input_Type', 'Count']
            chart_input = alt.Chart(input_counts).mark_bar(color='#2b7de9').encode(
                x=alt.X('Count:Q', title='Jumlah'),
                y=alt.Y('Input_Type:N', sort='-x', title='Jenis Input')
            ).properties(height=280)
            st.altair_chart(chart_input, use_container_width=True)
        else:
            st.info("Tidak ada data pada periode ini.")

    # 2. Top User Actions
    with col2:
        st.markdown("### Top User Actions")
        if 'User_Action' in df.columns and not df.empty:
            action_counts = df['User_Action'].value_counts().head(10).reset_index()
            action_counts.columns = ['User_Action', 'Count']
            chart_action = alt.Chart(action_counts).mark_bar(color='#8c6239').encode(
                x=alt.X('Count:Q', title='Jumlah'),
                y=alt.Y('User_Action:N', sort='-x', title='User Action')
            ).properties(height=280)
            st.altair_chart(chart_action, use_container_width=True)
        else:
            st.info("Tidak ada data pada periode ini.")

    # 3. Top Unrecognized Queries
    with col3:
        st.markdown("### Top Unrecognized Queries")
        if 'User_Action' in df.columns and not df.empty:
            unrecognized = df[df['User_Action'].str.contains("UNRESOLVED|EMOJI|STICKER|UNRECOGNIZED", case=False, na=False)]
            if not unrecognized.empty:
                summary_unrec = unrecognized['User_Action'].value_counts().reset_index()
                summary_unrec.columns = ['User_Action', 'Record Count']
                st.dataframe(summary_unrec, use_container_width=True, height=280, hide_index=True)
            else:
                st.dataframe(df.tail(3)[['User_Action']] if not df.empty else pd.DataFrame(), use_container_width=True, height=280, hide_index=True)
        else:
            st.dataframe(pd.DataFrame(), use_container_width=True, height=280)

    st.markdown("---")

    # --- BARIS KEDUA: ANALISIS LANJUTAN ---
    st.markdown("### Analisis Performa & Eksekusi Lanjutan")
    b_col1, b_col2, b_col3 = st.columns([1.5, 1.5, 1])

    # 1. Avg. Response Time by User Action
    with b_col1:
        st.markdown("##### Avg. Response Time by User Action")
        if 'User_Action' in df.columns and 'Response_Time_MS' in df.columns and not df.empty:
            avg_resp = df.groupby('User_Action')['Response_Time_MS'].mean().reset_index()
            avg_resp = avg_resp.sort_values(by='Response_Time_MS', ascending=False).head(10)
            
            chart_resp = alt.Chart(avg_resp).mark_bar(color='#52b788').encode(
                x=alt.X('Response_Time_MS:Q', title='Response Time (ms)'),
                y=alt.Y('User_Action:N', sort='-x', title='')
            ).properties(height=300)
            st.altair_chart(chart_resp, use_container_width=True)
        else:
            st.info("Data tidak tersedia.")

    # 2. FE vs BE Time (BE di bawah, FE di atas) dengan pembersihan Query_Menu
    with b_col2:
        st.markdown("##### FE vs BE Time (by Query Menu)")
        if {'Query_Menu', 'User_Action', 'Response_Time_MS'}.issubset(df.columns) and not df.empty:
            filtered_fe_be = df[df['User_Action'].str.upper().isin(['MINAPP_RENDER_MENU', 'MINAPP_GET_LIST_MENU'])].copy()
            
            if not filtered_fe_be.empty:
                def clean_query_menu(val):
                    val_str = str(val)
                    match = re.search(r'(\d+)', val_str)
                    if match:
                        return f"{match.group(1)} menu"
                    return val_str

                filtered_fe_be['Clean_Query_Menu'] = filtered_fe_be['Query_Menu'].apply(clean_query_menu)
                
                filtered_fe_be['Type'] = filtered_fe_be['User_Action'].str.upper().map({
                    'MINAPP_RENDER_MENU': 'FE_Time',
                    'MINAPP_GET_LIST_MENU': 'BE_Time'
                })
                
                fe_be_grouped = filtered_fe_be.groupby(['Clean_Query_Menu', 'Type'])['Response_Time_MS'].mean().reset_index()
                fe_be_grouped.rename(columns={'Response_Time_MS': 'Time_MS'}, inplace=True)
                
                chart_fe_be = alt.Chart(fe_be_grouped).mark_bar().encode(
                    x=alt.X('Time_MS:Q', title='Time (ms)'),
                    y=alt.Y('Clean_Query_Menu:N', sort='-x', title='Query Menu'),
                    color=alt.Color('Type:N', 
                                    scale=alt.Scale(domain=['BE_Time', 'FE_Time'], range=['#22c55e', '#3b82f6']),
                                    sort=['BE_Time', 'FE_Time'])
                ).properties(height=300)
                st.altair_chart(chart_fe_be, use_container_width=True)
            else:
                st.info("Data MINAPP kosong pada periode ini.")
        else:
            st.info("Kolom pendukung belum lengkap.")

    # 3. Last Execution Card (Berdasarkan rentang tanggal yang terfilter)
    with b_col3:
        st.markdown("##### Last Execution")
        
        minapp_df = df[df['User_Action'].str.upper().isin(['MINAPP_RENDER_MENU', 'MINAPP_GET_LIST_MENU'])] if not df.empty else pd.DataFrame()
        
        if not minapp_df.empty:
            render_df = minapp_df[minapp_df['User_Action'].str.upper() == 'MINAPP_RENDER_MENU']
            if not render_df.empty:
                latest_render = render_df.loc[render_df['Parsed_Date'].idxmax()] if 'Parsed_Date' in render_df.columns else render_df.iloc[-1]
                max_time = latest_render.get('Timestamp', '-')
                q_menu = latest_render.get('Query_Menu', '-')
                fe_time = latest_render.get('Response_Time_MS', 0)
            else:
                max_time = "-"
                q_menu = "-"
                fe_time = 0

            be_df = minapp_df[(minapp_df['User_Action'].str.upper() == 'MINAPP_GET_LIST_MENU') & (minapp_df['Query_Menu'] == q_menu)]
            if not be_df.empty:
                latest_be = be_df.iloc[-1]
                be_time = latest_be.get('Response_Time_MS', 0)
            else:
                be_time = 0

            total_time = be_time + fe_time
            
            match_menu = re.search(r'(\d+)', str(q_menu))
            display_menu = f"{match_menu.group(1)} Menu" if match_menu else str(q_menu)
        else:
            max_time = "-"
            display_menu = "-"
            fe_time = 0
            be_time = 0
            total_time = 0

        st.markdown(f"""
            <div class="metric-box">
                <b>Jumlah :</b> {display_menu}<br>
                <b>Waktu :</b> {max_time}<br>
                <b>FE (ms) :</b> {fe_time}<br>
                <b>BE (ms) :</b> {be_time}<br>
                <b>Total (ms) :</b> {total_time}
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Gagal memuat atau memproses data: {e}")
