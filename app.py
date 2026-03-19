import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Informasi Data Penduduk", layout="wide")

# --- KONFIGURASI DATABASE ---
file_path = 'database_penduduk.csv'

# --- FUNGSI LOGIKA OTOMATIS (Sama seperti Cxxdroid/Python sebelumnya) ---
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
    
    # Menentukan Rentang Usia
    if thn <= 5: rentang = "Balita"
    elif thn <= 6: rentang = "Anak Pra Sekolah"
    elif thn <= 12: rentang = "Anak Usia Sekolah"
    elif thn <= 18: rentang = "Remaja"
    elif thn <= 59: rentang = "Dewasa"
    else: rentang = "Lansia"
    
    usia_str = f"{thn} Thn, {bln} Bln, {hri} Hri"
    return usia_str, rentang

# --- FUNGSI MUAT & SIMPAN DATA (Format Excel Indonesia ;) ---
def load_data():
    if os.path.exists(file_path):
        return pd.read_csv(file_path, sep=';')
    else:
        # Buat file kosong dengan header
        df = pd.DataFrame(columns=["No", "Nama", "NIK", "Tanggal Lahir", "Jenis Kelamin", "Usia", "Rentang Usia", "Alamat Lengkap"])
        df.to_csv(file_path, index=False, sep=';')
        return df

def save_all_data(df):
    # Urutkan ulang nomor otomatis agar rapi
    df["No"] = range(1, len(df) + 1)
    df.to_csv(file_path, index=False, sep=';')

# --- INISIALISASI SESSION STATE ---
if 'selected_row_index' not in st.session_state:
    st.session_state.selected_row_index = None

# --- INTERFACE UTAMA ---
st.title("📋 Sistem Database Kependudukan Terintegrasi")
st.info("Form input dan pengelolaan data offline tersimpan di database_penduduk.csv (Pemisah ;)")

df = load_data()

# --- TABS: INPUT VS KELOLA ---
tab1, tab2 = st.tabs(["📝 Form Input Data Baru", "📊 Kelola & Edit Database"])

# ==========================================
# TAB 1: FORM INPUT DATA BARU
# ==========================================
with tab1:
    with st.form(key='form_input', clear_on_submit=True):
        st.subheader("Masukkan Identitas Penduduk")
        col1, col2 = st.columns(2)
        
        with col1:
            nama = st.text_input("Nama Lengkap").upper()
            nik = st.text_input("NIK (16 Digit)")
            tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1920, 1, 1), value=date(2000, 1, 1))
        
        with col2:
            jk = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            alamat = st.text_area("Alamat Lengkap")

        submit = st.form_submit_button("Simpan Data Baru")

    if submit:
        if nama and nik:
            # Pastikan NIK diawali ' agar aman di Excel
            nik_aman = f"'{nik}" if not nik.startswith("'") else nik
            
            # Hitung Usia Otomatis
            usia_str, rentang_str = hitung_usia_lengkap(tgl_lahir)
            no_urut = len(df) + 1

            # Siapkan Baris Baru
            data_baru = pd.DataFrame({
                "No": [no_urut],
                "Nama": [nama],
                "NIK": [nik_aman],
                "Tanggal Lahir": [tgl_lahir.strftime("%d/%m/%Y")],
                "Jenis Kelamin": [jk],
                "Usia": [usia_str],
                "Rentang Usia": [rentang_str],
                "Alamat Lengkap": [alamat]
            })

            # Append dan Simpan (Pemisah ;)
            data_baru.to_csv(file_path, mode='a', index=False, header=False, sep=';')
            st.success(f"✅ Data {nama} berhasil ditambahkan!")
            st.rerun() # Refresh untuk update tab2
        else:
            st.warning("⚠️ Mohon isi Nama dan NIK terlebih dahulu.")

