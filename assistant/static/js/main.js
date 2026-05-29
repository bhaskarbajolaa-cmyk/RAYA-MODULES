// Global State
let selectedLang = 'en'; // 'en' or 'hi'
let isScanActive = true;
let scanInterval = null;
let scanInProgress = false;
let lastExtractedFaceEncoding = null;

// Target patient demographic details for current session
let currentPatient = {
    name: null,
    age: null,
    gender: null,
    mobile: null,
    abha_number: null
};

// Web Speech APIs
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let speechRecognition = null;
if (SpeechRecognition) {
    speechRecognition = new SpeechRecognition();
    speechRecognition.continuous = false;
    speechRecognition.interimResults = false;
}

// DOM Elements
const video = document.getElementById('webcam');
const canvas = document.getElementById('snapshot-canvas');
const scannerRing = document.getElementById('scanner-ring');
const cameraStatusTxt = document.getElementById('camera-status-text');
const cameraSubTxt = document.getElementById('camera-sub-text');
const langSwitch = document.getElementById('lang-switch');
const btnResetDb = document.getElementById('btn-reset-db');
const btnManualScan = document.getElementById('btn-manual-scan');

// Form Actions
const btnShowLogin = document.getElementById('btn-show-login');
const btnShowRegister = document.getElementById('btn-show-register');
const btnLoginSearch = document.getElementById('btn-login-search');
const btnSubmitRegister = document.getElementById('btn-submit-register');
const btnSubmitSymptoms = document.getElementById('btn-submit-symptoms');
const btnMic = document.getElementById('btn-mic');

// Text Inputs
const inputLoginAbha = document.getElementById('login-abha-id');
const regName = document.getElementById('reg-name');
const regDob = document.getElementById('reg-dob');
const regGender = document.getElementById('reg-gender');
const regMobile = document.getElementById('reg-mobile');
const regPrefix = document.getElementById('reg-prefix');
const txtSymptomsInput = document.getElementById('txt-symptoms-input');

// Message Containers
const loginError = document.getElementById('login-error');
const registerError = document.getElementById('register-error');
const voicePreview = document.getElementById('voice-preview');
const voiceStatusTxt = document.getElementById('voice-status-txt');

// Flow Navigation Helper
function showCard(cardId) {
    document.querySelectorAll('.flow-card').forEach(card => card.classList.remove('active'));
    document.getElementById(cardId).classList.add('active');
}

// Visual feedback scanner rings
function setScannerState(state) {
    scannerRing.className = 'scanner-ring-container'; // clear states
    if (state === 'idle') scannerRing.classList.add('state-idle');
    else if (state === 'scan') scannerRing.classList.add('state-scan');
    else if (state === 'success') scannerRing.classList.add('state-success');
    else if (state === 'warning') scannerRing.classList.add('state-warning');
    else if (state === 'danger') scannerRing.classList.add('state-danger');
}

// Text-to-Speech Engine
function speak(text, callback) {
    if (!window.speechSynthesis) {
        if (callback) callback();
        return;
    }

    // Stop any current speaking
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    // Set appropriate accent
    if (selectedLang === 'hi') {
        utterance.lang = 'hi-IN';
    } else {
        utterance.lang = 'en-IN'; // Indian English
    }

    utterance.onend = function () {
        if (callback) callback();
    };

    utterance.onerror = function () {
        if (callback) callback();
    };

    window.speechSynthesis.speak(utterance);
}

// Chat bubbles helper
function addChatMessage(sender, text) {
    const chatContainer = document.getElementById('chat-messages');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerText = text;
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Camera stream initializer
async function initWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 },
            audio: false
        });
        video.srcObject = stream;
    } catch (err) {
        console.error("Camera access blocked: ", err);
        cameraStatusTxt.innerText = "Camera Blocked";
        cameraSubTxt.innerText = "Please check browser camera permissions.";
        setScannerState('danger');
    }
}

// Capture current video frame and return as base64 string
function captureFrame() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        // Flip image horizontally so it matches mirror stream
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        // Reset transform
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        return canvas.toDataURL('image/jpeg', 0.85);
    }
    return null;
}

// Automated Face Scan Loop
async function triggerFaceScan() {
    if (!isScanActive || scanInProgress) return;

    const base64Img = captureFrame();
    if (!base64Img) return;

    scanInProgress = true;
    setScannerState('scan');
    cameraStatusTxt.innerText = "Analyzing Face...";

    try {
        const response = await fetch('/api/face-scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: base64Img })
        });
        const data = await response.json();

        if (data.status === 'recognized') {
            handleScanSuccess(data);
        } else if (data.status === 'unrecognized') {
            handleScanUnknown(data);
        } else {
            // no face found
            setScannerState('idle');
            cameraStatusTxt.innerText = "Scanning Face...";
            cameraSubTxt.innerText = "Please look directly at the camera";
        }
    } catch (err) {
        console.error("Scan API Error:", err);
        setScannerState('idle');
    } finally {
        scanInProgress = false;
    }
}

