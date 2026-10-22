# Credix Order & Credit Status Transcriber 📄⚡

Aplikasi web dan CLI cerdas untuk membaca, mengekstrak, menghitung eksposur kredit, serta mentranskripsikan dokumen laporan pesanan **Credix Reports (`FRM-LOG-027`)** secara otomatis, cepat (< 1 detik), dan presisi sesuai matriks otorisasi SOP perusahaan.

🌐 **Live Demo Website:** [https://accountant-nine-omega.vercel.app/](https://accountant-nine-omega.vercel.app/)

---

## 📌 Latar Belakang & Masalah yang Diselesaikan

Dalam operasional harian, verifikasi dokumen laporan Credix sering kali memakan waktu 5–10 menit per pesanan karena proses manual:
1. Membaca lembaran tabel PDF yang padat dan sering kali bersambung antar-halaman (*cross-page*).
2. Menghitung manual menggunakan kalkulator apakah pesanan overlimit: `(Order Baru + Piutang Menggantung) - Limit Kredit`.
3. Memeriksa daftar faktur lama untuk mendeteksi tanggal jatuh tempo (*due date*) dan hari keterlambatan (*overdue*), khususnya untuk produk utama (Grup A).
4. Meneliti lembaran tabel matriks otorisasi untuk menentukan pejabat persetujuan yang berwenang (**SM**, **BM**, **RGM**, **HOR**, atau **GM**).
5. Mengetik ulang transkrip laporan ke format pesan chat/WhatsApp untuk diajukan ke atasan.

**Solusi Sistem Ini:**
Cukup unggah dokumen PDF atau jalankan via CLI, seluruh data toko, rincian piutang, kalkulasi eksposur, hingga tingkat otorisasi terdeteksi secara otomatis dan siap disalin ke clipboard dalam hitungan detik.

---

## ✨ Fitur Utama

- 🚀 **Ekstraksi PDF Otomatis & Cepat:** Memproses dokumen PDF puluhan halaman dalam hitungan milidetik tanpa OCR berat.
- 🔄 **Dukungan Pesanan Multi-Halaman (*Cross-Page*):** Rincian faktur yang terpotong di akhir halaman dan bersambung ke halaman berikutnya digabungkan kembali secara utuh.
- 🧮 **Kalkulasi Bisnis Otomatis Sesuai SOP:**
  - Pembersihan 4 digit awal nomor customer (`0100-` / `0103-`).
  - Pencocokan kode grup produk ke nama merek resmi via `category.json`.
  - Kalkulasi nominal dan persentase overlimit berdasarkan rumus resmi.
  - Evaluasi cerdas tampilan overdue (aturan khusus produk Faktur Grup A).
  - Penentuan otomatis level persetujuan pejabat Overlimit dan Overdue.
- ⚙️ **Dual-Engine Architecture (Switchable via `.env`):**
  - **Engine V1 (`transcriber/`):** Pendekatan awal berbasis koordinat geometris.
  - **Engine V2 (`transcriber_v2/`):** Pendekatan terbaru berbasis *adaptive vertical line clustering* dan pengenalan pola teks yang tangguh terhadap pembungkusan teks (*text-wrapping*).
- 📋 **One-Click Copy:** Tombol salin per-kolom, salin transkrip per-toko, serta salin semua transkrip sekaligus siap tempel (*paste*) ke WhatsApp/ERP.
- 🌐 **Web UI Modern & Responsif:** Antarmuka bersih, drag-and-drop, tab navigasi toko, dan tombol instan *"Coba File Contoh"*.
- ☁️ **Serverless Ready:** Kompatibel penuh untuk dideploy ke Vercel Serverless Function.

---

## 🏗️ Struktur Proyek

```text
transkrip/
├── api/                       # Endpoint backend serverless & API Flask
│   ├── index.py               # Handler utama API & local server runner
│   ├── parse.py               # Endpoint POST /api/parse (upload PDF)
│   ├── sample.py              # Endpoint GET /api/sample (contoh file)
│   └── category.json          # Salinan kamus kategori produk untuk Vercel
├── assets/                    # Gambar aset dokumentasi & diagram
├── docs/                      # Dokumentasi mendalam arsitektur
│   ├── ALUR_PROSES_TRANSKRIP.md       # Runtutan teknis step-by-step
│   └── ALUR_PROSES_TRANSKRIP_AWAM.md  # Panduan presentasi versi non-IT
├── file/                      # Berkas PDF contoh uji coba
│   ├── file.pdf
│   ├── file_2.pdf             # Contoh multi-order (11 toko)
│   ├── file_3.pdf             # Contoh fokus order (2 toko)
│   └── file_4.pdf             # Contoh kasus nama toko panjang & text-wrapping (4 toko)
├── public/                    # Frontend antarmuka web (Static Assets)
│   ├── index.html             # Halaman antarmuka pengguna
│   ├── app.js                 # Logika interaksi UI & pemanggilan API
│   └── style.css              # Styling modern responsif
├── transcriber/               # [Engine V1] Modular single-function (koordinat kaku)
├── transcriber_v2/            # [Engine V2] Modular single-function (clustering adaptif)
├── transcriber_factory.py     # Switcher dinamis yang membaca .env
├── app.py                     # Entrypoint lokal (python app.py)
├── order_scanner.py           # CLI runner (python order_scanner.py ...)
├── category.json              # Kamus pemetaan kode grup produk ke nama merek
├── formula.jpeg               # Matriks acuan resmi otorisasi perusahaan
├── GUIDE_PRESENTASI.txt       # Naskah rundown presentasi untuk presenter non-IT
├── requirements.txt           # Dependensi Python
├── vercel.json                # Konfigurasi routing Vercel
├── .env.example               # Template variabel environment
└── .env                       # File konfigurasi lokal (pilihan engine)
```

---

## ⚙️ Konfigurasi Dual-Engine (`.env`)

Sistem menyediakan mekanisme switch dinamis melalui file `.env`:

```env
# ==============================================================================
# Pilihan Engine Ekstraksi & Transkripsi Laporan Credix:
# v1 = Pendekatan Pertama (menggunakan koordinat kaku x & y di folder transcriber)
# v2 = Pendekatan Terbaru (menggunakan pola teks & baris adaptif di folder transcriber_v2)
# ==============================================================================
TRANSCRIBER_ENGINE=v2
```

### Perbedaan Engine V1 vs Engine V2:
| Fitur / Karakteristik | Engine V1 (`transcriber/`) | Engine V2 (`transcriber_v2/` - Rekomendasi) |
|---|---|---|
| **Metode Pengelompokan Baris** | Grid statis `round(y / 3) * 3` | *Adaptive Proximity Clustering* ($\Delta y \le 3.0$ pt) |
| **Toleransi Jarak Pixel** | Rentan jika selisih $\le 0.8$ pt | 100% konsisten menyatukan baris teks sejajar |
| **Nomor Customer Terpotong** | Mengambil potongan baris pertama saja | *Auto-join* menyambung prefix `0100-` dengan angka di baris bawahnya |
| **Nama Toko Multi-Baris** | Hanya membaca baris pertama | Menggabungkan nama toko bertingkat (`TK NADIN MAKMUR`) |

---

## 🚀 Panduan Instalasi & Menjalankan Lokal

### Prasyarat
- Python 3.10 atau versi lebih baru
- PIP (Python Package Installer)

### 1. Kloning Repositori
```bash
git clone <url-repository-ini>
cd transkrip
```

### 2. Siapkan Virtual Environment (Opsional namun Disarankan)
```bash
python -m venv venv
# Di Windows:
venv\Scripts\activate
# Di Linux/macOS:
source venv/bin/activate
```

### 3. Pasang Dependensi
```bash
pip install -r requirements.txt
```

### 4. Siapkan File `.env`
Salin template konfigurasi:
```bash
cp .env.example .env
```

---

## 💻 Cara Penggunaan

### A. Melalui Tampilan Web (Browser)
Jalankan server lokal:
```bash
python app.py
```
Buka browser dan akses alamat: **`http://127.0.0.1:5000`**

1. Tarik (*drag & drop*) file PDF ke kotak dropzone atau klik **"Pilih Dokumen PDF"**.
2. Anda juga dapat langsung menguji sistem dengan mengklik **"Coba File Contoh"**.
3. Hasil transkrip langsung tersaji lengkap dengan status badge dan tombol **"Salin Transkrip"**.

### B. Melalui Terminal / Command Line (CLI)
Jalankan file `order_scanner.py` dengan menyertakan path file PDF:
```bash
# Menjalankan dengan file uji bawaan:
python order_scanner.py file/file_4.pdf

# Menjalankan dengan file PDF apa saja:
python order_scanner.py path/ke/laporan_credix.pdf
```

---

## 📐 Ringkasan Logika Bisnis & Formula Otorisasi

### 1. Rumus Overlimit
$$\text{Total Eksposur} = \text{Amount Order Baru} + \text{Total Piutang Menggantung}$$
$$\text{Nominal Overlimit} = \text{Total Eksposur} - \text{Limit Kredit}$$
$$\text{Persentase Overlimit} = \left(\frac{\text{Nominal Overlimit}}{\text{Limit Kredit}}\right) \times 100\%$$

### 2. Matriks Otorisasi Overlimit
| Tier Batas Kredit | Overlimit $\le$ 30% | Overlimit > 30% |
|---|---|---|
| **0 s.d 40 Juta** | **SM** | **BM** (Piutang $\le 80$ jt) / **RGM** (Piutang $\le 100$ jt) / **HOR** / **GM** |
| **> 40 s.d 75 Juta** | **BM** | **RGM** (Piutang $\le 200$ jt) / **HOR** (Piutang $\le 300$ jt) / **GM** |
| **> 75 s.d 300 Juta** | **RGM** | **HOR** (Piutang $\le 600$ jt) / **GM** |
| **> 300 Juta** | **HOR** | **GM** |

### 3. Matriks Otorisasi Overdue
| Tier Batas Kredit | Overdue $\le$ 2 Hari | Overdue > 2 Hari |
|---|---|---|
| **0 s.d 40 Juta** | **BM** | **RGM** |
| **> 40 s.d 75 Juta** | **RGM** | **HOR** |
| **> 75 s.d 300 Juta** | **HOR** | **GM** |
| **> 300 Juta** | **GM S&G** | **GM** |

### 4. Aturan Tampilan Overdue
- Jika pesanan berstatus **Overlimit** $\rightarrow$ Keterlambatan overdue selalu ditampilkan.
- Jika pesanan **Underlimit** $\rightarrow$ Overdue hanya ditampilkan jika faktur berasal dari **Grup A (Kopi Reguler)** dan nilai hari overdue $\ge 0$.

---

## 🔌 Dokumentasi REST API

### 1. `POST /api/parse`
Memproses file PDF yang diunggah dan mengembalikan array objek order.
- **Content-Type:** `multipart/form-data`
- **Body:** `file` (File PDF biner)
- **Contoh Response JSON:**
  ```json
  {
    "success": true,
    "filename": "file_4.pdf",
    "file_size": 47149,
    "total_orders": 4,
    "orders": [
      {
        "order_num": 1,
        "tanggal_order": "16-OCT-26",
        "nama_toko": "TOKO NADINE SEJAHTERA",
        "nama_toko_str": "TOKO NADINE SEJAHTERA STR BM",
        "nomor_customer": "0026234",
        "limit_kredit": "Rp 1,000,000",
        "amount_penjualan": "Rp 1,783,496",
        "quantity": "Kopi Reguler SJA 32 Box (Total Non Box: 0)",
        "nominal_overlimit": 6155962.0,
        "pct_overlimit": "Rp 6,155,962 (616%)",
        "overdue_str": "-3 Hari (Faktur No. 4241891)",
        "oto_overlimit": "BM",
        "oto_overdue": "",
        "formatted_transcript": "..."
      }
    ]
  }
  ```

### 2. `GET /api/sample`
Endpoint cepat untuk menguji sistem menggunakan file sampel yang ada di server.

### 3. `GET /api/health`
Pemeriksaan status ketersediaan (*health-check*) service backend.

---

## 📚 Dokumentasi Terkait

Untuk pemahaman lebih dalam, silakan merujuk pada dokumen pendukung berikut:
- 📖 [**`docs/ALUR_PROSES_TRANSKRIP.md`**](docs/ALUR_PROSES_TRANSKRIP.md) : Penjelasan runtutan file dan fungsi teknis secara berurutan (*sequence diagram* & tabel pemanggil).
- 🗣️ [**`docs/ALUR_PROSES_TRANSKRIP_AWAM.md`**](docs/ALUR_PROSES_TRANSKRIP_AWAM.md) : Panduan alur proses menggunakan analogi *"Kantor Operasional Digital"* untuk presenter non-IT.
- ⏱️ [**`GUIDE_PRESENTASI.txt`**](GUIDE_PRESENTASI.txt) : Naskah rundown dan script bicara presentasi (10–15 menit).

---

## 👥 Kontributor & Pemeliharaan

Dikembangkan dan dipelihara untuk efisiensi operasional verifikasi laporan kredit dan pesanan.
Jika ada penambahan kode grup produk baru, cukup perbarui file [`category.json`](category.json) tanpa perlu mengubah kode program.
