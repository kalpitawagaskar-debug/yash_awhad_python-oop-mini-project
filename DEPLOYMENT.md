# Deployment Guide for EV Battery Thermal Intelligence Dashboard

This guide provides step-by-step instructions to deploy the **EV Battery Thermal Intelligence Dashboard** across different platforms.

---

## 📋 Overview & Prerequisites

- **Framework**: Streamlit (`ev_thermal_dashboard_app.py`)
- **Dataset**: `ev_battery_failure_dataset (1).csv` (~77.2 MB, 200,000 records)
- **Configuration**: Headless mode and dark styling are pre-configured in `.streamlit/config.toml`.

---

## 🚀 Option 1: Streamlit Community Cloud (Recommended & 100% Free)

Streamlit Community Cloud is the fastest, free method to host your application directly from a GitHub repository.

### Step 1: Initialize Git and Commit Your Project
Open PowerShell or your terminal in this project directory:

```powershell
# 1. Initialize git repository
git init

# 2. Stage files (ignoring __pycache__ and venv automatically via .gitignore)
git add .

# 3. Create your initial commit
git commit -m "Initial commit: EV Battery Thermal Dashboard with Streamlit and Plotly"
```

> **Note on Dataset Size**: `ev_battery_failure_dataset (1).csv` is **~77.2 MB**. GitHub permits single files up to **100 MB** (it will output a harmless yellow warning about files over 50 MB, but will accept the push).

### Step 2: Push to GitHub
1. Create a new repository on [GitHub](https://github.com/new) (e.g. `ev-battery-thermal-dashboard`).
2. Run:
```powershell
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
git push -u origin main
```

### Step 3: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **"New app"**.
3. Select:
   - **Repository**: `<YOUR-USERNAME>/<YOUR-REPO-NAME>`
   - **Branch**: `main`
   - **Main file path**: `ev_thermal_dashboard_app.py`
4. Click **"Deploy!"**.
5. Within 1–2 minutes, your dashboard will be live at a public URL (e.g., `https://<your-app-name>.streamlit.app`).

---

## 🤗 Option 2: Hugging Face Spaces (Free — 16 GB RAM)

Because the dataset has 200,000 rows and scikit-learn models, **Hugging Face Spaces** is an exceptional choice since it provides **16 GB RAM** on its free tier (compared to ~1 GB on Streamlit Cloud).

### Steps:
1. Sign up / Log in to [Hugging Face](https://huggingface.co/).
2. Navigate to [Hugging Face Spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
3. Choose:
   - **Space SDK**: `Streamlit`
   - **Hardware**: `CPU basic • 2 vCPU • 16GB RAM` (Free)
   - **Visibility**: Public or Private
4. Clone the space repository locally or push your files:
```powershell
git remote add hf https://huggingface.co/spaces/<YOUR-USERNAME>/<YOUR-SPACE-NAME>
git push hf main
```
5. In Hugging Face Space settings or in `README.md`, ensure the entrypoint is configured as `app_file: ev_thermal_dashboard_app.py` (or rename `ev_thermal_dashboard_app.py` to `app.py`).

---

## 🐳 Option 3: Docker Deployment (Container Platforms)

A production-ready [Dockerfile](file:///c:/Users/YASH/Downloads/EV_Battery_Thermal_Dashboard_Project/Dockerfile) and [docker-compose.yml](file:///c:/Users/YASH/Downloads/EV_Battery_Thermal_Dashboard_Project/docker-compose.yml) are included in this project.

### Run with Docker locally:
```bash
# Build the Docker image
docker build -t ev-thermal-dashboard .

# Run the container
docker run -p 8501:8501 ev-thermal-dashboard
```

### Run with Docker Compose:
```bash
docker-compose up -d
```
Access at `http://localhost:8501`.

### Deploy to Container Clouds:
- **Google Cloud Run**:
  ```bash
  gcloud run deploy ev-thermal-dashboard --source . --port 8501 --memory 2Gi --allow-unauthenticated
  ```
- **AWS App Runner / ECS**: Push the Docker image to Amazon ECR and deploy as a web service.
- **Render / Railway / Fly.io**: Connect your Git repo; they will automatically detect the `Dockerfile` and expose port `8501`.

---

## 🖥️ Option 4: Deploying on a Cloud Virtual Machine (Ubuntu / EC2)

To deploy on your own server (AWS EC2, DigitalOcean, Azure VM, Linode):

1. **SSH into the server and clone the repo**:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git
   git clone <YOUR-GITHUB-REPO-URL>
   cd <YOUR-REPO-NAME>
   ```

2. **Create a virtual environment and install packages**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Create a Systemd Service** (runs continuously in the background and auto-restarts on reboot):
   Create `/etc/systemd/system/ev_dashboard.service`:
   ```ini
   [Unit]
   Description=EV Battery Thermal Intelligence Dashboard
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/EV_Battery_Thermal_Dashboard_Project
   ExecStart=/home/ubuntu/EV_Battery_Thermal_Dashboard_Project/venv/bin/streamlit run ev_thermal_dashboard_app.py --server.port 8501 --server.address 0.0.0.0
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start and enable the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ev_dashboard
   sudo systemctl start ev_dashboard
   sudo systemctl status ev_dashboard
   ```

5. **(Optional) Configure Nginx reverse proxy with SSL**:
   Forward port 80/443 to `http://localhost:8501` and attach a free Let's Encrypt SSL certificate using Certbot.

---

## 📶 Option 5: Local Intranet / Office Network Sharing

To share the dashboard with colleagues on the same Wi-Fi or LAN without uploading anything to the public internet:

```powershell
python -m streamlit run ev_thermal_dashboard_app.py --server.address 0.0.0.0 --server.port 8501
```

Streamlit will print:
- **Local URL**: `http://localhost:8501`
- **Network URL**: `http://<your-local-ip>:8501`

Anyone on the same local network can access the dashboard using the Network URL.
