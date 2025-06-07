import os
import json
import platform
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

class MCPServersConfig:
    """
    A comprehensive configuration manager for Ollama desktop configuration
    with support for MCP tools management.
    """
    
    def __init__(self):
        """Initialize the ConfigManager with platform-specific paths."""
        self.system = platform.system()
        self._config_path = None
        self._config_dir = None
        self._setup_paths()
    
    def _setup_paths(self):
        """Set up configuration paths based on the operating system."""
        if self.system == "Darwin":  # macOS
            self._config_dir = os.path.expanduser("~/Library/Application Support/ollama_desktop")
            self._config_path = os.path.join(self._config_dir, "ollama_desktop_config.json")
        elif self.system == "Windows":
            self._config_dir = os.path.join(os.environ.get("APPDATA"), "ollama_desktop")
            self._config_path = os.path.join(self._config_dir, "ollama_desktop_config.json")
        else:  # Linux or other
            # For Linux, use XDG config directory
            xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            self._config_dir = os.path.join(xdg_config, "ollama_desktop")
            self._config_path = os.path.join(self._config_dir, "ollama_desktop_config.json")
    
    @property
    def config_path(self) -> str:
        """Get the configuration file path."""
        return self._config_path
    
    @property
    def config_dir(self) -> str:
        """Get the configuration directory path."""
        return self._config_dir
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration structure."""
        return {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"],
                    "active": True,
                    "type": "stdio"
                }
            },
            "tools": {},
            "settings": {
                "version": "1.0.0",
                "created_at": "",
                "last_modified": ""
            }
        }
    
    def _ensure_config_directory(self) -> bool:
        """Ensure the configuration directory exists."""
        if not os.path.exists(self._config_dir):
            try:
                os.makedirs(self._config_dir, exist_ok=True)
                return True
            except Exception as e:
                print(f"Error creating directory {self._config_dir}: {e}")
                return False
        return True
    
    def read_config(self) -> Optional[Dict[str, Any]]:
        """
        Read the ollama_desktop_config.json file from the appropriate location
        based on the operating system.
        
        Returns:
            dict: The contents of the config file as a dictionary, or None if error
        """
        # Check if the file exists
        if not os.path.exists(self._config_path):
            print(f"Config file not found at: {self._config_path}")
            # Create a default configuration file
            default_config = self._get_default_config()
            
            # Create directory if it doesn't exist
            if not self._ensure_config_directory():
                return None
            
            # Write the default configuration
            if self.write_config(default_config):
                print(f"Created default configuration file at: {self._config_path}")
                return default_config
            else:
                return None
        
        # Read and parse the JSON file
        try:
            with open(self._config_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
            return config_data
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in config file: {e}")
            return None
        except Exception as e:
            print(f"Error reading config file: {e}")
            return None
    
    def write_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Write data to the ollama_desktop_config.json file. Creates the file and directories
        if they don't exist.
        
        Args:
            config_data (dict): The configuration data to write to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create directory if it doesn't exist
        if not self._ensure_config_directory():
            return False
        
        # Add timestamp for last modification
        if "settings" not in config_data:
            config_data["settings"] = {}
        
        from datetime import datetime
        config_data["settings"]["last_modified"] = datetime.now().isoformat()
        
        # Write the JSON file
        try:
            with open(self._config_path, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error writing config file: {e}")
            return False
    
    def get_mcp_servers(self) -> Dict[str, Any]:
        """
        Get all MCP servers from the configuration.
        
        Returns:
            dict: Dictionary of MCP servers
        """
        config = self.read_config()
        if config is None:
            return {}
        return config.get("mcpServers", {})
    
    def add_mcp_server(self, name: str, server_config: Dict[str, Any]) -> bool:
        """
        Add a new MCP server to the configuration.
        
        Args:
            name: Name of the MCP server
            server_config: Configuration for the server
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None:
            config = self._get_default_config()
        
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Set default active status if not provided
        if "active" not in server_config:
            server_config["active"] = True
        
        config["mcpServers"][name] = server_config
        return self.write_config(config)
    
    def remove_mcp_server(self, name: str) -> bool:
        """
        Remove an MCP server from the configuration.
        
        Args:
            name: Name of the MCP server to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "mcpServers" not in config:
            return False
        
        if name in config["mcpServers"]:
            del config["mcpServers"][name]
            return self.write_config(config)
        
        return False
    
    def activate_mcp_server(self, name: str) -> bool:
        """
        Activate an MCP server.
        
        Args:
            name: Name of the MCP server to activate
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "mcpServers" not in config or name not in config["mcpServers"]:
            return False
        
        config["mcpServers"][name]["active"] = True
        return self.write_config(config)
    
    def deactivate_mcp_server(self, name: str) -> bool:
        """
        Deactivate an MCP server.
        
        Args:
            name: Name of the MCP server to deactivate
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "mcpServers" not in config or name not in config["mcpServers"]:
            return False
        
        config["mcpServers"][name]["active"] = False
        return self.write_config(config)
    
    def get_active_mcp_servers(self) -> Dict[str, Any]:
        """
        Get all active MCP servers.
        
        Returns:
            dict: Dictionary of active MCP servers
        """
        servers = self.get_mcp_servers()
        return {name: config for name, config in servers.items() 
                if config.get("active", True)}
    
    def add_tool(self, name: str, tool_config: Dict[str, Any]) -> bool:
        """
        Add a new tool to the configuration.
        
        Args:
            name: Name of the tool
            tool_config: Configuration for the tool
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None:
            config = self._get_default_config()
        
        if "tools" not in config:
            config["tools"] = {}
        
        # Set default active status if not provided
        if "active" not in tool_config:
            tool_config["active"] = True
        
        # Add timestamp
        from datetime import datetime
        tool_config["added_at"] = datetime.now().isoformat()
        
        config["tools"][name] = tool_config
        return self.write_config(config)
    
    def delete_tool(self, name: str) -> bool:
        """
        Delete a tool from the configuration.
        
        Args:
            name: Name of the tool to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "tools" not in config:
            return False
        
        if name in config["tools"]:
            del config["tools"][name]
            return self.write_config(config)
        
        return False
    
    def activate_tool(self, name: str) -> bool:
        """
        Activate a tool.
        
        Args:
            name: Name of the tool to activate
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "tools" not in config or name not in config["tools"]:
            return False
        
        config["tools"][name]["active"] = True
        return self.write_config(config)
    
    def deactivate_tool(self, name: str) -> bool:
        """
        Deactivate a tool.
        
        Args:
            name: Name of the tool to deactivate
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "tools" not in config or name not in config["tools"]:
            return False
        
        config["tools"][name]["active"] = False
        return self.write_config(config)
    
    def get_active_tools(self) -> Dict[str, Any]:
        """
        Get all active tools.
        
        Returns:
            dict: Dictionary of active tools
        """
        tools = self.get_all_tools()
        return {name: config for name, config in tools.items() 
                if config.get("active", True)}
    
    def update_tool(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing tool configuration.
        
        Args:
            name: Name of the tool to update
            updates: Dictionary of updates to apply
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "tools" not in config or name not in config["tools"]:
            return False
        
        # Update the tool configuration
        config["tools"][name].update(updates)
        
        # Add update timestamp
        from datetime import datetime
        config["tools"][name]["updated_at"] = datetime.now().isoformat()
        
        return self.write_config(config)
    
    def update_mcp_server(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing MCP server configuration.
        
        Args:
            name: Name of the MCP server to update
            updates: Dictionary of updates to apply
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = self.read_config()
        if config is None or "mcpServers" not in config or name not in config["mcpServers"]:
            return False
        
        # Update the server configuration
        config["mcpServers"][name].update(updates)
        
        # Add update timestamp
        from datetime import datetime
        config["mcpServers"][name]["updated_at"] = datetime.now().isoformat()
        
        return self.write_config(config)
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool configuration.
        
        Args:
            name: Name of the tool
            
        Returns:
            dict: Tool configuration or None if not found
        """
        tools = self.get_all_tools()
        return tools.get(name)
    
    def get_mcp_server(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific MCP server configuration.
        
        Args:
            name: Name of the MCP server
            
        Returns:
            dict: Server configuration or None if not found
        """
        servers = self.get_mcp_servers()
        return servers.get(name)
    
    def reset_to_default(self) -> bool:
        """
        Reset the configuration to default values.
        
        Returns:
            bool: True if successful, False otherwise
        """
        default_config = self._get_default_config()
        from datetime import datetime
        default_config["settings"]["created_at"] = datetime.now().isoformat()
        return self.write_config(default_config)
    
    def backup_config(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            str: Path to the backup file
        """
        config = self.read_config()
        if config is None:
            raise ValueError("No configuration to backup")
        
        if backup_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self._config_dir, f"ollama_desktop_config_backup_{timestamp}.json")
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=2, ensure_ascii=False)
            return backup_path
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    def restore_config(self, backup_path: str) -> bool:
        """
        Restore configuration from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            return self.write_config(config)
        except Exception as e:
            print(f"Failed to restore configuration: {e}")
            return False 