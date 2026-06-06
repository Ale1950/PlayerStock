/* DEV ONLY — reverse proxy stessa-origine su :8080.
 *   /api/*  -> http://localhost:8001 (backend)
 *   resto   -> file statici da frontend/dist (export Expo web, SPA fallback a index.html)
 * Esposto in https via ngrok. NON per produzione. Nessuna dipendenza esterna.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const BACKEND = { host: '127.0.0.1', port: 8001 };
const DIST = path.join(__dirname, 'frontend', 'dist');

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.map': 'application/json; charset=utf-8', '.ico': 'image/x-icon',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
  '.svg': 'image/svg+xml', '.webp': 'image/webp',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
};

function serveFile(filePath, res) {
  fs.readFile(filePath, (err, buf) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream' });
    res.end(buf);
  });
}

const server = http.createServer((req, res) => {
  // ---- /api -> backend ----
  if (req.url === '/api' || req.url.startsWith('/api/')) {
    const headers = { ...req.headers, host: `${BACKEND.host}:${BACKEND.port}` };
    const upstream = http.request(
      { host: BACKEND.host, port: BACKEND.port, path: req.url, method: req.method, headers },
      (up) => { res.writeHead(up.statusCode || 502, up.headers); up.pipe(res); },
    );
    upstream.on('error', (e) => { res.writeHead(502); res.end('Backend non raggiungibile: ' + e.message); });
    req.pipe(upstream);
    return;
  }

  // ---- statico (SPA) ----
  const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
  let rel = urlPath === '/' ? 'index.html' : urlPath.replace(/^\/+/, '');
  const full = path.join(DIST, rel);
  // anti path-traversal
  if (!full.startsWith(DIST)) { res.writeHead(403); res.end('Forbidden'); return; }
  fs.stat(full, (err, st) => {
    if (!err && st.isFile()) serveFile(full, res);
    else serveFile(path.join(DIST, 'index.html'), res); // fallback SPA (expo-router)
  });
});

server.listen(PORT, '0.0.0.0', () => console.log(`[dev-proxy] http://localhost:${PORT}  (/api -> :8001, resto -> frontend/dist)`));
