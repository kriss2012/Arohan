# Campus Network Security Architecture

## 1. Local Network Topology

The Institute Student Development Platform (ISDP) operates entirely inside the institute's campus LAN or isolated laboratory subnets.

```
[ CAMPUS LAB WORKSTATIONS ]        [ FACULTY LAPTOPS ]
          │                                  │
          └─────────────────┬────────────────┘
                            │ Campus Intranet (VLAN 10 / VLAN 20)
                            ▼
               [ CAMPUS APPLICATION SERVER ]
               ├── Reverse Proxy (TLS Termination)
               ├── FastAPI Backend Runtime (Port 8000)
               └── Local Storage & Database (Port NOT exposed)
```

---

## 2. Port & Firewall Policies

| Source | Destination | Protocol / Port | Policy | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| Any Workstation | Campus Server | TCP 443 (HTTPS) | **ALLOW** | Secure Application UI & API traffic |
| Any Workstation | Campus Server | TCP 80 (HTTP) | **REDIRECT** | Immediate redirect to HTTPS (301) |
| Workstation / Public | Campus Server | TCP 5432 / DB Port | **BLOCK** | Direct database access is strictly prohibited |
| Any Workstation | Campus Server | TCP 22 / 3389 | **RESTRICT** | SSH/RDP restricted to Administrative Subnet only |
| Campus Server | Internet (Cloud) | Any | **BLOCKED / OPTIONAL** | Zero external dependency; air-gapped support |

---

## 3. Transport Layer Security (TLS)

1. **Intranet TLS Certificates**: The campus application server utilizes a certificate signed by the institute's Root Certificate Authority (CA), pre-installed on managed laboratory devices.
2. **Strict Transport Security**: Modern ciphers (TLS 1.3 preferred, TLS 1.2 minimum) with Perfect Forward Secrecy (ECDHE). Weak ciphers (RC4, 3DES, MD5) are disabled.
3. **Internal Timestamp Header**: Every response provides `X-Server-Time-UTC` to guarantee synchronized client-server timing across laboratories without relying on public NTP servers.

---

## 4. Cross-Origin Resource Sharing (CORS)

- Wildcard (`*`) CORS is strictly disallowed in production deployments.
- Permitted origins are restricted to:
  - `http://localhost:5173` (local development/desktop shell)
  - `tauri://localhost` (desktop native bundle)
  - `https://isdp.imrd.ac.in` (official institutional intranet domain)
