#!/opt/ibgateway-venv/bin/python
import os, time, subprocess, pyotp
from dotenv import load_dotenv

load_dotenv('/root/.ibgateway.env')

LOGIN   = os.getenv('IBKR_LOGIN')
PASS    = os.getenv('IBKR_PASSWORD')
SECRET  = os.getenv('IBKR_TOTP_SECRET')
GATEWAY = '/root/Jts/ibgateway/1030/ibgateway'
DISP    = os.getenv('DISPLAY', ':0')

def start_xvfb():
    subprocess.Popen(['Xvfb', DISP, '-ac', '-screen', '0', '1024x768x24'])
    os.environ['DISPLAY'] = DISP
    time.sleep(3)

def launch():
    return subprocess.Popen([GATEWAY, '-role', 'gateway'])

def type_login(code):
    subprocess.call(['xdotool','search','--name','IB Gateway','windowactivate','--sync'])
    time.sleep(1)
    for text in [LOGIN, PASS, code]:
        subprocess.call(['xdotool','type',text])
        time.sleep(0.5)
        subprocess.call(['xdotool','key','Tab'])
    subprocess.call(['xdotool','key','Return'])

if __name__=='__main__':
    start_xvfb()
    proc = launch()
    time.sleep(10)
    totp = pyotp.TOTP(SECRET).now()
    type_login(totp)
    proc.wait()