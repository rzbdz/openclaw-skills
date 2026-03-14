---
name: remote-preview
description: Deploy a local file preview server listening on 0.0.0.0:8964. Supports directory tree navigation, syntax-highlighted code/text preview, XLSX file viewing, and markdown rendering with preview/source modes. Use when you need to share files for remote browser preview via http://<YOUR_SERVER_IP>:8964. Includes systemd service for automatic startup and management. Copy files to the share/ directory and provide clickable links.
---

# Remote Preview Server

Deploy a web-based file preview server for remote file browsing and viewing.

## Configuration

Replace `<YOUR_SERVER_IP>` with your OpenClaw server's IP address throughout this guide.

## Quick Start

1. **Start the server** (runs in background):
   ```bash
   python3 /root/.openclaw/workspace/skills/remote-preview/scripts/server.py
   ```

2. **Copy files to share**:
   ```bash
   cp /path/to/file ~/.openclaw/share/
   ```

3. **Generate preview link**:
   ```
   http://<YOUR_SERVER_IP>:8964/share/filename
   ```

## Features

- **Directory tree navigation** - Browse folder structure
- **Text/code preview** - Syntax highlighting for code files
- **Markdown rendering** - Two modes:
  - **Preview mode**: Renders markdown as formatted HTML with styling
  - **Source mode**: Shows raw markdown code with syntax highlighting
  - Toggle between modes with buttons in the header
- **XLSX preview** - View Excel files in table format
- **Direct file access** - Download any file from share/

## Markdown Support

When viewing `.md` files, the server automatically detects them and provides:

- **Preview Mode** (default): Renders markdown to HTML with support for:
  - Headers (# ## ###)
  - Bold and italic text
  - Code blocks and inline code
  - Links and blockquotes
  - Lists and basic formatting

- **Source Mode**: Display raw markdown with syntax highlighting

Click the "Preview" or "Source" buttons in the file header to toggle between modes.

## Server Management

**Check if running**:
```bash
lsof -i :8964
```

**Stop server**:
```bash
pkill -f "server.py"
```

**View logs**:
```bash
tail -f /tmp/remote-preview.log
```

## Workflow

When sharing files for preview:

1. Copy file to `share/` directory
2. Generate link: `http://<YOUR_SERVER_IP>:8964/share/<filename>`
3. Send link via messaging tool with clickable format

The server auto-detects file types and renders appropriately.

## Sending Clickable Links

Use the message tool to send clickable links:
```
message action=send message="[Click to preview](http://<YOUR_SERVER_IP>:8964/share/filename)"
```

Or send as a formatted card with the link embedded.

