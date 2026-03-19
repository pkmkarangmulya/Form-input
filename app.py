import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Tabulasi Lengkongjaya", layout="wide")

DB_FILE = 'database_tabulasi_fix.csv'

# --- FUNGSI MEMBERSIHKAN DATA (PENTING AGAR TIDAK ERROR) ---
def clean_header(df):
    """Mencari header asli dari file yang berantakan"""
    for i in range(len(df)):
        row = df.iloc[i].astype(str).values
        if 'NAMA' in [str(x).upper() for x in row]:
            df.columns = df.iloc[i]
            df = df.iloc[i+1:].reset_index(drop=True)
            break
    # Hapus kolom kosong (Unnamed)
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

# --- FUNGSI SKOR KESEHATAN ---
def hitung_skor(bb, tb, gds, td):
    catatan = []
    status = "Normal"
    
    # Skor IMT
    try:
        tb_m = float(tb) / 100
        imt = float(bb) / (tb_m * tb_m)
        if imt > 25: 
            catatan.append("🚨 Obesitas")
            status = "Risiko"
        elif imt < 18.5: catatan.append("⚠️ Kurang BB")
    except: pass

    # Skor GDS
    try:
        if float(gds) >= 200: 
            catatan.append("🚨 Gula Darah Tinggi")
            status = "Risiko"
    except: pass

    # Skor Tensi
    try:
        sistolik = int(str(td).split('/')[0])
        if sistolik >= 140: 
            catatan.append("🚨 Hipertensi")
            status = "Risiko"
    except: pass

    return " | ".join(catatan) if catatan else "✅ Sehat/Normal", status

# --- LOAD DATA ---
def get_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, sep=';')
    return pd.DataFrame()

# --- SIDEBAR: UPLOAD & RESET ---
with st.sidebar:
    st.header("⚙️ Manajemen Database")
    uploaded = st.file_uploader("Upload Master CSV Baru", type=["csv"])
    if uploaded:
        raw = pd.read_csv(uploaded, sep=None, engine='python')
        cleaned = clean_header(raw)
        cleaned.to_csv(DB_FILE, index=False, sep=';')
        st.success("Database Diperbarui!")
        st.rerun()
    
    if st.button("🗑️ Reset Database (Hapus Semua)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.rerun()

# --- MAIN APP ---
st.title("🏥 Sistem Informasi Kesehatan Lengkongjaya")
df = get_data()

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📝 Input & Skor", "🔍 Filter & Tabel", "📈 Analisis Evaluasi"])

    # TAB 1: INPUT DATA
    with tab1:
        with st.form("form_pemeriksaan"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nama = st.text_input("Nama Lengkap").upper()
                nik = st.text_input("NIK")
                # Tanggal Lahir tanpa batas (1900 - Hari Ini)
                tgl_lhr = st.date_input("Tanggal Lahir", min_value=date(1900,1,1), max_value=date.today(), value=date(1990,1,1))
            with c2:
                jk = st.selectbox("Jenis Kelamin", ["L", "P"])
                alamat = st.text_input("Alamat/Kampung")
                rt_rw = st.text_input("RT/RW (Contoh: 01/02)")
            with c3:
                bb = st.number_input("Berat Badan (kg)", min_value=0.0)
                tb = st.number_input("Tinggi Badan (cm)", min_value=0.0)
                td = st.text_input("Tensi (Contoh: 120/80)")
                gds = st.number_input("GDS", min_value=0)
            
            if st.form_submit_button("Simpan & Analisis"):
                skor_txt, status_final = hitung_skor(bb, tb, gds, td)
                umur = date.today().year - tgl_lhr.year
                
                new_row = pd.DataFrame([{
                    "NO": len(df)+1, "NAMA": nama, "NO NIK": f"'{nik}",
                    "TANGGAL LAHIR": tgl_lhr.strftime("%d/%m/%Y"),
                    "L": "TRUE" if jk == "L" else "FALSE",
                    "P": "TRUE" if jk == "P" else "FALSE",
                    "UMUR": f"{umur} Tahun",
                    "TD": td, "GDS": gds, "BB": bb, "TB": tb,
                    "STATUS KESEHATAN": skor_txt, "ALAMAT LENGKAP": alamat,
                    "RT/RW": rt_rw
                }])
                
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(DB_FILE, index=False, sep=';')
                st.success(f"Tersimpan! Status: {skor_txt}")
                st.rerun()

    # TAB 2: FILTER & TABEL
    with tab2:
        st.subheader("Filter Data Dinamis")
        col_f1, col_f2, col_f3 = st.columns(3)
        
        filtered_df = df.copy()
        with col_f1:
            s_nama = st.text_input("Cari Nama/NIK")
            if s_nama:
                filtered_df = filtered_df[filtered_df['NAMA'].str.contains(s_nama.upper(), na=False) | 
                                          filtered_df['NO NIK'].str.contains(s_nama, na=False)]
        with col_f2:
            if "RT/RW" in df.columns:
                list_rt = df["RT/RW"].unique().tolist()
                s_rt = st.multiselect("Filter RT/RW", list_rt)
                if s_rt: filtered_df = filtered_df[filtered_df["RT/RW"].isin(s_rt)]
        with col_f3:
            if "STATUS KESEHATAN" in df.columns:
                s_status = st.multiselect("Filter Status Kesehatan", ["✅ Sehat/Normal", "🚨 Obesitas", "🚨 Hipertensi", "🚨 Gula Darah Tinggi"])
                if s_status: 
                    # Filter jika salah satu kata kunci ada di kolom status
                    mask = filtered_df["STATUS KESEHATAN"].apply(lambda x: any(s in str(x) for s in s_status))
                    filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)
        st.download_button("📥 Download Data Terfilter", filtered_df.to_csv(index=False, sep=';'), "data_kesehatan.csv", "text/csv")

    # TAB 3: ANALISIS & EVALUASI
    with tab3:
        st.subheader("📊 Evaluasi Capaian Kesehatan")
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            # Grafik Status
            st.markdown("**Proporsi Kondisi Kesehatan**")
            fig = px.pie(df, names="STATUS KESEHATAN")
            st.plotly_chart(fig, use_container_width=True)
        with c_a2:
            # Grafik Partisipasi per RT
            st.markdown("**Jumlah Partisipasi per RT/RW**")
            if "RT/RW" in df.columns:
                fig2 = px.histogram(df, x="RT/RW")
                st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("👋 Selamat Datang! Database masih kosong. Silakan Upload file Master CSV (Tabulasi) melalui sidebar di kiri untuk memulai.")
