# streamlit-rename-app
# Otomatisasi Pengelolaan File Peta

Project ini dikembangkan sebagai bagian dari kegiatan Kerja Praktik di BPS Kabupaten Simalungun untuk mengotomatisasi proses pengelolaan file peta menggunakan *Python*. Sistem dirancang untuk membantu proses identifikasi dan penamaan ulang (*rename*) file peta berdasarkan kode tertentu yang diperoleh dari informasi pada file.

## Deskripsi

Pengelolaan file peta secara manual dapat membutuhkan waktu, terutama ketika jumlah file yang harus diproses cukup banyak. Oleh karena itu, dikembangkan sistem otomatisasi yang memanfaatkan Python dan QR Code detection untuk membantu mengidentifikasi file dan melakukan penamaan ulang secara otomatis.

Project ini mencakup proses pendeteksian QR Code, pengambilan kode sebagai identitas file, hingga proses *rename* berdasarkan format penamaan yang telah ditentukan.

## 🎯 Tujuan

* Mengotomatisasi proses penamaan ulang file peta.
* Memanfaatkan QR Code sebagai identitas untuk membantu proses pengelolaan file.
* Mengurangi proses manual dalam penamaan file.
* Meningkatkan konsistensi penamaan file peta.
* Menguji dan menyempurnakan sistem agar proses otomatisasi dapat berjalan sesuai kebutuhan.

## ⚙️ Fitur

### 1. Automatic File Rename

Melakukan penamaan ulang file peta secara otomatis berdasarkan kode tertentu.

### 2. QR Code Detection

Mendeteksi QR Code yang terdapat pada file peta dan mengambil informasi kode yang tersimpan di dalamnya.

### 3. File Identification

Menggunakan kode hasil pembacaan QR Code sebagai informasi untuk mengidentifikasi file peta.

### 4. Automated File Management

Memproses file secara otomatis sehingga pengguna tidak perlu melakukan *rename* file satu per satu.

### 5. Testing & Improvement

Melakukan pengujian terhadap sistem dan melakukan penyempurnaan berdasarkan hasil pengujian untuk meningkatkan keandalan proses *rename* otomatis.

## 🔄 Alur Proses

```text
File Peta
    │
    ▼
Pembacaan File
    │
    ▼
Deteksi QR Code
    │
    ▼
Ekstraksi Kode
    │
    ▼
Identifikasi File
    │
    ▼
Penentuan Nama File
    │
    ▼
Automatic Rename
    │
    ▼
File Peta Terorganisir
```

## 🛠️ Teknologi yang Digunakan

* **Python** — bahasa pemrograman utama untuk membangun sistem otomasi.
* **OpenCV** — digunakan dalam proses pengolahan gambar dan pendeteksian QR Code.
* **Pillow (PIL)** — digunakan untuk membaca dan memproses file gambar.

## 📂 Struktur Project

```text
├── input/
│   └── file_peta/
├── output/
│   └── file_peta_renamed/
├── main.py
├── requirements.txt
└── README.md
```

> Struktur folder dapat disesuaikan dengan implementasi project.

## 🚀 Cara Menjalankan

### 1. Clone Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Jalankan Program

```bash
python main.py
```

File peta yang akan diproses ditempatkan pada folder input. Sistem kemudian melakukan pendeteksian QR Code, mengambil kode identifikasi, dan menggunakan kode tersebut dalam proses penamaan ulang file.

## 🧪 Pengujian

Pengujian dilakukan untuk memastikan:

* QR Code dapat terdeteksi dengan baik.
* Informasi kode dapat dibaca dengan benar.
* Kode dapat digunakan untuk proses identifikasi file.
* File dapat di-*rename* sesuai format yang ditentukan.
* Proses *rename* dapat dilakukan pada beberapa file secara otomatis.
* Sistem dapat menangani kondisi ketika QR Code tidak berhasil terbaca.

## 📈 Hasil

Pengembangan sistem menghasilkan proses pengelolaan file peta yang lebih terotomatisasi. Dengan memanfaatkan QR Code sebagai informasi identifikasi, proses penamaan ulang file dapat dilakukan secara lebih **efisien dan konsisten** dibandingkan proses manual.

## 👩‍💻 Project Context

Project ini dikembangkan sebagai salah satu kegiatan selama **Kerja Praktik di BPT**, dengan fokus pada penerapan **Python untuk otomasi pengelolaan file dan pemanfaatan computer vision dalam proses identifikasi QR Code**.
