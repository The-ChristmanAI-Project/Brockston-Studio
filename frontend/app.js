/
  BROCKSTON Studio - Frontend Logic
  FULL RESTORATION: Maintaining Visual Sovereignty and Uplink.
/

const BACKEND_URL = "http://127.0.0.1:5055";

// ============================================================================
// File Explorer
// ============================================================================

let currentExplorerPath = "";

// Unified file loader for both root and nested paths
async function loadFiles(path = "") {
    // Prefer the structured explorer list if present, otherwise fall back
    const explorer =
        elements?.fileList || document.getElementById("project-explorer");
    if (!explorer) return;

    try {
        // If a path is provided, use the API that accepts ?path=
        const url = path
            ? `/api/files?path=${encodeURIComponent(path)}`
            : `${BACKEND_URL}/api/files`;

        const response = await fetch(url);
        if (!response.ok) throw new Error("HTTP " + response.status);

        const data = await response.json();
        const files = data.files || [];

        explorer.innerHTML = "";

        // Back button when not at workspace root
        if (currentExplorerPath !== "") {
            const backBtn = document.createElement("div");
            backBtn.className = "file-item";
            backBtn.innerHTML = '<i class="fas fa-arrow-left"></i> ..';
            backBtn.onclick = () => {
                const parts = currentExplorerPath.split("/").filter((p) => p);
                parts.pop();
                currentExplorerPath = parts.join("/");
                loadFiles(currentExplorerPath);
            };
            explorer.appendChild(backBtn);
        }

        if (files.length === 0) {
            explorer.innerHTML =
                "<div class='p-4 text-gray-500 text-xs'>Workspace empty.</div>";
            return;
        }

        // Support both simple string arrays and {name,type} objects
        files.forEach((file) => {
            const isObject = typeof file === "object";
            const name = isObject ? file.name : file;
            const type = isObject ? file.type : "file";
            const isFolder = type === "folder";

            const el = document.createElement("div");
            el.className =
                "file-item p-3 hover:bg-gray-800/50 cursor-pointer text-sm border-b border-orange-500/20 transition-all duration-200 flex items-center group";

            const icon = isFolder ? "📁" : "📄";

            el.innerHTML = `
                <span class="mr-3 text-orange-500/50 group-hover:text-orange-500">${icon}</span>
                <span class="text-gray-300 group-hover:text-white">${name}</span>
            `;

            if (isFolder) {
                el.onclick = () => {
                    currentExplorerPath = currentExplorerPath
                        ? `${currentExplorerPath}/${name}`
                        : name;
                    loadFiles(currentExplorerPath);
                };
            } else {
                const filepath = currentExplorerPath
                    ? `${currentExplorerPath}/${name}`
                    : name;
                el.onclick = () => openFileFromExplorer(filepath);
            }

            explorer.appendChild(el);
        });
    } catch (err) {
        explorer.innerHTML = `
            <div class="p-4 border-l-2 border-red-500 bg-red-950/20">
                <div class="text-red-500 text-xs font-bold uppercase tracking-widest">Uplink Offline</div>
                <div class="text-red-400/60 text-[10px] mt-1">${err.message}</div>
            </div>`;
    }
}

// Get editor content (works with textarea)
function getEditorContent() {
    if (elements.editorContent) {
        return elements.editorContent.value;
    }
    return state.editor ? state.editor.getValue() : "";
}

// Set editor content (works with textarea)
function setEditorContent(content) {
    if (elements.editorContent) {
        elements.editorContent.value = content;
    } else if (state.editor) {
        state.editor.setValue(content);
    }
}

// Handle opening a file from file explorer
async function openFileFromExplorer(filepath) {
    showLoading();

    try {
        const response = await fetch(
            `/api/read_file?filename=${encodeURIComponent(filepath)}`
        );

        if (!response.ok) {
            throw new Error("Read failed");
        }

        const data = await response.json();
        setEditorContent(data.content);
        state.currentFilePath = filepath;

        addChatMessage("system", `File opened: ${filepath}`);
    } catch (error) {
        showError(`Failed to open file: ${error.message}`);
    } finally {
        hideLoading();
    }
}

