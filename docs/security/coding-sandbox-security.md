# Student Coding Sandbox Security & Isolation Architecture

## 1. Threat Profile: Student Code is Untrusted Input

The ISDP evaluation pipeline allows students to submit programming assignments (Python, Java, C++, JavaScript). Student code must be treated as potentially hostile input designed to attempt:
- **Fork bombs** / resource starvation (`while True: os.fork()`).
- **Filesystem traversal** / reading institutional database files or system secrets (`open("/etc/passwd")`, reading `.env`).
- **Network egress** / attempting internal port scans on campus LAN.
- **Process execution** / spawning interactive shells or malware droppers.

---

## 2. Core Isolation Rule

**STUDENT CODE MUST NEVER RUN INSIDE THE MAIN FASTAPI SERVER PROCESS OR DIRECTLY ON THE DATABASE HOST SYSTEM.**

```
[ STUDENT SUBMISSION ]
          │
          ▼
[ EVALUATION DISPATCHER ]
          │
          │ Isolated Execution Request
          ▼
┌───────────────────────────────────────────────┐
│           EPHEMERAL SANDBOX CONTAINER        │
│                                               │
│ • Read-only root filesystem                   │
│ • Ephemeral scratch directory in RAM (tmpfs)  │
│ • Non-root user execution (UID 10001)         │
│ • Network namespace: NONE (Offline / airgap)  │
│ • CPU quota: 1.0 vCPU max                     │
│ • Memory quota: 256 MB max                    │
│ • Execution timeout: 5.0 seconds hard limit   │
│ • Process limit (PIDs): 16 max                │
└───────────────────────────────────────────────┘
          │
          ▼
[ STDOUT / STDERR HARVESTER ]
          │
          │ Scored Output & Execution Metrics
          ▼
[ ACADEMIC RESULT ENGINE ]
```

---

## 3. Strict Resource Controls & Quotas

| Constraint | Limit | Violation Handling |
| :--- | :--- | :--- |
| **CPU Time** | 5.0 seconds maximum | SIGKILL emitted; status set to `TIME_LIMIT_EXCEEDED`. |
| **Memory (RAM)** | 256 MB maximum | OOM Killer triggered; status set to `MEMORY_LIMIT_EXCEEDED`. |
| **Output Size** | 1 MB maximum | stdout/stderr truncated; prevents disk exhaustion via infinite print loops. |
| **Network Egress** | Disabled (`--net=none`) | Network sockets rejected (`EACCES`); prevents LAN or internet scanning. |
| **Filesystem Access** | Read-only container root; temporary RAM disk for output | File modifications outside `/tmp` rejected (`EROFS`). |
| **Max Processes** | 16 PIDs max | `pids-limit` prevents fork bomb creation. |
