# 🚀 WatchVerify

![Django](https://img.shields.io/badge/Django-Framework-green)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)

**WatchVerify** is a powerful Django-based analytics and monitoring platform designed to track user behavior, subscriptions, reports, revenue, and system health — all from a modern admin dashboard.

---

## 📊 Dashboard Preview

![WatchVerify Dashboard](./Site-administration-ChronoVerify-Admin-04-26-2026_04_49_AM.png)

---

## ✨ Key Features

### 📈 User Analytics

* Total registered users
* Daily active users
* Free vs premium segmentation
* Conversion tracking

### 📊 Reports & Insights

* Reports by category
* Monthly report generation
* Analysis trends visualization

### 🌍 Geographic Insights

* Users by country
* Market distribution
* Currency tracking

### 💰 Revenue Monitoring

* Monthly revenue overview
* Subscription-based earnings
* Conversion rate tracking

### 🤖 AI & Cost Monitoring

* API usage tracking
* Cost vs revenue analysis
* AI call monitoring

### ⚙️ System Health Monitoring

* API uptime tracking
* Database health status
* Error rate monitoring

### 🧾 Error Logging

* Real-time system error logs
* Debugging insights
* Failure tracking

---

## 🏗️ Tech Stack

| Layer      | Technology                          |
| ---------- | ----------------------------------- |
| Backend    | Django, Django REST Framework       |
| Database   | PostgreSQL / SQLite                 |
| Frontend   | Django Templates / Flutter |
| Charts     | Chart.js / Recharts                 |
| Auth       | Django Auth JWT                   |
| Deployment | Vps / Nginx / Gunicorn           |

---

## ⚡ Getting Started

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/watchverify.git
cd watchverify
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate:

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables

Create a `.env` file:

```env
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=127.0.0.1,localhost
```

---

### 5️⃣ Run Migrations

```bash
python manage.py migrate
```

### 6️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

### 7️⃣ Run Server

```bash
python manage.py runserver
```

App will run at:
👉 http://127.0.0.1:8000/

---

## 📁 Project Structure

```bash
watchverify/
│── apps/
│   ├── users/
│   ├── subscriptions/
│   ├── analytics/
│   ├── reports/
│   ├── payment/
│
│── chronoverify/
│── templates/
│── static/
│── media/
│── config/
│── manage.py
```

---

## 📡 API Endpoints

| Endpoint              | Method | Description       |
| --------------------- | ------ | ----------------- |
| `/api/users/`         | GET    | List users        |
| `/api/subscriptions/` | GET    | Subscription data |
| `/api/reports/`       | GET    | Reports data      |
| `/api/analytics/`     | GET    | Dashboard metrics |
| `/api/errors/`        | GET    | Error logs        |

---

## 🔐 Authentication

* FireBase Authentication
* JWT Authentication

---

## 🐳 Docker Setup (Optional)
-----If you want you can use docker-----

```bash
# Build container
docker build -t watchverify .

# Run container
docker run -d -p 8000:8000 watchverify
```

---

## 🚀 Deployment Guide

### Using Gunicorn + Nginx

```bash
pip install gunicorn
gunicorn config.wsgi:application
```

Configure **Nginx** as reverse proxy.

---

### Recommended Hosting

* AWS EC2
* DigitalOcean
* Render
* Railway

---

## 🧪 Testing

```bash
python manage.py test
```

---

## 📊 Future Improvements

* 🔔 Real-time notifications (WebSockets)
* 📱 Fully responsive mobile dashboard
* 🤖 Advanced AI insights
* 🔐 Role-based access control (RBAC)
* 📦 SaaS billing integration (Stripe)

---

## 🤝 Contributing

```bash
# Fork repo
# Create branch
git checkout -b feature-name

# Commit
git commit -m "Added feature"

# Push
git push origin feature-name
```

---

## 🐞 Known Issues

* Minor UI inconsistencies on small screens
* API optimization pending for large datasets

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Morshed Nayeem**

---

## ⭐ Support

If you like this project:

👉 Give it a ⭐ on GitHub
👉 Share with others
👉 Contribute 🚀

---