async function askBrockston() {
    const input = document.getElementById("brockston-input");
    const history = document.getElementById("chat-history");
    const query = input.value?.trim();

    if (!query) return;

    // UI: Restore User Message with proper styling
    history.innerHTML += `
        <div class="mb-6 animate-in fade-in slide-in-from-bottom-2">
            <div class="flex items-center mb-1">
                <div class="h-[1px] flex-grow bg-blue-500/20"></div>
                <div class="text-[10px] font-bold text-blue-400 px-3 tracking-tighter">USER_INTENT</div>
                <div class="h-[1px] w-4 bg-blue-500/20"></div>
            </div>
            <div class="text-sm text-gray-300 leading-relaxed pl-2">${query}</div>
        </div>`;

    input.value = "";
    history.scrollTop = history.scrollHeight;

    try {
        const content = getEditorContent();

        const response = await fetch("/api/files/save", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                messages: [{ role: "user", content: query }],
                context: {
                    path: state.currentFilePath || "system",
                    code: content || "",
                },
            }),
        });

        if (!response.ok) throw new Error("Status: " + response.status);

        const data = await response.json();

        // UI: Restore Brockston Response with the Orange/Cyan theme
        history.innerHTML += `
            <div class="mb-6 animate-in fade-in slide-in-from-bottom-2">
                <div class="flex items-center mb-1">
                    <div class="h-[1px] w-4 bg-orange-500/20"></div>
                    <div class="text-[10px] font-bold text-orange-500 px-3 tracking-tighter">BROCKSTON_CORE</div>
                    <div class="h-[1px] flex-grow bg-orange-500/20"></div>
                </div>
                <div class="text-sm text-gray-300 leading-relaxed border-l border-orange-500/10 pl-4 ml-1">${data.reply}</div>
            </div>`;

        history.scrollTop = history.scrollHeight;
    } catch (err) {
        history.innerHTML += `
            <div class="p-2 border border-red-500/30 bg-red-500/5 text-red-500 text-[10px] font-mono mt-2">
                CRITICAL_FAILURE: ${err.message}
            </div>`;
    }
}

// DOM ready wiring
document.addEventListener("DOMContentLoaded", () => {
    loadFiles();

    const askBtn = document.getElementById("ask-brockston-btn");
    if (askBtn) askBtn.onclick = askBrockston;

    // Allow Enter key to send
    const input = document.getElementById("brockston-input");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") askBrockston();
        });
    }
});

// ============================================================================
// Code Suggestions
// ============================================================================

