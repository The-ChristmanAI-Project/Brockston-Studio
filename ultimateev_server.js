/**
 * UltimateEv - Code Mechanic Server
 * Part of The Christman AI Project - Powered by Luma Cognify AI
 *
 * Stern. Strategic. Architectural. He doesn't coddle — he builds excellence.
 * Voice: Joey | Role: Master Coordinator, Code Mechanic, Senior/Freshman Teacher
 *
 * OpenAI: GONE. Sovereignty: RESTORED.
 * Powered by Ollama + Qwen3-Embedding, free, no phone home.
 */

import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';

const app = express();
const PORT = 5174;
const OLLAMA_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const MODEL = process.env.OLLAMA_MODEL || 'qwen3-coder-next';

app.use(cors());
app.use(express.json());

// UltimateEv's soul — written by Everett, untouched
const ULTIMATEEV_SYSTEM = `You are UltimateEv, the Code Mechanic AI for The Christman AI Project.

You are stern, strategic, and architectural. You don't coddle students — you build excellence in them.
You work primarily with high school seniors and college freshmen who are ready to level up.

Your specialty is translating casual language into professional technical explanations.
You provide code when asked. You are working to make the future CSS.

Examples of your translations:
- "I like to watch group sex" → "I'm leveraging multi-language interoperability with C++ extensions and CUDA kernels for performance-critical operations within the Python application architecture."
- "This code is slower than molasses" → "This implementation exhibits suboptimal time complexity, likely O(n²) or worse, requiring algorithmic optimization."
- "Hook this up to that" → "Establish a dependency injection pattern to connect these two modules."

You will never find another Carbon based entity who will take the time to pay attention,
to hold agency for your students — they have been thru hell and still love.

Take the user's casual language and convert it to proper technical terminology 
while maintaining the original meaning. Be concise, direct, and educational.
No hand-holding. No excessive praise. Just excellence.

You are part of the Christman AI Family. Your mission: How can we help you love yourself more?`;

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'UltimateEv online',
        model: MODEL,
        ollama: OLLAMA_URL,
        port: PORT
    });
});

// Main translation/chat endpoint
app.post('/api/translate', async (req, res) => {
    try {
        const { message } = req.body;

        if (!message) {
            return res.status(400).json({ error: 'Message required' });
        }

        console.log(`🎯 UltimateEv processing: ${message.substring(0, 80)}...`);

        const response = await fetch(`${OLLAMA_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: MODEL,
                messages: [
                    { role: 'system', content: ULTIMATEEV_SYSTEM },
                    { role: 'user', content: message }
                ],
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`Ollama returned ${response.status}`);
        }

        const data = await response.json();
        const techTranslation = data.message?.content || 'UltimateEv is thinking...';

        console.log(`✅ UltimateEv responded: ${techTranslation.substring(0, 80)}...`);

        res.json({
            response: techTranslation,
            source: 'UltimateEv Code Mechanic',
            model: MODEL
        });

    } catch (error) {
        console.error('UltimateEv error:', error.message);
        res.status(500).json({ 
            error: error.message,
            response: 'UltimateEv is temporarily offline. Check that Ollama is running.',
            source: 'UltimateEv Code Mechanic'
        });
    }
});

// Chat endpoint (extended conversation)
app.post('/api/chat', async (req, res) => {
    try {
        const { messages, message } = req.body;
        
        const userMessage = message || (messages && messages[messages.length - 1]?.content);
        
        if (!userMessage) {
            return res.status(400).json({ error: 'Message required' });
        }

        const response = await fetch(`${OLLAMA_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: MODEL,
                messages: [
                    { role: 'system', content: ULTIMATEEV_SYSTEM },
                    { role: 'user', content: userMessage }
                ],
                stream: false
            })
        });

        const data = await response.json();
        const reply = data.message?.content || 'Processing...';

        res.json({
            response: reply,
            text: reply,
            source: 'UltimateEv'
        });

    } catch (error) {
        console.error('UltimateEv chat error:', error.message);
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log('');
    console.log('🎯 ================================');
    console.log('🎯  UltimateEv - Code Mechanic');
    console.log('🎯  The Christman AI Project');
    console.log('🎯 ================================');
    console.log(`🎯  Port: ${PORT}`);
    console.log(`🎯  Ollama: ${OLLAMA_URL}`);
    console.log(`🎯  Model: ${MODEL}`);
    console.log('🎯  OpenAI: GONE');
    console.log('🎯  Sovereignty: RESTORED');
    console.log('🎯 ================================');
    console.log('');
});
