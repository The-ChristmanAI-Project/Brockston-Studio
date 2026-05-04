/**
 * BROCKSTON Studio Frontend Application
 *
 * Handles Monaco Editor integration, file operations, and BROCKSTON interactions.
 */

// Global state
const state = {
    editor: null,
    currentFilePath: null,
    proposedCode: null,
    chatHistory: [],
    terminal: null,
    terminalSocket: null,
    horizontalSplit: null,
    verticalSplit: null,
    selectedModel: 'brockston',
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,
    claudeHook: null,
};

// DOM elements - mapped to actual HTML IDs
const elements = {
    // File operations (using textarea editor instead of Monaco)
    editorContent: document.getElementById('editor-content'),
    filePathInput: null,  // Not in current HTML
    btnOpen: null,  // Not in current HTML
    btnSave: null,  // Not in current HTML

    // Chat elements
    chatLog: document.getElementById('chat-history'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    btnClearChat: null,  // Not in current HTML

    // File explorer
    fileList: document.getElementById('file-list'),

    // Current file display
    currentFileSpan: null,  // Not in current HTML

    // Comparison modal (not in current HTML)
    instructionInput: null,
    comparisonModal: null,
    btnCloseModal: null,
    btnApply: null,
    btnReject: null,
    currentCodePre: null,
    proposedCodePre: null,
    comparisonSummary: null,
    loadingOverlay: null,
    workspaceInfo: null,

    // Git modal elements (not in current HTML)
    btnGit: null,
    gitModal: null,
    btnCloseGitModal: null,
    btnCancelClone: null,
    btnCloneRepo: null,
    gitUrl: null,
    folderName: null,
    gitStatusMessage: null,

    // Terminal elements
    terminalContainer: document.getElementById('terminal'),
    btnClearTerminal: null,  // Not in current HTML
    btnNewTerminal: null,    // Not in current HTML

    // Model selection and speech elements (not in current HTML)
    modelSelector: null,
    btnSpeech: null,
    audioPlayer: null,

    // Claude elements
    claudeInput: document.getElementById('claude-input'),
    btnAskClaude: document.getElementById('btn-ask-claude'),
    claudeResponse: document.getElementById('claude-response'),
    claudeLoading: document.getElementById('claude-loading'),
    claudeError: document.getElementById('claude-error'),

    // Tab elements
    tabBrockston: document.getElementById('tab-brockston'),
    tabClaude: document.getElementById('tab-claude'),
    brockstonPanel: document.getElementById('brockston-panel'),
    claudePanel: document.getElementById('claude-panel'),
};

// Initialize application
function init() {
    // Initialize Claude hook
    state.claudeHook = useClaude();

    // Initialize Terminal
    initTerminal();

    // Attach event listeners for available elements
    attachEventListeners();

    // Load workspace info
    loadWorkspaceInfo();

    // Load file list
    loadFiles();

    console.log('BROCKSTON Studio initialized');
}

// Initialize Terminal
function initTerminal() {
    // Create xterm.js terminal instance
    state.terminal = new Terminal({
        cursorBlink: true,
        cursorStyle: 'block',
        fontSize: 14,
        fontFamily: '"Cascadia Code", "Fira Code", "Courier New", monospace',
        theme: {
            background: '#000000',
            foreground: '#f8fafc',
            cursor: '#00d9ff',
            cursorAccent: '#000000',
            selection: 'rgba(0, 217, 255, 0.3)',
            black: '#0a0e1a',
            red: '#ff6b6b',
            green: '#00ff9f',
            yellow: '#ffd93d',
            blue: '#00d9ff',
            magenta: '#bd00ff',
            cyan: '#6bceff',
            white: '#f8fafc',
            brightBlack: '#64748b',
            brightRed: '#ff8787',
            brightGreen: '#69ffb4',
            brightYellow: '#ffe066',
            brightBlue: '#4de4ff',
            brightMagenta: '#d966ff',
            brightCyan: '#89d4ff',
            brightWhite: '#ffffff',
        },
        scrollback: 1000,
        allowProposedApi: true,
    });

    // Add fit addon
    const fitAddon = new FitAddon.FitAddon();
    state.terminal.loadAddon(fitAddon);

    // Add web links addon
    const webLinksAddon = new WebLinksAddon.WebLinksAddon();
    state.terminal.loadAddon(webLinksAddon);

    // Open terminal in DOM
    state.terminal.open(elements.terminalContainer);
    fitAddon.fit();

    // Welcome message
    state.terminal.writeln('\x1b[1;36m╔══════════════════════════════════════════════╗\x1b[0m');
    state.terminal.writeln('\x1b[1;36m║\x1b[0m  \x1b[1;37mBROCKSTON Studio Terminal\x1b[0m                 \x1b[1;36m║\x1b[0m');
    state.terminal.writeln('\x1b[1;36m╚══════════════════════════════════════════════╝\x1b[0m');
    state.terminal.writeln('');
    state.terminal.writeln('\x1b[1;33mConnecting to shell...\x1b[0m');
    state.terminal.writeln('');

    // Handle window resize
    window.addEventListener('resize', () => {
        fitAddon.fit();
    });

    // Connect to WebSocket
    connectTerminalWebSocket();

    console.log('Terminal initialized');
}

// Connect Terminal to WebSocket
function connectTerminalWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/terminal`;

    try {
        state.terminalSocket = new WebSocket(wsUrl);

        state.terminalSocket.onopen = () => {
            console.log('Terminal WebSocket connected');
            state.terminal.writeln('\x1b[1;32m✓ Connected to shell\x1b[0m');
            state.terminal.writeln('');

            // Handle terminal input
            state.terminal.onData((data) => {
                if (state.terminalSocket && state.terminalSocket.readyState === WebSocket.OPEN) {
                    state.terminalSocket.send(JSON.stringify({
                        type: 'input',
                        data: data,
                    }));
                }
            });
        };

        state.terminalSocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'output') {
                state.terminal.write(message.data);
            }
        };

        state.terminalSocket.onerror = (error) => {
            console.error('Terminal WebSocket error:', error);
            state.terminal.writeln('\x1b[1;31m✗ Connection error\x1b[0m');
        };

        state.terminalSocket.onclose = () => {
            console.log('Terminal WebSocket closed');
            state.terminal.writeln('');
            state.terminal.writeln('\x1b[1;33m⚠ Connection closed. Click "New" to reconnect.\x1b[0m');
        };

    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        state.terminal.writeln('\x1b[1;31m✗ Failed to connect to shell\x1b[0m');
        state.terminal.writeln('\x1b[2;37m  WebSocket endpoint not available\x1b[0m');
    }
}

// Initialize Monaco Editor
function initMonacoEditor() {
    require(['vs/editor/editor.main'], function () {
        state.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
            value: '// Open a file to start editing...\n',
            language: 'javascript',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: true },
            fontSize: 14,
            tabSize: 4,
            wordWrap: 'on',
        });

        console.log('Monaco Editor initialized');
    });
}

// Attach event listeners
function attachEventListeners() {
    // Tab switching (always available)
    if (elements.tabBrockston) {
        elements.tabBrockston.addEventListener('click', () => switchTab('brockston'));
    }
    if (elements.tabClaude) {
        elements.tabClaude.addEventListener('click', () => switchTab('claude'));
    }

    // Claude ask button
    if (elements.btnAskClaude) {
        elements.btnAskClaude.addEventListener('click', handleAskClaude);
    }

    // Ctrl+S to save (global shortcut)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            handleSaveFile();
        }
    });

    console.log('Event listeners attached');
}

// Load workspace info
async function loadWorkspaceInfo() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        if (data.workspace) {
            elements.workspaceInfo.textContent = `Workspace: ${data.workspace}`;
        }
    } catch (error) {
        console.error('Failed to load workspace info:', error);
    }
}

// Get editor content (works with textarea)
function getEditorContent() {
    if (elements.editorContent) {
        return elements.editorContent.value;
    }
    return state.editor ? state.editor.getValue() : '';
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
        const response = await fetch(`/api/read_file?filename=${encodeURIComponent(filepath)}`);

        if (!response.ok) {
            throw new Error('Read failed');
        }

        const data = await response.json();
        setEditorContent(data.content);
        state.currentFilePath = filepath;

        addChatMessage('system', `File opened: ${filepath}`);

    } catch (error) {
        showError(`Failed to open file: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Handle saving a file
async function handleSaveFile() {
    if (!state.currentFilePath) {
        showError('No file open');
        return;
    }

    showLoading();

    try {
        const content = getEditorContent();

        const response = await fetch('/api/files/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                path: state.currentFilePath,
                content: content,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save file');
        }

        const data = await response.json();
        addChatMessage('system', `File saved: ${data.path}`);

    } catch (error) {
        showError(`Failed to save file: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Handle asking BROCKSTON a question
async function handleAskBrockston() {
    const instruction = elements.instructionInput.value.trim();
    if (!instruction) {
        showError('Please enter a question or instruction');
        return;
    }

    if (!state.currentFilePath) {
        showError('Please open a file first');
        return;
    }

    showLoading();

    try {
        const code = state.editor.getValue();

        // Build message history
        const messages = [
            {
                role: 'system',
                content: 'You are BROCKSTON, a reasoning engine that helps Everett, the architect, understand and improve his code. Be concise, precise, and helpful.',
            },
            {
                role: 'user',
                content: instruction,
            },
        ];

        const response = await fetch('/api/brockston/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messages,
                context: {
                    path: state.currentFilePath,
                    code: code,
                },
                model: state.selectedModel,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to communicate with BROCKSTON');
        }

        const data = await response.json();

        // Add to chat log
        addChatMessage('user', instruction);
        addChatMessage('assistant', data.reply);

        // Clear instruction input
        elements.instructionInput.value = '';

    } catch (error) {
        showError(`BROCKSTON error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Handle requesting code suggestions
async function handleSuggestFix() {
    const instruction = elements.instructionInput.value.trim();
    if (!instruction) {
        showError('Please enter an instruction (e.g., "refactor for clarity")');
        return;
    }

    if (!state.currentFilePath) {
        showError('Please open a file first');
        return;
    }

    showLoading();

    try {
        const code = state.editor.getValue();

        const response = await fetch('/api/brockston/suggest_fix', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
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
            throw new Error(error.error || 'Failed to get suggestions from BROCKSTON');
        }

        const data = await response.json();

        // Store proposed code
        state.proposedCode = data.proposed_code;

        // Show comparison modal
        showComparisonModal(code, data.proposed_code, data.summary);

        // Add to chat log
        addChatMessage('user', `Suggest fix: ${instruction}`);
        addChatMessage('assistant', `Proposed changes: ${data.summary}`);

        // Clear instruction input
        elements.instructionInput.value = '';

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
    elements.comparisonModal.classList.add('active');
}

// Close comparison modal
function closeComparisonModal() {
    elements.comparisonModal.classList.remove('active');
    state.proposedCode = null;
}

// Handle applying proposed changes
function handleApplyChanges() {
    if (state.proposedCode) {
        state.editor.setValue(state.proposedCode);
        addChatMessage('system', 'Proposed changes applied to editor. Remember to save!');
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
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    let roleLabel = 'BROCKSTON';
    if (role === 'user') roleLabel = 'You';
    else if (role === 'system') roleLabel = 'System';

    const contentHtml = content.replace(/\n/g, '<br>');

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
    const ext = filePath.split('.').pop().toLowerCase();
    const languageMap = {
        'js': 'javascript',
        'ts': 'typescript',
        'jsx': 'javascript',
        'tsx': 'typescript',
        'py': 'python',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'cs': 'csharp',
        'go': 'go',
        'rs': 'rust',
        'rb': 'ruby',
        'php': 'php',
        'swift': 'swift',
        'kt': 'kotlin',
        'html': 'html',
        'css': 'css',
        'scss': 'scss',
        'json': 'json',
        'xml': 'xml',
        'yaml': 'yaml',
        'yml': 'yaml',
        'md': 'markdown',
        'sh': 'shell',
        'bash': 'shell',
        'sql': 'sql',
    };

    return languageMap[ext] || 'plaintext';
}

// Show loading overlay
function showLoading() {
    elements.loadingOverlay.classList.add('active');
}

// Hide loading overlay
function hideLoading() {
    elements.loadingOverlay.classList.remove('active');
}

// Show error message
function showError(message) {
    addChatMessage('system', `ERROR: ${message}`);
}

// ============================================================================
// Git Operations
// ============================================================================

// Open Git modal
function openGitModal() {
    elements.gitModal.classList.add('active');
    elements.gitUrl.value = '';
    elements.folderName.value = '';
    elements.gitStatusMessage.textContent = '';
    elements.gitStatusMessage.className = 'git-status-message';
}

// Close Git modal
function closeGitModal() {
    elements.gitModal.classList.remove('active');
    elements.gitUrl.value = '';
    elements.folderName.value = '';
    elements.gitStatusMessage.textContent = '';
}

// Handle cloning a repository
async function handleCloneRepo() {
    const gitUrl = elements.gitUrl.value.trim();
    const folderName = elements.folderName.value.trim() || null;

    // Validate URL
    if (!gitUrl) {
        showGitStatus('Please enter a repository URL', 'error');
        return;
    }

    if (!gitUrl.startsWith('https://')) {
        showGitStatus('Please use an HTTPS URL (e.g., https://github.com/...)', 'error');
        return;
    }

    // Disable button during clone
    elements.btnCloneRepo.disabled = true;
    elements.btnCloneRepo.textContent = 'Cloning...';
    showGitStatus('Cloning repository, please wait...', 'info');

    try {
        const response = await fetch('/api/git/clone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                git_url: gitUrl,
                folder_name: folderName,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to clone repository');
        }

        // Success! Update UI with cloned repo path
        showGitStatus(`✓ Successfully cloned to: ${data.local_path}`, 'success');
        addChatMessage('system', `Repository cloned: ${data.workspace_name} at ${data.local_path}`);

        // Pre-fill the file path input with the cloned repo path
        elements.filePathInput.value = `${data.local_path}/`;

        // Close modal after a short delay
        setTimeout(() => {
            closeGitModal();
        }, 2000);

    } catch (error) {
        showGitStatus(`✗ Clone failed: ${error.message}`, 'error');
        console.error('Clone error:', error);
    } finally {
        elements.btnCloneRepo.disabled = false;
        elements.btnCloneRepo.textContent = 'Clone & Open';
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
    addChatMessage('system', `Switched to ${modelName} model`);
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
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Create media recorder
        state.mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm'
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
            const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
            await handleAudioRecorded(audioBlob);

            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };

        // Start recording
        state.mediaRecorder.start();
        state.isRecording = true;

        // Update UI
        elements.btnSpeech.textContent = '⏹️';
        elements.btnSpeech.classList.add('recording');
        addChatMessage('system', 'Recording... Click again to stop.');

        console.log('Recording started');

    } catch (error) {
        console.error('Microphone access error:', error);
        showError('Failed to access microphone. Please grant permission and try again.');
    }
}

// Stop audio recording
function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;

        // Update UI
        elements.btnSpeech.textContent = '🎤';
        elements.btnSpeech.classList.remove('recording');
        addChatMessage('system', 'Processing your voice message...');

        console.log('Recording stopped');
    }
}

// Handle recorded audio
async function handleAudioRecorded(audioBlob) {
    showLoading();

    try {
        // Step 1: Transcribe audio to text
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        const transcribeResponse = await fetch('/api/speech/transcribe', {
            method: 'POST',
            body: formData,
        });

        if (!transcribeResponse.ok) {
            const error = await transcribeResponse.json();
            throw new Error(error.error || 'Failed to transcribe audio');
        }

        const transcribeData = await transcribeResponse.json();
        const transcribedText = transcribeData.text;

        addChatMessage('user', `🎤 ${transcribedText}`);

        // Step 2: Get AI response (with speech)
        const code = state.currentFilePath ? state.editor.getValue() : '';

        const messages = [
            {
                role: 'system',
                content: 'You are BROCKSTON, a coding assistant for Everett, the architect. Be concise, precise, and helpful.',
            },
            {
                role: 'user',
                content: transcribedText,
            },
        ];

        const chatResponse = await fetch('/api/speech/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messages,
                context: state.currentFilePath ? {
                    path: state.currentFilePath,
                    code: code,
                } : null,
                model: state.selectedModel,
                voice: 'alloy',
            }),
        });

        if (!chatResponse.ok) {
            const error = await chatResponse.json();
            throw new Error(error.error || 'Failed to get AI response');
        }

        // Get response text from header
        const responseText = chatResponse.headers.get('X-Response-Text') || 'Audio response generated';

        // Get audio data
        const audioData = await chatResponse.blob();

        // Display response text
        addChatMessage('assistant', `🔊 ${responseText}`);

        // Play audio response
        playAudioResponse(audioData);

    } catch (error) {
        console.error('Speech processing error:', error);
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
        elements.audioPlayer.style.display = 'block';
        elements.audioPlayer.play();

        // Clean up URL after playback
        elements.audioPlayer.onended = () => {
            URL.revokeObjectURL(audioUrl);
        };

        console.log('Playing audio response');
    } catch (error) {
        console.error('Audio playback error:', error);
        showError('Failed to play audio response');
    }
}

