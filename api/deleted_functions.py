
@app.post("/mcp/connect", response_model=InitializeResponse, tags=["MCP"])
async def connect_to_mcp(request: MCPServerConnectRequest):
    """
    Connect to an MCP server
    
    - Supports both SSE and STDIO server types
    - Creates a new MCP client with the specified model
    - Returns a session ID for subsequent interactions
    """
    session_id = request.session_id or generate_session_id()
    if session_id in active_clients:
        await cleanup_session(session_id)
    
    client = await OllamaMCPPackage.create_client(model_name=request.model_name)
    
    success = False
    if request.server_type == "config" and request.server_url:  # Assuming server_url holds server_name
        success = await client.connect_to_configured_server(request.server_url)
    elif request.server_type == "sse":
        if not request.server_url:
            raise HTTPException(status_code=400, detail="server_url required for SSE")
        success = await client.connect_to_sse_server(request.server_url)
    elif request.server_type == "stdio":
        if not request.command or not request.args:
            raise HTTPException(status_code=400, detail="command and args required for STDIO")
        success = await client.connect_to_stdio_server(request.command, request.args)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported server type: {request.server_type}")
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to connect to MCP server")
    
    active_clients[session_id] = client
    await db.create_session(session_id=session_id, model_name=request.model_name, session_type="mcp_client")
    
    return InitializeResponse(session_id=session_id, status="connected", model=request.model_name)

