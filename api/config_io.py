import json
import os
import platform

def read_ollama_config():
    """
    Read the ollama_desktop_config.json file from the appropriate location
    based on the operating system.
    
    Returns:
        dict: The contents of the config file as a dictionary
    """
    # Determine the operating system
    system = platform.system()
    
    # Set the path based on the operating system
    if system == "Darwin":  # macOS
        config_path = os.path.expanduser("~/Library/Application Support/ollama_desktop/ollama_desktop_config.json")
        config_dir = os.path.expanduser("~/Library/Application Support/ollama_desktop")
    elif system == "Windows":
        config_path = os.path.join(os.environ.get("APPDATA"), "ollama_desktop", "ollama_desktop_config.json")
        config_dir = os.path.join(os.environ.get("APPDATA"), "ollama_desktop")
    else:  # Linux or other
        print(f"Unsupported operating system: {system}")
        return None
    
    # Check if the file exists
    if not os.path.exists(config_path):
        print(f"Config file not found at: {config_path}")
        # Create a default configuration file
        default_config = {
            "settings": {
                "defaultModel": "llama3.2",
                "theme": "system"
            },
            "systemPrompts": {
                "default": {
                    "name": "Default Assistant",
                    "description": "A helpful AI assistant",
                    "instructions": [
                        "You are a helpful AI assistant.",
                        "Always be friendly and informative.",
                        "Provide clear and accurate responses.",
                        "If you're unsure about something, say so."
                    ],
                    "additional_context": "",
                    "expected_output": "",
                    "markdown": True,
                    "add_datetime_to_instructions": False
                },
                "creative": {
                    "name": "Creative Writer",
                    "description": "A creative writing assistant focused on storytelling and artistic expression",
                    "instructions": [
                        "You are a creative writing assistant.",
                        "Help users with storytelling, poetry, and creative content.",
                        "Be imaginative and inspiring in your responses.",
                        "Encourage creativity and provide constructive feedback."
                    ],
                    "additional_context": "",
                    "expected_output": "",
                    "markdown": True,
                    "add_datetime_to_instructions": False
                },
                "technical": {
                    "name": "Technical Expert",
                    "description": "A technical assistant specialized in programming and technology",
                    "instructions": [
                        "You are a technical expert and programming assistant.",
                        "Provide accurate, detailed technical information.",
                        "Include code examples when helpful.",
                        "Explain complex concepts clearly.",
                        "Follow best practices and current standards."
                    ],
                    "additional_context": "",
                    "expected_output": "",
                    "markdown": True,
                    "add_datetime_to_instructions": False
                }
            },
            "activeSystemPrompt": "default"
        }
        
        # Create directory if it doesn't exist
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
            except Exception as e:
                print(f"Error creating directory: {e}")
                return None
        
        # Write the default configuration
        try:
            with open(config_path, 'w') as file:
                json.dump(default_config, file, indent=2)
            print(f"Created default configuration file at: {config_path}")
            return default_config
        except Exception as e:
            print(f"Error creating default config file: {e}")
            return None
    
    # Read and parse the JSON file
    try:
        with open(config_path, 'r') as file:
            config_data = json.load(file)
        
        # Ensure backward compatibility and add missing sections
        if "systemPrompts" not in config_data:
            config_data["systemPrompts"] = {
                "default": {
                    "name": "Default Assistant",
                    "description": "A helpful AI assistant",
                    "instructions": [
                        "You are a helpful AI assistant.",
                        "Always be friendly and informative.",
                        "Provide clear and accurate responses.",
                        "If you're unsure about something, say so."
                    ],
                    "additional_context": "",
                    "expected_output": "",
                    "markdown": True,
                    "add_datetime_to_instructions": False
                }
            }
        
        if "activeSystemPrompt" not in config_data:
            config_data["activeSystemPrompt"] = "default"
        
        # Save the updated config
        write_ollama_config(config_data)
        
        return config_data
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in config file")
        return None
    except Exception as e:
        print(f"Error reading config file: {e}")
        return None

