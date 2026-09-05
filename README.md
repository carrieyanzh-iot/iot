# iot

Raspberry PI 4
/bin; /dev; /etc; /home; /lib; /proc; /usr; /var

1. Basic system commands
# Check Raspberry Pi OS / Debian version
cat /etc/os-release
cat /proc/version
Linux system
│
├── OS / Distribution
│     └── Debian, Ubuntu, Raspberry Pi OS
│
└── Kernel
      └── Linux 6.x, Linux 5.x, etc.
# Kernel version
uname -a
# CPU information
lscpu
cat /proc/cpuinfo
| Command             | Purpose                                      | Output style           |
| ------------------- | -------------------------------------------- | ---------------------- |
| `lscpu`             | **Summary of CPU information**               | Easy to read           |
| `cat /proc/cpuinfo` | **Detailed information about each CPU/core** | Large, detailed output |


tar -czvf backup.tar.gz /home/user/mydata
tar -xzvf backup.tar.gz
tar = archive, gzip = compress.

# Memory
free -h
# Disk space
df -h
# Raspberry Pi temperature
vcgencmd measure_temp
# Reboot
sudo reboot
# Shutdown
sudo shutdown -h now (Powered off)
sudo shutdown -r now (restart)

2. Network / Internet commands
# Show IP addresses
ip addr
# Short version
hostname -I
# Show network interfaces
ip link
# Test Internet connection
ping google.com
# Test a specific IP
ping 8.8.8.8
# Check routing
ip route
# Check DNS
nslookup google.com
# Show listening ports
sudo ss -tulpn

3. Wi-Fi commands
# Show Wi-Fi interface
iwconfig
# Scan Wi-Fi networks
sudo iwlist wlan0 scan
# Check NetworkManager status
nmcli device status
# Show Wi-Fi connection
nmcli connection show
# Show Wi-Fi details
nmcli device wifi list

Connect to Wi-Fi:
sudo nmcli device wifi connect "YOUR_WIFI_NAME" password "YOUR_PASSWORD"


4. GPIO / IoT hardware
For sensors, LEDs, buttons, relays, etc., you may need GPIO tools.
Check GPIO:
gpioinfo
List GPIO chips:
gpiodetect
GPIO tools are based on Linux's libgpiod interface.
You can install them with:
sudo apt update
sudo apt install gpiod

5. I2C sensors
Many IoT sensors use I2C, for example temperature, humidity and OLED sensors.
Check I2C:
ls /dev/i2c*
Install I2C tools:
sudo apt install i2c-tools
Scan the I2C bus:
sudo i2cdetect -y 1

6. Serial / UART
Check serial devices:
ls /dev/tty*
Common Raspberry Pi serial device:
/dev/serial0
Check:
ls -l /dev/serial*

Typical IoT Python stack:
Python
  ↓
GPIO / I2C / SPI
  ↓
Sensor
  ↓
MQTT / HTTP
  ↓
Server / Cloud


MQTT — very important for IoT
Install Mosquitto:
sudo apt update
sudo apt install mosquitto 
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
sudo systemctl status mosquitto
mosquitto_sub -t "zigbee2mqtt/#" -v

mosquitto_sub -h 192.168.1.122 -t "sensor/temperature"
mosquitto_pub -h 192.168.1.122 -t "sensor/temperature" -m "25.5"

Sensor → MQTT Publisher → MQTT Broker → MQTT Subscriber


Docker commands
# Check Docker
docker --version

# Check running containers
docker ps

# Check all containers
docker ps -a

# List images
docker images

# Start container
docker start <container>

# Stop container
docker stop <container>

# View logs
docker logs <container>

# Follow logs
docker logs -f <container>

k3s / Kubernetes commands
# Check nodes
kubectl get nodes

# Check pods
kubectl get pods

# All namespaces
kubectl get pods -A

# Services
kubectl get svc

# Deployments
kubectl get deployments

# Ingress
kubectl get ingress

# Detailed information
kubectl describe pod <pod-name>

# Pod logs
kubectl logs <pod-name>


kubectl get nodes
kubectl get pods
kubectl get pods -A
kubectl get svc
kubectl get ingress

kubectl describe ingress hello-ingress
kubectl get deployment
kubectl get replicaset
kubectl get pod


Deployment
    ↓
ReplicaSet
    ↓
Pod
    ↓
Container


kubectl logs learnk3s-65b458668b-j6xhc
⭐ Raspberry Pi nice IoT/Kubernetes env：
Raspberry Pi 4
      │
      └── k3s
           ├── Traefik
           ├── CoreDNS
           ├── Metrics Server
           ├── Storage
           │
           └── Your Applications
                ├── learnk3s
                ├── spring-web
                ├── hello
                └── test


kubectl get all
kubectl get ingress
kubectl get pvc


IoT architecture could eventually look like:

┌──────────────┐
│ Temperature  │
│ Sensor       │
└──────┬───────┘
       │ GPIO/I2C
       ↓
┌──────────────┐
│ Raspberry Pi │
│ Python       │
└──────┬───────┘
       │ MQTT
       ↓
┌──────────────┐
│ MQTT Broker  │
└──────┬───────┘
       │
       ↓
┌────────────────────┐
│ k3s on Raspberry Pi│
│                    │
│ API + Database     │
│ Grafana            │
│ Prometheus         │
└────────────────────┘


