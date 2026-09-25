from socket import *
import os
import hashlib
import uuid
from urllib.parse import parse_qs, unquote_plus

HOST = ""
PORT = 8099
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sessions = {}

def guess_content_type(path):
    p = path.lower()
    if p.endswith(".html"):
        return "text/html; charset=utf-8"
    if p.endswith(".css"):
        return "text/css"
    if p.endswith(".png"):
        return "image/png"
    if p.endswith(".jpg") or p.endswith(".jpeg"):
        return "image/jpeg"
    return "application/octet-stream"

def send_response(conn, status, headers, body):
    headers = headers + [f"Content-Length: {len(body)}", "Connection: close"]
    resp = f"HTTP/1.1 {status}\r\n" + "\r\n".join(headers) + "\r\n\r\n"
    conn.sendall(resp.encode() + body)

def redirect_307(conn, location):
    send_response(conn, "307 Temporary Redirect", [f"Location: {location}"], b"")

def read_http_request(conn):
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk

    text = data.decode(errors="ignore")
    lines = text.split("\r\n")
    if not lines or not lines[0].strip():
        return "", "", "", {}, b""

    parts = lines[0].strip().split()
    if len(parts) != 3:
        return "", "", "", {}, b""

    method, path, version = parts

    headers = {}
    i = 1
    while i < len(lines) and lines[i]:
        if ":" in lines[i]:
            k, v = lines[i].split(":", 1)
            headers[k.lower().strip()] = v.strip()
        i += 1

    body = b""
    if "content-length" in headers:
        try:
            length = int(headers["content-length"])
        except ValueError:
            length = 0
        body = data.split(b"\r\n\r\n", 1)[1]
        while len(body) < length:
            chunk = conn.recv(4096)
            if not chunk:
                break
            body += chunk
        body = body[:length]

    return method, path, version, headers, body

def parse_form(body):
    s = unquote_plus(body.decode(errors="ignore"))
    return {k: v[0] for k, v in parse_qs(s).items()}

def parse_cookie(headers):
    out = {}
    raw = headers.get("cookie", "")
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out

def html_404(addr):
    return f"""
<html>
<head><title>Error 404</title></head>
<body>
<h1 style="color:red">The file is not found</h1>
<b>Ibrahim Irshaid 1231870</b><br>
<b>Kareem AbuZaitoun</b><br>
Client IP: {addr[0]}<br>
Client Port: {addr[1]}
</body>
</html>
""".encode()

def load_static(conn, addr, path):
    filename = path.split("?", 1)[0].lstrip("/")
    filename = os.path.normpath(filename).replace("\\", "/")
    if filename.startswith(".."):
        send_response(conn, "404 Not Found", ["Content-Type: text/html; charset=utf-8"], html_404(addr))
        return

    full = os.path.join(BASE_DIR, filename)
    if not os.path.isfile(full):
        send_response(conn, "404 Not Found", ["Content-Type: text/html; charset=utf-8"], html_404(addr))
        return

    with open(full, "rb") as f:
        body = f.read()

    send_response(conn, "200 OK", [f"Content-Type: {guess_content_type(filename)}"], body)

def register_user(username, password):
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        return False, "empty"

    db = os.path.join(BASE_DIR, "data.txt")
    if os.path.exists(db):
        with open(db, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                u, _ = line.split(":", 1)
                if u == username:
                    return False, "exists"

    hashed = hashlib.sha256(password.encode()).hexdigest()
    with open(db, "a", encoding="utf-8") as f:
        f.write(f"{username}:{hashed}\n")
    return True, "ok"

def check_user(username, password):
    username = (username or "").strip()
    password = password or ""
    db = os.path.join(BASE_DIR, "data.txt")
    if not os.path.exists(db):
        return False

    hashed = hashlib.sha256(password.encode()).hexdigest()
    with open(db, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            u, h = line.split(":", 1)
            if u == username and h == hashed:
                return True
    return False

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind((HOST, PORT))
serverSocket.listen(5)

print(f"Server running on port {PORT}")

while True:
    conn, addr = serverSocket.accept()
    try:
        method, path, version, headers, body = read_http_request(conn)
        print("HTTP REQUEST:", method, path, version)

        if not method:
            conn.close()
            continue

        if path == "/chat":
            redirect_307(conn, "https://chatgpt.com")
            continue
        if path == "/cf":
            redirect_307(conn, "https://www.cloudflare.com/")
            continue
        if path == "/rt":
            redirect_307(conn, "https://ritaj.birzeit.edu")
            continue

        if path in ["/", "/en", "/index.html"]:
            path = "/main_en.html"
        elif path == "/ar":
            path = "/main_ar.html"

        if path == "/register.html" and method.upper() == "POST":
            form = parse_form(body)
            username = form.get("username", "")
            password = form.get("password", "")
            ok, reason = register_user(username, password)
            if ok:
                send_response(conn, "200 OK", ["Content-Type: text/html; charset=utf-8"],
                              b"<h2>Registered successfully</h2><a href='/login.html'>Go to login</a>")
            else:
                if reason == "exists":
                    send_response(conn, "409 Conflict", ["Content-Type: text/html; charset=utf-8"],
                                  b"<h2>Username already exists</h2><a href='/register.html'>Try another username</a>")
                else:
                    send_response(conn, "400 Bad Request", ["Content-Type: text/html; charset=utf-8"],
                                  b"<h2>Username and password cannot be empty</h2><a href='/register.html'>Back</a>")
            continue

        if path == "/login.html" and method.upper() == "POST":
            form = parse_form(body)
            username = form.get("username", "")
            password = form.get("password", "")
            if check_user(username, password):
                sid = str(uuid.uuid4())
                sessions[sid] = username
                with open(os.path.join(BASE_DIR, "protected.html"), "rb") as f:
                    page = f.read()
                send_response(conn, "200 OK",
                              ["Content-Type: text/html; charset=utf-8",
                               f"Set-Cookie: sessionid={sid}; Path=/"],
                              page)
            else:
                send_response(conn, "401 Unauthorized",
                              ["Content-Type: text/html; charset=utf-8"],
                              b"<h2>Login failed</h2><a href='/login.html'>Try again</a>")
            continue

        if path == "/logout":
            cookies = parse_cookie(headers)
            sid = cookies.get("sessionid", "")
            if sid in sessions:
                del sessions[sid]
            send_response(conn, "200 OK", ["Content-Type: text/html; charset=utf-8"],
                          b"<h2>Logged out</h2><a href='/login.html'>Login again</a>")
            continue

        if path == "/protected.html":
            cookies = parse_cookie(headers)
            sid = cookies.get("sessionid", "")
            if sid in sessions:
                load_static(conn, addr, "/protected.html")
            else:
                redirect_307(conn, "/login.html")
            continue

        load_static(conn, addr, path)

    except Exception as e:
        send_response(conn, "500 Internal Server Error",
                      ["Content-Type: text/html; charset=utf-8"],
                      f"<pre>{e}</pre>".encode())
    finally:
        conn.close()
