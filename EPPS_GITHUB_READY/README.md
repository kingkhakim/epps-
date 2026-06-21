# EPPS Psychological Test System

Aplikasi psikotes EPPS (Edwards Personal Preference Schedule) berbasis Python dan Streamlit.

Project ini berisi:

- `app.py` sebagai antarmuka Streamlit.
- `scoring_engine.py` untuk menghitung skor EPPS.
- `interpretation_engine.py` untuk membuat interpretasi hasil.
- `item_bank.json` sebagai bank 225 item EPPS.
- `norms_male.csv` dan `norms_female.csv` sebagai data norma.
- `requirements.txt` sebagai daftar dependency.

## Fitur

- Input identitas peserta.
- Instruksi pengerjaan.
- Tes 225 item dalam 15 halaman.
- Validasi agar semua item terjawab.
- Scoring raw score 15 dimensi EPPS.
- Konversi skor ke percentile dan kategori norma.
- Consistency score.
- Interpretasi deskriptif per dimensi.
- Download hasil dalam format JSON dan CSV.

## Struktur Folder

```text
EPPS_GITHUB_READY/
├── app.py
├── scoring_engine.py
├── interpretation_engine.py
├── item_bank.json
├── norms_male.csv
├── norms_female.csv
├── requirements.txt
├── run_app.bat
├── .gitignore
└── README.md
```

Folder `results/` akan dibuat otomatis saat aplikasi menyimpan hasil. Folder tersebut tidak perlu di-upload ke GitHub.

## Cara Menjalankan di Komputer Lokal

### 1. Install Python

Pastikan Python sudah terinstall.

Disarankan menggunakan Python 3.10 atau lebih baru.

Cek versi Python:

```bash
python --version
```

### 2. Masuk ke Folder Project

```bash
cd EPPS_GITHUB_READY
```

### 3. Buat Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS atau Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependency

```bash
pip install -r requirements.txt
```

### 5. Jalankan Aplikasi

```bash
streamlit run app.py
```

Jika memakai Windows, Anda juga bisa klik dua kali:

```text
run_app.bat
```

Setelah berjalan, buka alamat yang muncul di terminal, biasanya:

```text
http://localhost:8501
```

## Cara Upload ke GitHub

### Opsi A: Upload Manual dari Website GitHub

1. Buka GitHub.
2. Klik `New repository`.
3. Isi nama repository, misalnya `epps-psychological-test`.
4. Jangan centang `Add a README file` karena README sudah tersedia.
5. Klik `Create repository`.
6. Upload semua file dari folder project ini.
7. Commit perubahan.

### Opsi B: Upload lewat Git Command

Jalankan perintah berikut dari folder project:

```bash
git init
git add .
git commit -m "Initial EPPS Streamlit app"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA_REPOSITORY.git
git push -u origin main
```

Ganti:

- `USERNAME` dengan username GitHub Anda.
- `NAMA_REPOSITORY` dengan nama repository Anda.

## Deploy ke Streamlit Community Cloud

1. Push project ini ke GitHub.
2. Buka https://streamlit.io/cloud.
3. Login dengan GitHub.
4. Klik `New app`.
5. Pilih repository project ini.
6. Isi main file path:

```text
app.py
```

7. Klik `Deploy`.

## Catatan Penting

- File `item_bank.json`, `norms_male.csv`, dan `norms_female.csv` wajib ada di folder yang sama dengan `app.py`.
- Jangan upload folder `.venv/`, `__pycache__/`, atau `results/`.
- Hasil tes tersimpan otomatis di folder `results/` saat scoring dilakukan.
- Interpretasi bersifat deskriptif dan sebaiknya digunakan bersama wawancara, observasi, dan konteks pemeriksaan profesional.

