from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI(title="Grok Agent Chat")

html = &#10;&#10;"""
&lt;!DOCTYPE html&gt;
&lt;html&gt;
&lt;head&gt;
    &lt;title&gt;Grok Agent&lt;/title&gt;
    &lt;script src=&quot;https://unpkg.com/htmx.org@1.9.10&quot;&gt;&lt;/script&gt;
    &lt;script src=&quot;https://cdn.tailwindcss.com&quot;&gt;&lt;/script&gt;
    &lt;script&gt;
        tailwind.config = {
          darkMode: 'class',
          theme: {
            extend: {
              colors: {
                primary: '#1f2937',
              }
            }
          }
        }
    &lt;/script&gt;
&lt;/head&gt;
&lt;body class=&quot;bg-gray-900 text-white min-h-screen p-8 font-mono&quot;&gt;
    &lt;div class=&quot;max-w-4xl mx-auto&quot;&gt;
        &lt;h1 class=&quot;text-4xl font-bold mb-12 text-center text-blue-400&quot;&gt;🤖 Grok Agent Chat&lt;/h1&gt;
        &lt;div id=&quot;chat-history&quot; class=&quot;bg-gray-800 border border-gray-700 p-6 rounded-xl mb-8 h-96 overflow-y-auto space-y-4&quot;&gt;&lt;/div&gt;
        &lt;form 
            id=&quot;chat-form&quot;
            hx-post=&quot;/chat&quot; 
            hx-target=&quot;#chat-history&quot; 
            hx-swap=&quot;beforeend&quot;
            hx-trigger=&quot;submit from:#chat-form&quot;
            class=&quot;flex gap-2&quot;&gt;
            &lt;input 
                name=&quot;goal&quot; 
                type=&quot;text&quot;
                placeholder=&quot;Enter your goal or command... (e.g., &#39;Add fizzbuzz feature&#39;)&quot;
                class=&quot;flex-1 p-4 bg-gray-700 border border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent&quot;
                autocomplete=&quot;off&quot;
                required&gt;
            &lt;button 
                type=&quot;submit&quot;
                class=&quot;bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 px-8 py-4 rounded-xl font-bold transition-all shadow-lg hover:shadow-xl&quot;&gt;
                Send 🚀
            &lt;/button&gt;
        &lt;/form&gt;
        &lt;p class=&quot;text-sm text-gray-400 mt-4 text-center&quot;&gt;
            Powered by &lt;a href=&quot;https://grok.x.ai&quot; class=&quot;text-blue-400 hover:underline&quot; target=&quot;_blank&quot;&gt;Grok&lt;/a&gt; | Live on port 8080
        &lt;/p&gt;
    &lt;/div&gt;
&lt;/body&gt;
&lt;/html&gt;
&#10;&#10;"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=html)

@app.post("/chat")
async def chat(request: Request):
    form = await request.form()
    goal = form.get("goal", "").strip()
    if not goal:
        return ""
    
    # TODO: Integrate with Redis pub/sub to send goal to agent
    # For now, mock response
    user_msg = f&#10;&lt;div class=&#34;flex justify-start mb-4&#34;&gt;&#10;    &lt;div class=&#34;bg-blue-900 p-4 rounded-2xl rounded-br-md max-w-xs&#34;&gt;{goal}&lt;/div&gt;&#10;&lt;/div&gt;
    agent_msg = &#10;&lt;div class=&#34;flex justify-end mb-4&#34;&gt;&#10;    &lt;div class=&#34;bg-gradient-to-r from-green-500 to-green-600 p-4 rounded-2xl rounded-bl-md max-w-xs animate-pulse&#34;&gt;&#10;        Processing &#39;{goal}&#39;... (Redis integration next!)&#10;    &lt;/div&gt;&#10;&lt;/div&gt;
    
    return user_msg + agent_msg
