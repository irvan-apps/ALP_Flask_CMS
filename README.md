# PT Arunika Loise Persada (ALP) - Flask CMS

Sistem Manajemen Konten (CMS) dinamis berbasis **Python Flask**, **SQLite**, dan **Tailwind CSS** untuk website profil perusahaan PT Arunika Loise Persada (General Contractor, Civil Engineering & Mechanical Electrical).

---

## 🚀 Fitur Utama

### 1. Halaman Publik (Frontend)
- **Desain Modern & Responsif**: Berbasis Tailwind CSS, nuansa warna brand ALP (Orange `#F58220`, Amber/Yellow `#FFC72C`, Dark Gray `#111827`).
- **Beranda Interaktif**:
  - Hero Section dinamis dengan badge, headline sorotan, deskripsi, dan 3 kartu statistik capaian.
  - Kartu profil perusahaan terverifikasi dengan alamat, domain, dan email resmi.
  - Bagian **Tentang Kami** lengkap dengan narasi sejarah dan capaian 20+ tahun pengalaman SDM.
  - Bagian **Visi & Misi** perusahaan.
  - Bagian **Layanan Kami** (Civil & Construction, Mechanical & Electrical) dengan daftar sub-layanan.
  - Bagian **Galeri Proyek** aktual di lapangan lengkap dengan filter dan label kategori (M&E, Civil, Electrical, Mechanical).
  - Bagian **Struktur Organisasi** (Dewan Direksi, Project Manager, K3 & Mutu).
  - Bagian **Legalitas Perusahaan** resmi (NIB OSS-RBA, Sertifikat LPJK, KBLI Konstruksi, SK Kemenkumham, NPWP Badan Usaha).
  - Bagian **Klien & Mitra Bisnis** (Jasa Marga, Schneider Electric, dll).
  - Formulir **Inquiry & Kontak Langsung** yang terhubung secara realtime ke database dan panel admin (AJAX modal tanpa reload halaman).
  - Tautan WhatsApp langsung dan navigasi menu mobile drawer.

### 2. Panel Pengelola CMS (Admin Panel)
- **Autentikasi Aman**: Login berbasis session dengan enkripsi kata sandi `pbkdf2:sha256`.
- **Dashboard Ringkasan**:
  - Kartu statistik jumlah Proyek, Layanan, Tim, Legalitas, Mitra, dan Pesan Masuk (inquiry).
  - Notifikasi badge pesan masuk belum dibaca (unread).
  - Akses cepat proyek dan inquiry terbaru.
- **Pengaturan Website & Profil**:
  - Ubah nama perusahaan, tagline, alamat kantor, email, nomor telepon, dan nomor WhatsApp.
  - Ubah teks hero banner, teks sorotan, dan 3 angka statistik.
  - Ubah narasi tentang kami, upload foto baru, serta ubah poin visi & misi.
- **Kelola Layanan Kami (CRUD)**:
  - Tambah, edit, dan hapus layanan.
  - Ubah kode nomor (01, 02), ikon FontAwesome, deskripsi, dan poin sub-layanan baris per baris.
- **Kelola Galeri Proyek (CRUD)**:
  - Tambah proyek baru dengan upload file gambar langsung dari komputer atau URL eksternal.
  - Atur kategori, deskripsi, nama klien/tag, dan urutan tampil.
- **Kelola Struktur Organisasi (CRUD)**:
  - Tambah/edit anggota direksi dan manajemen, peran jabatan, divisi, bio ringkas, dan foto.
- **Kelola Legalitas Perusahaan (CRUD)**:
  - Kelola nomor NIB, izin LPJK, SK Menkumham, instansi penerbit, dan tahun terbit.
- **Kelola Mitra & Klien (CRUD)**:
  - Kelola nama partner, keterangan kerjasama, dan ikon mitra.
- **Kotak Masuk Pesan (Inbox Inquiries)**:
  - Tinjau pesan yang dikirim oleh calon klien dari website.
  - Filter: Semua, Belum Dibaca, Sudah Dibaca.
  - Tombol aksi langsung: Balas via Email atau Hubungi via WhatsApp.
- **Akun & Keamanan**:
  - Ubah nama profil dan ganti kata sandi administrator.

---

## 🔑 Informasi Akses Panel Admin Rahasia

Panel CMS bersifat **rahasia** (tidak ada tombol/link login di halaman publik index):
- **URL Login Admin**: [http://127.0.0.1:5001/admin/login](http://127.0.0.1:5001/admin/login) (atau `domainkamu.com/admin/login`)
- **Username Default**: `admin`
- **Password Default**: `admin123`

*(Catatan: Anda dapat langsung mengganti password ini melalui menu **Akun & Keamanan** di dalam panel admin).*

---

## 💻 Cara Menjalankan Aplikasi

### Metode 1: Menggunakan Shell Script Cepat
```bash
./run.sh
```

### Metode 2: Manual Menggunakan Virtual Environment
```bash
# Aktifkan virtual environment
source venv/bin/activate

# Jalankan aplikasi Flask
python app.py
```

Aplikasi akan otomatis berjalan pada:
- **Halaman Website Utama**: [http://127.0.0.1:5001](http://127.0.0.1:5001)
- **Panel Admin CMS**: [http://127.0.0.1:5001/admin](http://127.0.0.1:5001/admin)

---

## 📁 Struktur Direktori

```
ALP_CMS/
├── app.py                      # Router utama Flask & Controller
├── db.py                       # Skema SQLite, inisialisasi, dan data awal (seeding)
├── requirements.txt            # Dependensi Python
├── run.sh                      # Shell script cepat untuk menjalankan CMS
├── alp_cms.db                  # Database SQLite lokal (otomatis dibuat)
├── static/
│   └── uploads/                # Direktori file foto/gambar yang diupload
└── templates/
    ├── base.html               # Template dasar publik (Tailwind CSS & FontAwesome)
    ├── index.html              # Landing page utama dinamis
    └── admin/
        ├── base_admin.html     # Layout dasar panel admin (Sidebar & Topbar)
        ├── login.html          # Halaman masuk (Login) admin
        ├── dashboard.html      # Halaman ringkasan statistik & aktivitas
        ├── settings.html       # Pengaturan profil, hero, & kontak
        ├── services.html       # Daftar layanan
        ├── service_form.html   # Form tambah/edit layanan
        ├── projects.html       # Galeri proyek portofolio
        ├── project_form.html   # Form tambah/edit proyek & upload foto
        ├── organization.html   # Kelola struktur organisasi & tim
        ├── legality.html       # Kelola dokumen izin & legalitas
        ├── clients.html        # Kelola mitra & klien kerja sama
        ├── messages.html       # Kotak masuk pesan inquiry klien
        └── profile.html        # Pengaturan akun admin & ganti sandi
```
