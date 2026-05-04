// hooks/useClaude.js - Claude integration utility for vanilla JS
class ClaudeHook {
    constructor() {
        this.loading = false;
        this.error = null;
    }

    async ask(messages, system = "") {
        this.loading = true;
        this.error = null;
        try {
            const res = await fetch("/api/claude", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages, system }),
            });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            const data = await res.json();
            return data.content;
        } catch (err) {
            this.error = err.message;
            console.error("Claude API error:", err);
            return null;
        } finally {
            this.loading = false;
        }
    }

    isLoading() {
        return this.loading;
    }

    getError() {
        return this.error;
    }

    clearError() {
        this.error = null;
    }
}

// Export for use in other files
const useClaude = () => new ClaudeHook();