// Recognised Repeating Customer
function handleScanSuccess(data) {
    isScanActive = false; // pause scanning
    scanInProgress = false;
    setScannerState('success');

    const patientName = data.user.full_name;
    cameraStatusTxt.innerText = "Face Verified";
    cameraSubTxt.innerText = `Welcome back, ${patientName}`;

    // Store demographic details
    currentPatient.name = patientName;
    currentPatient.abha_number = data.user.abha_number;

    if (data.abha_profile) {
        currentPatient.age = calculateAge(data.abha_profile.date_of_birth);
        currentPatient.gender = data.abha_profile.gender;
        currentPatient.mobile = data.abha_profile.mobile_number;

        // Show history table
        showHistoryLogs(data.abha_profile, data.history);
    }

    // Greet user and begin interview
    const greetingMsg = selectedLang === 'hi' ?
        `नमस्ते ${patientName}, अस्पताल में आपका स्वागत है। आज आपको क्या परेशानी हो रही है?` :
        `Namaste ${patientName}, welcome back. What symptoms are you experiencing today?`;

    speak(greetingMsg, () => {
        setupTriageSession(patientName);
    });
}

// Unregistered Face
function handleScanUnknown(data) {
    isScanActive = false;
    scanInProgress = false;
    setScannerState('warning');
    cameraStatusTxt.innerText = "Unregistered Face";
    cameraSubTxt.innerText = "Please log in manually or register.";

    // Store embedding vector for registration linkage
    lastExtractedFaceEncoding = data.face_encoding;

    const speakPrompt = selectedLang === 'hi' ?
        "नमस्ते, आपका चेहरा पंजीकृत नहीं है। कृपया नया आयुष्मान कार्ड बनाएं या लॉग इन करें।" :
        "Namaste, welcome to the hospital. Your face is unrecognized. Please create a new ABHA ID or search manually.";

    speak(speakPrompt);
    showCard('card-welcome');
}

// Show History logs at footer
function showHistoryLogs(profile, history) {
    document.getElementById('prof-abha').innerText = profile.abha_number;
    document.getElementById('prof-address').innerText = profile.abha_address;
    document.getElementById('prof-dob').innerText = `${profile.date_of_birth} (${calculateAge(profile.date_of_birth)} Years)`;
    document.getElementById('prof-gender').innerText = profile.gender;
    document.getElementById('prof-mobile').innerText = profile.mobile_number;

    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';

    if (history && history.length > 0) {
        history.forEach(enc => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${enc.date}</td>
                <td><strong>${enc.token_number}</strong></td>
                <td><span class="badge blue">${enc.department}</span></td>
                <td>${enc.symptoms}</td>
                <td>${enc.clinical_summary}</td>
            `;
            tbody.appendChild(tr);
        });
        document.getElementById('history-patient-badge').innerText = "Repeating Patient";
    } else {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="5" style="text-align:center; color:var(--text-secondary);">No previous hospital check-in logs found.</td>`;
        tbody.appendChild(tr);
        document.getElementById('history-patient-badge').innerText = "New Patient Link";
    }

    document.getElementById('patient-history-section').style.display = 'block';
}

// Start Triage UI
function setupTriageSession(name) {
    showCard('card-triage');
    document.getElementById('triage-patient-name').innerText = name;

    // Reset Chat panel
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = '';

    const initialText = selectedLang === 'hi' ?
        "नमस्ते, मैं आपकी कैसे मदद कर सकती हूँ? कृपया मुझे अपनी बीमारी के बारे में बताएं।" :
        "Namaste, I am your hospital assistant. How can I help you today? Please tell me your symptoms.";

    addChatMessage('assistant', initialText);

    // Auto trigger microphone listening
    startListening();
}

// Voice Listening (Speech-to-Text)
function startListening() {
    if (!speechRecognition) {
        voiceStatusTxt.innerText = "Speech-to-Text Unavailable";
        return;
    }

    // Configure voice language
    speechRecognition.lang = selectedLang === 'hi' ? 'hi-IN' : 'en-IN';

    btnMic.className = "btn-mic-active listening";
    voiceStatusTxt.innerText = "Listening...";
    voicePreview.innerText = "Speak now...";

    try {
        speechRecognition.start();
    } catch (err) {
        // Recognition already running or block
    }

    speechRecognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        voicePreview.innerText = `"${transcript}"`;
        addChatMessage('patient', transcript);
        btnMic.className = "btn-mic-active muted";
        voiceStatusTxt.innerText = "Processing details...";

        submitSymptoms(transcript);
    };

    speechRecognition.onerror = function (event) {
        console.error("Speech Recognition error: ", event.error);
        btnMic.className = "btn-mic-active muted";
        voiceStatusTxt.innerText = "Mic Idle";
        voicePreview.innerText = "Please try again or type below.";
    };

    speechRecognition.onend = function () {
        btnMic.className = "btn-mic-active muted";
        voiceStatusTxt.innerText = "Mic Idle";
    };
}

