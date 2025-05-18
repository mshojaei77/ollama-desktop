# Contributing to Ollama Desktop

## Development Setup

### Prerequisites
1. **Ollama**: Install from [ollama.com](https://ollama.com/)
2. **Python**: Python 3.8+
3. **Node.js and npm/yarn**: Latest LTS version recommended

### Setting Up Development Environment

1. **Clone the repository:**
```bash
git clone https://github.com/mshojaei77/ollama-desktop.git
cd ollama-desktop
```

2. **Set up Python environment:**
```bash
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Required packages in `requirements.txt`:
```txt
fastapi
uvicorn[standard]
pydantic
aiohttp
python-dotenv
```

3. **Install frontend dependencies:**
```bash
cd front
yarn install  # or npm install
cd ..
```

4. **Run for development:**
```bash
cd api
python ollama_mcp_api.py
```

## Technical Architecture

### Backend (FastAPI)
- Located in `api/` directory
- Run independently: `uvicorn ollama_mcp_api:app --reload --host 0.0.0.0 --port 8000`
- API docs at:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

### Frontend (React + Vite)
- Located in `front/` directory
- Run independently: `cd front && yarn dev`
- Available at `http://localhost:5173`

### System Architecture
- **Backend**: Python, FastAPI
- **Frontend**: React, TypeScript, Vite
- **AI Interaction**: Ollama
- **Database**: SQLite
- **UI**: Modern component library with Tailwind CSS

### Technical Features

#### Core API Features
- SSE (Server-Sent Events) for real-time streaming
- SQLite database for persistent storage
- CORS middleware configuration
- Automatic Ollama startup on Windows
- Database initialization & migration
- Comprehensive API documentation

#### MCP (Model Context Protocol) Technical Details
- Supports SSE and STDIO server types
- Configuration management via `ollama_desktop_config.json`
- Server connection handling and validation
- Direct query bypass options

## Contributing Guidelines

1. **Fork & Clone**
2. **Create Feature Branch**
   - Use descriptive names: `feature/xyz` or `fix/xyz`

3. **Code Standards**
   - Follow PEP 8 for Python
   - Use TypeScript for frontend
   - Write self-documenting code
   - Add comments for complex logic
   - Keep functions focused

4. **Commit Guidelines**
   - Clear, descriptive messages
   - Start with action verb
   - Reference issue numbers

5. **Testing**
   - Run all tests
   - Check linting
   - Test locally

6. **Pull Request Process**
   - Clear description
   - Link related issues
   - Wait for review
   - Address feedback

## Configuration Details
- MCP Server configs in `ollama_desktop_config.json`
- Environment variables
- Ollama endpoint configuration 