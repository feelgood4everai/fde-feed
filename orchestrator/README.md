# FDE Job Orchestrator Dashboard

A Streamlit dashboard for monitoring FDE-Feed job runs with SQLite backend.

## 🚀 Deploy on Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/your-template-id?referralCode=your-code)

Or deploy manually:
1. Fork this repo
2. Go to [Railway](https://railway.com)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select this repository
5. Railway auto-detects the configuration and deploys

## 🌐 Live Demo

Once deployed, your app will be available at:
`https://your-project-name.up.railway.app`

## 📊 Features

- 📈 Real-time job statistics
- 🔄 Job history with filtering
- 📈 Charts and visualizations
- 🔔 Notification history
- ⚙️ Database management

## 🛠️ Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📝 Environment Variables

- `PORT` - Port to run on (Railway sets this automatically)

## 📁 Project Structure

- `app.py` - Main Streamlit dashboard
- `runner.py` - Job orchestrator with retries
- `jobs.db` - SQLite database
- `schema.sql` - Database schema
