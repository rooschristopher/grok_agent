import os
import json
import re
from xai_sdk import Client
from xai_sdk.chat import user

code_gen_tool = {
    "type": "function",
    "function": {
        "name": "code_gen",
        "description": "Generate a Python code snippet from a natural language spec/prompt using the xAI Grok API. Returns the generated code as string.",
        "parameters": {
            "type": "object",
            "properties": {
                "spec": {
                    "type": "string",
                    "description": "Natural language description of the code to generate (e.g., 'a function to compute factorial')"
                }
            },
            "required": ["spec"]
        }
    }
}

def code_gen(spec: str) -> str:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return json.dumps({"error": "XAI_API_KEY not set in .env"})
    
    client = Client(api_key=api_key)
    model = "grok-beta"
    
    try:
        code_chat = client.chat.create(model=model, tools=[])
        prompt = f'''Generate ONLY the Python code snippet for this spec. No explanations, no markdown, no extra text.

Spec: {spec}'''
        code_chat.append(user(prompt))
        msg = code_chat.sample()
        content = msg.content.strip()
        
        # Clean common markdown code blocks
        code = re.sub(r'```(?:python|)?\s*\n?', '', content, flags=re.IGNORECASE | re.MULTILINE)
        code = re.sub(r'```\s*$', '', code, flags=re.MULTILINE)
        code = code.strip()
        
        if not code:
            code = content.strip()
        
        return json.dumps({"status": "success", "code": code})
    except Exception as e:
        return json.dumps({"error": f"Code generation failed: {str(e)}"})
