import os
import shutil
import streamlit as st
import easyocr
from PIL import Image
import re

# Direktori penyimpanan
UPLOAD_DIR = "uploaded"
RENAMED_DIR = "renamed"

# Membuat folder jika belum ada
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Inisialisasi EasyOCR
reader = easyocr.Reader(['en'])

st.title("🔍 Rename Gambar Otomatis Berdasarkan Kode OCR")

uploaded_files = st.file_uploader("Unggah satu atau lebih gambar", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

def extract_kode(texts):
    # Gabungkan semua hasil OCR jadi satu string
    gabungan = " ".join(texts)
    # Cari semua angka 4 digit atau lebih
    kode_list = re.findall(r'\b\d{3,}\b', gabungan)
    # Gabungkan dengan underscore
    return "_".join(kode_list) if kode_list else "TIDAK_TEMU_KODE"

if uploaded_files:
    st.write("📂 Hasil Rename:")

    for uploaded_file in uploaded_files:
        # Simpan ke folder upload
        original_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(original_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            # OCR semua teks
            result = reader.readtext(original_path)
            all_texts = [r[1] for r in result]

            if all_texts:
                # Ambil semua kode angka
                extracted_kode = extract_kode(all_texts)
                ext = os.path.splitext(uploaded_file.name)[1]
                new_filename = f"Hasil_{extracted_kode}_beres{ext}"
                new_path = os.path.join(RENAMED_DIR, new_filename)
                shutil.copy(original_path, new_path)

                st.success(f"✅ {uploaded_file.name} → {new_filename}")
            else:
                st.warning(f"⚠️ Tidak ada teks terbaca di {uploaded_file.name}")

        except Exception as e:
            st.error(f"❌ Gagal memproses {uploaded_file.name}: {e}")

# Download hasil
if os.listdir(RENAMED_DIR):
    with st.expander("📥 Download semua file hasil rename"):
        for filename in os.listdir(RENAMED_DIR):
            with open(os.path.join(RENAMED_DIR, filename), "rb") as f:
                st.download_button(f"Download {filename}", f, file_name=filename)