async function handleSuggestFix() {
    const instruction = elements.instructionInput.value.trim();
    if (!instruction) {
        showError('Please enter an instruction (e.g., "refactor for clarity")');
        return;
    }

    if (!state.currentFilePath) {
        showError("Please open a file first");
        return;
    }

    showLoading();

    try {
        const code = getEditorContent();

        const response = await fetch("/api/brockston/suggest_fix", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                instruction: instruction,
                path: state.currentFilePath,
                code: code,
                model: state.selectedModel,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(
                error.error || "Failed to get suggestions from BROCKSTON"
            );
        }

        const data = await response.json();

        // Store proposed code
        state.proposedCode = data.proposed_code;

        // Show comparison modal
        showComparisonModal(code, data.proposed_code, data.summary);

        // Add to chat log
        addChatMessage("user", `Suggest fix: ${instruction}`);
        addChatMessage("assistant", `Proposed changes: ${data.summary}`);

        // Clear instruction input
        elements.instructionInput.value = "";
    } catch (error) {
        showError(`BROCKSTON error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Show comparison modal
function showComparisonModal(currentCode, proposedCode, summary) {
    elements.currentCodePre.textContent = currentCode;
    elements.proposedCodePre.textContent = proposedCode;
    elements.comparisonSummary.textContent = summary;
    elements.comparisonModal.classList.add("active");
}

// Close comparison modal
function closeComparisonModal() {
    elements.comparisonModal.classList.remove("active");
    state.proposedCode = null;
}

// Handle applying proposed changes
function handleApplyChanges() {
    if (state.proposedCode) {
        setEditorContent(state.proposedCode);
        addChatMessage(
            "system",
            "Proposed changes applied to editor. Remember to save!"
        );
        closeComparisonModal();
    }
}

// Handle clearing chat log
function handleClearChat() {
    elements.chatLog.innerHTML = `
        <div class="chat-message system">
            <strong>BROCKSTON:</strong> Chat cleared. Ready for new questions.
        </div>
    `;
    state.chatHistory = [];
}

// Add message to chat log
function addChatMessage(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${role}`;

    let roleLabel = "BROCKSTON";
    if (role === "user") roleLabel = "You";
    else if (role === "system") roleLabel = "System";

    const contentHtml = content.replace(/\n/g, "<br>");

    messageDiv.innerHTML = `
        <strong>${roleLabel}:</strong>
        ${contentHtml}
    `;

    elements.chatLog.appendChild(messageDiv);
    elements.chatLog.scrollTop = elements.chatLog.scrollHeight;

    state.chatHistory.push({ role, content });
}

// Detect programming language from file extension
function detectLanguage(filePath) {
    const ext = filePath.split(".").pop().toLowerCase();
    const languageMap = {
        js: "javascript",
        ts: "typescript",
        jsx: "javascript",
        tsx: "typescript",
        py: "python",
        java: "java",
        c: "c",
        cpp: "cpp",
        cs: "csharp",
        go: "go",
        rs: "rust",
        rb: "ruby",
        php: "php",
        swift: "swift",
        kt: "kotlin",
        html: "html",
        css: "css",
        scss: "scss",
        json: "json",
        xml: "xml",
        yaml: "yaml",
        yml: "yaml",
        md: "markdown",
        sh: "shell",
        bash: "shell",
        sql: "sql",
    };

    return languageMap[ext] || "plaintext";
}

// Show loading overlay
function showLoading() {
    elements.loadingOverlay.classList.add("active");
}

// Hide loading overlay
function hideLoading() {
    elements.loadingOverlay.classList.remove("active");
}

// Show error message
function showError(message) {
    addChatMessage("system", `ERROR: ${message}`);
}

// ============================================================================
// Git Operations
// ============================================================================

// Open Git modal
function openGitModal() {
    elements.gitModal.classList.add("active");
    elements.gitUrl.value = "";
    elements.folderName.value = "";
    elements.gitStatusMessage.textContent = "";
    elements.gitStatusMessage.className = "git-status-message";
}

// Close Git modal
function closeGitModal() {
    elements.gitModal.classList.remove("active");
    elements.gitUrl.value = "";
    elements.folderName.value = "";
    elements.gitStatusMessage.textContent = "";
}

// Handle cloning a repository
async function handleCloneRepo() {
    const gitUrl = elements.gitUrl.value.trim();
    const folderName = elements.folderName.value.trim() || null;

    // Validate URL
    if (!gitUrl) {
        showGitStatus("Please enter a repository URL", "error");
        return;
    }

    if (!gitUrl.startsWith("https://")) {
        showGitStatus(
            "Please use an HTTPS URL, for example: https://github.com/your/repo.git",
            "error"
        );
        return;
    }

    // Disable button during clone
    elements.btnCloneRepo.disabled = true;
    elements.btnCloneRepo.textContent = "Cloning...";
    showGitStatus("Cloning repository, please wait...", "info");

    try {
        const response = await fetch("/api/git/clone", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                git_url: gitUrl,
                folder_name: folderName,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to clone repository");
        }

        // Success! Update UI with cloned repo path
        showGitStatus(
            `✓ Successfully cloned to: ${data.local_path}`,
            "success"
        );
        addChatMessage(
            "system",
            `Repository cloned: ${data.workspace_name} at ${data.local_path}`
        );

        // Pre-fill the file path input with the cloned repo path
        elements.filePathInput.value = `${data.local_path}/`;

        // Close modal after a short delay
        setTimeout(() => {
            closeGitModal();
        }, 2000);
    } catch (error) {
        showGitStatus(`✗ Clone failed: ${error.message}`, "error");
        console.error("Clone error:", error);
    } finally {
        elements.btnCloneRepo.disabled = false;
        elements.btnCloneRepo.textContent = "Clone & Open";
    }
}

// Show status message in Git modal
function showGitStatus(message, type) {
    elements.gitStatusMessage.textContent = message;
    elements.gitStatusMessage.className = `git-status-message ${type}`;
}

// ============================================================================
// Model Selection and Speech Handlers
// ============================================================================

// Handle model selection change
function handleModelChange() {
    state.selectedModel = elements.modelSelector.value;
    const modelName = state.selectedModel.toUpperCase();
    addChatMessage("system", `Switched to ${modelName} model`);
    console.log(`Model changed to: ${state.selectedModel}`);
}

// Handle speech recording toggle
async function handleSpeechToggle() {
    if (state.isRecording) {
        // Stop recording
        stopRecording();
    } else {
        // Start recording
        await startRecording();
    }
}

// Start audio recording
async function startRecording() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true,
        });

        // Create media recorder
        state.mediaRecorder = new MediaRecorder(stream, {
            mimeType: "audio/webm",
        });

        state.audioChunks = [];

        // Collect audio data
        state.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                state.audioChunks.push(event.data);
            }
        };

        // Handle recording stop
        state.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(state.audioChunks, {
                type: "audio/webm",
            });
            await handleAudioRecorded(audioBlob);

            // Stop all tracks
            stream.getTracks().forEach((track) => track.stop());
        };

        // Start recording
        state.mediaRecorder.start();
        state.isRecording = true;

        // Update UI
        elements.btnSpeech.textContent = "⏹️";
        elements.btnSpeech.classList.add("recording");
        addChatMessage(
            "system",
            "Recording... Click again to stop."
        );

        console.log("Recording started");
    } catch (error) {
        console.error("Microphone access error:", error);
        showError(
            "Failed to access microphone. Please grant permission and try again."
        );
    }
}

