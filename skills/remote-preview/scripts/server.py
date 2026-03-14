#!/usr/bin/env python3
import os
import sys
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote, urlparse, parse_qs
import logging
import re
import html as html_module

# Setup logging
logging.basicConfig(
    filename='/tmp/remote-preview.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Use relative path from script location for portability
SCRIPT_DIR = Path(__file__).parent.parent
SHARE_DIR = SCRIPT_DIR / 'share'
SHARE_DIR.mkdir(parents=True, exist_ok=True)

class PreviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = unquote(parsed_path.path)
        
        # Root - show directory tree
        if path == '/' or path == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_index_html().encode())
            return
        
        # Share directory access
        if path == '/share/' or path.startswith('/share/'):
            rel_path = path[7:].rstrip('/')  # Remove '/share/' and trailing slash
            file_path = SHARE_DIR / rel_path if rel_path else SHARE_DIR
            
            if not file_path.exists():
                self.send_error(404)
                return
            
            if file_path.is_dir():
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(self.get_dir_view_html(file_path, rel_path).encode())
                return
            
            # File preview
            if file_path.suffix.lower() == '.pdf':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(self.get_pdf_preview(file_path).encode())
                return
            
            if file_path.suffix.lower() == '.xlsx':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(self.get_xlsx_preview(file_path).encode())
                return
            
            # Markdown files
            if file_path.suffix.lower() == '.md':
                mode = parse_qs(parsed_path.query).get('mode', ['preview'])[0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(self.get_markdown_preview(file_path, mode).encode())
                return
            
            # Text/code files
            if self.is_text_file(file_path):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(self.get_code_preview(file_path).encode())
                return
            
            # Binary - download
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{file_path.name}"')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
            return
        
        self.send_error(404)
    
    def get_index_html(self):
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Remote Preview</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f5f5f5; }
        .container { display: flex; height: 100vh; }
        .sidebar { width: 300px; background: #fff; border-right: 1px solid #ddd; overflow-y: auto; }
        .content { flex: 1; padding: 20px; overflow-y: auto; }
        .header { padding: 15px; border-bottom: 1px solid #ddd; background: #fff; }
        .header h1 { margin: 0; font-size: 18px; }
        .tree { padding: 10px; }
        .tree-item { margin: 2px 0; }
        .tree-item a { display: block; padding: 8px 12px; color: #0066cc; text-decoration: none; border-radius: 4px; }
        .tree-item a:hover { background: #f0f0f0; }
        .tree-item.folder a { font-weight: 500; }
        .tree-item.file a { padding-left: 24px; }
        .welcome { padding: 20px; background: #fff; border-radius: 8px; }
        .welcome h2 { margin-top: 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="header">
                <h1>📁 Files</h1>
            </div>
            <div class="tree" id="tree"></div>
        </div>
        <div class="content">
            <div class="welcome">
                <h2>Welcome to Remote Preview</h2>
                <p>Select a file from the left to preview it.</p>
                <p>Supported formats:</p>
                <ul>
                    <li>📄 Text files (.txt, .md, .log, etc.)</li>
                    <li>💻 Code files (.py, .js, .html, .css, etc.) with syntax highlighting</li>
                    <li>📊 Excel files (.xlsx)</li>
                </ul>
            </div>
        </div>
    </div>
    <script>
        function loadTree() {
            fetch('/share/')
                .then(r => r.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const items = doc.querySelectorAll('.item a');
                    const tree = document.getElementById('tree');
                    tree.innerHTML = '';
                    items.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'tree-item';
                        const link = item.cloneNode(true);
                        div.appendChild(link);
                        tree.appendChild(div);
                    });
                });
        }
        loadTree();
    </script>
</body>
</html>'''
    
    def get_dir_view_html(self, dir_path, rel_path):
        items = []
        try:
            for item in sorted(dir_path.iterdir()):
                if rel_path:
                    rel = f"{rel_path}/{item.name}"
                else:
                    rel = item.name
                items.append({
                    'name': item.name,
                    'type': 'dir' if item.is_dir() else 'file',
                    'path': rel
                })
        except PermissionError:
            pass
        
        items_html = ''
        for item in items:
            icon = '📁' if item['type'] == 'dir' else '📄'
            items_html += f'<div class="item"><a href="/share/{item["path"]}">{icon} {item["name"]}</a></div>'
        
        back_link = '<a href="/share/">← Back to root</a>' if rel_path else ''
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Directory: {rel_path or 'share'}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 20px; }}
        .header {{ margin-bottom: 20px; }}
        .back {{ margin-bottom: 15px; }}
        .back a {{ padding: 8px 12px; background: #f0f0f0; border-radius: 4px; text-decoration: none; color: #0066cc; }}
        .back a:hover {{ background: #e0e0e0; }}
        .item {{ margin: 8px 0; }}
        .item a {{ display: inline-block; padding: 8px 12px; background: #f0f0f0; border-radius: 4px; text-decoration: none; color: #0066cc; }}
        .item a:hover {{ background: #e0e0e0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📁 {rel_path or 'share'}</h1>
    </div>
    {f'<div class="back">{back_link}</div>' if back_link else ''}
    <div class="items">
        {items_html if items_html else '<p>Empty directory</p>'}
    </div>
</body>
</html>'''
    
    def is_text_file(self, file_path):
        text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.sh', '.yaml', '.yml', '.xml', '.log'}
        return file_path.suffix.lower() in text_extensions or file_path.name.startswith('.')
    
    def get_markdown_preview(self, file_path, mode='preview'):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            content = '[Unable to read file]'
        
        if mode == 'source':
            # Source mode - show raw markdown
            return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{file_path.name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <style>
        body {{ font-family: monospace; margin: 0; background: #282c34; color: #abb2bf; }}
        .header {{ padding: 15px; background: #21252b; border-bottom: 1px solid #3e4451; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ margin: 0; font-size: 16px; }}
        .mode-toggle {{ display: flex; gap: 10px; }}
        .mode-toggle a {{ padding: 6px 12px; background: #3e4451; color: #abb2bf; text-decoration: none; border-radius: 4px; cursor: pointer; }}
        .mode-toggle a.active {{ background: #61afef; color: #282c34; }}
        pre {{ margin: 0; padding: 15px; overflow-x: auto; }}
        code {{ font-family: 'Monaco', 'Menlo', monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 {file_path.name}</h1>
        <div class="mode-toggle">
            <a href="?mode=preview">Preview</a>
            <a href="?mode=source" class="active">Source</a>
        </div>
    </div>
    <pre><code class="language-markdown">{html_module.escape(content)}</code></pre>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>'''
        else:
            # Preview mode - simple markdown to HTML conversion
            html_content = self.simple_markdown_to_html(content)
            
            return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{file_path.name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f5f5f5; }}
        .header {{ padding: 15px 20px; background: #fff; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ margin: 0; font-size: 18px; }}
        .mode-toggle {{ display: flex; gap: 10px; }}
        .mode-toggle a {{ padding: 6px 12px; background: #f0f0f0; color: #0066cc; text-decoration: none; border-radius: 4px; }}
        .mode-toggle a.active {{ background: #0066cc; color: #fff; }}
        .mode-toggle a:hover {{ background: #e0e0e0; }}
        .mode-toggle a.active:hover {{ background: #0052a3; }}
        .content {{ max-width: 900px; margin: 20px auto; padding: 20px; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .content h1, .content h2, .content h3 {{ margin-top: 24px; margin-bottom: 12px; }}
        .content h1 {{ font-size: 28px; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; }}
        .content h2 {{ font-size: 24px; }}
        .content h3 {{ font-size: 20px; }}
        .content p {{ line-height: 1.6; margin: 12px 0; }}
        .content code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
        .content pre {{ background: #282c34; color: #abb2bf; padding: 12px; border-radius: 4px; overflow-x: auto; }}
        .content pre code {{ background: none; padding: 0; }}
        .content blockquote {{ border-left: 4px solid #ddd; margin: 12px 0; padding-left: 12px; color: #666; }}
        .content ul, .content ol {{ margin: 12px 0; padding-left: 24px; }}
        .content li {{ margin: 6px 0; }}
        .content table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
        .content th, .content td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .content th {{ background: #f5f5f5; }}
        .content a {{ color: #0066cc; text-decoration: none; }}
        .content a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 {file_path.name}</h1>
        <div class="mode-toggle">
            <a href="?mode=preview" class="active">Preview</a>
            <a href="?mode=source">Source</a>
        </div>
    </div>
    <div class="content">
        {html_content}
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>'''
    
    def simple_markdown_to_html(self, text):
        """Simple markdown to HTML converter without external dependencies"""
        lines = text.split('\n')
        html = []
        in_code_block = False
        code_block = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    code_content = '\n'.join(code_block)
                    html.append(f'<pre><code>{html_module.escape(code_content)}</code></pre>')
                    code_block = []
                    in_code_block = False
                else:
                    in_code_block = True
                i += 1
                continue
            
            if in_code_block:
                code_block.append(line)
                i += 1
                continue
            
            # Headers
            if line.startswith('# '):
                html.append(f'<h1>{html_module.escape(line[2:])}</h1>')
            elif line.startswith('## '):
                html.append(f'<h2>{html_module.escape(line[3:])}</h2>')
            elif line.startswith('### '):
                html.append(f'<h3>{html_module.escape(line[4:])}</h3>')
            # Blockquotes
            elif line.startswith('> '):
                html.append(f'<blockquote>{html_module.escape(line[2:])}</blockquote>')
            # Lists
            elif line.startswith('- ') or line.startswith('* '):
                html.append(f'<li>{self.process_inline_markdown(line[2:])}</li>')
            # Paragraphs
            elif line.strip():
                html.append(f'<p>{self.process_inline_markdown(line)}</p>')
            
            i += 1
        
        return '\n'.join(html)
    
    def process_inline_markdown(self, text):
        """Process inline markdown: bold, italic, links, code"""
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        # Links
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        return text
    
    def get_pdf_preview(self, file_path):
        """Generate HTML preview for PDF files"""
        try:
            import base64
            with open(file_path, 'rb') as f:
                pdf_data = base64.b64encode(f.read()).decode()
            
            return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{file_path.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f5f5f5; }}
        .header {{ padding: 15px; background: #fff; border-bottom: 1px solid #ddd; }}
        .header h1 {{ margin: 0; font-size: 18px; }}
        .viewer {{ width: 100%; height: calc(100vh - 60px); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 {file_path.name}</h1>
    </div>
    <iframe class="viewer" src="data:application/pdf;base64,{pdf_data}"></iframe>
</body>
</html>'''
        except Exception as e:
            return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Error</title>
</head>
<body>
    <h1>Error previewing PDF</h1>
    <p>{str(e)}</p>
    <p><a href="/share/">Back to files</a></p>
</body>
</html>'''
    
    def get_code_preview(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            content = '[Unable to read file]'
        
        ext = file_path.suffix.lower()
        lang = {'py': 'python', 'js': 'javascript', 'html': 'html', 'css': 'css', 'json': 'json', 'md': 'markdown', 'sh': 'bash', 'yaml': 'yaml', 'yml': 'yaml', 'xml': 'xml'}.get(ext[1:], 'plaintext')
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{file_path.name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <style>
        body {{ font-family: monospace; margin: 0; background: #282c34; color: #abb2bf; }}
        .header {{ padding: 15px; background: #21252b; border-bottom: 1px solid #3e4451; }}
        .header h1 {{ margin: 0; font-size: 16px; }}
        pre {{ margin: 0; padding: 15px; overflow-x: auto; }}
        code {{ font-family: 'Monaco', 'Menlo', monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 {file_path.name}</h1>
    </div>
    <pre><code class="language-{lang}">{content}</code></pre>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>'''
    
    def get_xlsx_preview(self, file_path):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            
            rows = []
            for row in ws.iter_rows(values_only=True):
                rows.append(row)
            
            html = '<table border="1" style="border-collapse: collapse; margin: 20px;"><tr>'
            if rows:
                for cell in rows[0]:
                    html += f'<th style="padding: 8px; background: #f0f0f0;">{cell}</th>'
                html += '</tr>'
                for row in rows[1:]:
                    html += '<tr>'
                    for cell in row:
                        html += f'<td style="padding: 8px;">{cell}</td>'
                    html += '</tr>'
            html += '</table>'
        except Exception as e:
            html = f'<p>Error reading XLSX: {e}</p>'
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{file_path.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>📊 {file_path.name}</h1>
    {html}
</body>
</html>'''
    
    def log_message(self, format, *args):
        logging.info(format % args)

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8964), PreviewHandler)
    logging.info('Remote Preview Server started on 0.0.0.0:8964')
    print('Remote Preview Server running on http://panjunzhong.dc.com:8964')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Server stopped')
        sys.exit(0)
