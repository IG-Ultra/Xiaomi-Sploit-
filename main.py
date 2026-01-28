# ========================== PART 1: Setup & Utilities ==========================
import subprocess
import sys
import os
import hashlib
import random
import time
import linecache
from datetime import datetime, timezone, timedelta

# Install and import packages
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ["requests", "ntplib", "pytz", "urllib3", "icmplib", "colorama"]
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing package {package}...")
        install_package(package)

import ntplib
import pytz
import urllib3
import json
from icmplib import ping
from colorama import init, Fore, Style

# Clear console
os.system('cls' if os.name == 'nt' else 'clear')

# ===================== Colors Setup =====================
init(autoreset=True)
col_g = Fore.GREEN
col_gb = Style.BRIGHT + Fore.GREEN
col_b = Fore.BLUE
col_bb = Style.BRIGHT + Fore.BLUE
col_y = Fore.YELLOW
col_yb = Style.BRIGHT + Fore.YELLOW
col_r = Fore.RED
col_rb = Style.BRIGHT + Fore.RED

# ===================== Main Banner ================================================================
banner = f"""
{col_gb}==============================================================
{col_yb}
 __  ___                       _   ____        _       _ _    
 \ \/ (_) __ _  ___  _ __ ___ (_) / ___| _ __ | | ___ (_) |_  
  \  /| |/ _` |/ _ \| '_ ` _ \| | \___ \| '_ \| |/ _ \| | __| 
  /  \| | (_| | (_) | | | | | | |  ___) | |_) | | (_) | | |_  
 /_/\_\_|\__,_|\___/|_| |_| |_|_| |____/| .__/|_|\___/|_|\__| 
                                        |_|                   

{col_g}---------------------------------------------------------------
{col_bb}                  █▓▒▒░░░ Sonu Bagga ░░░▒▒▓█
{col_g}==============================================================={Fore.RESET}
"""
print(banner)

# ===================== Global Config =====================
ntp_servers = [
    "ntp0.ntp-servers.net", "ntp1.ntp-servers.net", "ntp2.ntp-servers.net",
    "ntp3.ntp-servers.net", "ntp4.ntp-servers.net", "ntp5.ntp-servers.net",
    "ntp6.ntp-servers.net"
]

MI_SERVERS = ['161.117.96.161', '20.157.18.26']

# ===================== Token Input =====================
token_number = int(input(col_g + "[Token line number]: " + Fore.RESET))
os.system('cls' if os.name == 'nt' else 'clear')
script_version = "ARU_FHL_v070425"
print(col_yb + f"{script_version}_token_#{token_number}:")
print(col_y + "Checking account status..." + Fore.RESET)
token = linecache.getline("token.txt", token_number).strip()
cookie_value = token
feedtime = float(linecache.getline("timeshift.txt", token_number).strip())
feed_time_shift = feedtime
feed_time_shift_1 = feed_time_shift / 1000

# ===================== Utility Functions =====================
def generate_device_id():
    random_data = f"{random.random()}-{time.time()}"
    device_id = hashlib.sha1(random_data.encode('utf-8')).hexdigest().upper()
    return device_id

