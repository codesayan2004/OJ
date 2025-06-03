# 🧑‍⚖️ CodeSphere - Online Coding Platform

CodeSphere is a web application that allows users to solve programming problems, compile code online, and submit solutions for automated evaluation, add problems — similar to platforms like Codeforces and LeetCode.

---

## 📁 Project Structure
---

## ⚙️ Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML/CSS/JavaScript
- **Database:** SQLite3 (for development)
- **Others:** Git, GitHub

---

## 🚀 Features

- User registration and login (email/password)
- Online code compilation (with support for multiple languages)
- Submit solutions and get verdicts (AC, WA, TLE, etc.)
- Admin panel for problem management
- Custom test case evaluation
- Submission history and results

---

## 🛠️ Setup Instructions

```bash
git clone https://github.com/codesayan2004/OJ.git
cd OJ
python -m venv myenv
source myenv/bin/activate
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
