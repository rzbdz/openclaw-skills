#!/usr/bin/env python3
import os
import sys
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote, urlparse
import logging

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
        text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.md', '.sh', '.yaml', '.yml', '.xml', '.log'}
        return file_path.suffix.lower() in text_extensions or file_path.name.startswith('.')
    
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
