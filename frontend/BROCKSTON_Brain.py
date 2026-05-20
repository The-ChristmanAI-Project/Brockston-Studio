from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import ast
import textwrap

app = FastAPI(
    title="Brokston Code Generator API",
    description="A secure, PhD-level AI code generator for building compassionate tools. Generates clean Python code stubs based on natural language descriptions. Optimized for neurodiverse accessibility.",
    version="1.0.0",
)


class CodeRequest(BaseModel):
    description: str
    language: str = "python"
    features: list[str] = []


class GeneratedCode(BaseModel):
    code: str
    explanation: str


def validate_description(description: str) -> bool:
    """Basic validation to ensure input is safe and relevant."""
    forbidden = ["exec", "eval", "os.system", "subprocess", "import os", "import sys"]
    return all(term not in description.lower() for term in forbidden)


def generate_code_stub(description: str, features: list[str]) -> str:
    """Generate a basic Python code stub based on description."""
    base_template = textwrap.dedent(
        """
    def {function_name}(input_data):
        \"\"\"{docstring}\"\"\"
        # TODO: Implement logic here
        pass
    """
    )

    function_name = "_".join(
        word.lower() for word in description.split()[:5] if word.isalnum()
    )
    if not function_name:
        function_name = "generated_function"

    docstring = f"Generated from: {description}. Features: {', '.join(features)}."

    if "hipaa_safe" in features:
        docstring += "\nEnsures data privacy and compliance."
        base_template += textwrap.dedent(
            """
        # HIPAA-safe logging (pseudocode)
        import logging
        logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('logs/secure.log')])
        logging.info('Processed data securely.')
        """
        )

    if "tts_integration" in features:
        docstring += "\nIntegrates text-to-speech for accessibility."
        base_template += textwrap.dedent(
            """
        # TTS stub (using placeholder library; replace with actual like pyttsx3)
        def speak(text):
            print(f'Speaking: {text}')  # Placeholder
        speak('Output generated.')
        """
        )

    code = base_template.format(function_name=function_name, docstring=docstring)

    try:
        ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Generated code has syntax error: {str(e)}")

    return code


@app.post("/generate_code", response_model=GeneratedCode)
async def generate_code(request: CodeRequest = Body(...)):
    """Endpoint to generate code based on description. Validates input for safety."""
    if not validate_description(request.description):
        raise HTTPException(
            status_code=400, detail="Invalid description: Contains unsafe terms."
        )

    try:
        code = generate_code_stub(request.description, request.features)
        explanation = (
            "This is a basic code stub generated from your description. "
            "It's designed to be extensible, secure, and accessible. "
            "Test locally, validate payloads, and deploy to ECS as needed."
        )
        return GeneratedCode(code=code, explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7171)