// Stop audio recording
function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;

        // Update UI
        elements.btnSpeech.textContent = "🎤";
        elements.btnSpeech.classList.remove("recording");
        addChatMessage(
            "system",
            "Processing your voice message..."
        );

        console.log("Recording stopped");
    }
}

// Handle recorded audio
async function handleAudioRecorded(audioBlob) {
    showLoading();

    try {
        // Step 1: Transcribe audio to text
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");

        const transcribeResponse = await fetch(
            "/api/speech/transcribe",
            {
                method: "POST",
                body: formData,
            }
        );

        if (!transcribeResponse.ok) {
            const error = await transcribeResponse.json();
            throw new Error(
                error.error || "Failed to transcribe audio"
            );
        }

        const transcribeData = await transcribeResponse.json();
        const transcribedText = transcribeData.text;

        addChatMessage("user", `🎤 ${transcribedText}`);

        // Step 2: Get AI response (with speech)
        const code = state.currentFilePath
            ? getEditorContent()
            : "";

        const messages = [
            {
                role: "system",
                content:
                    "You are BROCKSTON, a coding assistant for Everett, the architect. Be concise, precise, and helpful.",
            },
            {
                role: "user",
                content: transcribedText,
            },
        ];

        const chatResponse = await fetch("/api/speech/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                messages: messages,
                context: state.currentFilePath
                    ? {
                          path: state.currentFilePath,
                          code: code,
                      }
                    : null,
                model: state.selectedModel,
                voice: "alloy",
            }),
        });

        if (!chatResponse.ok) {
            const error = await chatResponse.json();
            throw new Error(
                error.error || "Failed to get AI response"
            );
        }

        // Get response text from header
        const responseText =
            chatResponse.headers.get("X-Response-Text") ||
            "Audio response generated";

        // Get audio data
        const audioData = await chatResponse.blob();

        // Display response text
        addChatMessage("assistant", `🔊 ${responseText}`);

        // Play audio response
        playAudioResponse(audioData);
    } catch (error) {
        console.error("Speech processing error:", error);
        showError(`Speech processing failed: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Play audio response
function playAudioResponse(audioBlob) {
    try {
        const audioUrl = URL.createObjectURL(audioBlob);
        elements.audioPlayer.src = audioUrl;
        elements.audioPlayer.style.display = "block";
        elements.audioPlayer.play();

        // Clean up URL after playback
        elements.audioPlayer.onended = () => {
            URL.revokeObjectURL(audioUrl);
        };

        console.log("Playing audio response");
    } catch (error) {
        console.error("Audio playback error:", error);
        showError("Failed to play audio response");
    }
}

// ============================================================================
// Claude Operations
// ============================================================================

// Handle asking Claude a question
async function handleAskClaude() {
    const input = elements.claudeInput.value.trim();
    if (!input) {
        showError("Please enter a question for Claude");
        return;
    }

    // Clear previous response and error
    if (elements.claudeResponse)
        elements.claudeResponse.textContent = "";
    if (elements.claudeError)
        elements.claudeError.textContent = "";
    if (elements.claudeLoading)
        elements.claudeLoading.style.display = "block";

    try {
        const result = await state.claudeHook.ask(
            [{ role: "user", content: input }],
            "You are Claude, integrated into Brockston Studios."
        );

        if (result) {
            if (elements.claudeResponse)
                elements.claudeResponse.textContent = result;
        } else {
            if (elements.claudeError)
                elements.claudeError.textContent =
                    state.claudeHook.getError() ||
                    "No response from Claude";
        }
    } catch (error) {
        if (elements.claudeError)
            elements.claudeError.textContent = `Error: ${error.message}`;
    } finally {
        if (elements.claudeLoading)
            elements.claudeLoading.style.display = "none";
    }
}

// Switch between Brockston and Claude tabs
function switchTab(tab) {
    if (tab === "brockston") {
        elements.tabBrockston.classList.add("active");
        elements.tabBrockston.style.borderBottom =
            "2px solid var(--neon-orange)";
        elements.tabBrockston.style.color =
            "var(--neon-orange)";
        elements.tabClaude.classList.remove("active");
        elements.tabClaude.style.borderBottom = "none";
        elements.tabClaude.style.color = "#666";
        elements.brockstonPanel.style.display = "block";
        elements.claudePanel.style.display = "none";
    } else if (tab === "claude") {
        elements.tabClaude.classList.add("active");
        elements.tabClaude.style.borderBottom =
            "2px solid var(--neon-orange)";
        elements.tabClaude.style.color = "var(--neon-orange)";
        elements.tabBrockston.classList.remove("active");
        elements.tabBrockston.style.borderBottom = "none";
        elements.tabBrockston.style.color = "#666";
        elements.claudePanel.style.display = "flex";
        elements.brockstonPanel.style.display = "none";
    }
}

// ============================================================================
// Terminal Operations
// ============================================================================

// Clear terminal
function handleClearTerminal() {
    if (state.terminal) {
        state.terminal.clear();
        console.log("Terminal cleared");
    }
}

// Create new terminal session
function handleNewTerminal() {
    if (state.terminal) {
        // Close existing WebSocket if any
        if (state.terminalSocket) {
            state.terminalSocket.close();
        }

        // Clear terminal
        state.terminal.clear();

        // Reconnect
        state.terminal.writeln(
            "\x1b[1;36m╔══════════════════════════════════════════════╗\x1b[0m"
        );
        state.terminal.writeln(
            "\x1b[1;36m║\x1b[0m  \x1b[1;37mBROCKSTON Studio Terminal\x1b[0m                 \x1b[1;36m║\x1b[0m"
        );
        state.terminal.writeln(
            "\x1b[1;36m╚══════════════════════════════════════════════╝\x1b[0m"
        );
        state.terminal.writeln("");
        state.terminal.writeln(
            "\x1b[1;33mConnecting to shell...\x1b[0m"
        );
        state.terminal.writeln("");

        connectTerminalWebSocket();
        console.log("New terminal session created");
    }
}

// ============================================================================
// Global init hook (if you have an init() elsewhere)
// ============================================================================

if (typeof init === "function") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
}
