# Ollama Vision: Using the `llama3.2-vision` Model

Ollama Vision extends the Ollama platform with multimodal capabilities. The `llama3.2-vision` model is an instruction‑tuned, image‑reasoning generative model available in 11B and 90B sizes. Use it to analyze, describe, and extract information from images via CLI, Python, or JavaScript.

---

## Prerequisites

- Ollama CLI (vX.X+)
- Python 3.8+ (for Python SDK)
- Node.js (for JavaScript SDK)

Install the SDKs:

```
pip install ollama
npm install ollama
```

Pull the vision model:

```
ollama pull llama3.2-vision
```

---

## 1. Command‑Line Interface (CLI)

Run the model directly from your terminal:

```
ollama run llama3.2-vision "Describe this image: ./art.jpg"
```

**Example Output:**

The image shows a colorful poster featuring an illustration of a cartoon character with spiky hair…

---

## 2. Python SDK

```python
import ollama

response = ollama.chat(
    model="llama3.2-vision",
    messages=[{
        "role": "user",
        "content": "What is in this image? Be concise.",
        "images": ["./art.jpg"]
    }]
)

print(response["message"]["content"])
```

---

## 3. JavaScript SDK

```javascript
import ollama from "ollama"

const response = await ollama.chat({
  model: "llama3.2-vision",
  messages: [{
    role: "user",
    content: "Describe this image:",
    images: ["./art.jpg"]
  }]
})

console.log(response.message.content)
```

> **Tip:** You can also supply base64-encoded strings or raw bytes in the `images` array.

---

## Advanced Usage

### Object Detection

```
ollama run llama3.2-vision "Tell me what you see: ./pic.jpg"
```

### Text Recognition

```
ollama run llama3.2-vision "What does the text say? ./wordart.png"
```

### Streaming Responses (Python)

```python
from ollama import generate
import httpx

raw = httpx.get("https://example.com/image.jpg").content

for chunk in generate(
    model="llama3.2-vision",
    prompt="Explain this image:",
    images=[raw],
    stream=True
):
    print(chunk["response"], end="", flush=True)
print()
```

---

## Structured JSON Output (Python + Pydantic)

```python
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from ollama import chat

class Object(BaseModel):
    name: str
    confidence: float
    attributes: str

class ImageSchema(BaseModel):
    summary: str
    objects: list[Object]
    scene: str
    colors: list[str]
    time_of_day: Literal["Morning", "Afternoon", "Evening", "Night"]
    setting: Literal["Indoor", "Outdoor", "Unknown"]
    text_content: str | None = None

response = chat(
    model="llama3.2-vision",
    format=ImageSchema.model_json_schema(),
    messages=[{
        "role": "user",
        "content": "Analyze this image and return detailed JSON output.",
        "images": [Path("./document.png")],
    }],
    options={"temperature": 0}
)

analysis = ImageSchema.model_validate_json(response["message"]["content"])
print(analysis.json(indent=2))
```