Scope: 
Create a push-to-talk walkie talkie system between two Raspberry Pi 5's.
Use ReSpeaker 2-mic pi HAT for audio input and output device.

Operating system: Raspberry Pi OS Lite (64-bit)

Notes:
This code could definitely be improved but it worked for my purposes.
I experienced 2 main problems when putting this code together:
    1. There is a hardware incompatibility between the ReSpeaker 2-mic pi HAT and the Pi 5 as documented at https://github.com/HinTak/seeed-voicecard/issues/19.
    For some reason if you have the full Raspberry Pi OS (64-bit) Operating system, installing the drivers for the HAT breaks the HDMI display so you can only access the Pi via SSH.
    I tested with a Pi 4 and I did not run into this issue.
    Solution:
    Switch Operating System Raspberry Pi OS Lite (64-bit).
    This can easily be done using a Raspberry Pi Imager from their website.

    2. Reconstructing the audio on the receiver device.
    When I would set the receive buffer to be the same size as the send buffer, the audio quality went to 0.
    Solution:
    I just kept changing the send and receive buffer sizes until I found one that sounded good.
    For some reason setting the tx buffer size to 2**10 and the rx buffer size to 2**12 made it work.
    But once you get data to go through, these can be tweaked to improve audio quality.


Below are the steps I took to configure the hardware and software so that the code will run.
$ means to execute the following in a terminal.

1. flash sd card with 64-bit LITE OS

2. once booted up, set IP Address.

	$ sudo nano /etc/network/interfaces.d/eth0

    add this text and make sure the address coresponds to the ipaddress used in the python script:
        auto eth0
        iface eth0 inet static
        address 192.168.1.194
        netmask 255.255.255.0
        gateway 192.168.1.1	

    *use 192.168.1.195 for the other Pi.

3. enable SSH (optional):
	$ sudo systemctl enable ssh
	$ sudo systemctl start ssh

4. install:
	$ sudo apt update
	$ sudo apt install git

5. install drivers:
	$ git clone https://github.com/HinTak/seeed-voicecard.git
	$ cd seeed-voicecard
	$ sudo ./install.sh
	$ sudo reboot now

7.set up virtual environment (optional):
    $ sudo apt install python3-pip
	$ python3 -m venv /home/user/example_env
	$ source /home/user/example_env/bin/activate

8. install python packages and dependencies:
	sudo apt install portaudio19-dev
	pip install pyaudio gpiozero numpy

9. set up GPIO
	$ sudo chown root:gpio /dev/gpio*
	$ sudo chmod 660 /dev/gpio*
	$ sudo nano /etc/udev/rules.d/99-gpio.rules

    add this text to the 99-gpio.rules file:
    	KERNEL=="gpio*", MODE="0660", GROUP="gpio"
	
	$ sudo reboot now

