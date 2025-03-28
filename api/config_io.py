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
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                }
            }
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