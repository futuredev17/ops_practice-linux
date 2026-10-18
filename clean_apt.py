import os
print("=== Cleaning apt cache ===")
os.system("sudo apt-get clean -y")
print("Cleanup complete!")