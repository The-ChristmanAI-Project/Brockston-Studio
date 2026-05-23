"""Ollama Configuration for Brockston-Studio"""
import os

OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "models": {
        "coding": {
            "model": "qwen2.5-coder:32b",
            "temperature": 0.1,
            "max_tokens": 4096,
            "purpose": "code_generation"
        },
        "conversation": {
            "model": "llama3.2:3b",
            "temperature": 0.7,
            "max_tokens": 2048,
            "purpose": "conversation"
        }
    },
    "default_model": "llama3.2:3b"
}
