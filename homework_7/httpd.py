"""Module for simple http server"""
import argparse
import os
import socket
import multiprocessing
import urllib.parse
import mimetypes
from datetime import datetime

CRLF = "\r\n"

def parse_args():
    """Parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", dest="root", type=str, default='src', help="Document root")
    parser.add_argument("-w", dest="workers", type=int, default=4, help="Number of workers")
    parser.add_argument("-p", dest="port", type=int, default=80, help="Port to bind")
    return parser.parse_args()

def start_worker(server_socket, document_root):
    """Starts worker"""
    while True:
        client_socket, _ = server_socket.accept()
        handle_client(client_socket, document_root)

def handle_client(client_socket, document_root):
    """Handle request"""
    try:
        request = client_socket.recv(4096).decode('utf-8', errors='ignore')
        if not request:
            client_socket.close()
            return

        lines = request.splitlines()
        if not lines:
            client_socket.close()
            return

        request_line = lines[0]
        parts = request_line.split()
        if len(parts) < 3:
            send_response(client_socket, 400, "Bad Request")
            return

        method, raw_path, _ = parts
        path = urllib.parse.unquote(raw_path.split("?")[0])

        if not path.startswith("/"):
            send_response(client_socket, 400, "Bad Request")
            return

        fs_path = os.path.normpath(os.path.join(document_root, path.lstrip("/")))

        if not fs_path.startswith(os.path.abspath(document_root)):
            send_response(client_socket, 403, "Forbidden")
            return

        if raw_path.endswith("/") and not os.path.isdir(fs_path):
            send_response(client_socket, 404, "Not Found")
            return

        if os.path.isdir(fs_path):
            fs_path = os.path.join(fs_path, "index.html")

        if not os.path.exists(fs_path):
            send_response(client_socket, 404, "Not Found")
            return


        if method not in ["GET", "HEAD"]:
            send_response(client_socket, 405, "Method Not Allowed")
            return

        with open(fs_path, "rb") as f:
            content = f.read()

        send_response(client_socket, 200, "OK", content, fs_path, head_only=(method == "HEAD"))
    finally:
        client_socket.close()

def send_response(client_socket, code, status, body=b"", fs_path=None, head_only=False):
    """Send response formatted for http"""
    headers = [
        f"HTTP/1.1 {code} {status}",
        f"Date: {http_date()}",
        "Server: httpd/0.1",
        f"Content-Length: {len(body)}",
        f"Content-Type: {get_mime_type(fs_path)}" if fs_path else "Content-Type: text/plain",
        "Connection: close",
        ""
    ]
    response_headers = CRLF.join(headers) + CRLF

    if head_only:
        client_socket.sendall(response_headers.encode())
    else:
        client_socket.sendall(response_headers.encode() + body)

def get_mime_type(path):
    """Mime-type of files for http"""
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"

def http_date():
    """Date formatted"""
    return datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

def main():
    """Main execution"""
    args = parse_args()
    document_root = os.path.abspath(args.root)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    server_socket.bind(('0.0.0.0', args.port))
    server_socket.listen(128)

    workers = []
    for _ in range(args.workers):
        p = multiprocessing.Process(target=start_worker, args=(server_socket, document_root))
        p.start()
        workers.append(p)

    print("Server started")

    for p in workers:
        p.join()

if __name__ == "__main__":
    main()
