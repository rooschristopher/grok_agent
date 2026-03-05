import os
import json
from dotenv import load_dotenv
load_dotenv()
from xai_sdk import Client
from pathlib import Path
from tools.debug import auto_debug

client = Client(api_key=os.getenv("XAI_API_KEY"))
if not os.getenv("XAI_API_KEY"):
    print("No XAI_API_KEY")
    exit(1)

target_dir = Path('.')
result = auto_debug(client, target_dir, 'python demo_buggy.py', context_files=['demo_buggy.py'])
print(json.dumps(result, indent=2))