# 🚀 Finance Management System (24/7 Reliable)

A professional finance dashboard designed for high availability and premium user experience. This full-stack application features a **FastAPI** backend, a **Liquid-Glass UI** frontend, and a custom **Cron-Wakeup Architecture** to ensure 24/7 uptime on free-tier hosting.

---

## 🌟 Key Features
- **Premium UI/UX**: Custom "Liquid Glass" design with animated glassmorphism and modern typography.
- **24/7 Availability**: Automated cron-job integration to eliminate Render's free-tier "cold start" (60s+ wake-up delay).
- **Secure Authentication**: Multi-layered auth system including Email OTP verification.
- **Transaction Analytics**: Real-time spending analysis with Category Charts (Chart.js).
- **Docker Ready**: Fully containerized backend for consistent deployments across environments.

## 🏗️ Technical Architecture
- **Frontend**: Vanilla HTML5/CSS3/JS (Static site optimized for Vercel)
- **Backend**: Python FastAPI (Deployed via Docker on Render)
- **Database**: PostgreSQL (Managed)
- **CI/CD**: Git-triggered deployments with **Vercel Crons** for backend warming.

## ⚡ 24/7 Reliability Solution
One of the core challenges with free-tier hosting (like Render) is the automatic spin-down after 15 minutes of inactivity. I implemented a custom **Vercel Cron Job** that:
1. Triggers every 10 minutes.
2. Calls the backend API root.
3. Keeps the server "hot" and responsive, resulting in **instant login experiences** for all users.

---

## 📁 Project Structure
```text
├── api/                  # FastAPI Backend (Python)
│   ├── main.py           # core API router
│   ├── auth.py           # handle authentication logic
│   ├── cron_ping.py      # Vercel "Keep-Alive" function
│   └── database.py       # SQL Alchemy connection
├── frontend/             # Responsive Liquid Glass UI
│   └── index.html        # Main dashboard application
├── db/                   # Database migrations & scripts
├── Dockerfile            # Container definition for API
├── render.yaml           # Deployment configuration
├── requirements.txt      # Project dependencies
└── vercel.json           # Vercel Cron & Frontend config
```

---

## 🛠️ How to Run Locally

### Backend (Python)
1. Install dependencies: `pip install -r requirements.txt`
2. Configure settings in `.env`
3. Start the server: `uvicorn api.main:app --reload`

### Frontend
Since the frontend is static, simply open `frontend/index.html` in your browser or serve it via any static server.

---

## 📈 Optimization & Performance
- **Serverless Integration**: Leveraged Vercel Serverless Functions to manage backend health without additional infrastructure costs.
- **Zero-Delay Experience**: Reduced first-load latency from ~60s down to <1s by implementing the cron-ping strategy.

---
*Created by Yash Ghone*