// ============================================================================
// Claude Operations
// ============================================================================

// Handle asking Claude a question
async function handleAskClaude() {
    const input = elements.claudeInput.value.trim();
    if (!input) {
        showError('Please enter a question for Claude');
        return;
    }

    // Clear previous response and error
    if (elements.claudeResponse) elements.claudeResponse.textContent = '';
    if (elements.claudeError) elements.claudeError.textContent = '';
    if (elements.claudeLoading) elements.claudeLoading.style.display = 'block';

    try {
        const result = await state.claudeHook.ask([
            { role: "user", content: input }
        ], "You are Claude, integrated into Brockston Studios.");

        if (result) {
            if (elements.claudeResponse) elements.claudeResponse.textContent = result;
        } else {
            if (elements.claudeError) elements.claudeError.textContent = state.claudeHook.getError() || 'No response from Claude';
        }
    } catch (error) {
        if (elements.claudeError) elements.claudeError.textContent = `Error: ${error.message}`;
    } finally {
        if (elements.claudeLoading) elements.claudeLoading.style.display = 'none';
    }
}

// Switch between Brockston and Claude tabs
function switchTab(tab) {
    if (tab === 'brockston') {
        elements.tabBrockston.classList.add('active');
        elements.tabBrockston.style.borderBottom = '2px solid var(--neon-orange)';
        elements.tabBrockston.style.color = 'var(--neon-orange)';
        elements.tabClaude.classList.remove('active');
        elements.tabClaude.style.borderBottom = 'none';
        elements.tabClaude.style.color = '#666';
        elements.brockstonPanel.style.display = 'block';
        elements.claudePanel.style.display = 'none';
    } else if (tab === 'claude') {
        elements.tabClaude.classList.add('active');
        elements.tabClaude.style.borderBottom = '2px solid var(--neon-orange)';
        elements.tabClaude.style.color = 'var(--neon-orange)';
        elements.tabBrockston.classList.remove('active');
        elements.tabBrockston.style.borderBottom = 'none';
        elements.tabBrockston.style.color = '#666';
        elements.claudePanel.style.display = 'flex';
        elements.brockstonPanel.style.display = 'none';
    }
}