# ==========================================
# TAB 2: KELOLA & EDIT DATABASE
# ==========================================
with tab2:
    st.subheader("Database & Kontrol Data")
    
    # Fitur Cari Cepat (Sama seperti Cxxdroid)
    search_term = st.text_input("🔍 Cari Cepat (Nama/NIK)")
    df_display = df
    if search_term:
        df_display = df[df['Nama'].str.contains(search_term.upper()) | df['NIK'].str.contains(search_term)]
    
    # Menampilkan Tabel Berlangganan (st.dataframe)
    st.write("Silakan pilih baris dari tabel di bawah ini untuk mengedit atau menghapus.")
    edited_df = st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Input Nomor Urut (Mengambil logika Cxxdroid)
    no_urutan_kelola = st.number_input("Nomor urut yang akan dikelola (Kolom No):", min_value=0, max_value=len(df), step=1)

    if no_urutan_kelola > 0:
        actual_index = no_urutan_kelola - 1
        st.divider()
        st.subheader(f"Kontrol Data No: {no_urutan_kelola}")
        
        # Ambil data lama
        old_data = df.iloc[actual_index]
        
        # Parse tanggal lahir lama
        old_tgl_str = old_data["Tanggal Lahir"]
        try:
            old_tgl_obj = datetime.strptime(old_tgl_str, "%d/%m/%Y").date()
        except:
            old_tgl_obj = date(2000, 1, 1)

        # --- FORM EDIT ---
        with st.form(key='form_edit'):
            st.markdown(f"**Data Saat Ini:** {old_data['Nama']} | {old_data['Rentang Usia']}")
            colE1, colE2 = st.columns(2)
            
            with colE1:
                e_nama = st.text_input("Nama Baru", value=old_data["Nama"])
                e_nik = st.text_input("NIK Baru", value=old_data["NIK"])
                e_tgl_lahir = st.date_input("Tanggal Lahir Baru", value=old_tgl_obj)
            
            with colE2:
                e_jk = st.selectbox("Jenis Kelamin Baru", ["Laki-laki", "Perempuan"], index=0 if old_data["Jenis Kelamin"] == "Laki-laki" else 1)
                e_alamat = st.text_area("Alamat Baru", value=old_data["Alamat Lengkap"])

            submit_edit = st.form_submit_button("Simpan Perubahan")

        # --- TOMBOL HAPUS ---
        st.warning("⚠️ Perhatian: Hapus data tidak bisa dikembalikan!")
        confirm_hapus = st.checkbox("Saya yakin ingin menghapus data ini")
        submit_hapus = st.button("🔴 Hapus Data", disabled=not confirm_hapus)

        # --- LOGIKA TOMBOL ---
        # 1. LOGIKA SIMPAN PERUBAHAN
        if submit_edit:
            usia_baru, rentang_baru = hitung_usia_lengkap(e_tgl_lahir)
            
            # Update baris di Vector/DataFrame
            df.at[actual_index, "Nama"] = e_nama.upper()
            df.at[actual_index, "NIK"] = f"'{e_nik}" if not e_nik.startswith("'") else e_nik
            df.at[actual_index, "Tanggal Lahir"] = e_tgl_lahir.strftime("%d/%m/%Y")
            df.at[actual_index, "Jenis Kelamin"] = e_jk
            df.at[actual_index, "Usia"] = usia_baru
            df.at[actual_index, "Rentang Usia"] = rentang_baru
            df.at[actual_index, "Alamat Lengkap"] = e_alamat
            
            save_all_data(df)
            st.success(f"✅ Data diperbarui!")
            st.rerun()

        # 2. LOGIKA HAPUS DATA (Sama seperti Cxxdroid)
        if submit_hapus:
            if confirm_hapus:
                df = df.drop(df.index[actual_index])
                save_all_data(df)
                st.error(f"🔴 Data berhasil dihapus!")
                st.rerun()
            else:
                st.warning("Mohon centang konfirmasi sebelum menghapus.")

# --- TOMBOL DOWNLOAD CSV GLOBAL ---
st.divider()
st.subheader("📥 Laporan Database Global")
if not df.empty:
    # Memastikan format Excel Indonesia (sep=;)
    csv_global = df.to_csv(index=False, sep=';').encode('utf-8')
    st.download_button(
        label="Unduh Database Global (CSV/Excel)",
        data=csv_global,
        file_name='database_penduduk_global.csv',
        mime='text/csv',
    )
