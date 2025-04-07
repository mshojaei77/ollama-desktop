# Agent Icons

This directory contains the icons for all agents in the Ollama Desktop application.

## Naming Convention

Icon files should be named according to the following convention:

1. Use the agent's ID as the filename
2. Use PNG format (.png extension)

For example, if your agent has the ID "my-custom-agent", the icon file should be named:
```
my-custom-agent.png
```

## Icon Requirements

- Recommended size: 256x256 pixels (square)
- Format: PNG with transparency
- File size: Keep under 500KB for optimal performance

## Automatic Icon Loading

The application will automatically look for an icon file with the agent's ID in this directory. If found, it will use that icon instead of any URL specified in the agent's configuration.

If no matching icon is found, the application will fall back to:
1. The icon URL specified in the agent configuration
2. A default placeholder icon

## Adding New Icons

To add a new icon:
1. Create or obtain a PNG file for your agent
2. Name it according to the agent's ID (e.g., "my-agent-id.png")
3. Place it in this directory
4. The application will automatically detect and use the icon the next time it loads 