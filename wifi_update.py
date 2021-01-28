import json

##programa para registro de nueva red wifi

def createWifiConfig(SSID, password):

    config_lines = [
    '\n',
    'network={',
    '\tssid="{}"'.format(SSID),
    '\tpsk="{}"'.format(password),
    '\tkey_mgmt=WPA-PSK',
    '}'
    ]

    config = '\n'.join(config_lines)
    #print(config)

    with open("/home/pi/Desktop/NODO_2/comunicacion/wpa_supplicant.conf", "a+") as wifi:
        wifi.write(config)
    os.system("sudo cp /home/pi/Desktop/NODO_2/comunicacion/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf")
    



