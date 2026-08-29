# SIH PS26188: AI Fake Identity & Document Screening Backend

FastAPI OCR, Algorithmic Validation, and Supabase Cross-Check Engine for Ministry of Home Affairs (MHA) SIH Problem Statement 26188.

---

## 🏗️ Architecture & Features

1. **OCR & Image Preprocessing Pipeline (`ocr.py`):**
   - Ingests scanned image uploads (JPEG/PNG).
   - Preprocesses images via OpenCV (de-noising, contrast adjustment, adaptive Gaussian thresholding).
   - Extracts structured identity fields: Name, Date of Birth (DOB), ID Number, Gender, and Father's Name.
2. **Algorithmic Validation Layer (`validators.py`):**
   - **Aadhaar:** 12-digit Verhoeff Dihedral Checksum calculation ($D_5$ permutation & multiplication tables), checks for invalid starting digits (`0` or `1`).
   - **PAN Card:** Income Tax Department syntax check (`AAAAA9999A`), entity code verification (4th character: `P` for Individual, `C` for Company, etc.), and surname initial correlation.
3. **Database Cross-Check (`db.py`):**
   - Connects to Supabase PostgreSQL table `government_id_registry`.
   - Automatic graceful fallback to an in-memory mock registry for offline/zero-config testing.
4. **FastAPI Route (`main.py`):**
   - `POST /extract-and-validate`: Ingests multi-part image, runs OCR + validation + cross-check, and returns a structured forensic verdict and telemetry trace.

---

## ⚡ Quick Start

### 1. Setup Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note on OCR Engine (Tesseract):**
> Make sure `tesseract` is installed on your OS:
> - **macOS:** `brew install tesseract`
> - **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
> - **Windows:** Download installer from UB-Mannheim GitHub.

### 2. Configure Environment (Optional)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(If Supabase credentials are left empty, the server automatically uses the built-in mock database).*

### 3. Run FastAPI Server

```bash
uvicorn main:app --reload --port 8000
```
Open **Interactive API Docs (Swagger UI)** at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Validation Tests

Verify the Verhoeff checksum algorithm and PAN rules:
```bash
python test_api.py
```

---

## 🗄️ Supabase Setup & Seed Data

1. Open your Supabase project SQL Editor.
2. Paste and run the contents of [supabase_schema.sql](file:///Users/rudrapratap/sih/sih26188/backend/supabase_schema.sql).
3. Alternatively, run the Python seed script:
   ```bash
   python seed_data.py
   ```
