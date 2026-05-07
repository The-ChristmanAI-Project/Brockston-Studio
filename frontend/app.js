/**
 * BROCKSTON Studio - Frontend Logic
 * FULL RESTORATION: Maintaining Visual Sovereignty and Uplink.
 */

const BACKEND_URL = "http://127.0.0.1:5055";

async function loadFiles() {
    const explorer = document.getElementById("project-explorer");
    if (!explorer) return;

    try {
        const response = await fetch(BACKEND_URL + "/api/files");
        if (!response.ok) throw new Error("HTTP " + response.status);
        
        const data = await response.json();
        const files = data.files || [];

        if (files.length === 0) {
            explorer.innerHTML = "<div class='p-4 text-gray-500 text-xs'>Workspace empty.</div>";
            return;
        }

        // RESTORED: Orange border barriers and hover effects
        explorer.innerHTML = files.map(file => `
            <div class="file-item p-3 hover:bg-gray-800/50 cursor-pointer text-sm border-b border-orange-500/20 transition-all duration-200 flex items-center group" onclick="openFile('${file}')">
                <span class="mr-3 text-orange-500/50 group-hover:text-orange-500">📄</span>
                <span class="text-gray-300 group-hover:text-white">${file}</span>
            </div>
        `).join("");

    } catch (err) {
        explorer.innerHTML = `
            <div class="p-4 border-l-2 border-red-500 bg-red-950/20">
                <div class="text-red-500 text-xs font-bold uppercase tracking-widest">Uplink Offline</div>
                <div class="text-red-400/60 text-[10px] mt-1">${err.message}</div>
            </div>`;
    }
}

async function openFile(path) {
    console.log("Opening file:", path);
    // Logic for loading into Monaco goes here
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
        const response = await fetch(BACKEND_URL + "/api/brockston/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messages: [{ role: "user", content: query }],
                context: { path: "system", code: "" }
            })
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
