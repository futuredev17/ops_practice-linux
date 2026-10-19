# 🐧 Linux Ops Practice & Automation

Hands-on Linux operations practice: system health checks, systemd services and timers, Dockerized services, and real troubleshooting notes. I am building this repository on the way to a DevOps / Cloud Engineer role.

## 🛠️ Tech Stack

- **OS**: Ubuntu 24.04 (VM)
- **Service management**: systemd (services + timers)
- **Automation**: Python 3, Bash
- **Containers**: Docker, Docker Compose
- **Web / Database**: Nginx, MySQL 8
- **Networking & Security**: SSH, UFW, NAT / port forwarding

## 📂 Repository Layout

| Path | Purpose |
| --- | --- |
| `system_check.sh` | System health check: disk, memory, and top processes |
| `docker_monitor.py` | Checks running containers and warns when one is down |
| `clean_apt.py` | Cleans the APT cache; also packaged as a Docker image |
| `df_daemon.py` | Disk-usage monitor used with a systemd service |
| `log_archiver.sh` | Archives and rotates log files |
| `Dockerfile` | Builds the image for `clean_apt.py` |
| `docker-compose.yml` | Nginx + MySQL stack with a bind-mounted data directory |
| `web/` | Static page served by Nginx |
| `conf/` | Service and application configuration |
| `script/` | Helper scripts |
| `backup/`, `log/` | Runtime output (not tracked) |
| `db_data/` | MySQL data directory (bind mount, not tracked) |

## 🚀 Quick Start

### Monitoring scripts

```bash
chmod +x system_check.sh
./system_check.sh
python3 docker_monitor.py
```

### Web + database stack

```bash
cp .env.example .env        # set MYSQL_ROOT_PASSWORD
docker compose up -d
docker compose ps
```

Open <http://localhost:8081>.

```bash
docker compose down         # stop and remove the stack
```

### systemd units

```bash
sudo cp systemd/clean-apt.service /etc/systemd/system/
sudo cp systemd/clean-apt.timer   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now clean-apt.timer
systemctl list-timers clean-apt.timer
```

## 🚑 Troubleshooting Notes

### 1. `port is already allocated`

**Cause**: the host's native Nginx was listening on port 80 (the container was originally mapped to 80 and now uses 8081), and an old container was still holding port 3306 through `docker-proxy`.

**Diagnosis**:

```bash
sudo ss -tulpn | grep -E ':(80|3306)'
docker ps -a
```

**Fix**: stopped the host Nginx and removed the stale container so the ports were released:

```bash
sudo systemctl stop nginx
docker compose down
```

`kill -9` was used only as a last resort on a leftover proxy process.

### 2. Compose / YAML errors

**Cause**: tabs instead of spaces, and volume keys nested at the wrong level, which produced `additional properties not allowed` and `did not find expected key`.

**Fix**: strict two-space indentation and an absolute path for the bind mount:

```yaml
volumes:
  - /home/user/Germany/ops_practice/db_data:/var/lib/mysql
```

### 3. MySQL data not visible in the project directory

**Cause**: Docker created a named volume under `/var/lib/docker/volumes/` instead of binding to the project folder.

**Diagnosis**:

```bash
docker volume ls
docker inspect <container> --format '{{json .Mounts}}'
```

**Fix**: replaced the named volume with a bind mount to an absolute host path, so `db_data/` appears in the project directory and survives `docker compose down`.

## 🧠 Lessons Learned

- Pin image versions (for example `mysql:8.4`, `nginx:1.27`) instead of `latest` for reproducible builds.
- Keep secrets in `.env` and commit only `.env.example`.
- Do not publish database ports on a host with a public IP; containers can reach MySQL over the Compose network.
- `docker compose down` is the clean way to release ports; reserve `kill -9` for stuck processes.

## 🚀 Roadmap

- [ ] Kubernetes basics (k3s) and Helm
- [ ] CI/CD with GitHub Actions
- [ ] AWS Certified Solutions Architect – Associate (SAA-C03)
- [ ] IELTS 7.0 and German B1
- [ ] DevOps / Cloud Engineer role in Germany

---

*One commit a day.*