def get_initial_beijing_time():
    client = ntplib.NTPClient()
    beijing_tz = pytz.timezone("Asia/Shanghai")
    for server in ntp_servers:
        try:
            print(col_y + "\nFetching current time in Beijing..." + Fore.RESET)
            response = client.request(server, version=3)
            ntp_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
            beijing_time = ntp_time.astimezone(beijing_tz)
            print(col_g + f"[Beijing time]: " + Fore.RESET + f"{beijing_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
            return beijing_time
        except Exception as e:
            print(f"Error connecting to {server}: {e}")
    print("Could not connect to any NTP server.")
    return None

def get_synchronized_beijing_time(start_beijing_time, start_timestamp):
    elapsed = time.time() - start_timestamp
    current_time = start_beijing_time + timedelta(seconds=elapsed)
    return current_time
def wait_until_target_time(start_beijing_time, start_timestamp):
    next_day = start_beijing_time + timedelta(days=1)
    print(col_y + "\nRequesting bootloader unlock..." + Fore.RESET)
    print(col_g + "[Configured delay]: " + Fore.RESET + f"{feed_time_shift:.2f} ms.")
    target_time = next_day.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=feed_time_shift_1)
    print(col_g + "[Waiting until]: " + Fore.RESET + f"{target_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print("Do not close this window...")

    while True:
        current_time = get_synchronized_beijing_time(start_beijing_time, start_timestamp)
        time_diff = target_time - current_time
        if time_diff.total_seconds() > 1:
            time.sleep(min(1.0, time_diff.total_seconds() - 1))
        elif current_time >= target_time:
            print(f"Target time reached: {current_time.strftime('%Y-%m-%d %H:%M:%S.%f')}. Starting requests...")
            break
        else:
            time.sleep(0.0001)

class HTTP11Session:
    def __init__(self):
        self.http = urllib3.PoolManager(
            maxsize=10,
            retries=True,
            timeout=urllib3.Timeout(connect=2.0, read=15.0),
            headers={}
        )

    def make_request(self, method, url, headers=None, body=None):
        try:
            request_headers = headers or {}
            request_headers['Content-Type'] = 'application/json; charset=utf-8'
            if method == 'POST':
                if body is None:
                    body = '{"is_retry":true}'.encode('utf-8')
                request_headers['Content-Length'] = str(len(body))
                request_headers['Accept-Encoding'] = 'gzip, deflate, br'
                request_headers['User-Agent'] = 'okhttp/4.12.0'
                request_headers['Connection'] = 'keep-alive'
            response = self.http.request(method, url, headers=request_headers, body=body, preload_content=False)
            return response
        except Exception as e:
            print(f"[Network error] {e}")
            return None

def check_unlock_status(session, cookie_value, device_id):
    url = "https://sgp-api.buy.mi.com/bbs/api/global/user/bl-switch/state"
    headers = {"Cookie": f"new_bbs_serviceToken={cookie_value};versionCode=500411;versionName=5.4.11;deviceId={device_id};"}
    try:
        response = session.make_request('GET', url, headers=headers)
        if response is None:
            print("[Error] Cannot fetch unlock status.")
            return False
        response_data = json.loads(response.data.decode('utf-8'))
        response.release_conn()
        data = response_data.get("data", {})
        is_pass = data.get("is_pass")
        button_state = data.get("button_state")
        deadline_format = data.get("deadline_format", "")

        if is_pass == 4 and button_state == 1:
            print(col_g + "[Account status]: " + Fore.RESET + "Request can be submitted.")
            return True
        else:
            print(col_g + "[Account status]: " + Fore.RESET + f"Cannot submit request. Status: {is_pass}, Button: {button_state}")
            return False
    except Exception as e:
        print(f"[Error checking status] {e}")
        return False

def main():
    device_id = generate_device_id()
    session = HTTP11Session()

    if not check_unlock_status(session, cookie_value, device_id):
        input("Press Enter to exit...")
        return

    start_beijing_time = get_initial_beijing_time()
    if start_beijing_time is None:
        input("Press Enter to exit...")
        return

    start_timestamp = time.time()
    wait_until_target_time(start_beijing_time, start_timestamp)

    url = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"
    headers = {"Cookie": f"new_bbs_serviceToken={cookie_value};versionCode=500411;versionName=5.4.11;deviceId={device_id};"}

    try:
        while True:
            request_time = get_synchronized_beijing_time(start_beijing_time, start_timestamp)
            print(col_g + "[Request]: " + Fore.RESET + f"Sending request at {request_time.strftime('%Y-%m-%d %H:%M:%S.%f')} (UTC+8)")
            response = session.make_request('POST', url, headers=headers)
            if response is None:
                continue
            response_data = response.data
            response.release_conn()
            try:
                json_response = json.loads(response_data.decode('utf-8'))
                print(col_g + "[Response]: " + Fore.RESET + f"{json_response}")
            except:
                print("[Error] Invalid JSON response.")
    except KeyboardInterrupt:
        print("\n[Exiting...]")
        exit()

if __name__ == "__main__":
    main()