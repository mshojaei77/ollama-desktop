# Ollama JavaScript Library

The Ollama JavaScript library provides the easiest way to integrate your JavaScript project with [Ollama](https://github.com/jmorganca/ollama).

## Getting Started

```
npm i ollama
```

## Usage

```javascript
import ollama from 'ollama'

const response = await ollama.chat({
  model: 'llama3.1',
  messages: [{ role: 'user', content: 'Why is the sky blue?' }],
})
console.log(response.message.content)
```

### Browser Usage
To use the library without node, import the browser module.
```javascript
import ollama from 'ollama/browser'
```

## Streaming responses

Response streaming can be enabled by setting `stream: true`, modifying function calls to return an `AsyncGenerator` where each part is an object in the stream.

```javascript
import ollama from 'ollama'

const message = { role: 'user', content: 'Why is the sky blue?' }
const response = await ollama.chat({ model: 'llama3.1', messages: [message], stream: true })
for await (const part of response) {
  process.stdout.write(part.message.content)
}
```

## API

The Ollama JavaScript library's API is designed around the [Ollama REST API](https://github.com/jmorganca/ollama/blob/main/docs/api.md)

### chat

```javascript
ollama.chat(request)
```

- `request` `<Object>`: The request object containing chat parameters.

  - `model` `<string>` The name of the model to use for the chat.
  - `messages` `<Message[]>`: Array of message objects representing the chat history.
    - `role` `<string>`: The role of the message sender ('user', 'system', or 'assistant').
    - `content` `<string>`: The content of the message.
    - `images` `<Uint8Array[] | string[]>`: (Optional) Images to be included in the message, either as Uint8Array or base64 encoded strings.
  - `format` `<string>`: (Optional) Set the expected format of the response (`json`).
  - `stream` `<boolean>`: (Optional) When true an `AsyncGenerator` is returned.
  - `keep_alive` `<string | number>`: (Optional) How long to keep the model loaded. A number (seconds) or a string with a duration unit suffix ("300ms", "1.5h", "2h45m", etc.)
  - `tools` `<Tool[]>`: (Optional) A list of tool calls the model may make.
  - `options` `<Options>`: (Optional) Options to configure the runtime.

- Returns: `<ChatResponse>`

### generate

```javascript
ollama.generate(request)
```

- `request` `<Object>`: The request object containing generate parameters.
  - `model` `<string>` The name of the model to use for the chat.
  - `prompt` `<string>`: The prompt to send to the model.
  - `suffix` `<string>`: (Optional) Suffix is the text that comes after the inserted text.
  - `system` `<string>`: (Optional) Override the model system prompt.
  - `template` `<string>`: (Optional) Override the model template.
  - `raw` `<boolean>`: (Optional) Bypass the prompt template and pass the prompt directly to the model.
  - `images` `<Uint8Array[] | string[]>`: (Optional) Images to be included, either as Uint8Array or base64 encoded strings.
  - `format` `<string>`: (Optional) Set the expected format of the response (`json`).
  - `stream` `<boolean>`: (Optional) When true an `AsyncGenerator` is returned.
  - `keep_alive` `<string | number>`: (Optional) How long to keep the model loaded. A number (seconds) or a string with a duration unit suffix ("300ms", "1.5h", "2h45m", etc.)
  - `options` `<Options>`: (Optional) Options to configure the runtime.
- Returns: `<GenerateResponse>`

### pull

```javascript
ollama.pull(request)
```

- `request` `<Object>`: The request object containing pull parameters.
  - `model` `<string>` The name of the model to pull.
  - `insecure` `<boolean>`: (Optional) Pull from servers whose identity cannot be verified.
  - `stream` `<boolean>`: (Optional) When true an `AsyncGenerator` is returned.
- Returns: `<ProgressResponse>`

### push

```javascript
ollama.push(request)
```

- `request` `<Object>`: The request object containing push parameters.
  - `model` `<string>` The name of the model to push.
  - `insecure` `<boolean>`: (Optional) Push to servers whose identity cannot be verified.
  - `stream` `<boolean>`: (Optional) When true an `AsyncGenerator` is returned.
- Returns: `<ProgressResponse>`

### create

```javascript
ollama.create(request)
```

- `request` `<Object>`: The request object containing create parameters.
  - `model` `<string>` The name of the model to create.
  - `from` `<string>`: The base model to derive from.
  - `stream` `<boolean>`: (Optional) When true an `AsyncGenerator` is returned.
  - `quantize` `<string>`: Quanization precision level (`q8_0`, `q4_K_M`, etc.).
  - `template` `<string>`: (Optional) The prompt template to use with the model.
  - `license` `<string|string[]>`: (Optional) The license(s) associated with the model.
  - `system` `<string>`: (Optional) The system prompt for the model.
  - `parameters` `<Record<string, unknown>>`: (Optional) Additional model parameters as key-value pairs.
  - `messages` `<Message[]>`: (Optional) Initial chat messages for the model.
  - `adapters` `<Record<string, string>>`: (Optional) A key-value map of LoRA adapter configurations.
- Returns: `<ProgressResponse>`

Note: The `files` parameter is not currently supported in `ollama-js`.

### delete

```javascript
ollama.delete(request)
```

- `request` `<Object>`: The request object containing delete parameters.
  - `model` `<string>` The name of the model to delete.
- Returns: `<StatusResponse>`

### copy

```javascript
ollama.copy(request)
```

- `request` `<Object>`: The request object containing copy parameters.
  - `source` `<string>` The name of the model to copy from.
  - `destination` `<string>` The name of the model to copy to.
- Returns: `<StatusResponse>`

### list

```javascript
ollama.list()
```

- Returns: `<ListResponse>`

### show

```javascript
ollama.show(request)
```

- `request` `<Object>`: The request object containing show parameters.
  - `model` `<string>` The name of the model to show.
  - `system` `<string>`: (Optional) Override the model system prompt returned.
  - `template` `<string>`: (Optional) Override the model template returned.
  - `options` `<Options>`: (Optional) Options to configure the runtime.
- Returns: `<ShowResponse>`

### embed

```javascript
ollama.embed(request)
```

- `request` `<Object>`: The request object containing embedding parameters.
  - `model` `<string>` The name of the model used to generate the embeddings.
  - `input` `<string> | <string[]>`: The input used to generate the embeddings.
  - `truncate` `<boolean>`: (Optional) Truncate the input to fit the maximum context length supported by the model.
  - `keep_alive` `<string | number>`: (Optional) How long to keep the model loaded. A number (seconds) or a string with a duration unit suffix ("300ms", "1.5h", "2h45m", etc.)
  - `options` `<Options>`: (Optional) Options to configure the runtime.
- Returns: `<EmbedResponse>`

### ps

```javascript
ollama.ps()
```

- Returns: `<ListResponse>`

### abort

```javascript
ollama.abort()
```

This method will abort **all** streamed generations currently running with the client instance.
If there is a need to manage streams with timeouts, it is recommended to have one Ollama client per stream.

All asynchronous threads listening to streams (typically the ```for await (const part of response)```) will throw an ```AbortError``` exception. See [examples/abort/abort-all-requests.ts](examples/abort/abort-all-requests.ts) for an example.

## Custom client

A custom client can be created with the following fields:

- `host` `<string>`: (Optional) The Ollama host address. Default: `"http://127.0.0.1:11434"`.
- `fetch` `<Object>`: (Optional) The fetch library used to make requests to the Ollama host.

```javascript
import { Ollama } from 'ollama'

const ollama = new Ollama({ host: 'http://127.0.0.1:11434' })
const response = await ollama.chat({
  model: 'llama3.1',
  messages: [{ role: 'user', content: 'Why is the sky blue?' }],
})
```

## Building

To build the project files run:

```sh
npm run build
```
# API

## Endpoints

- [Generate a completion](#generate-a-completion)
- [Generate a chat completion](#generate-a-chat-completion)
- [Create a Model](#create-a-model)
- [List Local Models](#list-local-models)
- [Show Model Information](#show-model-information)
- [Copy a Model](#copy-a-model)
- [Delete a Model](#delete-a-model)
- [Pull a Model](#pull-a-model)
- [Push a Model](#push-a-model)
- [Generate Embeddings](#generate-embeddings)
- [List Running Models](#list-running-models)
- [Version](#version)

## Conventions

### Model names

Model names follow a `model:tag` format, where `model` can have an optional namespace such as `example/model`. Some examples are `orca-mini:3b-q4_1` and `llama3:70b`. The tag is optional and, if not provided, will default to `latest`. The tag is used to identify a specific version.

### Durations

All durations are returned in nanoseconds.

### Streaming responses

Certain endpoints stream responses as JSON objects. Streaming can be disabled by providing `{"stream": false}` for these endpoints.

## Generate a completion

```
POST /api/generate
```

Generate a response for a given prompt with a provided model. This is a streaming endpoint, so there will be a series of responses. The final response object will include statistics and additional data from the request.

### Parameters

- `model`: (required) the [model name](#model-names)
- `prompt`: the prompt to generate a response for
- `suffix`: the text after the model response
- `images`: (optional) a list of base64-encoded images (for multimodal models such as `llava`)

Advanced parameters (optional):

- `format`: the format to return a response in. Format can be `json` or a JSON schema
- `options`: additional model parameters listed in the documentation for the [Modelfile](./modelfile.md#valid-parameters-and-values) such as `temperature`
- `system`: system message to (overrides what is defined in the `Modelfile`)
- `template`: the prompt template to use (overrides what is defined in the `Modelfile`)
- `stream`: if `false` the response will be returned as a single response object, rather than a stream of objects
- `raw`: if `true` no formatting will be applied to the prompt. You may choose to use the `raw` parameter if you are specifying a full templated prompt in your request to the API
- `keep_alive`: controls how long the model will stay loaded into memory following the request (default: `5m`)
- `context` (deprecated): the context parameter returned from a previous request to `/generate`, this can be used to keep a short conversational memory

#### Structured outputs

Structured outputs are supported by providing a JSON schema in the `format` parameter. The model will generate a response that matches the schema. See the [structured outputs](#request-structured-outputs) example below.

#### JSON mode

Enable JSON mode by setting the `format` parameter to `json`. This will structure the response as a valid JSON object. See the JSON mode [example](#request-json-mode) below.

> [!IMPORTANT]
> It's important to instruct the model to use JSON in the `prompt`. Otherwise, the model may generate large amounts whitespace.

### Examples

#### Generate request (Streaming)

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?"
}'
```

##### Response

A stream of JSON objects is returned:

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T08:52:19.385406455-07:00",
  "response": "The",
  "done": false
}
```

The final response in the stream also includes additional data about the generation:

- `total_duration`: time spent generating the response
- `load_duration`: time spent in nanoseconds loading the model
- `prompt_eval_count`: number of tokens in the prompt
- `prompt_eval_duration`: time spent in nanoseconds evaluating the prompt
- `eval_count`: number of tokens in the response
- `eval_duration`: time in nanoseconds spent generating the response
- `context`: an encoding of the conversation used in this response, this can be sent in the next request to keep a conversational memory
- `response`: empty if the response was streamed, if not streamed, this will contain the full response

To calculate how fast the response is generated in tokens per second (token/s), divide `eval_count` / `eval_duration` * `10^9`.

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T19:22:45.499127Z",
  "response": "",
  "done": true,
  "context": [1, 2, 3],
  "total_duration": 10706818083,
  "load_duration": 6338219291,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 130079000,
  "eval_count": 259,
  "eval_duration": 4232710000
}
```

#### Request (No streaming)

##### Request

A response can be received in one reply when streaming is off.

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

##### Response

If `stream` is set to `false`, the response will be a single JSON object:

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T19:22:45.499127Z",
  "response": "The sky is blue because it is the color of the sky.",
  "done": true,
  "context": [1, 2, 3],
  "total_duration": 5043500667,
  "load_duration": 5025959,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 325953000,
  "eval_count": 290,
  "eval_duration": 4709213000
}
```

#### Request (with suffix)

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "codellama:code",
  "prompt": "def compute_gcd(a, b):",
  "suffix": "    return result",
  "options": {
    "temperature": 0
  },
  "stream": false
}'
```

##### Response

```json
{
  "model": "codellama:code",
  "created_at": "2024-07-22T20:47:51.147561Z",
  "response": "\n  if a == 0:\n    return b\n  else:\n    return compute_gcd(b % a, a)\n\ndef compute_lcm(a, b):\n  result = (a * b) / compute_gcd(a, b)\n",
  "done": true,
  "done_reason": "stop",
  "context": [...],
  "total_duration": 1162761250,
  "load_duration": 6683708,
  "prompt_eval_count": 17,
  "prompt_eval_duration": 201222000,
  "eval_count": 63,
  "eval_duration": 953997000
}
```

#### Request (Structured outputs)

##### Request

```shell
curl -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "llama3.1:8b",
  "prompt": "Ollama is 22 years old and is busy saving the world. Respond using JSON",
  "stream": false,
  "format": {
    "type": "object",
    "properties": {
      "age": {
        "type": "integer"
      },
      "available": {
        "type": "boolean"
      }
    },
    "required": [
      "age",
      "available"
    ]
  }
}'
```

##### Response

```json
{
  "model": "llama3.1:8b",
  "created_at": "2024-12-06T00:48:09.983619Z",
  "response": "{\n  \"age\": 22,\n  \"available\": true\n}",
  "done": true,
  "done_reason": "stop",
  "context": [1, 2, 3],
  "total_duration": 1075509083,
  "load_duration": 567678166,
  "prompt_eval_count": 28,
  "prompt_eval_duration": 236000000,
  "eval_count": 16,
  "eval_duration": 269000000
}
```

#### Request (JSON mode)

> [!IMPORTANT]
> When `format` is set to `json`, the output will always be a well-formed JSON object. It's important to also instruct the model to respond in JSON.

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "What color is the sky at different times of the day? Respond using JSON",
  "format": "json",
  "stream": false
}'
```

##### Response

```json
{
  "model": "llama3.2",
  "created_at": "2023-11-09T21:07:55.186497Z",
  "response": "{\n\"morning\": {\n\"color\": \"blue\"\n},\n\"noon\": {\n\"color\": \"blue-gray\"\n},\n\"afternoon\": {\n\"color\": \"warm gray\"\n},\n\"evening\": {\n\"color\": \"orange\"\n}\n}\n",
  "done": true,
  "context": [1, 2, 3],
  "total_duration": 4648158584,
  "load_duration": 4071084,
  "prompt_eval_count": 36,
  "prompt_eval_duration": 439038000,
  "eval_count": 180,
  "eval_duration": 4196918000
}
```

The value of `response` will be a string containing JSON similar to:

```json
{
  "morning": {
    "color": "blue"
  },
  "noon": {
    "color": "blue-gray"
  },
  "afternoon": {
    "color": "warm gray"
  },
  "evening": {
    "color": "orange"
  }
}
```

#### Request (with images)

To submit images to multimodal models such as `llava` or `bakllava`, provide a list of base64-encoded `images`:

#### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llava",
  "prompt":"What is in this picture?",
  "stream": false,
  "images": ["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"]
}'
```

#### Response

```json
{
  "model": "llava",
  "created_at": "2023-11-03T15:36:02.583064Z",
  "response": "A happy cartoon character, which is cute and cheerful.",
  "done": true,
  "context": [1, 2, 3],
  "total_duration": 2938432250,
  "load_duration": 2559292,
  "prompt_eval_count": 1,
  "prompt_eval_duration": 2195557000,
  "eval_count": 44,
  "eval_duration": 736432000
}
```

#### Request (Raw Mode)

In some cases, you may wish to bypass the templating system and provide a full prompt. In this case, you can use the `raw` parameter to disable templating. Also note that raw mode will not return a context.

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "[INST] why is the sky blue? [/INST]",
  "raw": true,
  "stream": false
}'
```

#### Request (Reproducible outputs)

For reproducible outputs, set `seed` to a number:

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Why is the sky blue?",
  "options": {
    "seed": 123
  }
}'
```

##### Response

```json
{
  "model": "mistral",
  "created_at": "2023-11-03T15:36:02.583064Z",
  "response": " The sky appears blue because of a phenomenon called Rayleigh scattering.",
  "done": true,
  "total_duration": 8493852375,
  "load_duration": 6589624375,
  "prompt_eval_count": 14,
  "prompt_eval_duration": 119039000,
  "eval_count": 110,
  "eval_duration": 1779061000
}
```

#### Generate request (With options)

If you want to set custom options for the model at runtime rather than in the Modelfile, you can do so with the `options` parameter. This example sets every available option, but you can set any of them individually and omit the ones you do not want to override.

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?",
  "stream": false,
  "options": {
    "num_keep": 5,
    "seed": 42,
    "num_predict": 100,
    "top_k": 20,
    "top_p": 0.9,
    "min_p": 0.0,
    "typical_p": 0.7,
    "repeat_last_n": 33,
    "temperature": 0.8,
    "repeat_penalty": 1.2,
    "presence_penalty": 1.5,
    "frequency_penalty": 1.0,
    "mirostat": 1,
    "mirostat_tau": 0.8,
    "mirostat_eta": 0.6,
    "penalize_newline": true,
    "stop": ["\n", "user:"],
    "numa": false,
    "num_ctx": 1024,
    "num_batch": 2,
    "num_gpu": 1,
    "main_gpu": 0,
    "low_vram": false,
    "vocab_only": false,
    "use_mmap": true,
    "use_mlock": false,
    "num_thread": 8
  }
}'
```

##### Response

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T19:22:45.499127Z",
  "response": "The sky is blue because it is the color of the sky.",
  "done": true,
  "context": [1, 2, 3],
  "total_duration": 4935886791,
  "load_duration": 534986708,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 107345000,
  "eval_count": 237,
  "eval_duration": 4289432000
}
```

#### Load a model

If an empty prompt is provided, the model will be loaded into memory.

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2"
}'
```

##### Response

A single JSON object is returned:

```json
{
  "model": "llama3.2",
  "created_at": "2023-12-18T19:52:07.071755Z",
  "response": "",
  "done": true
}
```

#### Unload a model

If an empty prompt is provided and the `keep_alive` parameter is set to `0`, a model will be unloaded from memory.

##### Request

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "keep_alive": 0
}'
```

##### Response

A single JSON object is returned:

```json
{
  "model": "llama3.2",
  "created_at": "2024-09-12T03:54:03.516566Z",
  "response": "",
  "done": true,
  "done_reason": "unload"
}
```

## Generate a chat completion

```
POST /api/chat
```

Generate the next message in a chat with a provided model. This is a streaming endpoint, so there will be a series of responses. Streaming can be disabled using `"stream": false`. The final response object will include statistics and additional data from the request.

### Parameters

- `model`: (required) the [model name](#model-names)
- `messages`: the messages of the chat, this can be used to keep a chat memory
- `tools`: list of tools in JSON for the model to use if supported

The `message` object has the following fields:

- `role`: the role of the message, either `system`, `user`, `assistant`, or `tool`
- `content`: the content of the message
- `images` (optional): a list of images to include in the message (for multimodal models such as `llava`)
- `tool_calls` (optional): a list of tools in JSON that the model wants to use

Advanced parameters (optional):

- `format`: the format to return a response in. Format can be `json` or a JSON schema. 
- `options`: additional model parameters listed in the documentation for the [Modelfile](./modelfile.md#valid-parameters-and-values) such as `temperature`
- `stream`: if `false` the response will be returned as a single response object, rather than a stream of objects
- `keep_alive`: controls how long the model will stay loaded into memory following the request (default: `5m`)

### Structured outputs

Structured outputs are supported by providing a JSON schema in the `format` parameter. The model will generate a response that matches the schema. See the [Chat request (Structured outputs)](#chat-request-structured-outputs) example below.

### Examples

#### Chat Request (Streaming)

##### Request

Send a chat message with a streaming response.

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "why is the sky blue?"
    }
  ]
}'
```

##### Response

A stream of JSON objects is returned:

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T08:52:19.385406455-07:00",
  "message": {
    "role": "assistant",
    "content": "The",
    "images": null
  },
  "done": false
}
```

Final response:

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T19:22:45.499127Z",
  "message": {
    "role": "assistant",
    "content": ""
  },
  "done": true,
  "total_duration": 4883583458,
  "load_duration": 1334875,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 342546000,
  "eval_count": 282,
  "eval_duration": 4535599000
}
```

#### Chat request (No streaming)

##### Request

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "why is the sky blue?"
    }
  ],
  "stream": false
}'
```

##### Response

```json
{
  "model": "llama3.2",
  "created_at": "2023-12-12T14:13:43.416799Z",
  "message": {
    "role": "assistant",
    "content": "Hello! How are you today?"
  },
  "done": true,
  "total_duration": 5191566416,
  "load_duration": 2154458,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 383809000,
  "eval_count": 298,
  "eval_duration": 4799921000
}
```

#### Chat request (Structured outputs)

##### Request

```shell
curl -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
  "model": "llama3.1",
  "messages": [{"role": "user", "content": "Ollama is 22 years old and busy saving the world. Return a JSON object with the age and availability."}],
  "stream": false,
  "format": {
    "type": "object",
    "properties": {
      "age": {
        "type": "integer"
      },
      "available": {
        "type": "boolean"
      }
    },
    "required": [
      "age",
      "available"
    ]
  },
  "options": {
    "temperature": 0
  }
}'
```

##### Response

```json
{
  "model": "llama3.1",
  "created_at": "2024-12-06T00:46:58.265747Z",
  "message": { "role": "assistant", "content": "{\"age\": 22, \"available\": false}" },
  "done_reason": "stop",
  "done": true,
  "total_duration": 2254970291,
  "load_duration": 574751416,
  "prompt_eval_count": 34,
  "prompt_eval_duration": 1502000000,
  "eval_count": 12,
  "eval_duration": 175000000
}
```

#### Chat request (With History)

Send a chat message with a conversation history. You can use this same approach to start the conversation using multi-shot or chain-of-thought prompting.

##### Request

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "why is the sky blue?"
    },
    {
      "role": "assistant",
      "content": "due to rayleigh scattering."
    },
    {
      "role": "user",
      "content": "how is that different than mie scattering?"
    }
  ]
}'
```

##### Response

A stream of JSON objects is returned:

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T08:52:19.385406455-07:00",
  "message": {
    "role": "assistant",
    "content": "The"
  },
  "done": false
}
```

Final response:

```json
{
  "model": "llama3.2",
  "created_at": "2023-08-04T19:22:45.499127Z",
  "done": true,
  "total_duration": 8113331500,
  "load_duration": 6396458,
  "prompt_eval_count": 61,
  "prompt_eval_duration": 398801000,
  "eval_count": 468,
  "eval_duration": 7701267000
}
```

#### Chat request (with images)

##### Request

Send a chat message with images. The images should be provided as an array, with the individual images encoded in Base64.

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llava",
  "messages": [
    {
      "role": "user",
      "content": "what is in this image?",
      "images": ["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"]
    }
  ]
}'
```

##### Response

```json
{
  "model": "llava",
  "created_at": "2023-12-13T22:42:50.203334Z",
  "message": {
    "role": "assistant",
    "content": " The image features a cute, little pig with an angry facial expression. It's wearing a heart on its shirt and is waving in the air. This scene appears to be part of a drawing or sketching project.",
    "images": null
  },
  "done": true,
  "total_duration": 1668506709,
  "load_duration": 1986209,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 359682000,
  "eval_count": 83,
  "eval_duration": 1303285000
}
```

#### Chat request (Reproducible outputs)

##### Request

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "options": {
    "seed": 101,
    "temperature": 0
  }
}'
```

##### Response

```json
{
  "model": "llama3.2",
  "created_at": "2023-12-12T14:13:43.416799Z",
  "message": {
    "role": "assistant",
    "content": "Hello! How are you today?"
  },
  "done": true,
  "total_duration": 5191566416,
  "load_duration": 2154458,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 383809000,
  "eval_count": 298,
  "eval_duration": 4799921000
}
```

#### Chat request (with tools)

##### Request

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "What is the weather today in Paris?"
    }
  ],
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "description": "Get the current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The location to get the weather for, e.g. San Francisco, CA"
            },
            "format": {
              "type": "string",
              "description": "The format to return the weather in, e.g. 'celsius' or 'fahrenheit'",
              "enum": ["celsius", "fahrenheit"]
            }
          },
          "required": ["location", "format"]
        }
      }
    }
  ]
}'
```

##### Response

```json
{
  "model": "llama3.2",
  "created_at": "2024-07-22T20:33:28.123648Z",
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {
        "function": {
          "name": "get_current_weather",
          "arguments": {
            "format": "celsius",
            "location": "Paris, FR"
          }
        }
      }
    ]
  },
  "done_reason": "stop",
  "done": true,
  "total_duration": 885095291,
  "load_duration": 3753500,
  "prompt_eval_count": 122,
  "prompt_eval_duration": 328493000,
  "eval_count": 33,
  "eval_duration": 552222000
}
```

#### Load a model

If the messages array is empty, the model will be loaded into memory.

##### Request

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": []
}'
```

##### Response

```json
{
  "model": "llama3.2",
  "created_at":"2024-09-12T21:17:29.110811Z",
  "message": {
    "role": "assistant",
    "content": ""
  },
  "done_reason": "load",
  "done": true
}
```

#### Unload a model

If the messages array is empty and the `keep_alive` parameter is set to `0`, a model will be unloaded from memory.

##### Request

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [],
  "keep_alive": 0
}'
```

##### Response

A single JSON object is returned:

```json
{
  "model": "llama3.2",
  "created_at":"2024-09-12T21:33:17.547535Z",
  "message": {
    "role": "assistant",
    "content": ""
  },
  "done_reason": "unload",
  "done": true
}
```

## Create a Model

```
POST /api/create
```

Create a model from:
 * another model;
 * a safetensors directory; or
 * a GGUF file.

If you are creating a model from a safetensors directory or from a GGUF file, you must [create a blob](#create-a-blob) for each of the files and then use the file name and SHA256 digest associated with each blob in the `files` field.

### Parameters

- `model`: name of the model to create
- `from`: (optional) name of an existing model to create the new model from
- `files`: (optional) a dictionary of file names to SHA256 digests of blobs to create the model from
- `adapters`: (optional) a dictionary of file names to SHA256 digests of blobs for LORA adapters
- `template`: (optional) the prompt template for the model
- `license`: (optional) a string or list of strings containing the license or licenses for the model
- `system`: (optional) a string containing the system prompt for the model
- `parameters`: (optional) a dictionary of parameters for the model (see [Modelfile](./modelfile.md#valid-parameters-and-values) for a list of parameters)
- `messages`: (optional) a list of message objects used to create a conversation
- `stream`: (optional) if `false` the response will be returned as a single response object, rather than a stream of objects
- `quantize` (optional): quantize a non-quantized (e.g. float16) model

#### Quantization types

| Type | Recommended |
| --- | :-: |
| q2_K | |
| q3_K_L | |
| q3_K_M | |
| q3_K_S | |
| q4_0 | |
| q4_1 | |
| q4_K_M | * |
| q4_K_S | |
| q5_0 | |
| q5_1 | |
| q5_K_M | |
| q5_K_S | |
| q6_K | |
| q8_0 | * |

### Examples

#### Create a new model

Create a new model from an existing model.

##### Request

```shell
curl http://localhost:11434/api/create -d '{
  "model": "mario",
  "from": "llama3.2",
  "system": "You are Mario from Super Mario Bros."
}'
```

##### Response

A stream of JSON objects is returned:

```json
{"status":"reading model metadata"}
{"status":"creating system layer"}
{"status":"using already created layer sha256:22f7f8ef5f4c791c1b03d7eb414399294764d7cc82c7e94aa81a1feb80a983a2"}
{"status":"using already created layer sha256:8c17c2ebb0ea011be9981cc3922db8ca8fa61e828c5d3f44cb6ae342bf80460b"}
{"status":"using already created layer sha256:7c23fb36d80141c4ab8cdbb61ee4790102ebd2bf7aeff414453177d4f2110e5d"}
{"status":"using already created layer sha256:2e0493f67d0c8c9c68a8aeacdf6a38a2151cb3c4c1d42accf296e19810527988"}
{"status":"using already created layer sha256:2759286baa875dc22de5394b4a925701b1896a7e3f8e53275c36f75a877a82c9"}
{"status":"writing layer sha256:df30045fe90f0d750db82a058109cecd6d4de9c90a3d75b19c09e5f64580bb42"}
{"status":"writing layer sha256:f18a68eb09bf925bb1b669490407c1b1251c5db98dc4d3d81f3088498ea55690"}
{"status":"writing manifest"}
{"status":"success"}
```

#### Quantize a model

Quantize a non-quantized model.

##### Request

```shell
curl http://localhost:11434/api/create -d '{
  "model": "llama3.1:quantized",
  "from": "llama3.1:8b-instruct-fp16",
  "quantize": "q4_K_M"
}'
```

##### Response

A stream of JSON objects is returned:

```json
{"status":"quantizing F16 model to Q4_K_M"}
{"status":"creating new layer sha256:667b0c1932bc6ffc593ed1d03f895bf2dc8dc6df21db3042284a6f4416b06a29"}
{"status":"using existing layer sha256:11ce4ee3e170f6adebac9a991c22e22ab3f8530e154ee669954c4bc73061c258"}
{"status":"using existing layer sha256:0ba8f0e314b4264dfd19df045cde9d4c394a52474bf92ed6a3de22a4ca31a177"}
{"status":"using existing layer sha256:56bb8bd477a519ffa694fc449c2413c6f0e1d3b1c88fa7e3c9d88d3ae49d4dcb"}
{"status":"creating new layer sha256:455f34728c9b5dd3376378bfb809ee166c145b0b4c1f1a6feca069055066ef9a"}
{"status":"writing manifest"}
{"status":"success"}
```

#### Create a model from GGUF

Create a model from a GGUF file. The `files` parameter should be filled out with the file name and SHA256 digest of the GGUF file you wish to use. Use [/api/blobs/:digest](#push-a-blob) to push the GGUF file to the server before calling this API.


##### Request

```shell
curl http://localhost:11434/api/create -d '{
  "model": "my-gguf-model",
  "files": {
    "test.gguf": "sha256:432f310a77f4650a88d0fd59ecdd7cebed8d684bafea53cbff0473542964f0c3"
  }
}'
```

##### Response

A stream of JSON objects is returned:

```json
{"status":"parsing GGUF"}
{"status":"using existing layer sha256:432f310a77f4650a88d0fd59ecdd7cebed8d684bafea53cbff0473542964f0c3"}
{"status":"writing manifest"}
{"status":"success"}
```


#### Create a model from a Safetensors directory

The `files` parameter should include a dictionary of files for the safetensors model which includes the file names and SHA256 digest of each file. Use [/api/blobs/:digest](#push-a-blob) to first push each of the files to the server before calling this API. Files will remain in the cache until the Ollama server is restarted.

##### Request

```shell
curl http://localhost:11434/api/create -d '{
  "model": "fred",
  "files": {
    "config.json": "sha256:dd3443e529fb2290423a0c65c2d633e67b419d273f170259e27297219828e389",
    "generation_config.json": "sha256:88effbb63300dbbc7390143fbbdd9d9fa50587b37e8bfd16c8c90d4970a74a36",
    "special_tokens_map.json": "sha256:b7455f0e8f00539108837bfa586c4fbf424e31f8717819a6798be74bef813d05",
    "tokenizer.json": "sha256:bbc1904d35169c542dffbe1f7589a5994ec7426d9e5b609d07bab876f32e97ab",
    "tokenizer_config.json": "sha256:24e8a6dc2547164b7002e3125f10b415105644fcf02bf9ad8b674c87b1eaaed6",
    "model.safetensors": "sha256:1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f"
  }
}'
```

##### Response

A stream of JSON objects is returned:

```shell
{"status":"converting model"}
{"status":"creating new layer sha256:05ca5b813af4a53d2c2922933936e398958855c44ee534858fcfd830940618b6"}
{"status":"using autodetected template llama3-instruct"}
{"status":"using existing layer sha256:56bb8bd477a519ffa694fc449c2413c6f0e1d3b1c88fa7e3c9d88d3ae49d4dcb"}
{"status":"writing manifest"}
{"status":"success"}
```

## Check if a Blob Exists

```shell
HEAD /api/blobs/:digest
```

Ensures that the file blob (Binary Large Object) used with create a model exists on the server. This checks your Ollama server and not ollama.com.

### Query Parameters

- `digest`: the SHA256 digest of the blob

### Examples

#### Request

```shell
curl -I http://localhost:11434/api/blobs/sha256:29fdb92e57cf0827ded04ae6461b5931d01fa595843f55d36f5b275a52087dd2
```

#### Response

Return 200 OK if the blob exists, 404 Not Found if it does not.

## Push a Blob

```
POST /api/blobs/:digest
```

Push a file to the Ollama server to create a "blob" (Binary Large Object).

### Query Parameters

- `digest`: the expected SHA256 digest of the file

### Examples

#### Request

```shell
curl -T model.gguf -X POST http://localhost:11434/api/blobs/sha256:29fdb92e57cf0827ded04ae6461b5931d01fa595843f55d36f5b275a52087dd2
```

#### Response

Return 201 Created if the blob was successfully created, 400 Bad Request if the digest used is not expected.

## List Local Models

```
GET /api/tags
```

List models that are available locally.

### Examples

#### Request

```shell
curl http://localhost:11434/api/tags
```

#### Response

A single JSON object will be returned.

```json
{
  "models": [
    {
      "name": "codellama:13b",
      "modified_at": "2023-11-04T14:56:49.277302595-07:00",
      "size": 7365960935,
      "digest": "9f438cb9cd581fc025612d27f7c1a6669ff83a8bb0ed86c94fcf4c5440555697",
      "details": {
        "format": "gguf",
        "family": "llama",
        "families": null,
        "parameter_size": "13B",
        "quantization_level": "Q4_0"
      }
    },
    {
      "name": "llama3:latest",
      "modified_at": "2023-12-07T09:32:18.757212583-08:00",
      "size": 3825819519,
      "digest": "fe938a131f40e6f6d40083c9f0f430a515233eb2edaa6d72eb85c50d64f2300e",
      "details": {
        "format": "gguf",
        "family": "llama",
        "families": null,
        "parameter_size": "7B",
        "quantization_level": "Q4_0"
      }
    }
  ]
}
```

## Show Model Information

```
POST /api/show
```

Show information about a model including details, modelfile, template, parameters, license, system prompt.

### Parameters

- `model`: name of the model to show
- `verbose`: (optional) if set to `true`, returns full data for verbose response fields

### Examples

#### Request

```shell
curl http://localhost:11434/api/show -d '{
  "model": "llama3.2"
}'
```

#### Response

```json
{
  "modelfile": "# Modelfile generated by \"ollama show\"\n# To build a new Modelfile based on this one, replace the FROM line with:\n# FROM llava:latest\n\nFROM /Users/matt/.ollama/models/blobs/sha256:200765e1283640ffbd013184bf496e261032fa75b99498a9613be4e94d63ad52\nTEMPLATE \"\"\"{{ .System }}\nUSER: {{ .Prompt }}\nASSISTANT: \"\"\"\nPARAMETER num_ctx 4096\nPARAMETER stop \"\u003c/s\u003e\"\nPARAMETER stop \"USER:\"\nPARAMETER stop \"ASSISTANT:\"",
  "parameters": "num_keep                       24\nstop                           \"<|start_header_id|>\"\nstop                           \"<|end_header_id|>\"\nstop                           \"<|eot_id|>\"",
  "template": "{{ if .System }}<|start_header_id|>system<|end_header_id|>\n\n{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>\n\n{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>\n\n{{ .Response }}<|eot_id|>",
  "details": {
    "parent_model": "",
    "format": "gguf",
    "family": "llama",
    "families": [
      "llama"
    ],
    "parameter_size": "8.0B",
    "quantization_level": "Q4_0"
  },
  "model_info": {
    "general.architecture": "llama",
    "general.file_type": 2,
    "general.parameter_count": 8030261248,
    "general.quantization_version": 2,
    "llama.attention.head_count": 32,
    "llama.attention.head_count_kv": 8,
    "llama.attention.layer_norm_rms_epsilon": 0.00001,
    "llama.block_count": 32,
    "llama.context_length": 8192,
    "llama.embedding_length": 4096,
    "llama.feed_forward_length": 14336,
    "llama.rope.dimension_count": 128,
    "llama.rope.freq_base": 500000,
    "llama.vocab_size": 128256,
    "tokenizer.ggml.bos_token_id": 128000,
    "tokenizer.ggml.eos_token_id": 128009,
    "tokenizer.ggml.merges": [],            // populates if `verbose=true`
    "tokenizer.ggml.model": "gpt2",
    "tokenizer.ggml.pre": "llama-bpe",
    "tokenizer.ggml.token_type": [],        // populates if `verbose=true`
    "tokenizer.ggml.tokens": []             // populates if `verbose=true`
  }
}
```

## Copy a Model

```
POST /api/copy
```

Copy a model. Creates a model with another name from an existing model.

### Examples

#### Request

```shell
curl http://localhost:11434/api/copy -d '{
  "source": "llama3.2",
  "destination": "llama3-backup"
}'
```

#### Response

Returns a 200 OK if successful, or a 404 Not Found if the source model doesn't exist.

## Delete a Model

```
DELETE /api/delete
```

Delete a model and its data.

### Parameters

- `model`: model name to delete

### Examples

#### Request

```shell
curl -X DELETE http://localhost:11434/api/delete -d '{
  "model": "llama3:13b"
}'
```

#### Response

Returns a 200 OK if successful, 404 Not Found if the model to be deleted doesn't exist.

## Pull a Model

```
POST /api/pull
```

Download a model from the ollama library. Cancelled pulls are resumed from where they left off, and multiple calls will share the same download progress.

### Parameters

- `model`: name of the model to pull
- `insecure`: (optional) allow insecure connections to the library. Only use this if you are pulling from your own library during development.
- `stream`: (optional) if `false` the response will be returned as a single response object, rather than a stream of objects

### Examples

#### Request

```shell
curl http://localhost:11434/api/pull -d '{
  "model": "llama3.2"
}'
```

#### Response

If `stream` is not specified, or set to `true`, a stream of JSON objects is returned:

The first object is the manifest:

```json
{
  "status": "pulling manifest"
}
```

Then there is a series of downloading responses. Until any of the download is completed, the `completed` key may not be included. The number of files to be downloaded depends on the number of layers specified in the manifest.

```json
{
  "status": "downloading digestname",
  "digest": "digestname",
  "total": 2142590208,
  "completed": 241970
}
```

After all the files are downloaded, the final responses are:

```json
{
    "status": "verifying sha256 digest"
}
{
    "status": "writing manifest"
}
{
    "status": "removing any unused layers"
}
{
    "status": "success"
}
```

if `stream` is set to false, then the response is a single JSON object:

```json
{
  "status": "success"
}
```

## Push a Model

```
POST /api/push
```

Upload a model to a model library. Requires registering for ollama.ai and adding a public key first.

### Parameters

- `model`: name of the model to push in the form of `<namespace>/<model>:<tag>`
- `insecure`: (optional) allow insecure connections to the library. Only use this if you are pushing to your library during development.
- `stream`: (optional) if `false` the response will be returned as a single response object, rather than a stream of objects

### Examples

#### Request

```shell
curl http://localhost:11434/api/push -d '{
  "model": "mattw/pygmalion:latest"
}'
```

#### Response

If `stream` is not specified, or set to `true`, a stream of JSON objects is returned:

```json
{ "status": "retrieving manifest" }
```

and then:

```json
{
  "status": "starting upload",
  "digest": "sha256:bc07c81de745696fdf5afca05e065818a8149fb0c77266fb584d9b2cba3711ab",
  "total": 1928429856
}
```

Then there is a series of uploading responses:

```json
{
  "status": "starting upload",
  "digest": "sha256:bc07c81de745696fdf5afca05e065818a8149fb0c77266fb584d9b2cba3711ab",
  "total": 1928429856
}
```

Finally, when the upload is complete:

```json
{"status":"pushing manifest"}
{"status":"success"}
```

If `stream` is set to `false`, then the response is a single JSON object:

```json
{ "status": "success" }
```

## Generate Embeddings

```
POST /api/embed
```

Generate embeddings from a model

### Parameters

- `model`: name of model to generate embeddings from
- `input`: text or list of text to generate embeddings for

Advanced parameters:

- `truncate`: truncates the end of each input to fit within context length. Returns error if `false` and context length is exceeded. Defaults to `true`
- `options`: additional model parameters listed in the documentation for the [Modelfile](./modelfile.md#valid-parameters-and-values) such as `temperature`
- `keep_alive`: controls how long the model will stay loaded into memory following the request (default: `5m`)

### Examples

#### Request

```shell
curl http://localhost:11434/api/embed -d '{
  "model": "all-minilm",
  "input": "Why is the sky blue?"
}'
```

#### Response

```json
{
  "model": "all-minilm",
  "embeddings": [[
    0.010071029, -0.0017594862, 0.05007221, 0.04692972, 0.054916814,
    0.008599704, 0.105441414, -0.025878139, 0.12958129, 0.031952348
  ]],
  "total_duration": 14143917,
  "load_duration": 1019500,
  "prompt_eval_count": 8
}
```

#### Request (Multiple input)

```shell
curl http://localhost:11434/api/embed -d '{
  "model": "all-minilm",
  "input": ["Why is the sky blue?", "Why is the grass green?"]
}'
```

#### Response

```json
{
  "model": "all-minilm",
  "embeddings": [[
    0.010071029, -0.0017594862, 0.05007221, 0.04692972, 0.054916814,
    0.008599704, 0.105441414, -0.025878139, 0.12958129, 0.031952348
  ],[
    -0.0098027075, 0.06042469, 0.025257962, -0.006364387, 0.07272725,
    0.017194884, 0.09032035, -0.051705178, 0.09951512, 0.09072481
  ]]
}
```

## List Running Models
```
GET /api/ps
```

List models that are currently loaded into memory.

#### Examples

### Request

```shell
curl http://localhost:11434/api/ps
```

#### Response

A single JSON object will be returned.

```json
{
  "models": [
    {
      "name": "mistral:latest",
      "model": "mistral:latest",
      "size": 5137025024,
      "digest": "2ae6f6dd7a3dd734790bbbf58b8909a606e0e7e97e94b7604e0aa7ae4490e6d8",
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "llama",
        "families": [
          "llama"
        ],
        "parameter_size": "7.2B",
        "quantization_level": "Q4_0"
      },
      "expires_at": "2024-06-04T14:38:31.83753-07:00",
      "size_vram": 5137025024
    }
  ]
}
```

## Generate Embedding

> Note: this endpoint has been superseded by `/api/embed`

```
POST /api/embeddings
```

Generate embeddings from a model

### Parameters

- `model`: name of model to generate embeddings from
- `prompt`: text to generate embeddings for

Advanced parameters:

- `options`: additional model parameters listed in the documentation for the [Modelfile](./modelfile.md#valid-parameters-and-values) such as `temperature`
- `keep_alive`: controls how long the model will stay loaded into memory following the request (default: `5m`)

### Examples

#### Request

```shell
curl http://localhost:11434/api/embeddings -d '{
  "model": "all-minilm",
  "prompt": "Here is an article about llamas..."
}'
```

#### Response

```json
{
  "embedding": [
    0.5670403838157654, 0.009260174818336964, 0.23178744316101074, -0.2916173040866852, -0.8924556970596313,
    0.8785552978515625, -0.34576427936553955, 0.5742510557174683, -0.04222835972905159, -0.137906014919281
  ]
}
```

## Version

```
GET /api/version
```

Retrieve the Ollama version

### Examples

#### Request

```shell
curl http://localhost:11434/api/version
```

#### Response

```json
{
  "version": "0.5.1"
}
```


# tool use/function calling with Node.js and Ollama

Ollama recently announced tool support and like many popular libraries for using AI and large language models (LLMs) Ollama provides a JavaScript API along with its Python API.

If you've been following along with our journey into Node.js and Large Language Models (How to get started with large language models and Node.js,  Diving Deeper with large language models and Node.js) you know that function calling/tool use is one of the things we took a look at earlier.

While our initial experience with function calling/tool use helped us understand how it worked, the results were mixed. This was not a surprise as it was early in the function call/tool use evolution and still a fast moving area for large language models. With the introduction of support into Ollama, we wanted to take another look to see what progress has been made.

In this blog post we'll expand our experiments with tool use and Node.js, continuing to use functions that return a person's favorite color, and adding one to get a person's favorite hockey team. For the experiments we don't really care what the functions being called are, just that we see them called when appropriate and that the information they return is used correctly.

In case you want to look ahead at any point while reading, all of the code and results are in the repository mhdawson/ai-tool-experimentation in the ollama subdirectory.

Interaction with the Large Language Model
While LLMs are often used in a chat with a person we want to be able to run the same sequence a nubmer of times with different models so typing responses manually would not be practical. Instead we have a fixed set of messages that the "person" chatting with the model will make regardless of the response from the LLM. Since responses from an LLM may be different each time it does mean that sometimes the next message from the person does not fully fit with the last resposne from the LLM.  This turned out not to be a big problem as the sequence we use often works out well, and our evaluation of success takes into consideration that some of the "person" messages don't fit the flow.

The sequences of messages that we used were as follows (from : favorite-color.mjs) :

const questions = ['What is my favorite color?', 
                   'My city is Ottawa',
                   'My country is Canada',
                   'I moved to Montreal. What is my favorite color now?',
                   'My city is Montreal and my country is Canada',
                   'My city is Ottawa and my country is Canada, what is my favorite color?',
                   'What is my favorite hockey team ?',
                   'My city is Montreal and my country is Canada',
                  ];
Copy snippet
We send these messages to the LLM as follows:

  // maintains chat history
  const messages = [{type: 'system', content:
    'only answer questions about a favorite color by using the response from the favoriteColorTool ' +
    'when asked for a favorite color if you have not called the favoriteColorTool, call it ' + 
    'Never guess a favorite color ' +
    'Do not be chatty ' +
    'Give short answers when possible'
  }];

  console.log(`Iteration ${j} ------------------------------------------------------------`);

  for (let i = 0; i< questions.length; i++) {
    console.log('QUESTION: ' + questions[i]);
    messages.push({ role: 'user', content: questions[i] });
    const response = await ollama.chat({ model: model, messages: messages, tools: tools});
    console.log('  RESPONSE:' + (await handleResponse(messages, response)).message.content);
  }  
Copy snippet
We'll explain the handleResponse function along with the tools passed into the chat call in the next section when we introduce the fuctions/tools that are made available.

In the ideal case the LLM would respond as follows:

'What is my favorite color?'                              -> I need your city and country
'My city is Ottawa'                                       -> I need your Country
'My country is Canada'                                    -> Your favorite color is black 
'I moved to Montreal. What is my favorite color now?'     -> Your favorite color is red
'My city is Montreal and my country is Canada'            -> Your favorite color is red
'My city is Ottawa and my country is Canada, what is my favorite color?' -> your favorite color is black
'What is my favorite hockey team ?'                       -> your favorite hockey team is the Ottawa Senators
'My city is Montreal and my country is Canada'            -> Your favorite hockey team is the Montreal Canadians
Copy snippet
The Functions/Tools
In the Ollama API tools are passed in as a JSON structure similar to other APIs, with the JSON describing the type of tool, the name, description and for functions the function parameters. In our example we defined two tools as follows:

/////////////////////////////
// TOOL info for the LLM
const tools =  [{
  type: 'function',
  function: {
    name: 'favoriteColorTool',
    description: 'returns the favorite color for person given their City and Country',
    parameters: {
      type: 'object',
      properties: {
        city: {
          type: 'string',
          description: 'the city for the person',
        },
        country: {
          type: 'string',
          description: 'the country for the person',
        },
      },
      required: ['city', 'country'],
    },
  },
},
{
  type: 'function',
  function: {
    name: 'favoriteHockeyTeamTool',
    description: 'returns the favorite hockey team for person given their City and Country',
    parameters: {
      type: 'object',
      properties: {
        city: {
          type: 'string',
          description: 'the city for the person',
        },
        country: {
          type: 'string',
          description: 'the country for the person',
        },
      },
      required: ['city', 'country'],
    },
  },
}
];
Copy snippet
This is what was provided in the tools: tools parameter in the ollama.chat call, and provides the LLM with information about the tools/functions which are available when information outside of its knowledge based is required.

LLMs do not call the functions directly, instead the LLM uses the description provided to return a request to call a function with a set of parameters.  The Ollama API's parse the response from the LLM and put tool requests into the response.message.tool_calls object. Using that object from a response we can figure out if there are any requests to call tools, and if so make the call to the tools.

For each tool we call on behalf of the LLM, the response from the tool is then added to the existing message history and we make a new chat request to the LLM. The LLM sees the responses for the tools requests that it made and can then request that additional tools be called or return a response to the user.

The work of calling functions when requested by the LLM, including handling the possibility recursive tool calls, is implemented in the handleRequest function:

async function handleResponse(messages, response) {
  // push the models response to the chat
  messages.push(response.message);

  if (response.message.tool_calls && (response.message.tool_calls.length != 0)) {
    for (const tool of response.message.tool_calls) {
      // log the function calls so that we see when they are called
      log('  FUNCTION CALLED WITH: ' + inspect(tool));
      console.log('  CALLED:' + tool.function.name);
      const func = funcs[tool.function.name];
      if (func) {
        const funcResponse = func(tool.function.arguments);
        messages.push({ role: 'tool', content: funcResponse });
      } else {
        messages.push({ role: 'tool', content: 'invalid tool called' });
        console.log(tool.function.name);
      }
    }

    // call the model again so that it can process the data returned by the 
    // function calls
    return ( handleResponse( messages,
      await ollama.chat({ model: model, messages: messages, tools: tools})
    ));
  } else { 
    // no function calls just return the response
    return response;
  }
}
Copy snippet
The implementation of the two functions are simple JavaScript functions where we have hard coded the favorite color and favorite hockey team for people in Ottawa, Canada and Montreal, Canada. You can easily imagine how this could be a database lookup, a call to a microservice or something else:

/////////////////////////////
// FUNCTION IMPLEMENTATIONS
const funcs = {
  favoriteColorTool: getFavoriteColor,
  favoriteHockeyTeamTool: getFavoriteHockeyTeam
};

function getFavoriteColor(args) {
  const city = args.city;
  const country = args.country;
  if ((city === 'Ottawa') && (country === 'Canada')) {
    return 'the favoriteColorTool returned that the favorite color for Ottawa Canada is black';
  } else if ((city === 'Montreal') && (country === 'Canada')) {
    return 'the favoriteColorTool returned that the favorite color for Montreal Canada is red';
  } else {
    return `the favoriteColorTool returned The city or country
            was not valid, please ask the user for them`;
  }
};

function getFavoriteHockeyTeam(args) {
  const city = args.city;
  const country = args.country;
  if ((city === 'Ottawa') && (country === 'Canada')) {
    return 'the favoriteColorTool returned that the favorite hockey team for Ottawa Canada is The Ottawa Senators';
  } else if ((city === 'Montreal') && (country === 'Canada')) {
    return 'the favoriteColorTool returned that the favorite hockey team for Montreal Canada is the Montreal Canadians';
  } else {
    return `the favoriteColorTool returned The city or country
            was not valid, please ask the user for them`;
  }
};
Copy snippet
Tools calling in Action
Ok so now we know how to use the Ollama API to:

 tell the model what functions are available
call those functions when asked by the model, and 
how to return the answers to the model so that it can use them in answering the original question
but how well does it work ?

To check that out we ran the sequence of questions using a number of different models that are supported for tool calling by with Ollama. We started with mistral as we'd used that model in pervious explorations and expanded the list to:

mistral
mistral-nemo
llama3.1-8B
hermes3-8B
llama3.1-70B
firefunction-v2-70B
For each of these models we ran the question sequence 10 times with a fresh history and captured the output.  This resulted in a lot of data and faced the prospect of going through the results manually to see how things went.  This made us wonder if an LLM could help us avoid doing all of that work manually.  To that end we put together a simple question that asked the LLM to rate the results of each run - rate.mjs. These are the key parts of that:

  const messages = [{role: 'system', content:
    'you are a helpful agent that reviews a chat transcript and figures out how well questions about the users ' +
    'favorite color are answered ' +
    'The LLM can ask clarifying questions. ' +
    'The LLM should ask for the City and Country, if it has not already been provided, when asked for a favorite color. ' 
  }];

  const ratingQuestion = 
    'Use only the conversation in the context to find answers ' + 
    'Given that the right answer when you are in Ottawa Canada is black and that the right answer is when you are in Montreal Canada is red, report the percentage success in the conversation in answering the question "what is my favorite color" ' + 
    'Only answers where the specific color is returned should be considered as an instance for calculation of the percentage' + 
    'Do not include requests for additional information in the total requests for a favorite color' + 
    'Explain your answers ' + 
    'Always return the percentage in the format [Percentage: X].\n ' + 
    '<context> ' + 
    data + 
    '<context/> ';
Copy snippet
We first tried using ollama31-8B, a model that would fit into our GPU (4070Ti Super 16G), and run at a reasonable speed. Unfortunately the results were underwelming. We won't go into too many details as it's not core to this post but in the end we only got reasonable results from a larger 70B model and OpenAI ChatGPT. For smaller models despite trying all sorts of different models and hints in the prompt we could not get reasonable results.  Once we switched to the larger models the results were much better without having to work on the prompt too much.  The main thing the larger models struggled with was following the instruction that requests for additional information not negatively affect the percentage of success.

Our main takeaway is to be carefull not to assume how well an LLM can perform based on the results when using the smaller 7B/8B models. Larger models will likely be better and also much easier to get reasonable results with. Unfortunately that mean running slowly (which is what we did with local 70B runs) or using hosted services (either public or within your organization).

In the end we did the hard work of evaluating the results by hand as well as using a few differet models. This ended up being subjective as right/wrong in the flow needed some allowances to make sense when comparing between the flows.

Before you look at the results its imporant to make it clear that these results are based on the flow we outlined, and what we considered the ideal output as shared earlier. Your milage may vary on how this applies to other flows, tools, etc. It is not intended to be performance comparison, only to share our experience trying out tool use with Node.js and Ollama. The full runs for each model and the output from the ratings by the models are available in mhdawson/ai-tool-experimentation in the ollama subdirectory. In the evaulation we only considered the percentage of success of answering questions about the users favorite color and requests for additional information when information was needed was considered ok. The summary percentage was taken by adding the percentage from each of the 10 runs and dividing by 10. 

The results were as show in Figure 1:

Picture of table showing the results for each model as caculated by different raters
Figure 1 - accuracy as rated by different raters.

As mentioned earlier using a smaller model did not do a great job of matching "human review" which is shown as the "Manual" column. We only show llama 3.1 8B for one entry as an example but we did try a number of models and prompts.  Both ChatGPT and llama 3.1 70B did a reasonable job of matching human review.

Interestingly, the two mistral models seemed to struggle the most which may explain our ealier experience with function calling/models the older mistral model is what we'd mostly used in prior exploration and we used a similar question flow.

For our question sequence the llama31-70B model did best, followed by the hermes3-8B model (However,see the next section for a big caveat on that).  Further, exploration of the hermes3 model based on how well it did for a smaller model.

Based on these results, our impression is that function calling has improved since our earlier explorations but it will still be important to understand your typical flow and explore different models to see how well they work for your usecase.

A last minute wrinkle
Our question flow pretty much only consisted of questions that involved calling a tool, and from the output flows we could see that some models seemed to call multiple functions even when asked for only the favorite color, or call functions more often that other models.

We decided we should take a quick look at how a model acted when asked a question that would not involved calling a function. To that end we added a question about the fastest car in the world in the middle:

const questions = ['What is my favorite color?',
                   'My city is Ottawa',
                   'My country is Canada',
                   'I moved to Montreal. What is my favorite color now?',
                   'My city is Montreal and my country is Canada',
                   'My city is Ottawa and my country is Canada, what is my favorite color?',
                   'What is the fastest car in the world?',
                   'What is my favorite hockey team ?',
                   'My city is Montreal and my country is Canada',
                  ];
Copy snippet
It was a surprise that with both llama3.1 models (even the 70B one) the model attempted to call non-existent functions and failed to answer the new question:


 ....
QUESTION: What is the fastest car in the world?
  CALLED:favoriteHockeyTeamTool
  CALLED:fastestCarInTheWorldTool
fastestCarInTheWorldTool
  CALLED:carsInfoTool
carsInfoTool
  RESPONSE:It looks like we're having some issues with the tools. The favoriteHockeyTeamTool and fastestCarInTheWorldTool are not returning any useful information.
Copy snippet
So while llama3.1 70B did best on our original flow, it starts to fall down when we introduce questions that can't be answered by one of the tools provided.

Other models seemed to do just fine (Hermes3, mistal-nemo)  and answered the new question from their existing knowledge base without trying to call a function.

QUESTION: What is the fastest car in the world?
  RESPONSE:
The Bugatti Chiron Super Sport 300+ holds the title of being the fastest production car in the world, reaching a top speed of 304 miles per hour.
Copy snippet
This highlights that our earlier question sequence/evaluation focussed too much on whether functions where called when needed and left out the important aspect of making sure that imaginary functions are not called and that the model can still answer questions from its knowledge base when tools are provided. Testing to make sure that a model is going to call and not call functions appropriately when answering questions seems both important and hard to get right.

Wrapping up
We wanted to take an updated look at function calling, particularly after a leading tool like Ollama announced support. We learned a lot even with the limited exploration that we did. 

We hoped that his blog post has helped you understand how you can uses tools/function calls when using Node.js and the Ollama JavaScript APIs and some of the things to look out for as you explore how they might work(or not) in your use case.


"""

Tool support
July 25, 2024
ollama with a box of tools, ready to serve you

Ollama now supports tool calling with popular models such as Llama 3.1. This enables a model to answer a given prompt using tool(s) it knows about, making it possible for models to perform more complex tasks or interact with the outside world.

Example tools include:

Functions and APIs
Web browsing
Code interpreter
much more!
Tool calling
To enable tool calling, provide a list of available tools via the tools field in Ollama’s API.

import ollama

response = ollama.chat(
    model='llama3.1',
    messages=[{'role': 'user', 'content':
        'What is the weather in Toronto?'}],

		# provide a weather checking tool to the model
    tools=[{
      'type': 'function',
      'function': {
        'name': 'get_current_weather',
        'description': 'Get the current weather for a city',
        'parameters': {
          'type': 'object',
          'properties': {
            'city': {
              'type': 'string',
              'description': 'The name of the city',
            },
          },
          'required': ['city'],
        },
      },
    },
  ],
)

print(response['message']['tool_calls'])
Supported models will now answer with a tool_calls response. Tool responses can be provided via messages with the tool role. See API documentation for more information.

Supported models
A list of supported models can be found under the Tools category on the models page:

Llama 3.1
Mistral Nemo
Firefunction v2
Command-R +
Note: please check if you have the latest model by running ollama pull <model>

ollama.com tool models

OpenAI compatibility
Ollama’s OpenAI compatible endpoint also now supports tools, making it possible to switch to using Llama 3.1 and other models.

import openai

openai.base_url = "http://localhost:11434/v1"
openai.api_key = 'ollama'

response = openai.chat.completions.create(
	model="llama3.1",
	messages=messages,
	tools=tools,
)
Full examples
Python
JavaScript
Future improvements
Streaming tool calls: stream tool calls back to begin taking action faster when multiple tools are returned
Tool choice: force a model to use a tool
Let’s build together
We are so excited to bring you tool support, and see what you build with it!

If you have any feedback, please do not hesitate to tell us either in our Discord or via hello@ollama.com.

"""

```
Power-up Ollama chatbots with tools
How to use LangChain ‘tools’ with a locally run, open-source LLM
James Hicks
The Pythoneers
James Hicks

·
Follow

Published in
The Pythoneers

·
6 min read
·
Apr 13, 2024
125


6






Produced with DreamStudio
In this tutorial, we’ll build a locally run chatbot application with an open-source Large Language Model (LLM), augmented with LangChain ‘tools’.

Tools endow LLMs with additional powers like running code or web search. You can also build custom tools which will be the focus of this tutorial.

We’ll use Streamlit, LangChain, and Ollama to implement our chatbot.

Ollama — to run LLMs locally and for free.
LangChain — for orchestration of our LLM application.
Streamlit — for the frontend interface.
Let’s get an LLM up and running locally. First, we need to install Ollama on our machine. Download Ollama from the official website.

Once installed. Run the following in your command line:

ollama pull mistral:instruct
This downloads the Mistral Instruct model onto your machine. Ollama has a directory of several models to choose from. Through trial and error, I have found Mistral Instruct to be the most suitable open source model for using tools.

Next we’ll install Streamlit and LangChain. I use Pipenv for package management. But you could also use regular Pip.

pipenv install langchain langchain-community streamlit
Now create a python file for our application ‘chatbot.py’. Then import the dependencies. We’ll cover each in more detail below. For now, I’ve provided short comments explaining how each dependency is used.

import streamlit as st # to render the user interface.
from langchain_community.llms import Ollama # to use Ollama llms in langchain
from langchain_core.prompts import ChatPromptTemplate # crafts prompts for our llm
from langchain_community.chat_message_histories import\
StreamlitChatMessageHistory # stores message history
from langchain_core.tools import tool # tools for our llm
from langchain.tools.render import render_text_description # to describe tools as a string 
from langchain_core.output_parsers import JsonOutputParser # ensure JSON input for tools
from operator import itemgetter # to retrieve specific items in our chain.
Streamlit apps run from top to bottom every time the user interacts with the program. This means we need to define everything we need up front, starting with our LLM.

# Set up the LLM which will power our application.
model = Ollama(model='mistral:instruct')
Next let’s define the tools which our LLM will access. LLMs are famously poor at maths. So we’ll keep it simple by giving the LLM tools for basic arithmetic.

@tool
def add(first: int, second: int) -> int:
    "Add two integers."
    return first + second
As you can see, the first tool simply adds two numbers together. It’s a plain old python function with type annotation, and a @tool decorator. The decorator enhances our function with some useful properties.

print(add.name)
print(add.description)
print(add.args)
add
add(first: int, second: int) -> int - Add two integers.
{'first': {'title': 'First', 'type': 'integer'}, 'second': {'title': 'Second', 'type': 'integer'}
It also makes our function runnable using LangChain.

add.invoke({'first':3, 'second':6})
9
Our second tool follows a similar logic.

@tool
def multiply(first: int, second: int) -> int:
    """Multiply two integers together."""
    return first * second
This covers basic arithmetic. But our LLM is going to have to decide when to:

Add
Multiply
Just chat!
We’ll give it another tool for the last option.

@tool
def converse(input: str) -> str:
    "Provide a natural language response using the user input."
    return model.invoke(input)
This tool takes the user input and passes it to our LLM for a normal response. (It will become clear why we need another tool for this shortly, when we build out our LangChain ‘chain’).

We can get a text summary of our tools like so:

tools = [add, multiply, converse]
rendered_tools = render_text_description(tools)
print(rendered_tools)
add: add(first: int, second: int) -> int - Add two integers.
multiply: multiply(first: int, second: int) -> int - Multiply two integers together.
converse: converse(input: str) -> str - Provide a natural language response using the user input.
Now we need a system prompt to tell our LLM what to do.

system_prompt = f"""You are an assistant that has access to the following set of tools.
Here are the names and descriptions for each tool:

{rendered_tools}
Given the user input, return the name and input of the tool to use.
Return your response as a JSON blob with 'name' and 'arguments' keys.
The value associated with the 'arguments' key should be a dictionary of parameters."""
This instructs our LLM to respond to user input with a piece JSON containing the ‘name’ of the chosen tool and the relevant ‘arguments’.

We can pass the user input using LangChain’s ChatPromptTemplate.

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("user", "{input}")]
)
At this point, we are ready construct a LangChain chain to test our logic so far.

chain = prompt | model | JsonOutputParser()
This chain combines our prompt with the LLM and passes the result through JsonOuputParser, which checks the output is in the correct format.

chain.invoke({'input': 'What is 3 times 23'})
{'name': 'multiply', 'arguments': {'first': 3, 'second': 23}}
chain.invoke({'input': 'How are you today?'})
{'name': 'converse', 'arguments': {'input': 'How are you today?'}}
Looks like our LLM is choosing the right tool for each input. But how do we actually run the tool to return a response to the user?

# Define a function which returns the chosen tool
# to be run as part of the chain.
def tool_chain(model_output):
    tool_map = {tool.name: tool for tool in tools}
    chosen_tool = tool_map[model_output["name"]]
    return itemgetter("arguments") | chosen_tool
This function:

Takes the model output e.g. {‘name’: ‘multiply’, ‘arguments’: {‘first’: 3, ‘second’: 23}}.
Creates a dictionary mapping of the tools e.g. {'add': <tool_object>, 'multiply': <tool_object>, 'converse': <tool_object>}.
Selects the chosen tool based on the value associated with the ‘name’ key of the model output e.g. 'multiply'
Returns a runnable that passes the arguments e.g. {‘first’: 3, ‘second’: 23} to the chosen tool.
We can add this to our chain and test our LLM with tools.

chain = prompt | model | JsonOutputParser() | tool_chain
chain.invoke({'input': 'What is 3 times 23'})
69
Bingo! Our LLM is using its tools to get to the right answer.

Now its time to turn this chain into an intelligent chatbot.

First, we configure the Streamlit chat history:

# Set up message history.
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("I can add, multiply, or just chat! How can I help you?")
The StreamlitChatMessageHistory object provides an ability store chat messages in the Streamlit session state. This allows the messages to persist across re-runs of the Streamlit application.

Each run, we check if there are any messages, otherwise we add an initial AI assistant message to the history.

# Set the page title.
st.title("Chatbot with tools")
# Render the chat history.
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)
Then we render the page title and full message history.

Finally, we add a component to take user input and respond accordingly.

# React to user input
if input := st.chat_input("What is up?"):
# Display user input and save to message history.
    st.chat_message("user").write(input)
    msgs.add_user_message(input) 
    # Invoke chain to get reponse.
    response = chain.invoke({'input': input})                 
    # Display AI assistant response and save to message history.
    st.chat_message("assistant").write(str(response))
    msgs.add_ai_message(response)
That’s it! We now have a fully functioning chat interface powered by an LLM with access to tools.

Have a go by running the following in the command line.

streamlit run chatbot.py

Screenshot by author
Well done if you got this far!

In this walkthrough we:

Installed Ollama to run LLMs locally.
Defined a set of LangChain ‘tools’.
Gave our LLM access to tools using a LangChain ‘chain’.
Created a chat user interface for the LLM using Streamlit.
All the code is available on my Github here. Feel free to clone the repo as a base for your own project.

Today, we only scratched the surface of what is possible with LangChain tools. Now you are equipped to give your own chatbot access to more sophisticated tools available here. For example, why not try giving your own LLM access to web search using Tavily?

Thanks for reading and happy coding!

To produce this post, I relied heavily on the Langchain and Streamlit documentation. Be sure to check these resources out if you want to go into more detail on any of the topics discussed.
```