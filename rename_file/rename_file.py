import streamlit as st
import os
import sqlite3
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import easyocr
import numpy as np
import zipfile
import tempfile
import shutil
import time
import logging
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
os.makedirs(UPLOAD_FOLDER, exist_ok=True, mode=0o777)

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

# === Helper Functions ===
@st.cache_resource
def load_ocr_model():
    """Cache OCR model untuk performa lebih baik"""
    logger.info("Loading OCR model...")
    try:
        return easyocr.Reader(['id', 'en'])
    except Exception as e:
        logger.error(f"Gagal load OCR model: {e}")
        st.error("Gagal memuat model OCR. Aplikasi tidak dapat berjalan.")
        st.stop()

reader = load_ocr_model()

def insert_riwayat(username: str, waktu: str, awal: str, akhir: str):
    """Menyimpan riwayat rename ke database"""
    try:
        conn.execute("INSERT INTO riwayat VALUES (?, ?, ?, ?)", 
                    (username, waktu, awal, akhir))
        conn.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")

def get_user_riwayat(username: str):
    """Mengambil riwayat rename dari database"""
    try:
        c = conn.cursor()
        c.execute("""SELECT waktu, nama_awal, nama_akhir 
                     FROM riwayat WHERE username = ? 
                     ORDER BY waktu DESC""", (username,))
        return c.fetchall()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

