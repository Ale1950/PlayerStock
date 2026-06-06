# DEV ONLY — backend raggiungibile in LAN (telefono sulla stessa Wi-Fi).
# Bind su 0.0.0.0 (tutte le interfacce). NON usare in produzione senza reverse-proxy/TLS/sicurezza.
& "$PSScriptRoot\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8001
