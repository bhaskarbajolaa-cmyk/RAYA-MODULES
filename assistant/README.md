# Hospital AI Receptionist Kiosk (ABDM Integrated)

A modern, highly integrated, and workable outpatient receptionist kiosk for government hospitals. It unifies facial biometric identification, simulated ABHA (Ayushman Bharat Health Account) records, digital health card generation, automated speech-guided clinical triage, and token printing.

## Core Features

1. **Biometric Face Verification**:
   - Captures real-time camera frames and extracts face encodings using the `face_recognition` library.
   - Performs nearest-neighbor similarity search in SQLite using a custom compiled C-based `euclidean_distance` function.
   
2. **ABHA Patient Registry Linkage**:
   - Queries a simulated central ABHA registry (`abha.db`) for demographic records.
   - Automatically identifies repeating patients and loads their history of past hospital visits.
   
3. **Conversational Clinical Triage**:
   - Walks the user through an interview using Hindi/English speech synthesis (`window.speechSynthesis`) and voice input transcription (`webkitSpeechRecognition`).
   - Determines the department routing (Cardiology, Gynecology, Dental, ENT, Orthopedics, Gastroenterology, Dermatology, Ophthalmology, Neurology, General Medicine, or Emergency) and maps the triage priority level:
     - 🔴 **EMERGENCY (RED)**: Immediate medical threat.
     - 🟡 **URGENT (YELLOW)**: Severe but stable.
     - 🟢 **NORMAL (GREEN)**: Standard clinic queue.
   - Uses a robust keyword-based rule parser fallback when offline, or connects to a local **Ollama** server (`deepseek-r1:1.5b`) for clinical reasoning.

4. **Token Generator & PDF Printout**:
   - Creates sequential token numbers (e.g. `CARD-001`) and logs encounters in the local hospital database.
   - Dynamically compiles a beautiful pocket-sized PDF ticket (`fpdf` library) and displays it directly in the UI dashboard for downloading or printing.

5. **Premium UI Dashboard**:
   - Dark obsidian glassmorphic card design with active neon glowing video rings indicating scanner state.
   - Conversational chat transcript panel, mobile-friendly forms, and interactive historical tables.

---

## Workspace Architecture

```
assistant/
├── app.py                  # FastAPI server and routing REST endpoints
├── abha_client.py          # Simulated Central ABDM Registry client
├── biometric_matcher.py    # Face recognition & dlib vector calculations
├── database.py             # Database creators, custom sqlite extensions, and seed data
├── triage_processor.py     # Symptom analysis and pocket PDF ticket generation
├── README.md               # Documentation
│
├── abha.db                 # SQLite Simulated Central ABDM patient profiles
├── raya.db                 # SQLite local face embedding biometric records
├── hospital.db             # SQLite local hospital encounters & patients log
│
└── static/                 # Front-end Assets
    ├── index.html          # Receptionist Kiosk main HTML dashboard
    ├── css/
    │   └── styles.css      # Custom stylesheet (Glassmorphism & Glowing states)
    ├── js/
    │   └── main.js         # Webcam canvas stream, speech API loops, and AJAX hooks
    └── tokens/             # Generated PDF ticket documents
```

---

## Database Schemas

### 1. Biometric Local Registry (`raya.db`)
- `raya_users`:
  - `id` (INTEGER PRIMARY KEY)
  - `full_name` (TEXT)
  - `face_encoding` (BLOB) - 128-dimensional float32 vector
  - `abha_number` (TEXT)
  - `last_checkin` (TIMESTAMP)

### 2. National ABDM Registry (`abha.db`)
- `patients`:
  - `abha_number` (TEXT PRIMARY KEY) - Format: `91-XXXX-XXXX-XXXX`
  - `abha_address` (TEXT UNIQUE) - Format: `username@abdm`
  - `full_name` (TEXT)
  - `date_of_birth` (TEXT) - YYYY-MM-DD
  - `gender` (TEXT) - M/F/O
  - `mobile_number` (TEXT)
  - `health_records` (TEXT JSON blob)

### 3. Local Hospital Registry (`hospital.db`)
- `patients`:
  - `id` (INTEGER PRIMARY KEY)
  - `name` (TEXT), `abha_number` (TEXT), `age` (INTEGER), `gender` (TEXT), `mobile` (TEXT)
- `encounters`:
  - `id` (INTEGER PRIMARY KEY)
  - `patient_id` (INTEGER) - Foreign key
  - `date` (TEXT)
  - `token_number` (TEXT)
  - `department` (TEXT)
  - `symptoms` (TEXT)
  - `priority` (TEXT)
  - `clinical_summary` (TEXT)

---

## Run Kiosk Locally

### Prerequisites
Make sure your system contains a working camera and use Google Chrome or Microsoft Edge (to ensure full compatibility with the Web Speech API).

### Startup Command
Run the server using the pre-configured virtual environment containing biometric libraries:
```powershell
B:\RAYA\RAYA-MODULES\TOKENN\env\Scripts\python.exe b:\RAYA\assistant\app.py
```

Open your browser to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)