// Submit Symptoms to Backend
async function submitSymptoms(symptomsText) {
    if (!symptomsText || symptomsText.trim().length < 3) return;

    try {
        const payload = {
            abha_number: currentPatient.abha_number,
            patient_name: currentPatient.name || "Unknown Patient",
            age: currentPatient.age || 25,
            gender: currentPatient.gender || "M",
            mobile: currentPatient.mobile || "0000000000",
            symptoms: symptomsText
        };

        const response = await fetch('/api/triage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            displayTokenResult(data.triage);
        } else {
            addChatMessage('assistant', "I encountered an error analyzing your symptoms. Let me register you in General Medicine.");
            setTimeout(() => {
                displayTokenResult({
                    token_number: "GEN-999",
                    major_id: 1,
                    department: "GENERAL MEDICINE",
                    priority: "NORMAL",
                    pdf_url: "#"
                });
            }, 3000);
        }
    } catch (err) {
        console.error("Triage Error:", err);
    }
}

// Display Generated Token
function displayTokenResult(triage) {
    showCard('card-token');

    // Set UI Details
    document.getElementById('lbl-token-number').innerText = triage.token_number;
    document.getElementById('lbl-token-queue').innerText = triage.major_id;
    document.getElementById('lbl-token-dept').innerText = triage.department;
    document.getElementById('lbl-token-priority').innerText = triage.priority;

    // Set priority badge styling
    const badge = document.getElementById('token-badge-priority');
    badge.innerText = triage.priority;
    badge.className = "badge";
    if (triage.priority.includes("RED") || triage.priority.includes("EMERGENCY")) badge.classList.add("red");
    else if (triage.priority.includes("YELLOW") || triage.priority.includes("URGENT")) badge.classList.add("gold");
    else badge.classList.add("green");

    // Map PDF download link; preview frame removed.
    const pdfFrame = document.getElementById('pdf-preview-frame');
    if (pdfFrame) pdfFrame.src = triage.pdf_url;
    const downloadLink = document.getElementById('lnk-download-pdf');
    if (downloadLink) downloadLink.href = triage.pdf_url;

    // Announce token voice
    const announceMsg = selectedLang === 'hi' ?
        `पंजीकरण सफल रहा। आपका टोकन नंबर ${triage.token_number} है। कृपया ${triage.department} विभाग में जाएं।` :
        `Registration complete. Your token number is ${triage.token_number}. Please proceed to ${triage.department}.`;

    speak(announceMsg);
}

// Reset Kiosk Kiosk Flow
function resetKiosk() {
    isScanActive = true;
    lastExtractedFaceEncoding = null;
    currentPatient = { name: null, age: null, gender: null, mobile: null, abha_number: null };

    document.getElementById('patient-history-section').style.display = 'none';
    showCard('card-welcome');
    setScannerState('idle');
    cameraStatusTxt.innerText = "Scanning face...";
    cameraSubTxt.innerText = "Please stand in front of the scanner";
}

// Search Central ABHA registry manually
async function searchManualABHA() {
    const abhaId = inputLoginAbha.value.trim();
    if (!abhaId) return;

    loginError.style.display = 'none';

    try {
        const response = await fetch('/api/abha/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ abha_id: abhaId })
        });
        const data = await response.json();

        if (data.status === 'success' && data.found) {
            isScanActive = false;
            setScannerState('success');

            const profile = data.profile;
            currentPatient.name = profile.full_name;
            currentPatient.abha_number = profile.abha_number;
            currentPatient.age = calculateAge(profile.date_of_birth);
            currentPatient.gender = profile.gender;
            currentPatient.mobile = profile.mobile_number;

            showHistoryLogs(profile, data.history);

            // Greets patient
            const greetText = selectedLang === 'hi' ?
                `सत्यापित! स्वागत है ${profile.full_name}। चलिए आपकी जांच शुरू करते हैं।` :
                `Verified! Welcome back ${profile.full_name}. Let's begin your symptom check.`;

            speak(greetText, () => {
                // Link current face embedding dynamically if scanned earlier
                if (lastExtractedFaceEncoding) {
                    linkBiometrics(profile.full_name, profile.abha_number);
                }
                setupTriageSession(profile.full_name);
            });
        } else {
            loginError.innerText = "ABHA profile not found. Please check spelling or register.";
            loginError.style.display = 'block';
            const message = selectedLang === 'en' ? "Profile not found." : "प्रोफ़ाइल नहीं मिली।";
            speak(message);
        }
    } catch (err) {
        console.error("ABHA lookup error: ", err);
    }
}

