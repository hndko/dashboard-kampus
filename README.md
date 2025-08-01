# 🎓 Dashboard Analisis Kepuasan Fasilitas Kampus

Ini adalah proyek tugas sekolah untuk membuat dashboard web interaktif menggunakan Streamlit. Dashboard ini memvisualisasikan data dari survei kepuasan terhadap fasilitas di Sekolah Tinggi Hukum Militer (STHM).

### 📊 Tampilan Dashboard

![Contoh Tampilan](https://i.imgur.com/8aZ3A1p.png)
_(Anda bisa mengganti link di atas dengan screenshot dashboard Anda sendiri)_

---

### ✨ Fitur Utama

- **Visualisasi Agregat:** Menampilkan ringkasan skor kepuasan rata-rata untuk berbagai kategori fasilitas (Ruang Kelas, Perpustakaan, Kantin, dll.) dalam bentuk grafik batang.
- **Filter Interaktif:** Pengguna dapat memfilter data berdasarkan demografi responden, seperti:
  - Status (Mahasiswa/Staff/Dosen)
  - Jenis Kelamin
  - Kelompok Usia
- **Analisis Detail:** Kemampuan untuk melihat rincian skor kepuasan untuk setiap pertanyaan dalam kategori fasilitas yang dipilih.

---

### 🚀 Instalasi & Cara Menjalankan

Ikuti langkah-langkah berikut untuk menjalankan dashboard ini di komputer Anda.

**1. Prasyarat**

- Pastikan Anda sudah menginstal **Python 3.8** atau versi yang lebih baru.

**2. Clone atau Unduh Proyek**

- Clone repositori ini (jika ada di Git) atau cukup unduh file proyeknya.
  ```bash
  git clone [link-ke-repositori-anda]
  cd [nama-folder-proyek]
  ```

**3. Buat dan Aktifkan Lingkungan Virtual**

- Ini adalah praktik terbaik untuk menjaga dependensi proyek tetap terisolasi.

  ```bash
  # Membuat lingkungan virtual
  python -m venv venv

  # Mengaktifkan lingkungan (Windows)
  .\venv\Scripts\activate

  # Mengaktifkan lingkungan (macOS/Linux)
  source venv/bin/activate
  ```

**4. Instal Dependensi**

- Instal semua library yang dibutuhkan dengan satu perintah menggunakan file `requirements.txt`.
  ```bash
  pip install -r requirements.txt
  ```

**5. Jalankan Aplikasi Streamlit**

- Setelah semua dependensi terinstal, jalankan aplikasi.
  ```bash
  streamlit run app.py
  ```
- Buka browser Anda dan akses alamat URL yang muncul di terminal (biasanya `http://localhost:8501`).

---

### 📁 Struktur Folder Proyek

```
dashboard-kampus/
|-- venv/                  # Folder lingkungan virtual
|-- data_preprocessed.csv  # Dataset survei
|-- app.py                 # Kode utama aplikasi Streamlit
|-- requirements.txt       # Daftar dependensi Python
|-- README.md              # File ini
```
