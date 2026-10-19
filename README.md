# 🐧 Linux Ops Practice & Automation

This repository contains my daily practice scripts, automation tools, and troubleshooting records as I transition into a DevOps / Cloud Engineer role.

## 🛠️ Tech Stack
- **OS**: Ubuntu 24.04 (Virtual Machine)
- **Containerization**: Docker, Docker Compose
- **Automation**: Python3, Bash Shell
- **Network & Security**: UFW Firewall, Nginx

## 📂 Project Structure

### 1. System Monitoring & Automation
- `system_check.sh`: A comprehensive system health check script (disk, memory, top processes, etc.).
- `docker_monitor.py`: A Python script that checks the health of running Docker containers and prints warnings if any container is down.
- `clean_apt.py`: Python script to clean apt cache (containerized).

### 2. Docker Deployment (Web + Database)
- `Dockerfile`: Builds a custom image for the Python cleanup script.
- `docker-compose.yml`: Deploys a full stack including an Nginx web server (port 8081) and a MySQL database (port 3306), with volume mounting for data persistence.

## 🚑 Troubleshooting Records (Real-world Scenarios)

During the deployment, I encountered and resolved several critical issues:

1. **Port Conflict (`port is already allocated`)**:
   - **Cause**: The host system's native Nginx was occupying port 80, and orphaned `docker-proxy` processes were holding port 3306.
   - **Solution**: Used `ss -tulpn | grep <port>` to identify the PIDs, killed the processes using `kill -9`, and stopped the system Nginx (`systemctl stop nginx`) to free up ports.

2. **YAML Syntax Errors**:
   - **Cause**: Incorrect indentation (using Tab instead of spaces) and nested volume definitions causing `additional properties not allowed` or `did not find expected key`.
   - **Solution**: Rewrote the `docker-compose.yml` ensuring strict 2-space indentation and absolute paths for volume mounting.

3. **Data Persistence (Volume Missing)**:
   - **Cause**: Docker automatically created a named volume (hidden in `/var/lib/docker/volumes/`) instead of mapping to the local directory.
   - **Solution**: Modified the `volumes` directive to use the absolute local path: `/home/user/Germany/ops_practice/db_data:/var/lib/mysql`, successfully exposing the data folder in the project directory.

## 🚀 Future Goals
- Deep dive into Kubernetes (K8s) and CI/CD pipelines.
- Obtain AWS Certified Solutions Architect (SAA).
- Transition to a Cloud/DevOps Engineer role.

---
*Keep striving, outdo yesterday.*
