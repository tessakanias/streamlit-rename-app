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
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup OCR reader
reader = easyocr.Reader(['en'], gpu=False)

# Database setup
db_path = "ocr_results.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    kode_wilayah TEXT,
                    timestamp TEXT
                )''')
conn.commit()

def validate_image(image_path: str) -> bool:
    return image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))

def preprocess_image(img: Image.Image) -> Image.Image:
    """Preprocessing dari versi lama: grayscale, kontras tinggi, sharpen"""
    try:
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        return img
    except Exception as e:
        logger.error(f"Preprocessing error: {e}")
        return img

def extract_kode_wilayah(image_path: str) -> Optional[str]:
    """Ekstrak kode wilayah 14 digit dengan metode dari kode lama + rotasi"""
    try:
        if not validate_image(image_path):
            return None

        img = Image.open(image_path)
        best_result = None

        for angle in [0, 90, 180, 270]:
            rotated = img.rotate(angle, expand=True)
            processed = preprocess_image(rotated)
            np_img = np.array(processed)
            result = reader.readtext(np_img, detail=0)

            for text in result:
                digits = ''.join(filter(str.isdigit, text))
                if len(digits) == 14:
                    return digits
                elif not best_result and digits:
                    best_result = digits

        return best_result if best_result else None
    except Exception as e:
        logger.error(f"OCR error on {image_path}: {e}")
        return None

def save_result_to_db(filename: str, kode: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO results (filename, kode_wilayah, timestamp) VALUES (?, ?, ?)",
                   (filename, kode, timestamp))
    conn.commit()

def process_and_rename(image_path: str, output_folder: str) -> Optional[str]:
    kode = extract_kode_wilayah(image_path)
    if kode:
        new_name = f"{kode}{os.path.splitext(image_path)[1]}"
        new_path = os.path.join(output_folder, new_name)
        shutil.copy(image_path, new_path)
        save_result_to_db(os.path.basename(image_path), kode)
        return new_name
    return None

def handle_uploaded_file(uploaded_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        if uploaded_file.name.endswith('.zip'):
            zip_path = os.path.join(tmpdir, uploaded_file.name)
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                image_paths = [os.path.join(tmpdir, name) for name in zip_ref.namelist()
                               if validate_image(name)]
        else:
            image_paths = []
            file_path = os.path.join(tmpdir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            if validate_image(file_path):
                image_paths.append(file_path)

        output_folder = os.path.join(tmpdir, "renamed")
        os.makedirs(output_folder, exist_ok=True)

        renamed_files = []
        for img_path in image_paths:
            renamed = process_and_rename(img_path, output_folder)
            if renamed:
                renamed_files.append(renamed)

        if renamed_files:
            zip_output = os.path.join(tmpdir, "renamed_files.zip")
            with zipfile.ZipFile(zip_output, 'w') as zipf:
                for fname in renamed_files:
                    full_path = os.path.join(output_folder, fname)
                    zipf.write(full_path, fname)

            with open(zip_output, "rb") as f:
                st.download_button("Download Hasil Rename (ZIP)", f, file_name="hasil_rename.zip")

st.title("OCR Rename File Gambar - Kode Wilayah")

uploaded_file = st.file_uploader("Upload Gambar atau ZIP", type=['jpg', 'jpeg', 'png', 'bmp', 'zip'])
if uploaded_file:
    handle_uploaded_file(uploaded_file)

st.subheader("Riwayat Pengolahan")
cursor.execute("SELECT filename, kode_wilayah, timestamp FROM results ORDER BY id DESC LIMIT 10")
data = cursor.fetchall()
if data:
    for row in data:
        st.text(f"{row[2]} | {row[0]} ➜ {row[1]}")
else:
    st.text("Belum ada data.")
