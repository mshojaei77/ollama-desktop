import json
from ollama import Client

# Initialize Ollama client
client = Client()  # default connects to http://localhost:11434

# Define tool schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Return current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city":  {"type": "string"},
                    "units": {"type": "string", "enum": ["metric", "imperial"]}
                },
                "required": ["city"]
            }
        }
    }
]

# Construct system prompt, injecting the tool schemas
system_prompt = (
    "You are a smart assistant.\n"
    "If a user's request can be satisfied by any tool below, respond only with valid JSON that matches the tool's parameters.\n"
    "Do NOT add extra keys.\n"
    "Tools: " + json.dumps(tools) + "\n"
)

# Example conversation with Persian prompt
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user",   "content": "هوا در تهران چطور است؟"}
]

# Send user query to the base Persian Gemma model with embedded tool schema
response = client.chat(
    model="mshojaei77/gemma3persian-tools",
    messages=messages
)

message = response['message']

# Attempt to parse a JSON tool call from the assistant content
try:
    content = message.get('content', '').strip()
    # Remove markdown code block if present
    if content.startswith('```json\n') and content.endswith('\n```'):
        content = content[len('```json\n'):-len('\n```')]
    elif content.startswith('```') and content.endswith('```'):
        content = content[3:-3]
    call = json.loads(content)
    args = call # Directly use the parsed JSON as args
except json.JSONDecodeError:
    call = None

if args and 'city' in args:
    # Call the Python stub assuming it's a get_weather call
    def get_weather(city, units="metric"):
        # Dummy implementation: replace with real API calls
        return {"city": city, "temperature": 25, "units": units}
    result = get_weather(**args)

    # Append the tool call result to messages
    messages.append({
        "role": "tool",
        "name": "get_weather",
        "content": json.dumps(result)
    })


    messages[0] = {
        "role": "system",
        "content": "شما یک دستیار مفید هستید. با استفاده از اطلاعات آب‌وهوا، به پرسش کاربر به زبان طبیعی و فارسی پاسخ دهید."
    }
    # Send follow-up with tool result and new instructions for a natural language response
    final = client.chat(model="gemma3persian-tools", messages=messages)
    print("Final model response:")
    print(final['message']['content'])
else:
    print("No valid tool call in model response:")
    print(message.get('content')) 