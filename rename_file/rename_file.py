import streamlit as st
import os
import sqlite3
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
import easyocr
import numpy as np
import zipfile
import tempfile
import shutil
import logging
import re
from typing import Optional

# === Setup Logging ===
logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# === Konfigurasi Aplikasi ===
st.set_page_config(layout="wide")
st.title("📝 Rename File Gambar")

# === Constants ===
UPLOAD_FOLDER = 'uploaded_files'
MAX_ZIP_SIZE = 200 * 1024 * 1024  # 200MB
VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Database Setup ===
def init_db():
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
    return conn

conn = init_db()

# === Cache OCR Model ===
@st.cache_resource
def load_ocr_model():
    try:
        return easyocr.Reader(['id', 'en'])
    except Exception as e:
        st.error("Gagal memuat model OCR.")
        logger.error(f"OCR load error: {e}")
        st.stop()

reader = load_ocr_model()

# === Helper Function ===
def insert_riwayat(username: str, waktu: str, awal: str, akhir: str):
    try:
        conn.execute("INSERT INTO riwayat VALUES (?, ?, ?, ?)", 
                     (username, waktu, awal, akhir))
        conn.commit()
    except Exception as e:
        logger.error(f"Database insert error: {e}")

def get_user_riwayat(username: str):
    try:
        c = conn.cursor()
        c.execute("SELECT waktu, nama_awal, nama_akhir FROM riwayat WHERE username = ? ORDER BY waktu DESC", (username,))
        return c.fetchall()
    except Exception as e:
        logger.error(f"Database read error: {e}")
        return []

def preprocess_image(img: Image.Image) -> Image.Image:
    img = img.convert('L')  # Grayscale
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)  # Tingkatkan kontras
    img = img.filter(ImageFilter.SHARPEN)  # Pertajam
    return img

def extract_kode_wilayah(image_path: str) -> Optional[str]:
    try:
        img = Image.open(image_path)

        for angle in [0, 90, 180, 270]:
            rotated = img.rotate(angle, expand=True)
            processed = preprocess_image(rotated)
            np_img = np.array(processed)
            results = reader.readtext(np_img, detail=0)

            for text in results:
                match = re.search(r'\b\d{14}\b', text)
                if match:
                    return match.group(0)

        return None
    except Exception as e:
        logger.error(f"OCR error on {image_path}: {e}")
        return None

def rename_and_save(original_path: str, new_name: str) -> Optional[str]:
    try:
        base_dir = os.path.dirname(original_path)
        ext = os.path.splitext(original_path)[1]
        new_path = os.path.join(base_dir, new_name + ext)

        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(base_dir, f"{new_name}_{counter}{ext}")
            counter += 1

        os.rename(original_path, new_path)
        return new_path
    except Exception as e:
        logger.error(f"Rename error: {e}")
        return None

# === UI Layout ===
username = "default_user"
tab1, tab2, tab3 = st.tabs(["📤 Upload Gambar", "📁 Rename dari Arsip ZIP", "📜 Riwayat Rename"])

# Tab 1
with tab1:
    st.header("📤 Upload Gambar")
    uploaded_file = st.file_uploader("Unggah gambar", type=VALID_IMAGE_EXTENSIONS)

    if uploaded_file:
        with st.spinner("🔄 Memproses gambar..."):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filename = f"temp_{timestamp}_{uploaded_file.name}"
                temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)

                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())

                kode = extract_kode_wilayah(temp_path)

                if kode:
                    new_name = f"Hasil_{kode}_beres"
                    final_path = rename_and_save(temp_path, new_name)

                    if final_path:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        insert_riwayat(username, now, uploaded_file.name, os.path.basename(final_path))

                        st.success(f"✅ Berhasil rename: {os.path.basename(final_path)}")
                        with Image.open(final_path) as img:
                            st.image(img, caption="Hasil", use_column_width=True)

                        with open(final_path, "rb") as f:
                            st.download_button("⬇️ Download", data=f.read(), file_name=os.path.basename(final_path), mime="image/jpeg")
                else:
                    st.warning("⚠️ Kode wilayah tidak ditemukan.")
                    os.remove(temp_path)
            except Exception as e:
                st.error(f"Gagal memproses: {str(e)}")

# Tab 2
with tab2:
    st.header("📁 Rename Gambar dari Arsip ZIP")
    archive_file = st.file_uploader("Unggah file .zip", type=["zip"])

    if archive_file:
        if archive_file.size > MAX_ZIP_SIZE:
            st.error("❌ File terlalu besar.")
        else:
            with st.spinner("📂 Memproses ZIP..."):
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        zip_path = os.path.join(temp_dir, archive_file.name)
                        with open(zip_path, 'wb') as f:
                            f.write(archive_file.getbuffer())

                        extract_dir = os.path.join(temp_dir, "extracted")
                        os.makedirs(extract_dir, exist_ok=True)

                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)

                        renamed_dir = os.path.join(temp_dir, "renamed")
                        os.makedirs(renamed_dir, exist_ok=True)

                        image_files = []
                        for root, _, files in os.walk(extract_dir):
                            for file in files:
                                if file.lower().endswith(VALID_IMAGE_EXTENSIONS):
                                    image_files.append(os.path.join(root, file))

                        if not image_files:
                            st.warning("Tidak ada gambar valid di dalam ZIP.")
                        else:
                            progress = st.progress(0)
                            count = 0

                            for i, img_path in enumerate(image_files):
                                kode = extract_kode_wilayah(img_path)
                                progress.progress((i + 1) / len(image_files))

                                if kode:
                                    new_name = f"Hasil_{kode}_beres"
                                    ext = os.path.splitext(img_path)[1]
                                    new_path = os.path.join(renamed_dir, new_name + ext)

                                    counter = 1
                                    while os.path.exists(new_path):
                                        new_path = os.path.join(renamed_dir, f"{new_name}_{counter}{ext}")
                                        counter += 1

                                    shutil.copy(img_path, new_path)
                                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    insert_riwayat(username, now, os.path.basename(img_path), os.path.basename(new_path))
                                    count += 1

                            if count > 0:
                                zip_output = os.path.join(temp_dir, "hasil_rename.zip")
                                with zipfile.ZipFile(zip_output, 'w') as zipf:
                                    for file in os.listdir(renamed_dir):
                                        zipf.write(os.path.join(renamed_dir, file), arcname=file)

                                st.success(f"{count} gambar berhasil di-rename.")
                                with open(zip_output, "rb") as f:
                                    st.download_button("⬇️ Download ZIP", data=f.read(), file_name="hasil_rename.zip", mime="application/zip")
                            else:
                                st.warning("Tidak ada gambar yang berhasil di-rename.")
                    except Exception as e:
                        st.error(f"Gagal memproses ZIP: {str(e)}")

# Tab 3
with tab3:
    st.header("📜 Riwayat Rename")
    riwayat = get_user_riwayat(username)

    if not riwayat:
        st.info("Belum ada riwayat.")
    else:
        for i, (waktu, awal, akhir) in enumerate(riwayat):
            with st.expander(f"{i+1}. {waktu} | {awal} ➔ {akhir}"):
                file_path = os.path.join(UPLOAD_FOLDER, akhir)
                st.write(f"Awal: {awal}")
                st.write(f"Akhir: {akhir}")
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button("⬇️ Download", data=f.read(), file_name=akhir, mime="image/jpeg", key=f"dl_{i}")
                else:
                    st.warning("File tidak ditemukan.")
