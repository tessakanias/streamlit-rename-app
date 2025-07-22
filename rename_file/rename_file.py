import streamlit as st
import os
import sqlite3
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
import easyocr
import numpy as np
import re

# === Setup halaman Streamlit ===
st.set_page_config(layout="wide")
st.title("📝 Rename File Gambar")

# === Folder Upload (pastikan tersedia) ===
UPLOAD_FOLDER = 'uploaded_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Cache dan spinner untuk model OCR ===
@st.cache_resource
def get_reader():
    try:
        with st.spinner("🔄 Memuat model OCR (EasyOCR)... Harap tunggu..."):
            return easyocr.Reader(['id', 'en'])
    except Exception as e:
        st.error(f"❌ Gagal memuat model OCR: {e}")
        st.stop()

reader = get_reader()
st.info("ℹ️ Model OCR sudah dimuat. Jika ini pertama kali, proses bisa memakan waktu beberapa menit.")

# === Fungsi ekstraksi kode wilayah dengan preprocessing dan rotasi ===
def extract_kode_wilayah(image_path):
    try:
        img = Image.open(image_path)
    except Exception as e:
        st.error(f"❌ Gagal membuka gambar: {e}")
        return None

    def preprocess(img):
        img = img.convert('L')  # grayscale
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        return img

    kode_pattern = r'\b\d{14}\b'
    best_result = None

    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        processed = preprocess(rotated)
        np_img = np.array(processed)
        try:
            result = reader.readtext(np_img, detail=0)
        except Exception as e:
            st.warning(f"Gagal membaca OCR pada rotasi {angle}: {e}")
            continue
        for text in result:
            if any(c.isdigit() for c in text):
                match = [t for t in result if len(t) == 14 and t.isdigit()]
                if match:
                    return match[0]
                elif not best_result:
                    best_result = text

    return best_result if best_result else None

# === Database SQLite ===
conn = sqlite3.connect('riwayat.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS riwayat (
        username TEXT,
        waktu TEXT,
        nama_awal TEXT,
        nama_akhir TEXT
    )
''')
conn.commit()

def insert_riwayat(username, waktu, awal, akhir):
    c.execute("INSERT INTO riwayat VALUES (?, ?, ?, ?)", (username, waktu, awal, akhir))
    conn.commit()

def get_user_riwayat(username):
    c.execute("SELECT waktu, nama_awal, nama_akhir FROM riwayat WHERE username = ? ORDER BY waktu DESC", (username,))
    return c.fetchall()

# Username default (karena tidak login)
username = "default_user"

# === Tab Layout ===
tab1, tab2, tab3 = st.tabs(["📤 Upload Gambar", "📁 Rename dari Folder", "📜 Riwayat Rename"])

# === Tab 1: Upload Gambar ===
with tab1:
    st.header("📤 Upload Gambar")
    uploaded_file = st.file_uploader("Unggah gambar", type=['jpg', 'jpeg', 'png'])

    if uploaded_file is not None:
        with st.spinner("🔄 Sedang memproses gambar..."):
            filename = uploaded_file.name
            save_path = os.path.join(UPLOAD_FOLDER, filename)

            # Simpan file upload
            try:
                with open(save_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
            except Exception as e:
                st.error(f"Gagal menyimpan file: {e}")
                st.stop()

            # Ekstrak kode wilayah
            try:
                kode = extract_kode_wilayah(save_path)
            except Exception as e:
                st.error(f"❌ Error saat ekstraksi OCR: {e}")
                kode = None

            if kode:
                ext = os.path.splitext(filename)[-1]
                base_name = f"Hasil_{kode}_beres"
                new_name = f"{base_name}{ext}"
                new_path = os.path.join(UPLOAD_FOLDER, new_name)

                counter = 1
                while os.path.exists(new_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    new_path = os.path.join(UPLOAD_FOLDER, new_name)
                    counter += 1

                try:
                    os.rename(save_path, new_path)
                except Exception as e:
                    st.error(f"Gagal mengganti nama file: {e}")
                    st.stop()

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                insert_riwayat(username, now, filename, new_name)
                st.success(f"✅ Berhasil rename gambar menjadi: {new_name}")
                with open(new_path, "rb") as f:
                    st.download_button(
                        label="Download Hasil Rename",
                        data=f.read(),
                        file_name=new_name,
                        mime="image/jpeg"
                    )
            else:
                st.warning("⚠️ Gagal mengenali kode wilayah.")

# === Tab 2: Rename dari Folder Path ===
with tab2:
    st.header("📁 Rename Gambar dari Folder")
    folder_path = st.text_input("Masukkan path folder:")

    if folder_path and os.path.isdir(folder_path):
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if st.button("Mulai Rename"):
            with st.spinner("🔄 Sedang memproses folder..."):
                count = 0
                for file in files:
                    full_path = os.path.join(folder_path, file)
                    kode = extract_kode_wilayah(full_path)
                    if kode:
                        new_name = f"Hasil_{kode}_beres{os.path.splitext(file)[-1]}"
                        new_path = os.path.join(folder_path, new_name)
                        try:
                            os.rename(full_path, new_path)
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            insert_riwayat(username, now, file, new_name)
                            count += 1
                        except Exception as e:
                            st.error(f"Gagal rename: {file} → {e}")
                st.success(f"✅ Selesai! {count} gambar berhasil di-rename.")

# === Tab 3: Riwayat Rename ===
with tab3:
    st.header("📜 Riwayat Rename")
    riwayat = get_user_riwayat(username)

    for waktu, awal, akhir in riwayat:
        path_file = os.path.join(UPLOAD_FOLDER, akhir)
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"{waktu} | {awal} ➔ {akhir}")
        with col2:
            if os.path.exists(path_file):
                with open(path_file, "rb") as f:
                    st.download_button(
                        label="⬇️",
                        data=f.read(),
                        file_name=akhir,
                        mime="image/jpeg",
                        key=path_file
                    )
