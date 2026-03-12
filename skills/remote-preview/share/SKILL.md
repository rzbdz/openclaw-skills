---
name: remote-preview
description: Deploy a local file preview server listening on 0.0.0.0:8964. Supports directory tree navigation, syntax-highlighted code/text preview, and XLSX file viewing. Use when you need to share files with Junzhong for remote browser preview via http://panjunzhong.dc.com:8964. Copy files to the share/ directory and provide clickable links.
---

# Remote Preview Server

Deploy a web-based file preview server for remote file browsing and viewing.

## Quick Start

1. **Start the server** (runs in background):
   ```bash
   python3 /root/.openclaw/workspace/skills/remote-preview/scripts/server.py
   ```

2. **Copy files to share**:
   ```bash
   cp /path/to/file /root/.openclaw/workspace/skills/remote-preview/share/
   ```

3. **Generate preview link**:
   ```
   http://panjunzhong.dc.com:8964/share/filename
   ```

## Features

- **Directory tree navigation** - Browse folder structure
- **Text/code preview** - Syntax highlighting for code files
- **XLSX preview** - View Excel files in table format
- **Direct file access** - Download any file from share/

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

When Junzhong asks to preview a file:

1. Copy file to `share/` directory
2. Generate link: `http://panjunzhong.dc.com:8964/share/<filename>`
3. Send link via Feishu using message tool with clickable format

The server auto-detects file types and renders appropriately.

## Sending Clickable Links to Feishu

Use the message tool to send clickable links:
```
message action=send channel=feishu message="[Click to preview](http://panjunzhong.dc.com:8964/share/filename)"
```

Or send as a formatted card with the link embedded.