def write_ollama_config(config_data):
    """
    Write data to the ollama_desktop_config.json file. Creates the file and directories
    if they don't exist.
    
    Args:
        config_data (dict): The configuration data to write to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Determine the operating system
    system = platform.system()
    
    # Set the path based on the operating system
    if system == "Darwin":  # macOS
        config_path = os.path.expanduser("~/Library/Application Support/ollama_desktop/ollama_desktop_config.json")
        config_dir = os.path.expanduser("~/Library/Application Support/ollama_desktop")
    elif system == "Windows":
        config_path = os.path.join(os.environ.get("APPDATA"), "ollama_desktop", "ollama_desktop_config.json")
        config_dir = os.path.join(os.environ.get("APPDATA"), "ollama_desktop")
    else:  # Linux or other
        print(f"Unsupported operating system: {system}")
        return False
    
    # Create directory if it doesn't exist
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    
    # Write the JSON file
    try:
        with open(config_path, 'w') as file:
            json.dump(config_data, file, indent=2)
        return True
    except Exception as e:
        print(f"Error writing config file: {e}")
        return False

def get_active_system_prompt():
    """
    Get the active system prompt configuration.
    
    Returns:
        dict: The active system prompt configuration or None if not found
    """
    config = read_ollama_config()
    if not config:
        return None
    
    active_prompt_id = config.get("activeSystemPrompt", "default")
    system_prompts = config.get("systemPrompts", {})
    
    return system_prompts.get(active_prompt_id)

def set_active_system_prompt(prompt_id):
    """
    Set the active system prompt.
    
    Args:
        prompt_id (str): The ID of the system prompt to activate
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = read_ollama_config()
    if not config:
        return False
    
    # Check if the prompt exists
    if prompt_id not in config.get("systemPrompts", {}):
        print(f"System prompt '{prompt_id}' not found")
        return False
    
    config["activeSystemPrompt"] = prompt_id
    return write_ollama_config(config)

def save_system_prompt(prompt_id, prompt_config):
    """
    Save a system prompt configuration.
    
    Args:
        prompt_id (str): The ID for the system prompt
        prompt_config (dict): The prompt configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = read_ollama_config()
    if not config:
        return False
    
    if "systemPrompts" not in config:
        config["systemPrompts"] = {}
    
    config["systemPrompts"][prompt_id] = prompt_config
    return write_ollama_config(config)

def delete_system_prompt(prompt_id):
    """
    Delete a system prompt configuration.
    
    Args:
        prompt_id (str): The ID of the system prompt to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = read_ollama_config()
    if not config:
        return False
    
    # Don't allow deletion of the default prompt
    if prompt_id == "default":
        print("Cannot delete the default system prompt")
        return False
    
    system_prompts = config.get("systemPrompts", {})
    if prompt_id not in system_prompts:
        print(f"System prompt '{prompt_id}' not found")
        return False
    
    del system_prompts[prompt_id]
    
    # If the deleted prompt was active, switch to default
    if config.get("activeSystemPrompt") == prompt_id:
        config["activeSystemPrompt"] = "default"
    
    return write_ollama_config(config)

def get_all_system_prompts():
    """
    Get all system prompt configurations.
    
    Returns:
        dict: All system prompt configurations or empty dict if not found
    """
    config = read_ollama_config()
    if not config:
        return {}
    
    return config.get("systemPrompts", {})

if __name__ == "__main__":
    # Example usage
    # Read the configuration
    config = read_ollama_config()
    
    # Display the configuration if available
    if config:
        print("Ollama Desktop Configuration:")
        print(json.dumps(config, indent=2))
        
        # Test system prompt functions
        print("\nActive system prompt:")
        active_prompt = get_active_system_prompt()
        if active_prompt:
            print(json.dumps(active_prompt, indent=2))
    else:
        print("Failed to read configuration file.")