@app.post("/mcp/query/stream", tags=["MCP"])
async def mcp_query_stream(request: ChatRequest):
    """
    Send a message to an MCP client and stream the response using SSE
    
    - Requires a valid session_id from a previous /chat/initialize-with-mcp or /mcp/connect call
    - Streams the model's response, including MCP tool execution results
    - Saves the conversation history to the database once completed
    """
    if request.session_id not in active_clients:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response from MCPClient"""
        try:
            print('! in generate_stream')
            client = active_clients[request.session_id]
            # queue = asyncio.Queue()
            
            # Save user message to history
            await db.add_chat_message(request.session_id, "user", request.message)
            
            # Process query with MCP tools and stream the response
            full_response = []
            tools = []
            
            # Use a custom streaming method (to be added to MCPClient)
            async for chunk in client.process_query_stream(request.message):
                if chunk is None:
                    break
                try:
                    chunk_data = json.loads(chunk.replace('data: ', ''))
                except json.JSONDecodeError as e:
                    app_logger.error(f"JSON decode error: {str(e)}. Chunk: {chunk}")
                    continue  # Skip this chunk and continue with the next one
                
                if chunk_data['type'] == 'token':
                    if isinstance(chunk_data['response'], str):
                        full_response.append(chunk_data['response'])
                    else:
                        app_logger.error(f"Unexpected type in full_response: {type(chunk_data['response'])}, value: {chunk_data['response']}")
                        full_response.append(str(chunk_data['response']))
                    yield chunk
                elif chunk_data['type'] == 'tool':
                    tools.append(chunk_data)
                    yield chunk
            
            print('! tools', tools)
            # Combine the full response for logging and history
            complete_response = ''.join(full_response)
            app_logger.info(f"Streamed complete response: {complete_response[:100]}...")
            
            # Update session activity
            await db.update_session_activity(request.session_id)
            
            # Save assistant response to history
            await db.add_chat_message(request.session_id, "assistant", complete_response, tools=tools)
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            app_logger.error(f"Error streaming MCP query: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )
    
@app.post("/mcp/direct-query", response_model=ChatResponse)
async def process_direct_query(request: ChatRequest):
    """Process a direct query with Ollama (no MCP tools)"""
    if request.session_id not in active_clients:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        client = active_clients[request.session_id]
        
        # Set direct mode
        client.direct_mode = True
        
        # Process direct query
        response = await client.process_direct_query(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        app_logger.error(f"Error processing direct query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing direct query: {str(e)}")

@app.post("/chat/initialize-with-mcp", response_model=InitializeResponse, tags=["Chat"])
async def initialize_chat_with_mcp(request: InitializeRequest):
    """
    Initialize a chat with active MCP servers if available, otherwise create a regular chat
    
    - Checks for active MCP servers
    - If active servers exist, creates a chat with MCP integration
    - If no active servers, falls back to regular chat
    """
    try:
        # Validate model name is not empty
        if not request.model_name or request.model_name.strip() == "":
            raise HTTPException(status_code=400, detail="Model name cannot be empty")
        
        session_id = request.session_id or generate_session_id()
        print("-----")
        print("session_id", session_id)
        print("-----")
        # Clean up existing session if it exists
        # if session_id in active_chatbots or session_id in active_clients:
        #     await cleanup_session(session_id)
        
        # Get active MCP servers
        # active_servers = await db.get_active_mcp_servers()
        config = await OllamaMCPPackage.load_mcp_config()
        servers_config = config.get("mcpServers", {})
        print("servers_config", servers_config)
        
        # If there are active MCP servers, use them
        if servers_config:
            app_logger.info(f"Initializing chat with active MCP servers: {servers_config}")
            for server in servers_config:
                print("!!server_config", server)
                server_config = servers_config[server]

                if not server_config:
                    app_logger.warning(f"No config found for active server {server}, falling back to regular chat")
                    return await initialize_chatbot(request)
                
                if not server_config.get('active', False):
                    app_logger.warning(f"Server {server} is not active, skipping")
                    continue
                
                # Create MCP client
                client = await OllamaMCPPackage.create_client(model_name=request.model_name)
                
                # Connect to server based on type
                server_type = server_config.get('type', 'stdio')
                
                if server_type == "sse":
                    server_url = server_config.get('url')
                    if not server_url:
                        raise HTTPException(status_code=400, detail="Server URL not found in config")
                    
                    await client.connect_to_sse_server(server_url=server_url)
                
                elif server_type == "stdio":
                    command = server_config.get('command')
                    args = server_config.get('args', [])
                    
                    if not command:
                        raise HTTPException(status_code=400, detail="Command not found in config")
                    
                    await client.connect_to_stdio_server(command=command, args=args)
                
            # Store in active clients
            active_clients[session_id] = client
            
            # Save to database
            await db.create_session(
                session_id=session_id,
                model_name=request.model_name,
                session_type="mcp_client",
                system_message=request.system_message
            )
            
            return InitializeResponse(
                session_id=session_id,
                status="connected_with_mcp",
                model=request.model_name
            )
        else:
            # No active MCP servers, fall back to regular chat
            app_logger.info("No active MCP servers, initializing regular chat")
            return await initialize_chatbot(request)
            
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error initializing chat with MCP: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@app.post("/chat/message/stream", tags=["Chat"])
async def chat_message_stream(request: ChatRequest):
    """
    Send a message to a chatbot and stream the response using SSE
    
    - Requires a valid session_id from a previous /chat/initialize call
    - Returns a streaming response from the model
    - Always tries MCP functionality first if available
    - Saves the conversation history to the database once completed
    """
    # Check if session exists in either active clients or active chatbots
    if request.session_id not in active_chatbots:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response using MCP tools when available"""
        try:
            print('! in generate_stream')
            
            # Save user message to history
            await db.add_chat_message(request.session_id, "user", request.message)
            
            # Set up variables to collect the full response
            full_response = []
            tools = []
            
            # Log the request to help with debugging
            app_logger.info(f"Starting stream for message: {request.message[:50]}...")
            
            # Try MCP client if available for this session
            has_mcp = request.session_id in active_clients
            print('! has_mcp', has_mcp)
            if has_mcp:
                client = active_clients[request.session_id]
                app_logger.info(f"Using MCP client for session {request.session_id}")
                
                # Process query with MCP tools and stream the response
                async for chunk in client.process_query_stream(request.message):
                    if chunk is None:
                        break
                        
                    try:
                        chunk_data = json.loads(chunk.replace('data: ', ''))
                    except json.JSONDecodeError as e:
                        app_logger.error(f"JSON decode error: {str(e)}. Chunk: {chunk}")
                        continue  # Skip this chunk and continue with the next one
                    
                    if chunk_data['type'] == 'token':
                        if isinstance(chunk_data['response'], str):
                            full_response.append(chunk_data['response'])
                        else:
                            app_logger.error(f"Unexpected type in full_response: {type(chunk_data['response'])}, value: {chunk_data['response']}")
                            full_response.append(str(chunk_data['response']))
                        yield chunk
                    elif chunk_data['type'] == 'tool':
                        tools.append(chunk_data)
                        yield chunk
                
                print('! tools', tools)
            # Use regular chatbot if MCP not available or no response from MCP
            else:
                # Get the appropriate chatbot instance
                chatbot = None
                if request.session_id in active_chatbots:
                    chatbot = active_chatbots[request.session_id]
                elif request.session_id in active_clients:
                    # Try to use client's internal chatbot if MCP is not working
                    client = active_clients[request.session_id]
                    if hasattr(client, 'chatbot') and client.chatbot:
                        chatbot = client.chatbot
                
                if not chatbot:
                    app_logger.error(f"No chatbot found for session {request.session_id}")
                    yield f"data: {json.dumps({'error': 'No chatbot found for this session'})}\n\n"
                    return
                
                try:
                    # Use the chatbot's streaming method to get chunks directly from Ollama
                    async for chunk in chatbot.chat_stream(request.message):
                        if chunk is None:
                            app_logger.warning("Received None chunk from chat_stream")
                            continue
                        
                        # Extract the content from chunk depending on format
                        if isinstance(chunk, dict):
                            if 'message' in chunk and 'content' in chunk['message']:
                                text = chunk['message']['content']
                            elif 'content' in chunk:
                                text = chunk['content']
                            elif 'text' in chunk:
                                text = chunk['text']
                            else:
                                app_logger.warning(f"Unrecognized chunk format: {chunk}")
                                continue
                        elif isinstance(chunk, str):
                            text = chunk
                        else:
                            app_logger.warning(f"Unrecognized chunk type: {type(chunk)}")
                            continue
                        
                        if not text:
                            continue
                            
                        # Add to the full response
                        full_response.append(text)
                        
                        # Send the chunk as an SSE event
                        yield f"data: {json.dumps({'text': text})}\n\n"
                except Exception as e:
                    app_logger.error(f"Error during streaming: {str(e)}", exc_info=True)
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    raise
            
            # Combine the full response for logging
            complete_response = ''.join(full_response)
            
            # Log the complete response
            if complete_response:
                app_logger.info(f"Streamed complete response: {complete_response[:100]}...")
            else:
                app_logger.warning("No content received in stream - empty response")
                # Add a fallback response if nothing was streamed
                fallback_response = "I'm sorry, I couldn't generate a response. There might be an issue with the model."
                yield f"data: {json.dumps({'text': fallback_response})}\n\n"
                complete_response = fallback_response
            
            # Update session activity
            await db.update_session_activity(request.session_id)
            
            # Save assistant response to history (with tools if MCP was used)
            await db.add_chat_message(request.session_id, "assistant", complete_response, tools=tools)
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            app_logger.error(f"Error streaming chat message: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )




class BaseChatbot:
    """Base class for chatbot implementations"""

    def __init__(
        self,
        model_name: str = "llama3.2",
        vision_model_name: str = "granite3.2-vision",
        system_message: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the base chatbot.

        Args:
            model_name: Name of the model to use
            system_message: Optional system message to set context
            verbose: Whether to output verbose logs
        """
        self.model_name = model_name
        self.system_message = system_message
        self.verbose = verbose
        self.memory = ConversationBufferMemory(return_messages=True)
        # Added vector store attribute
        self.vector_store: Optional[FAISS] = None
        self.vector_store_path: Optional[Path] = None # Store path for persistence if needed
        # Store the vision model name
        self.vision_model_name = vision_model_name

    async def initialize(self) -> None:
        """Initialize the chatbot - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement initialize()")

    async def chat(self, message: str) -> str:
        """Process a chat message and return the response"""
        raise NotImplementedError("Subclasses must implement chat()")

    async def cleanup(self) -> None:
        """Clean up any resources used by the chatbot"""
        # Base implementation resets memory
        self.memory = ConversationBufferMemory(return_messages=True)
        # Clean up vector store if it exists and was stored temporarily
        if self.vector_store_path and self.vector_store_path.exists():
             try:
                 # Check if it's a directory before removing
                 if self.vector_store_path.is_dir():
                     shutil.rmtree(self.vector_store_path)
                     app_logger.info(f"Removed temporary vector store at {self.vector_store_path}")
                 elif self.vector_store_path.is_file():
                    # FAISS can also save as a single file with .faiss extension
                    self.vector_store_path.unlink()
                    app_logger.info(f"Removed temporary vector store file at {self.vector_store_path}")

             except Exception as e:
                 app_logger.error(f"Error removing vector store at {self.vector_store_path}: {e}")
        self.vector_store = None
        self.vector_store_path = None

    def get_history(self) -> List[BaseMessage]:
        """Get the conversation history"""
        memory_variables = self.memory.load_memory_variables({})
        return memory_variables.get("history", [])

    def clear_history(self) -> None:
        """Clear the conversation history"""
        self.memory.clear()



if __name__ == "__main__":
    # Example usage
    # Uncomment to test writing a new config
    """
    sample_config = {
        "mcpServers": {
            "fetch": {
                "command": "uvx",
                "args": ["mcp-server-fetch"]
            }
        }
    }
    
    if write_ollama_config(sample_config):
        print("Successfully wrote configuration file.")
    else:
        print("Failed to write configuration file.")
    """
    
    # Read the configuration
    config = read_ollama_config()
    
    # Display the configuration if available
    if config:
        print("Ollama Desktop Configuration:")
        print(json.dumps(config, indent=2))
    else:
        print("Failed to read configuration file.")