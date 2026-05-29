# RAYA Hospital Kiosk

RAYA is a smart, multi-modal hospital kiosk designed to run locally. It features a touch-screen interface, a background facial recognition check, and a push-to-talk Voice Assistant for registering new patients (ABHA profiles) completely hands-free.

## Architecture
- **Frontend**: Next.js, TailwindCSS, Framer Motion, Web Speech API
- **Backend**: FastAPI, SQLite, SQLAlchemy

## Prerequisites
- Node.js (v18+)
- Python (3.10+)

## Running the Application

### 1. Start the Backend (FastAPI)
The backend manages the SQLite databases, face matching endpoints, token generation, and ABHA mock integration.

```bash
cd Raya/backend

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Start the server (auto-reloads and auto-creates DB tables)
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Frontend (Next.js)
The frontend serves the Kiosk UI, Face Scanner, and Voice Assistant.

```bash
cd Raya/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The application will be available at `http://localhost:3000`.

## Features
- **Department Selection**: Tap to select a department or use the "Tap to Record Symptoms" button.
- **Voice Assistant**: Say "Nahi" when asked for an ABHA number to trigger a full conversational flow asking for Aadhaar, Mobile, and OTP.
- **Face Recognition**: Silently logs returning users in when they click the Voice Assistant.