def validate_image(file_path: str) -> bool:
    """Validasi apakah file gambar tidak corrupt"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        logger.error(f"Invalid image: {file_path} - {e}")
        return False

def preprocess_image(img: Image.Image) -> Image.Image:
    """Preprocessing gambar untuk OCR"""
    try:
        # Convert ke grayscale
        img = img.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Binarization
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        
        return img
    except Exception as e:
        logger.error(f"Preprocessing error: {e}")
        return img

def extract_kode_wilayah(image_path: str) -> Optional[str]:
    """Ekstrak kode wilayah dari gambar menggunakan OCR"""
    try:
        if not validate_image(image_path):
            return None

        with Image.open(image_path) as img:
            processed_img = preprocess_image(img)
            
            # Coba 4 orientasi berbeda
            for angle in [0, 90, 180, 270]:
                rotated = processed_img.rotate(angle, expand=True)
                np_img = np.array(rotated)
                
                # OCR processing
                results = reader.readtext(np_img, detail=0)
                
                # Cari pola 14 digit
                for text in results:
                    digits = ''.join(filter(str.isdigit, text))
                    if len(digits) == 14:
                        return digits
                        
        return None
    except Exception as e:
        logger.error(f"OCR error on {image_path}: {e}")
        return None

def rename_and_save(original_path: str, new_name: str) -> Optional[str]:
    """Rename file dengan handle duplikasi"""
    try:
        base_dir = os.path.dirname(original_path)
        ext = os.path.splitext(original_path)[1]
        new_path = os.path.join(base_dir, new_name + ext)
        
        # Handle nama duplikat
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(base_dir, f"{new_name}_{counter}{ext}")
            counter += 1
            
        os.rename(original_path, new_path)
        return new_path
    except Exception as e:
        logger.error(f"Rename error: {original_path} -> {new_name} - {e}")
        return None

# === UI Layout ===
username = "default_user"  # Bisa diganti dengan auth system
tab1, tab2, tab3 = st.tabs(["📤 Upload Gambar", "📁 Rename dari Arsip ZIP", "📜 Riwayat Rename"])

# Tab 1: Upload Gambar Tunggal
with tab1:
    st.header("📤 Upload Gambar")
    uploaded_file = st.file_uploader("Unggah gambar", type=VALID_IMAGE_EXTENSIONS)

    if uploaded_file is not None:
        with st.spinner("🔄 Sedang memproses gambar..."):
            try:
                # Simpan file upload
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_filename = f"temp_{timestamp}_{uploaded_file.name}"
                temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
                
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Proses OCR
                kode = extract_kode_wilayah(temp_path)
                
                if kode:
                    # Rename file
                    new_name = f"Hasil_{kode}_beres"
                    final_path = rename_and_save(temp_path, new_name)
                    
                    if final_path:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        insert_riwayat(username, now, uploaded_file.name, os.path.basename(final_path))
                        
                        st.success(f"✅ Berhasil rename gambar menjadi: {os.path.basename(final_path)}")
                        
                        # Tampilkan preview gambar
                        with Image.open(final_path) as img:
                            st.image(img, caption="Hasil", use_column_width=True)
                        
                        # Download button
                        with open(final_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download Hasil Rename",
                                data=f.read(),
                                file_name=os.path.basename(final_path),
                                mime="image/jpeg"
                            )
                else:
                    st.warning("⚠️ Gagal mengenali kode wilayah.")
                    os.remove(temp_path)
                    
            except Exception as e:
                st.error(f"❌ Error memproses gambar: {str(e)}")
                logger.error(f"Upload error: {e}")

# Tab 2: Proses Archive ZIP
with tab2:
    st.header("📁 Rename Gambar dari Arsip ZIP")
    archive_file = st.file_uploader("Unggah file .zip", type=["zip"], 
                                  help="Maksimal 200MB")

    if archive_file:
        if archive_file.size > MAX_ZIP_SIZE:
            st.error(f"❌ File terlalu besar. Maksimal {MAX_ZIP_SIZE//(1024*1024)}MB")
            st.stop()
            
        with st.spinner("📂 Memproses file ZIP..."):
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Simpan file ZIP
                    zip_path = os.path.join(temp_dir, archive_file.name)
                    with open(zip_path, 'wb') as f:
                        f.write(archive_file.getbuffer())
                    
                    # Ekstrak ZIP
                    extract_dir = os.path.join(temp_dir, "extracted")
                    os.makedirs(extract_dir, exist_ok=True)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    st.success(f"✅ Berhasil ekstrak {len(zip_ref.namelist())} file")
                    
                    # Proses gambar
                    renamed_dir = os.path.join(temp_dir, "renamed")
                    os.makedirs(renamed_dir, exist_ok=True)
                    
                    image_files = []
                    for root, _, files in os.walk(extract_dir):
                        for file in files:
                            if file.lower().endswith(VALID_IMAGE_EXTENSIONS):
                                image_files.append(os.path.join(root, file))
                    
                    if not image_files:
                        st.warning("⚠️ Tidak ditemukan file gambar (.jpg/.jpeg/.png) dalam ZIP.")
                        st.stop()
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    success_count = 0
                    
                    for i, img_path in enumerate(image_files):
                        progress = (i + 1) / len(image_files)
                        progress_bar.progress(progress)
                        status_text.text(f"Memproses {i+1}/{len(image_files)}: {os.path.basename(img_path)}")
                        
                        try:
                            kode = extract_kode_wilayah(img_path)
                            if kode:
                                new_name = f"Hasil_{kode}_beres"
                                new_path = os.path.join(renamed_dir, new_name + os.path.splitext(img_path)[1])
                                
                                # Handle duplikat
                                counter = 1
                                while os.path.exists(new_path):
                                    new_path = os.path.join(renamed_dir, f"{new_name}_{counter}{os.path.splitext(img_path)[1]}")
                                    counter += 1
                                
                                shutil.copy(img_path, new_path)
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                insert_riwayat(username, now, os.path.basename(img_path), os.path.basename(new_path))
                                success_count += 1
                            else:
                                st.warning(f"⚠️ Kode wilayah tidak ditemukan di: {os.path.basename(img_path)}")
                        except Exception as e:
                            logger.error(f"Process error {img_path}: {e}")
                            st.error(f"❌ Gagal memproses {os.path.basename(img_path)}: {str(e)}")
                    
                    # Buat ZIP hasil
                    if success_count > 0:
                        zip_output_path = os.path.join(temp_dir, "hasil_rename.zip")
                        with zipfile.ZipFile(zip_output_path, 'w') as zipf:
                            for file in os.listdir(renamed_dir):
                                file_path = os.path.join(renamed_dir, file)
                                zipf.write(file_path, arcname=file)
                        
                        st.success(f"✅ Selesai! {success_count}/{len(image_files)} gambar berhasil di-rename.")
                        
                        # Download button
                        with open(zip_output_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download Hasil Rename (ZIP)",
                                data=f.read(),
                                file_name="hasil_rename.zip",
                                mime="application/zip"
                            )
                    else:
                        st.warning("⚠️ Tidak ada gambar yang berhasil di-rename.")
                
                except zipfile.BadZipFile:
                    st.error("❌ File ZIP corrupt atau tidak valid.")
                except Exception as e:
                    st.error(f"❌ Error memproses ZIP: {str(e)}")
                    logger.error(f"ZIP processing error: {e}")

# Tab 3: Riwayat Rename
with tab3:
    st.header("📜 Riwayat Rename")
    riwayat = get_user_riwayat(username)
    
    if not riwayat:
        st.info("Belum ada riwayat rename.")
    else:
        for i, (waktu, awal, akhir) in enumerate(riwayat):
            with st.expander(f"{i+1}. {waktu} | {awal} ➔ {akhir}"):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**Original:** {awal}")
                    st.write(f"**Renamed:** {akhir}")
                    st.write(f"**Waktu:** {waktu}")
                
                with col2:
                    file_path = os.path.join(UPLOAD_FOLDER, akhir)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download",
                                data=f.read(),
                                file_name=akhir,
                                mime="image/jpeg",
                                key=f"dl_{i}"
                            )
                    else:
                        st.warning("File tidak ditemukan")
