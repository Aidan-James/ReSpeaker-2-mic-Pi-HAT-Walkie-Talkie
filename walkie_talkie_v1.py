from gpiozero import Button
from gpiozero import LED
from signal import pause
import pyaudio
import socket
import time
import threading
import numpy as np
import subprocess

# configurable variables
debounce_time = 0.1
set_volume = 20
TX_CHANNELS = 2
RX_CHANNELS = 2           # depends on audio input device
TX_RATE = 44100        # depends on audio input device
RX_RATE = 44100

# do not change variables
UDP_PORT = 8001
FORMAT = pyaudio.paInt16
CHUNK = 2**10
AUDIO_DEVICE = "seeed-2mic-voicecard"
BTN_PRESS = False
SCRIPT_RUNNING = True
dev_idx = -1
last_pressed_time = 0
BUTTON_PIN = 17

def get_ip_address():
    '''
    return IP address of this device to configure local variables
    '''
    result = subprocess.run(['ifconfig', "eth0"], stdout=subprocess.PIPE)
    
    # Decode the result to get it as a string
    output = result.stdout.decode('utf-8')

    # Find the IP address in the output
    for line in output.split('\n'):
        if 'inet ' in line:
            # Split the line and return the second part, which is the IP address
            return line.split()[1]
    return None


# configure device specific variables
this_IP = get_ip_address()
if this_IP == "192.168.1.195":
    UDP_IP = "192.168.1.194"
    temp_idx = 0
elif this_IP == "192.168.1.194":
    UDP_IP = "192.168.1.195"
    temp_idx = 1
else:
    print("IP error")
    exit()

# initialize audio device
p = pyaudio.PyAudio()
button = Button(BUTTON_PIN)
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(i, info['name'], info['defaultSampleRate'], info['maxOutputChannels'])
    if info['name'][0:20] == AUDIO_DEVICE:
        dev_idx = info['index']





# dev_idx = temp_idx      # use this to select device by index rather than by name


print(f"I am {this_IP}")
print("audio device index: " + str(dev_idx))


# callback functions
def rx_audio():
    '''
    UDP listener.
    Runs in background until KeyboardInterrupt (ctrl+c) is triggered by user.
    '''

    global SCRIPT_RUNNING

    CHUNK = 2**12

    stream = p.open(format=FORMAT, channels=RX_CHANNELS, rate=RX_RATE, output=True, frames_per_buffer=CHUNK, output_device_index=dev_idx)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * CHUNK)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.settimeout(0.5)
    print("listening for audio...")

    while SCRIPT_RUNNING:
        try:
            data, addr = sock.recvfrom(CHUNK)
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_data = audio_data * (set_volume / 100)
            audio_data = np.clip(audio_data, -32768, 32767).astype(np.int16)
            stream.write(audio_data.tobytes())
        
        except socket.timeout as ex:
            pass

    stream.close()
    sock.close()
    p.terminate()


def tx_audio():
    '''
    transmit audio as long as button is pressed.
    '''
    global BTN_PRESS

    

    # theses variables cause issues so I print them so I can do a sanity check
    print(f"tx sample rate: {TX_RATE}")
    print(f"rx sample rate: {RX_RATE}")
    print(f"tx_channels: {TX_CHANNELS}")
    print(f"rx_channels: {RX_CHANNELS}")

    stream = p.open(format=FORMAT, channels=TX_CHANNELS, rate=TX_RATE, input=True, frames_per_buffer=CHUNK, input_device_index=dev_idx)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("transmitting...")
    data = stream.read(CHUNK)
    try:
        while BTN_PRESS and SCRIPT_RUNNING:
            data = stream.read(CHUNK)
            sock.sendto(data, (UDP_IP, UDP_PORT))
    except Exception as ex:
        print(f"xmit audio error caught:\n{ex}")

    stream.close()
    sock.close()

def button_pressed():
    '''
    button down.
    start tx_audio thread.
    check timimg constraint.
    '''
    global last_pressed_time
    global BTN_PRESS

    current_time = time.time()
    
    # start tx thread
    if current_time - last_pressed_time >= debounce_time:
        BTN_PRESS = True
        thread = threading.Thread(target=tx_audio)
        thread.start()
        last_pressed_time = current_time

    else:
        print(f"allow for {debounce_time}s before pressing again.")

def button_released():
    '''
    button up.
    end tx_audio thread.
    '''
    global BTN_PRESS
    print("end transmission.\n")
    BTN_PRESS = False

if __name__ == '__main__':
    '''
    configure button callback functions.
    begin UDP listener thread.
    '''
    try:
        button.when_pressed = button_pressed
        button.when_released = button_released
        listener_thread = threading.Thread(target=rx_audio)
        listener_thread.start()
        pause()
    except KeyboardInterrupt:
        SCRIPT_RUNNING = False
        listener_thread.join()
        p.terminate()
        button.close()
        print("\nexit gracefully.")
        exit()