// Register Face Embedding with ABHA Number
async function linkBiometrics(name, abhaNum) {
    if (!lastExtractedFaceEncoding) return;
    try {
        await fetch('/api/register-face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                full_name: name,
                face_encoding: lastExtractedFaceEncoding,
                abha_number: abhaNum
            })
        });
        console.log("Registered face biometrics linked with ABHA.");
    } catch (err) {
        console.error("Biometric link error: ", err);
    }
}

// Register new ABHA Card
async function createNewABHACard() {
    const name = regName.value.trim();
    const dob = regDob.value;
    const gender = regGender.value;
    const mobile = regMobile.value.trim();
    const prefix = regPrefix.value.trim();

    if (!name || !dob || !mobile || !prefix) {
        registerError.innerText = "Please fill in all demographic details.";
        registerError.style.display = 'block';
        return;
    }

    registerError.style.display = 'none';

    try {
        const payload = {
            full_name: name,
            date_of_birth: dob,
            gender: gender,
            mobile_number: mobile,
            preferred_prefix: prefix
        };

        const response = await fetch('/api/abha/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            const profile = data.profile;
            currentPatient.name = profile.full_name;
            currentPatient.abha_number = profile.abha_number;
            currentPatient.age = calculateAge(profile.date_of_birth);
            currentPatient.gender = profile.gender;
            currentPatient.mobile = profile.mobile_number;

            showHistoryLogs(profile, []);

            // Greets new patient
            const successText = selectedLang === 'hi' ?
                `सफलतापूर्वक नया डिजिटल हेल्थ कार्ड बनाया गया। आयुष्मान नंबर: ${profile.abha_number}।` :
                `Successfully created your new ABHA account. Your ABHA ID is ${profile.abha_number}.`;

            speak(successText, () => {
                // Link current face embedding dynamically
                if (lastExtractedFaceEncoding) {
                    linkBiometrics(profile.full_name, profile.abha_number);
                }
                setupTriageSession(profile.full_name);
            });
        } else {
            registerError.innerText = "Error generating ABHA account.";
            registerError.style.display = 'block';
        }
    } catch (err) {
        console.error("ABHA Registration failed: ", err);
    }
}

// Reset and seed database demo helper
async function resetDatabaseDemo() {
    btnResetDb.innerText = "Resetting...";
    try {
        const response = await fetch('/api/init-db', { method: 'POST' });
        const data = await response.json();
        if (data.status === 'success') {
            speak("Registry database reset and seeded successfully.");
            alert("National ABHA and Local Biometric registries reset!");
            resetKiosk();
        }
    } catch (err) {
        console.error("DB Reset failed: ", err);
    } finally {
        btnResetDb.innerText = "Reset DB";
    }
}

// Utility: Calculate Age from YYYY-MM-DD
function calculateAge(dobStr) {
    const dob = new Date(dobStr);
    const diff_ms = Date.now() - dob.getTime();
    const age_dt = new Date(diff_ms);
    return Math.abs(age_dt.getUTCFullYear() - 1970);
}

// EVENT LISTENERS REGISTER
langSwitch.addEventListener('change', (e) => {
    selectedLang = e.target.checked ? 'hi' : 'en';
    resetKiosk();
});

btnResetDb.addEventListener('click', resetDatabaseDemo);
btnManualScan.addEventListener('click', triggerFaceScan);

btnShowLogin.addEventListener('click', () => showCard('card-login'));
btnShowRegister.addEventListener('click', () => showCard('card-register'));

btnLoginSearch.addEventListener('click', searchManualABHA);
btnSubmitRegister.addEventListener('click', createNewABHACard);

btnMic.addEventListener('click', startListening);

btnSubmitSymptoms.addEventListener('click', () => {
    const txt = txtSymptomsInput.value.trim();
    if (txt) {
        addChatMessage('patient', txt);
        txtSymptomsInput.value = '';
        submitSymptoms(txt);
    }
});

txtSymptomsInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const txt = txtSymptomsInput.value.trim();
        if (txt) {
            addChatMessage('patient', txt);
            txtSymptomsInput.value = '';
            submitSymptoms(txt);
        }
    }
});

// App Startup
window.addEventListener('load', () => {
    initWebcam();
    // Run face scan matching every 3.5 seconds
    scanInterval = setInterval(triggerFaceScan, 3500);
});
