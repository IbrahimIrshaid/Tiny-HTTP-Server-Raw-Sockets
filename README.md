# Tiny HTTP Server from Raw Sockets

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![stdlib only](https://img.shields.io/badge/dependencies-stdlib%20only-2ea44f)

This is an HTTP/1.1 web server written directly on top of `socket`, with **no `http.server` and no framework**. It parses requests by hand, serves static files with the correct MIME types, and supports **user registration and login** with hashed passwords, **cookie-based sessions**, a protected page, **307 redirects** and custom error pages, in English and Arabic.

The repo also includes a small **TCP-control / UDP-data transfer test** that measures datagram loss and reordering.

## Web server — `webserver/`

```bash
cd webserver
python server.py          # → http://localhost:8099
```

| Route | Behaviour |
|---|---|
| `/`, `/en`, `/index.html` | English home page |
| `/ar` | Arabic home page (RTL) |
| `GET/POST /register.html` | Registration form. `POST` creates the user: **409** if the name is taken, **400** if a field is empty |
| `GET/POST /login.html` | Login form. On success, sets `sessionid=<uuid4>` and returns the protected page; otherwise **401** |
| `/protected.html` | Served only with a valid session cookie, otherwise **307 → /login.html** |
| `/logout` | Deletes the server-side session |
| `/chat`, `/cf`, `/rt` | **307** redirects to external sites |
| anything else | Static file from `webserver/`, or a custom **404** page that shows the client's IP and port |

**Implementation notes**

- **Request parsing:** reads until `\r\n\r\n`, splits out the request line and headers, then keeps reading until it has `Content-Length` bytes of body. The form body is decoded with `parse_qs`.
- **Static files:** paths are normalised, and anything that resolves outside the web root (`..`) gets a 404. `Content-Type` is chosen from the file extension.
- **Auth:** users are stored in `data.txt` as `username:sha256(password)` (created on first registration and git-ignored). Sessions live in an in-memory `dict` keyed by a random UUID.

Verified with `curl`:

```text
/                200 text/html; charset=utf-8
/ar              200 text/html; charset=utf-8
/style.css       200 text/css
/nope            404 text/html; charset=utf-8
/chat            307 → https://chatgpt.com/
/protected.html  307 → /login.html            (no cookie)
register alice   200    duplicate register   409
login            200    wrong password       401
/protected.html  200                          (with session cookie)
/../../Windows/win.ini   404                  (path traversal blocked)
```

**Known limitations** (it's a teaching server): it handles one connection at a time, closes the connection after each response, hashes passwords with unsalted SHA-256 (a real server would use `bcrypt`/`scrypt`), and keeps sessions in memory only.

## UDP transfer test — `udp-transfer-test/`

The client opens a TCP control connection, sends `start`, then fires **1,000,001 UDP datagrams** (the numbers 0 … 1,000,000) at the server as fast as it can. The server counts how many arrive and how many arrive out of order, and stops after a 2-second gap.

```bash
python udp-transfer-test/server.py      # terminal 1
python udp-transfer-test/client.py      # terminal 2 → type: start
```

On loopback it received **999,977 of 1,000,001 datagrams (≈ 0.002% loss) with 0 reordered**. Even on localhost, UDP drops packets once the receive buffer overflows.

---

*Team project (2 students), Computer Networks (ENCS3320), Birzeit University, Fall 2025/26.*
