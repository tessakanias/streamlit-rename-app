# Automatic Map Image Renaming

Aplikasi berbasis Python dan Streamlit untuk mengotomatisasi proses penamaan ulang (*rename*) file gambar peta berdasarkan kode wilayah 14 digit yang terdeteksi dari gambar menggunakan Optical Character Recognition (OCR).

Project ini dikembangkan sebagai bagian dari kegiatan Kerja Praktik di BPS untuk membantu meningkatkan efisiensi pengelolaan file peta, khususnya ketika terdapat banyak file yang perlu diidentifikasi dan diberi nama secara konsisten.

## Overview

Proses penamaan file peta secara manual dapat memerlukan waktu dan berisiko menimbulkan kesalahan. Aplikasi ini memanfaatkan EasyOCR untuk membaca teks pada gambar dan mencari pola kode wilayah berupa 14 digit angka.

##  Features

### 1. Rename Single Image

Pengguna dapat mengunggah satu file gambar peta dengan format:

* `.jpg`
* `.jpeg`
* `.png`

Aplikasi akan:

1. Membaca gambar.
2. Melakukan preprocessing.
3. Mendeteksi teks menggunakan EasyOCR.
4. Mencari kode wilayah 14 digit.
5. Membuat nama file baru berdasarkan kode.
6. Menyediakan file hasil rename untuk diunduh.

###  2. Batch Rename from ZIP

Aplikasi juga mendukung pemrosesan banyak gambar melalui **arsip ZIP**.

Dengan alur:

```text
ZIP File
   │
   ▼
Extract Images
   │
   ▼
OCR Processing
   │
   ▼
Detect 14-Digit Code
   │
   ▼
Generate New Filename
   │
   ▼
Create Output ZIP
```

Setiap gambar yang berhasil diidentifikasi akan disalin ke folder output dengan nama baru, kemudian seluruh hasil dikemas kembali menjadi file ZIP.

### 🔍 3. OCR-Based Code Detection

Sistem menggunakan EasyOCR untuk mendeteksi teks pada gambar.

Untuk meningkatkan kemungkinan kode terbaca, gambar diproses menggunakan beberapa tahap:

* Grayscale conversion
* Contrast enhancement
* Image sharpening
* Rotation pada sudut `0°`, `90°`, `180°`, dan `270°`

### 4. Duplicate Filename Handling

Jika nama file hasil rename sudah digunakan, sistem secara otomatis menambahkan nomor urut.

Contoh:

```text
Hasil_12345678901234_beres.jpg
Hasil_12345678901234_beres_1.jpg
Hasil_12345678901234_beres_2.jpg
```

### 5. Rename History

Setiap proses rename dicatat ke dalam database SQLite yang menyimpan:

* Waktu proses
* Nama file awal
* Nama file hasil rename
* Username

Riwayat dapat dilihat melalui menu **Riwayat Rename** pada aplikasi.

## Tech Stack

| Technology       | Usage                                   |
| ---------------- | --------------------------------------- |
| *Python*         | Bahasa pemrograman utama                |
| *Streamlit*      | Web interface                           |
| *EasyOCR*        | Optical Character Recognition           |
| *OpenCV / NumPy* | Pemrosesan dan manipulasi citra         |
| *Pillow (PIL)*   | Image preprocessing                     |
| *SQLite*         | Penyimpanan riwayat rename              |
| *Zipfile*        | Pemrosesan arsip ZIP                    |
| *Logging*        | Pencatatan error dan aktivitas aplikasi |

##  Image Processing

Sebelum dilakukan OCR, gambar diproses untuk membantu meningkatkan keterbacaan teks.

```text
Original Image
      │
      ▼
Grayscale
      │
      ▼
Contrast Enhancement
      │
      ▼
Sharpening
      │
      ▼
Rotation
      │
      ▼
EasyOCR
      │
      ▼
14-Digit Code Detection
```

Sistem mencoba empat orientasi gambar:

```text
0° → 90° → 180° → 270°
```

Pendekatan ini digunakan untuk menangani gambar peta yang memiliki orientasi teks berbeda.

## Database

Aplikasi menggunakan SQLite untuk menyimpan riwayat proses rename.

Struktur tabel:

```text
riwayat
├── username
├── waktu
├── nama_awal
└── nama_akhir
```

Database memungkinkan pengguna melihat kembali file yang telah diproses melalui halaman Riwayat Rename.

## Project Structure

```text
automatic-map-renaming/
│
├── main.py
├── requirements.txt
├── README.md
│
├── uploaded_files/
│
├── riwayat.db
└── app.log
```

> Struktur dapat disesuaikan dengan struktur repository yang digunakan.

##  Installation

Clone repository:

```bash
git clone <repository-url>
cd automatic-map-renaming
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Jalankan aplikasi:

```bash
streamlit run main.py
```

Aplikasi kemudian dapat diakses melalui browser.

## Requirements

Contoh dependency yang digunakan:

```text
streamlit
easyocr
Pillow
numpy
```

Library bawaan Python seperti `sqlite3`, `zipfile`, `tempfile`, `shutil`, `logging`, `os`, dan `re` tidak perlu di-install secara terpisah.

## Testing & Improvement

Pengujian dilakukan untuk mengevaluasi kemampuan sistem dalam:

* Membaca kode wilayah dari gambar.
* Menangani gambar dengan orientasi berbeda.
* Melakukan rename secara otomatis.
* Memproses banyak gambar dalam satu file ZIP.
* Menangani duplikasi nama file.
* Mencatat hasil proses ke dalam database.
* Menangani gambar yang tidak memiliki kode wilayah yang berhasil terbaca.

Hasil pengujian digunakan sebagai dasar untuk melakukan penyempurnaan pada proses OCR dan mekanisme rename otomatis.

## Project Objective

Project ini bertujuan untuk:

* Mengurangi proses penamaan file peta secara manual.
* Meningkatkan efisiensi pengelolaan file.
* Menjaga konsistensi format penamaan file.
* Memanfaatkan OCR untuk mengidentifikasi informasi dari gambar.
* Menyediakan proses batch untuk menangani banyak file sekaligus.

## Project Context

Project ini dikembangkan selama Kerja Praktik di BPS sebagai implementasi pemanfaatan Python, OCR, image processing, dan database untuk mendukung otomasi dalam pengelolaan file peta.

---

Python • Streamlit • EasyOCR • Image Processing • SQLite
