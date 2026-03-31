from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI(title="Grok Agent")

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grok Agent</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {}
            }
        }
    </script>
</head>
<body class="bg-gray-900 text-white min-h-screen p-8 font-mono">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-5xl font-bold mb-12 text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Grok Agent 🚀
        </h1>
        <div id="output" class="border-2 border-gray-600 p-6 h-96 overflow-y-auto mb-8 bg-gray-800 rounded-lg shadow-xl">
            <div class="text-green-400">Agent ready! Enter a task below.</div>
        </div>
        <form id="task-form" class="flex gap-4">
            <input 
                id="task-input" 
                name="task" 
                type="text" 
                class="flex-1 p-4 bg-gray-700 border-2 border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none text-lg placeholder-gray-400"
                placeholder="Describe your coding task or goal..."
            >
            <button 
                type="submit"
                hx-post="/chat" 
                hx-include="#task-input"
                hx-target="#output" 
                hx-swap="beforeend"
                class="bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 px-8 py-4 rounded-lg font-bold text-lg shadow-lg transition-all"
            >
                Send Task
            </button>
        </form>
        <div id="status" class="mt-8 p-4 bg-gray-700 rounded-lg text-sm">
            Status: Idle
        </div>
    </div>
</body>
</html>
    """
    return html_content

@app.post("/chat", response_class=HTMLResponse)
async def chat(task: str = Form(...)):
    return f"""
<div class="mb-4 p-4 bg-blue-900/50 border-l-4 border-blue-400 rounded-r-lg">
    <strong class="text-blue-300">Task: </strong>{task}<br>
    <strong class="text-green-400">Executing...</strong>
</div>
<script>
    setTimeout(() => {{
        const output = document.getElementById('output');
        output.insertAdjacentHTML('beforeend', `
            <div class="mb-4 p-4 bg-green-900/50 border-l-4 border-green-400 rounded-r-lg">
                <strong class="text-green-300">Done!</strong> Task processed (simulation).
            </div>
        `);
        output.scrollTop = output.scrollHeight;
    }}, 1500);
</script>
    """
