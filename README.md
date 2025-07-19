# Proyek Akhir Grafika Komputer: Aplikasi Interaktif 2D & 3D

[cite_start]Proyek ini merupakan tugas akhir untuk mata kuliah Grafika Komputer[cite: 1, 2], yang diimplementasikan menggunakan Python dan pustaka PyOpenGL. Proyek ini terdiri dari dua aplikasi utama: sebuah program menggambar 2D interaktif dan sebuah program visualisasi objek 3D.

## ✨ Fitur Utama

### 🎨 Aplikasi 2D Interaktif
- [cite_start]**Penggambaran Objek Dasar**: Menggambar Titik, Garis, Persegi, dan Elips menggunakan input dari klik mouse[cite: 30, 31, 32, 33, 34, 35].
- [cite_start]**Manajemen Atribut**: Kemampuan untuk mengubah warna dan ketebalan garis objek yang digambar[cite: 36, 38, 39].
- [cite_start]**Transformasi Geometri**: Objek yang dipilih dapat dikenai Translasi, Rotasi, dan Skala melalui input keyboard[cite: 40, 41].
- **Seleksi Objek**: Memilih satu atau beberapa objek untuk dimanipulasi.
- **Windowing & Clipping**: Menentukan sebuah *window* aktif. [cite_start]Objek di dalamnya akan berubah warna menjadi hijau [cite: 49][cite_start], sedangkan objek di luar akan dipotong (*clipping*) menggunakan algoritma Cohen-Sutherland[cite: 50].

### 🧊 Aplikasi 3D Interaktif
- [cite_start]**Visualisasi Objek 3D**: Menampilkan objek 3D (kubus secara default) dan mendukung pemuatan model dari file `.obj`[cite: 53, 54, 56].
- [cite_start]**Transformasi 3D**: Melakukan Translasi dan Rotasi objek menggunakan keyboard dan mouse[cite: 57, 58].
- [cite_start]**Pencahayaan dan Shading**: Implementasi model pencahayaan sederhana (Phong/Gouraud) yang mencakup komponen *Ambient*, *Diffuse*, dan *Specular light* untuk memberikan efek realistis[cite: 59, 60, 61, 62, 63].
- [cite_start]**Kontrol Kamera**: Menggunakan proyeksi perspektif (`gluPerspective`) dan posisi kamera (`gluLookAt`) untuk tampilan 3D yang dinamis[cite: 65, 66].
- **Manajemen File**: Mengekspor kondisi objek saat ini ke dalam format file `.obj`.

## 🛠️ Teknologi yang Digunakan
- **Bahasa**: Python 3
- **Pustaka**: PyOpenGL, PyOpenGL_accelerate

## ⚙️ Instalasi dan Setup

Untuk menjalankan proyek ini di lingkungan lokal Anda, ikuti langkah-langkah berikut:

1.  **Clone repositori ini:**
    ```sh
    git clone [https://github.com/NAMA_USER/NAMA_REPO.git](https://github.com/NAMA_USER/NAMA_REPO.git)
    cd NAMA_REPO
    ```

2.  **Buat dan aktifkan lingkungan virtual (disarankan):**
    ```sh
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS / Linux
    source venv/bin/activate
    ```

3.  **Instal dependensi yang diperlukan:**
    ```sh
    pip install PyOpenGL PyOpenGL_accelerate
    ```
    [cite_start]*Catatan: Perintah instalasi ini tercantum dalam penanganan eror di dalam kode sumber[cite: 69, 108].*

## 🚀 Cara Menjalankan

Proyek ini terdiri dari dua file Python utama.

- **Untuk menjalankan aplikasi 2D:**
  ```sh
  python Modul_A_2D.py
  ```

- **Untuk menjalankan aplikasi 3D:**
  ```sh
  python Modul_B_3D.py
  ```
Setelah dijalankan, panduan penggunaan lengkap akan muncul di terminal untuk masing-masing aplikasi.

## 👨‍💻 Author

- [cite_start]**Nama**: Achmad Ardi Sukmadi [cite: 4]
- [cite_start]**NIM**: 202310370311049 [cite: 4]
- [cite_start]**Universitas**: Universitas Muhammadiyah Malang [cite: 5]
- [cite_start]**Fakultas**: Fakultas Teknik [cite: 6]
- [cite_start]**Program Studi**: Informatika [cite: 7]
