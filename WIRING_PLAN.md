# Brockston IDE - Complete Wiring & Rebuild Plan

**Mission:** Get this IDE working for students with autism, nonverbal/Down syndrome communication needs.  
**Status:** Complete module rebuild (damaged, rebuilding from scratch)  
**Date:** May 8, 2026

---

## 🎯 CORE SYSTEMS TO WIRE

### 1. **Speech System** (Input/Output)
**Goal:** Students can speak to ask questions, IDE responds with audio/text

**Components:**
- Backend: `speech_service.py` (TTS synthesis)
- Backend: `real_speech_recognition.py` (STT - mock for now)
- API: `/api/transcribe` - audio → text
- API: `/api/speak` - text → audio
- API: `/ws/speech` - WebSocket for streaming

**Status:** 
- ✅ ElevenLabs removed
- ❌ No actual speech-to-text (using mock)
- ❌ No real TTS (using mock MP3)
- ❌ APIs not wired to main.py

**What Needs Work:**
1. Remove Vosk references from all files
2. Create `/api/transcribe` endpoint (accept audio bytes, return text)
3. Create `/api/speak` endpoint (accept text, return audio bytes)
4. Wire enhanced_speech_recognition.py to main.py
5. Add WebSocket for streaming

---

### 2. **Code Execution System** (Run Code)
**Goal:** Students write code, press "Run", code executes safely with output

**Components:**
- `brockston_client.py` - LLM interaction ✅ (exists, works)
- Need: Sandboxed Python executor
- API: `/api/execute` - run code with timeout/limits
- API: `/api/test` - run with test cases

**Status:**
- ✅ Ollama integration works
- ❌ No code execution endpoint
- ❌ No sandbox security

**What Needs Work:**
1. Create `code_executor.py` with timeout/limits
2. Add `/api/execute` POST endpoint
3. Add `/api/test` POST endpoint
4. Wire to WebSocket terminal

---

### 3. **Learning System** (Help Students Learn)
**Goal:** Track student progress, identify struggles, provide scaffolding

**Components:**
- `proactive_intelligence.py` - Learning detection ✅ (exists)
- `autonomous_learning_engine.py` - Self-improvement ✅ (exists)
- Need: Integrate with chat/code endpoints
- API: `/api/explain` - explain concept
- API: `/api/hint` - give hint for problem
- API: `/api/progress` - student progress

**Status:**
- ✅ Learning modules exist
- ❌ Not connected to API
- ❌ No student progress tracking

**What Needs Work:**
1. Create `/api/explain` endpoint
2. Create `/api/hint` endpoint  
3. Create `/api/progress` endpoint
4. Wire learning engine to these endpoints
5. Add student session tracking

---

### 4. **Git/Repository System** (Save Work)
**Goal:** Students save code to Git, track versions, push to repo

**Components:**
- `git_service.py` ✅ (exists, fixed)
- API: `/api/git/clone` - clone repo
- API: `/api/git/commit` - save changes
- API: `/api/git/status` - check status

**Status:**
- ✅ git_service.py working
- ❌ APIs not wired

**What Needs Work:**
1. Create `/api/git/clone` endpoint
2. Create `/api/git/commit` endpoint
3. Create `/api/git/status` endpoint
4. Create `/api/git/remote-url` endpoint

---

### 5. **Frontend Integration** (UI for Students)
**Goal:** Simple, accessible UI students can use

**Components:**
- `frontend/` folder (partial, needs work)
- Need: HTML/JS UI
- Need: WebSocket connections
- Need: Accessible buttons, large text, symbols

**Status:**
- ⚠️ Partial HTML exists
- ❌ Not connected to backend
- ❌ Not accessible

**What Needs Work:**
1. Create simple HTML interface
2. Add WebSocket client
3. Add speech button (if speech available)
4. Add "Run Code" button
5. Add "Ask Derek" chat
6. Add file browser
7. Make highly accessible (big buttons, symbols)

