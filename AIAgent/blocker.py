import ctypes
import os
import time
import psutil

# Path to Windows hosts file
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"

# We add a unique tag so we can clean up our own blocks easily
BLOCK_TAG = "# AI_AGENT_BLOCK"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def block_websites(websites):
    """Adds the list of websites to the hosts file to block them."""
    if not is_admin():
        print("Trạng thái: Không có quyền Admin để chặn web.")
        return False
        
    try:
        with open(HOSTS_PATH, 'r+') as file:
            content = file.read()
            # If our tag is not there, we will add it at the bottom.
            if BLOCK_TAG not in content:
                file.write(f"\n{BLOCK_TAG}\n")
            
            # Since we just want to replace our block block, it's easier to rewrite the non-blocked part
            file.seek(0)
            lines = file.readlines()
            # Keep only lines that don't belong to our block
            clean_lines = [line for line in lines if not line.strip().endswith(BLOCK_TAG) and line.strip() != BLOCK_TAG]
            
            file.seek(0)
            file.truncate()
            file.writelines(clean_lines)
            
            # Now add the block tag and new blocked sites
            file.write(f"\n{BLOCK_TAG}\n")
            for site in websites:
                file.write(f"{REDIRECT_IP} {site} {BLOCK_TAG}\n")
                file.write(f"{REDIRECT_IP} www.{site} {BLOCK_TAG}\n")
        return True
    except Exception as e:
        print(f"Lỗi khi chặn web: {e}")
        return False

def unblock_websites():
    """Removes our blocked websites from the hosts file."""
    if not is_admin():
        return False
        
    try:
        with open(HOSTS_PATH, 'r+') as file:
            lines = file.readlines()
            file.seek(0)
            file.truncate()
            for line in lines:
                if not line.strip().endswith(BLOCK_TAG) and line.strip() != BLOCK_TAG:
                    file.write(line)
        return True
    except Exception as e:
        print(f"Lỗi khi bỏ chặn web: {e}")
        return False

def scan_and_kill_apps(apps_list):
    """Scans running processes and kills those matching the blacklist."""
    killed_apps = []
    
    # apps_list may contain things like 'steam.exe'
    target_names = [app.lower() for app in apps_list]
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pinfo = proc.info
            if pinfo['name'] and pinfo['name'].lower() in target_names:
                proc.kill()
                print(f"Đã đóng ứng dụng vi phạm: {pinfo['name']}")
                killed_apps.append(pinfo['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    return killed_apps
