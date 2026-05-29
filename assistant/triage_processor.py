import os
import re
import json
import sqlite3
from datetime import datetime
from typing import Optional, Tuple
from fpdf import FPDF
from database import get_hospital_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_DIR = os.path.join(BASE_DIR, "static", "tokens")
os.makedirs(TOKENS_DIR, exist_ok=True)

class TriageProcessor:
    def __init__(self):
        pass

    def rule_based_triage(self, symptoms_text: str) -> tuple:
        """
        Fallback keyword-based parser that determines department and priority.
        Returns: (dept_name, rgb_color_tuple, priority_level)
        """
        rep = symptoms_text.lower().strip()
        
        # Default values
        dept = "GENERAL MEDICINE"
        color = (0, 128, 0)
        level = "NORMAL (GREEN)"
        
        # 1. Immediate Life-Threatening Emergency Override
        if any(x in rep for x in ["heart attack", "stroke", "unconscious", "passed out", "severe chest pain", "can't breathe", "gasping"]): 
            return "EMERGENCY DEPT", (255, 0, 0), "EMERGENCY (RED)"
            
        # 2. Specific Departments
        if any(x in rep for x in ["heart", "chest pain", "cardiac", "shortness of breath", "palpitation", "heavy chest", "angina"]): 
            dept, color, level = "CARDIOLOGY", (255, 0, 0), "EMERGENCY (RED)"
        elif any(x in rep for x in ["headache", "migraine", "brain", "seizure", "dizzy", "vertigo", "faint", "numbness", "tingling", "paralysis", "concussion", "head injury", "tremor"]): 
            dept, color, level = "NEUROLOGY", (255, 165, 0), "URGENT (YELLOW)"
        elif any(x in rep for x in ["fracture", "bone", "joint", "sprain", "ligament", "ortho", "broken", "twisted ankle", "knee pain", "spine", "shoulder pain", "arthritis", "muscle tear"]): 
            dept, color, level = "ORTHOPEDICS", (255, 165, 0), "URGENT (YELLOW)"
        elif any(x in rep for x in ["stomach", "abdomen", "gastric", "vomit", "puke", "diarrhea", "liver", "constipation", "nausea", "heartburn", "acid reflux", "ulcer", "food poisoning", "loose motion"]): 
            dept, color, level = "GASTROENTEROLOGY", (0, 128, 0), "NORMAL (GREEN)"
        elif any(x in rep for x in ["tooth", "dental", "gum", "dentist", "cavity", "toothache", "root canal", "jaw pain"]): 
            dept, color, level = "DENTAL DEPT", (0, 128, 0), "NORMAL (GREEN)"
        elif any(x in rep for x in ["eye", "vision", "blur", "blind", "cataract", "conjunctivitis", "squint"]): 
            dept, color, level = "OPHTHALMOLOGY", (0, 128, 0), "NORMAL (GREEN)"
        elif any(x in rep for x in ["ear", "nose", "throat", "hearing", "deaf", "sinus", "tonsil", "sore throat", "nosebleed", "swallow"]): 
            dept, color, level = "ENT DEPT", (0, 128, 0), "NORMAL (GREEN)"
        elif any(x in rep for x in ["skin", "rash", "itch", "acne", "pimple", "allergy", "hives", "eczema", "burn", "hair loss", "blister", "dermatitis"]): 
            dept, color, level = "DERMATOLOGY", (0, 128, 0), "NORMAL (GREEN)"
        elif any(x in rep for x in ["pregnancy", "pregnant", "period", "menstruation", "vaginal", "uterus", "cramp", "gynecology", "maternity", "miscarriage"]): 
            dept, color, level = "GYNECOLOGY", (255, 165, 0), "URGENT (YELLOW)"
            
        return dept, color, level

    def determine_triage(self, symptoms_text: str) -> tuple:
        """
        Attempts to use Ollama's deepseek-r1:1.5b for triage.
        If it fails, falls back to the rule-based approach.
        """
        # Try local Ollama first
        try:
            import ollama
            prompt = f"""
            Identify the hospital department and triage priority from this patient description:
            "{symptoms_text}"

            Select from these departments:
            - EMERGENCY DEPT (Use for immediate life-threatening conditions like severe chest pain, stroke, breathing failure, etc.)
            - CARDIOLOGY
            - NEUROLOGY
            - ORTHOPEDICS
            - GASTROENTEROLOGY
            - DENTAL DEPT
            - OPHTHALMOLOGY
            - ENT DEPT
            - DERMATOLOGY
            - GYNECOLOGY
            - GENERAL MEDICINE (Default fallback)

            Select from these priorities:
            - EMERGENCY (RED) (Immediate threat to life)
            - URGENT (YELLOW) (Severe but not life-threatening)
            - NORMAL (GREEN) (Standard clinic checkup)

            Respond ONLY in a strict JSON format with keys:
            - "department": The department name.
            - "priority": The priority level.
            - "summary": A concise bulleted clinical summary of findings in English (max 3 bullet points).
            """
            response = ollama.chat(
                model='deepseek-r1:1.5b',
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 200}
            )
            raw = response['message']['content']
            # Strip deepseek thoughts if present
            clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            clean = clean.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            
            dept = data.get("department", "GENERAL MEDICINE").upper()
            priority = data.get("priority", "NORMAL (GREEN)").upper()
            summary = data.get("summary", "")
            
            # Map colors
            if "RED" in priority or "EMERGENCY" in priority:
                color = (255, 0, 0)
                priority = "EMERGENCY (RED)"
            elif "YELLOW" in priority or "URGENT" in priority:
                color = (255, 165, 0)
                priority = "URGENT (YELLOW)"
            else:
                color = (0, 128, 0)
                priority = "NORMAL (GREEN)"
                
            return dept, color, priority, summary
        except Exception:
            # Fallback to rule based
            dept, color, level = self.rule_based_triage(symptoms_text)
            summary = f"Patient presented with symptoms: {symptoms_text}."
            return dept, color, level, summary

    def process_encounter(self, abha_number: Optional[str], patient_name: str, age: int, gender: str, mobile: str, symptoms: str) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 1. Run Triage
        dept, color, level, summary = self.determine_triage(symptoms)
        
        # 2. Get Database Connection & Create/Lookup Patient
        with get_hospital_connection() as conn:
            cursor = conn.cursor()
            
            # Find patient ID or insert
            if abha_number:
                cursor.execute("SELECT id FROM patients WHERE abha_number = ?", (abha_number,))
                row = cursor.fetchone()
            else:
                cursor.execute("SELECT id FROM patients WHERE name = ? AND mobile = ?", (patient_name, mobile))
                row = cursor.fetchone()
                
            if row:
                patient_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO patients (name, abha_number, age, gender, mobile) VALUES (?, ?, ?, ?, ?)",
                    (patient_name, abha_number, age, gender, mobile)
                )
                patient_id = cursor.lastrowid
                
            # Count today's total encounters
            cursor.execute("SELECT COUNT(*) FROM encounters WHERE date = ?", (today,))
            total_today = cursor.fetchone()[0]
            
            # Count department specific encounters today
            cursor.execute("SELECT COUNT(*) FROM encounters WHERE date = ? AND department = ?", (today, dept))
            dept_today = cursor.fetchone()[0]
            
            major_id = total_today + 1
            dept_code = dept[:4].upper()
            token_number = f"{dept_code}-{(dept_today + 1):03d}"
            
            # Save encounter
            cursor.execute(
                """
                INSERT INTO encounters (patient_id, date, token_number, department, symptoms, priority, clinical_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (patient_id, today, token_number, dept, symptoms, level, summary)
            )
            conn.commit()

        # 3. Generate PDF
        pdf_path = self.generate_pdf_ticket(patient_name, age, gender, mobile, today, token_number, major_id, dept, level, color, summary)
        
        return {
            "token_number": token_number,
            "major_id": major_id,
            "department": dept,
            "priority": level,
            "clinical_summary": summary,
            "pdf_url": f"/static/tokens/{token_number}.pdf"
        }

    def generate_pdf_ticket(self, name: str, age: int, gender: str, mobile: str, date_str: str, token_num: str, major_id: int, dept: str, level: str, color: tuple, summary: str) -> str:
        pdf_filename = f"{token_num}.pdf"
        pdf_path = os.path.join(TOKENS_DIR, pdf_filename)
        
        pdf = FPDF(format=(100, 150)) # Pocket ticket size: 100mm wide, 150mm high
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, "GOVT HOSPITAL KIOSK", align='C', ln=1)
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, "Smart Receptionist & Triage", align='C', ln=1)
        pdf.ln(4)
        
        # Token Highlight Box
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(5, pdf.get_y(), 90, 28, 'F')
        
        pdf.set_y(pdf.get_y() + 2)
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(0)
        pdf.cell(0, 12, token_num, align='C', ln=1)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, f"Queue No: {major_id} | Date: {date_str}", align='C', ln=1)
        pdf.ln(5)
        
        # Priority Bar
        pdf.set_fill_color(*color)
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f" DEPT: {dept} | {level}", fill=True, align='C', ln=1)
        pdf.ln(4)
        
        # Patient Details
        pdf.set_text_color(0)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 5, f"PATIENT: {name.upper()}", ln=1)
        pdf.set_font("Arial", '', 8.5)
        pdf.cell(0, 5, f"Age: {age}  |  Gender: {gender}  |  Mobile: {mobile}", ln=1)
        pdf.ln(2)
        pdf.line(5, pdf.get_y(), 95, pdf.get_y())
        pdf.ln(3)
        
        # Clinical Summary
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 5, "CLINICAL SUMMARY & FINDINGS:", ln=1)
        pdf.set_font("Arial", '', 8)
        
        # Split summary into lines/bullets
        lines = summary.split('\n')
        for line in lines:
            line = line.replace('–', '-').replace('—', '-').replace('”', '"').replace('“', '"').replace('*', '').replace('#', '').strip()
            if line:
                # Wrap text properly
                pdf.multi_cell(0, 4, f"- {line}")
                
        # Footer
        pdf.set_y(-12)
        pdf.set_font("Arial", 'I', 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 4, "Presented at outpatient desk upon call.", align='C', ln=1)
        pdf.cell(0, 3, "Powered by RAYA AI Receptionist Kiosk", align='C', ln=1)
        
        pdf.output(pdf_path)
        return pdf_path