---

## 🔨 EXECUTION ORDER (Priority)

### **PHASE 1: Clean Up & Core APIs (TODAY - 3-4 hours)**
- [ ] Remove ALL Vosk references
- [ ] Update requirements.txt (remove vosk, sounddevice, webrtcvad)
- [ ] Simplify transcriber.py to mock-only
- [ ] Wire main.py core endpoints
- [ ] Create code_executor.py with sandbox
- [ ] Create `/api/execute` endpoint
- [ ] Test with curl/Postman

### **PHASE 2: Speech System (2-3 hours)**
- [ ] Complete speech_service.py
- [ ] Create `/api/transcribe` endpoint (mock for now)
- [ ] Create `/api/speak` endpoint
- [ ] Test speech endpoints
- [ ] Add WebSocket `/ws/speech` (optional)

### **PHASE 3: Learning System (2-3 hours)**
- [ ] Create `/api/explain` endpoint
- [ ] Create `/api/hint` endpoint
- [ ] Create `/api/progress` endpoint
- [ ] Wire proactive_intelligence.py
- [ ] Test learning endpoints

### **PHASE 4: Git System (1-2 hours)**
- [ ] Create `/api/git/*` endpoints
- [ ] Test git operations
- [ ] Add safety checks

### **PHASE 5: Frontend (2-4 hours)**
- [ ] Create simple HTML UI
- [ ] Add WebSocket client
- [ ] Add buttons & forms
- [ ] Make accessible
- [ ] Test end-to-end

### **PHASE 6: Polish & Testing (1-2 hours)**
- [ ] Full end-to-end test
- [ ] Error handling
- [ ] Documentation
- [ ] Quick start for students

---

## 🚀 START NOW: PHASE 1

### Step 1: Remove Vosk (ALL files)
1. transcriber.py - remove vosk imports, simplify to mock
2. brockston_vocal_interface.py - remove vosk checks
3. COMPLETION_REPORT.md - remove vosk mentions
4. requirements.txt - remove vosk, sounddevice, webrtcvad

### Step 2: Wire main.py
Add these endpoints:
```python
@app.post("/api/execute")
async def execute_code(request: ExecuteRequest):
    # Run code in sandbox

@app.post("/api/transcribe")  
async def transcribe_audio(file: UploadFile):
    # Mock: return text

@app.post("/api/speak")
async def synthesize_speech(request: SpeakRequest):
    # Mock: return audio bytes
```

### Step 3: Create code_executor.py
Sandboxed Python execution with timeout/limits

### Step 4: Test Everything
`curl -X POST http://localhost:8000/api/execute -d '{"code": "print(\"hello\")"}'`

---

## 📊 Current Status Dashboard

| Component | Status | Priority | ETC |
|-----------|--------|----------|-----|
| Speech Input | ⚠️ Broken (Vosk) | HIGH | 30m |
| Speech Output | ⚠️ Mock only | HIGH | 20m |
| Code Execution | ❌ Missing | CRITICAL | 1h |
| Learning System | ✅ Modules exist | MEDIUM | 1h |
| Git System | ✅ Service exists | MEDIUM | 45m |
| Frontend | ⚠️ Partial | MEDIUM | 3h |
| Terminal | ✅ Coded | LOW | needs test |
| Chat/AI | ✅ Working | HIGH | ✓ |

**Total Estimated Time: 10-14 hours**  
**Critical Path: Code Execution + Speech (2-3 hours to MVP)**

---

## 🎓 For Your Students

When this is done, they'll have:
- 🎤 Speech input (ask questions)
- 📢 Speech output (Derek responds)
- ⌨️ Code editor (write programs)
- ▶️ Execute button (run code safely)
- 💾 Git save (backup to repository)
- 🧠 Derek AI (help & hints)
- 📈 Progress tracking

Everything accessible, safe, and built with dignity.

---

**Next Action:** Start PHASE 1 wiring. Let's get this working! 💪
