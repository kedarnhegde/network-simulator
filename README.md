# 🛰️ Network Simulator

A modular simulation platform built for the **CS-576 project**.  
Uses **backend (FastAPI)** and **frontend (React + Vite)**.

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/kedarnhegde/network-simulator.git
cd network-simulator
```

### 2️⃣ Create and activate virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

*(On Windows PowerShell):*
```powershell
.\.venv\Scripts\activate
```

---

## 🧩 Backend Setup

### Install dependencies
```bash
make install-backend # Make sure you're in .venv 
```

### Run the FastAPI backend
```bash
make run-backend # Make sure you're in .venv 
```

By default, the backend runs on:  
📍 **http://localhost:8000**

---

## 🧪 API Endpoints

| Endpoint            | Method              | Description                                 |
|---------------------|---------------------|---------------------------------------------|
| `/health`           | GET                 | Health check (returns `{"status":"ok"}`)    |
| `/nodes`            | GET / POST / DELETE | Manage network nodes                         |
| `/control/start`    | POST                | Start the simulation                         |
| `/control/pause`    | POST                | Pause the simulation                          |
| `/control/reset`    | POST                | Reset the simulation                          |
| `/metrics`          | GET                 | Simulation metrics (time, energy, etc.)       |

---

## 💻 Frontend Setup

```bash
make install-frontend
make run-frontend
```

Default Vite dev server: **http://localhost:5173**

---

## 🧰 Available Makefile Commands

| Command                 | Description                                      |
|-------------------------|--------------------------------------------------|
| `make run-backend`      | Start FastAPI backend with auto-reload           |
| `make install-backend`  | Install backend dependencies                      |
| `make run-frontend`     | Start React frontend                              |
| `make install-frontend` | Install frontend dependencies                     |
| `make clean`            | Remove cache, build, and node_modules             |
| `make help`             | Show available commands                            |

---

## 🧹 Cleaning Up

Remove Python caches, build artifacts, and node modules:
```bash
make clean
```

---

## 👥 Contributors

- [@kedarnhegde](https://github.com/kedarnhegde)  
- Group 6 — CS-576, Fall 2025
