import paramiko
import json
import logging
from concurrent.futures import ThreadPoolExecutor

# 1. Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("report.txt", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def audit_server(server_info):
    host = server_info["host"]
    user = server_info["username"]
    pwd = server_info["password"]

    logging.info(f"Connecting to {host}...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=user, password=pwd, timeout=5)

        # Execute commands
        stdin, stdout, stderr = client.exec_command("free -h | grep Mem && df -h | grep '/$'")
        output = stdout.read().decode().strip()

        # Log the result
        logging.info(f"--- Audit Report for {host} ---")
        for line in output.split('\n'):
            logging.info(line)
        logging.info(f"--------------------------------\n")

    except Exception as e:
        logging.error(f"Failed to connect to {host}: {e}\n")
    finally:
        client.close()

def main():
    logging.info("=== Starting Bulk Audit Process ===")

    # 2. Read Config
    try:
        with open("servers.json", "r") as f:
            servers = json.load(f)
    except Exception as e:
        logging.error(f"Cannot read servers.json: {e}")
        return

    # 3. Run concurrently (ThreadPool)
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(audit_server, servers)

    logging.info("=== Bulk Audit Completed ===")

if __name__ == "__main__":
    main()