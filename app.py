import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Tabulasi Data Lengkongjaya", layout="wide")

# --- KONFIGURASI FILE ---
DEFAULT_FILE = 'database_puskesmas.csv'

# --- FUNGSI LOGIKA OTOMATIS ---
def hitung_usia_lengkap(tgl_lahir):
    today = date.today()
    thn = today.year - tgl_lahir.year
    bln = today.month - tgl_lahir.month
    hri = today.day - tgl_lahir.day
    if hri < 0:
        bln -= 1
        hri += 30
    if bln < 0:
        thn -= 1
        bln += 12
    
    usia_str = f"{thn} Tahun {bln} Bulan {hri} Hari"
    
    # Kategori sesuai format Puskesmas
    if thn <= 5: kelompok = "BALITA 0-5 TH"
    elif thn <= 12: kelompok = "ANAK SEKOLAH"
    elif thn <= 18: kelompok = "REMAJA"
    elif thn <= 59: kelompok = "PRODUKTIF 18-59 TH"
    else: kelompok = "LANSIA ≥60 TH"
    
    return usia_str, kelompok

def load_data():
    if os.path.exists(DEFAULT_FILE):
        return pd.read_csv(DEFAULT_FILE, sep=';')
    else:
        # Template kolom sesuai file yang Anda upload
        columns = [
            "NO", "NAMA", "L", "P", "NO NIK", "NO BPJS", "Status BPJS", 
            "TANGGAL LAHIR", "UMUR", "Kelompok Umur", "ALAMAT LENGKAP", 
            "RT", "RW", "TD", "TB", "BB", "LP", "GDS"
        ]
        return pd.DataFrame(columns=columns)

# --- INTERFACE ---
st.title("🏥 Sistem Tabulasi Hasil Pemeriksaan CKG")
st.subheader("UPT PUSKESMAS KARANGMULYA - DESA LENGKONGJAYA")

# --- FITUR UPLOAD DATABASE ---
with st.expander("📂 Upload Database Lama (File CSV)"):
    uploaded_file = st.file_uploader("Pilih file CSV hasil tabulasi sebelumnya", type=["csv"])
    if uploaded_file is not None:
        try:
            # Membaca file yang diupload (asumsi menggunakan ; atau ,)
            df_upload = pd.read_csv(uploaded_file, sep=None, engine='python')
            df_upload.to_csv(DEFAULT_FILE, index=False, sep=';')
            st.success("✅ Database berhasil diperbarui dari file upload!")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

df = load_data()

tab1, tab2 = st.tabs(["📝 Input Pemeriksaan Baru", "📊 Lihat & Kelola Data"])

# --- TAB 1: INPUT DATA ---
with tab1:
    with st.form("form_input", clear_on_submit=True):
        st.markdown("### Identitas & Hasil Pemeriksaan")
        c1, c2, c3 = st.columns(3)
        with c1:
            nama = st.text_input("Nama Lengkap").upper()
            nik = st.text_input("No NIK")
            bpjs = st.text_input("No BPJS")
        with c2:
            tgl_lhr = st.date_input("Tanggal Lahir", value=date(2000, 1, 1))
            jk = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            status_bpjs = st.selectbox("Status BPJS", ["AKTIF", "TIDAK AKTIF"])
        with c3:
            alamat = st.text_input("Kampung/Alamat")
            rt = st.text_input("RT")
            rw = st.text_input("RW")
            
        st.markdown("### Hasil Klinis")
        k1, k2, k3, k4 = st.columns(4)
        with k1: td = st.text_input("Tensi (TD)")
        with k2: tb = st.text_input("Tinggi Badan (TB)")
        with k3: bb = st.text_input("Berat Badan (BB)")
        with k4: gds = st.text_input("Gula Darah (GDS)")
        
        submit = st.form_submit_button("Simpan ke Tabulasi")

    if submit:
        usia_txt, kelompok_txt = hitung_usia_lengkap(tgl_lhr)
        l_val = "TRUE" if jk == "Laki-laki" else "FALSE"
        p_val = "TRUE" if jk == "Perempuan" else "FALSE"
        
        new_row = {
            "NO": len(df) + 1,
            "NAMA": nama,
            "L": l_val, "P": p_val,
            "NO NIK": f"'{nik}",
            "NO BPJS": f"'{bpjs}",
            "Status BPJS": status_bpjs,
            "TANGGAL LAHIR": tgl_lhr.strftime("%d %B %Y"),
            "UMUR": usia_txt,
            "Kelompok Umur": kelompok_txt,
            "ALAMAT LENGKAP": alamat,
            "RT": rt, "RW": rw,
            "TD": td, "TB": tb, "BB": bb, "GDS": gds
        }
        
        df_new = pd.DataFrame([new_row])
        df_new.to_csv(DEFAULT_FILE, mode='a', index=False, header=not os.path.exists(DEFAULT_FILE), sep=';')
        st.success(f"Data {nama} Berhasil Disimpan!")
        st.rerun()

# --- TAB 2: KELOLA DATA ---
with tab2:
    st.subheader("Data Tabulasi Terdaftar")
    
    # Filter Pencarian
    search = st.text_input("🔍 Cari berdasarkan Nama atau NIK")
    if search:
        df_view = df[df['NAMA'].str.contains(search.upper(), na=False) | df['NO NIK'].str.contains(search, na=False)]
    else:
        df_view = df
        
    st.dataframe(df_view, use_container_width=True)
    
    # Tombol Hapus Data Terakhir
    if st.button("🔴 Hapus Baris Terakhir"):
        if not df.empty:
            df = df.drop(df.index[-1])
            df.to_csv(DEFAULT_FILE, index=False, sep=';')
            st.warning("Baris terakhir telah dihapus.")
            st.rerun()

    # Download Data
    csv = df.to_csv(index=False, sep=';').encode('utf-8')
    st.download_button("📥 Download Hasil Tabulasi (Excel Ready)", data=csv, file_name="HASIL_TABULASI_FIX.csv", mime="text/csv")