// ============================================================================
// Terminal Operations
// ============================================================================

// Clear terminal
function handleClearTerminal() {
    if (state.terminal) {
        state.terminal.clear();
        console.log('Terminal cleared');
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
        state.terminal.writeln('\x1b[1;36m╔══════════════════════════════════════════════╗\x1b[0m');
        state.terminal.writeln('\x1b[1;36m║\x1b[0m  \x1b[1;37mBROCKSTON Studio Terminal\x1b[0m                 \x1b[1;36m║\x1b[0m');
        state.terminal.writeln('\x1b[1;36m╚══════════════════════════════════════════════╝\x1b[0m');
        state.terminal.writeln('');
        state.terminal.writeln('\x1b[1;33mConnecting to shell...\x1b[0m');
        state.terminal.writeln('');

        connectTerminalWebSocket();
        console.log('New terminal session created');
    }
}

// ============================================================================
// File Explorer
// ============================================================================

let currentExplorerPath = '';

// Load files from the workspace
async function loadFiles(path = '') {
    if (!elements.fileList) return;

    try {
        const res = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
        const data = await res.json();

        elements.fileList.innerHTML = '';

        // Add back button if not at root
        if (currentExplorerPath !== '') {
            const backBtn = document.createElement('div');
            backBtn.className = 'file-item';
            backBtn.innerHTML = '<i class="fas fa-arrow-left"></i> ..';
            backBtn.onclick = () => {
                const parts = currentExplorerPath.split('/').filter(p => p);
                parts.pop();
                currentExplorerPath = parts.join('/');
                loadFiles(currentExplorerPath);
            };
            elements.fileList.appendChild(backBtn);
        }

        // Add files and folders
        (data.files || []).forEach(file => {
            const el = document.createElement('div');
            el.className = 'file-item';
            const icon = file.type === 'folder' ? 'fa-folder' : 'fa-file-code';
            el.innerHTML = `<i class="fas ${icon}"></i> ${file.name}`;

            if (file.type === 'file') {
                const filepath = currentExplorerPath ? `${currentExplorerPath}/${file.name}` : file.name;
                el.onclick = () => openFileFromExplorer(filepath);
            } else {
                el.onclick = () => {
                    currentExplorerPath = currentExplorerPath ? `${currentExplorerPath}/${file.name}` : file.name;
                    loadFiles(currentExplorerPath);
                };
            }

            elements.fileList.appendChild(el);
        });
    } catch (err) {
        elements.fileList.innerHTML = `<div style="color:red">Failed to load files: ${err.message}</div>`;
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
