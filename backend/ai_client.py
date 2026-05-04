import os
import httpx

# Configuration - Your Brockston on port 8777
BROCKSTON_URL = os.getenv("BROCKSTON_BASE_URL", "http://localhost:8777")
USE_BROCKSTON = os.getenv("USE_BROCKSTON", "true").lower() == "true"

def get_ai_response(user_prompt: str) -> str:
    """
    Get AI response from YOUR Brockston server.
    """
    if not USE_BROCKSTON:
        return "[AI Error]: BROCKSTON integration is disabled."

    try:
        response = httpx.post(
            f"{BROCKSTON_URL}/api/chat",
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Brockston, a helpful coding assistant for Everett, "
                            "the architect. Be clear, educational, and encouraging."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ]
            },
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("text", data.get("response", data.get("content", str(data))))
        return f"[AI Error]: Brockston returned {response.status_code}"

    except Exception as e:
        return f"[AI Error]: {str(e)}"

if __name__ == "__main__":
    print(f"Using Brockston: {USE_BROCKSTON}")
    print(f"Brockston URL: {BROCKSTON_URL}")
    print(get_ai_response("Hello Everett"))
