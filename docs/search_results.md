To pull and use a model from Ollama within a Python FastAPI application, you can follow these steps based on existing integration examples and best practices:

## 1. Install Ollama and Pull the Model

First, install Ollama on your local machine and pull the desired model using the Ollama CLI. For example, to pull the `llama3.1` model:

```bash
ollama pull llama3.1
```

This downloads the model locally so it can be run without internet access[2][4].

## 2. Set Up FastAPI Project and Dependencies

Create a Python environment and install necessary packages:

```bash
pip install fastapi requests uvicorn
```

Ollama also provides a Python package that can be installed via `pip install ollama` for easier API interaction[1].

## 3. Create FastAPI Endpoints to Interact with Ollama API

Ollama runs a local server (usually on port 11434) that exposes an HTTP API to generate text from models. You can create FastAPI endpoints that send POST requests to this API.

Here is a minimal example of a FastAPI app that sends prompts to the Ollama model and returns the response:

```python
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json

app = FastAPI()

class RequestBody(BaseModel):
    model: str
    prompt: str
    stream: bool = False

OLLAMA_API_URL = "http://localhost:11434/api/generate"
HEADERS = {"Content-Type": "application/json"}

@app.post("/generate")
def generate_text(body: RequestBody):
    payload = {
        "model": body.model,
        "prompt": body.prompt,
        "stream": body.stream
    }
    response = requests.post(OLLAMA_API_URL, headers=HEADERS, data=json.dumps(payload), stream=body.stream)
    if response.status_code == 200:
        if body.stream:
            # For streaming, yield lines (this requires async streaming endpoint setup)
            return response.iter_lines()
        else:
            return response.json()
    else:
        return {"error": response.text}
```

This example sends a request to Ollama's local API to generate text from the specified model and prompt[4].

## 4. Run FastAPI Server

Run your FastAPI app with:

```bash
uvicorn app:app --reload
```

The server will listen on `http://localhost:8000`.

## 5. Example Usage

You can test the API with curl or Python scripts. For example, using curl:

```bash
curl -X POST "http://localhost:8000/generate" -H "Content-Type: application/json" -d '{"model":"llama3.1","prompt":"Write a haiku.","stream":false}'
```

Or use a Python helper function to send requests, as demonstrated in the Ollama-FastAPI integration demo:

```python
import requests
import json

def send_request(model, prompt, stream=False, formatted=False):
    url = "http://localhost:8000/generate_formatted" if formatted else "http://localhost:8000/generate"
    headers = {"Content-Type": "application/json"}
    data = {"model": model, "prompt": prompt, "stream": stream}
    response = requests.post(url, headers=headers, data=json.dumps(data), stream=stream)
    if response.status_code == 200:
        if formatted:
            json_response = response.json()
            print(json_response["response"])
        else:
            for line in response.iter_lines():
                if line:
                    print(line.decode('utf-8'))
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Example call
send_request("llama3.1", "Write a haiku.", stream=False)
```

This function sends a request to your FastAPI server which in turn calls Ollama[1][5].

---

## Summary

- Use Ollama CLI to pull models locally (`ollama pull `).
- Create a FastAPI app that sends POST requests to Ollama’s local API (`http://localhost:11434/api/generate`).
- Handle streaming or non-streaming responses as needed.
- Run FastAPI server and send requests to your endpoints, which proxy calls to Ollama.

This approach allows you to integrate Ollama models into your Python FastAPI applications for local, private, and efficient AI model inference[1][2][4].

Citations:
[1] https://github.com/darcyg32/Ollama-FastAPI-Integration-Demo
[2] https://dev.to/vivekyadav200988/chatbot-application-using-models-available-in-ollama-17n9
[3] https://www.youtube.com/watch?v=cy6EAp4iNN4
[4] https://dev.to/evolvedev/setup-rest-api-service-of-ai-by-using-local-llms-with-ollama-2d81
[5] https://github.com/darcyg32/Ollama-FastAPI-Integration-Demo/blob/main/send_request.py
[6] https://github.com/darcyg32/Ollama-FastAPI-Integration-Demo/blob/main/app.py
[7] https://rabiloo.com/blog/fewest-scripts-maximum-power-serve-llms-locally-with-ollama
[8] https://www.youtube.com/watch?v=pLNqaTxvx3M
[9] https://www.youtube.com/watch?v=0c96PQd3nA8
[10] https://www.youtube.com/watch?v=hTjVA1hVSzc
[11] https://vadim.blog/deepseek-r1-ollama-fastapi

---
Answer from Perplexity: pplx.ai/share