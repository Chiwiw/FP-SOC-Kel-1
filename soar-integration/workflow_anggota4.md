# ANGGOTA 4

# SOAR Integration, AI Pipeline, Playbook Response, dan Benchmarking

## Project

Reducing SOC False Alarms Through Human-AI Collaboration

---

# 1. Tujuan Anggota 4

Mengintegrasikan model Machine Learning hasil pekerjaan Anggota 3 ke dalam sistem SOAR sehingga:

1. Alert Wazuh dianalisis terlebih dahulu oleh AI.
2. Alert dengan probabilitas True Positive tinggi diteruskan ke workflow respons.
3. Alert dengan probabilitas False Positive tinggi diturunkan prioritasnya.
4. Workflow respons dapat berjalan otomatis.
5. Performa sebelum dan sesudah AI dapat dibandingkan.

---

# 2. Infrastruktur

## VM-1 : wazuh-manager

Fungsi:

```text
Wazuh Manager
Wazuh Dashboard
Wazuh API
AI Scoring API
Local SOAR Engine
```

IP:

```text
IP_MANAGER
```

Direktori kerja:

```text
/home/azureuser/soc-project
```

---

## VM-2 : wazuh-agent-fe

Fungsi:

```text
Frontend Application
Wazuh Agent
Target Response
```

IP:

```text
IP_FRONTEND
```

Direktori:

```text
/home/azureuser/playbooks
```

---

## VM-3 : wazuh-agent-attack

Fungsi:

```text
Attack Simulation
```

Tools:

```text
hping3
curl
GoPhish
```

---

# 3. Struktur Folder

## VM Manager

```text
/home/azureuser/soc-project

├── ai-model
│
│   ├── app.py
│   ├── score_alert.py
│   │
│   ├── artifacts
│   │   ├── alert_tp_fp_model.joblib
│   │   ├── metrics.json
│   │   └── top_features.json
│   │
│   └── src
│
├── local-soar
│
│   ├── soar_engine.py
│   ├── config.json
│   ├── sample_alert.json
│   └── logs
│
└── benchmark
```

---

## VM Frontend

```text
/home/azureuser/playbooks

└── playbook_actions.sh
```

---

# 4. Setup AI Scoring API

Lokasi:

```text
VM-1 (wazuh-manager)
```

Masuk:

```bash
ssh azureuser@IP_MANAGER
```

---

## Masuk Folder AI

```bash
cd ~/soc-project/ai-model
```

---

## Membuat Virtual Environment

```bash
python3 -m venv venv
```

Aktifkan:

```bash
source venv/bin/activate
```

---

## Install Dependency

```bash
pip install flask
pip install pandas
pip install joblib
pip install scikit-learn
```

atau:

```bash
pip install -r requirements.txt
```

---

## Menjalankan API

```bash
python app.py
```

Port:

```text
5000
```

---

## Test API

```bash
curl http://localhost:5000/health
```

Output:

```json
{
  "status":"ok"
}
```

---

# 5. Menjadikan AI API Sebagai Service

File:

```text
/etc/systemd/system/ai-api.service
```

Isi:

```ini
[Unit]
Description=AI Scoring API
After=network.target

[Service]
User=azureuser
WorkingDirectory=/home/azureuser/soc-project/ai-model

ExecStart=/home/azureuser/soc-project/ai-model/venv/bin/python /home/azureuser/soc-project/ai-model/app.py

Restart=always

[Install]
WantedBy=multi-user.target
```

---

Reload:

```bash
sudo systemctl daemon-reload
```

Enable:

```bash
sudo systemctl enable ai-api
```

Start:

```bash
sudo systemctl start ai-api
```

Cek:

```bash
sudo systemctl status ai-api
```

---

# 6. Setup Local SOAR Engine

Lokasi:

```text
VM-1 (wazuh-manager)
```

---

## Membuat Folder

```bash
mkdir -p ~/soc-project/local-soar
```

Masuk:

```bash
cd ~/soc-project/local-soar
```

---

## File Config

Lokasi:

```text
/home/azureuser/soc-project/local-soar/config.json
```

Isi:

```json
{
    "frontend_vm":"IP_FRONTEND",
    "frontend_user":"azureuser",
    "playbook_path":"/home/azureuser/playbooks/playbook_actions.sh"
}
```

---

# 7. Setup SSH Tanpa Password

Dilakukan dari:

```text
VM Manager
```

Generate:

```bash
ssh-keygen
```

Enter semua.

---

Copy key:

```bash
ssh-copy-id azureuser@IP_FRONTEND
```

---

Test:

```bash
ssh azureuser@IP_FRONTEND
```

Jika tidak meminta password berarti berhasil.

---

# 8. Membuat Playbook Response

Lokasi:

```text
VM Frontend
```

Folder:

```bash
mkdir -p ~/playbooks
```

File:

```text
/home/azureuser/playbooks/playbook_actions.sh
```

Isi:

```bash
#!/bin/bash

ACTION=$1
TARGET=$2

case "$ACTION" in

ddos_block)

sudo iptables -A INPUT -s "$TARGET" -j DROP
;;

malware_isolate)

sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT

sudo iptables -P INPUT DROP
sudo iptables -P OUTPUT DROP
;;

lock_user)

sudo passwd -l "$TARGET"
;;

esac
```

Permission:

```bash
chmod +x ~/playbooks/playbook_actions.sh
```

---

# 9. Membuat SOAR Engine

Lokasi:

```text
VM Manager
```

File:

```text
/home/azureuser/soc-project/local-soar/soar_engine.py
```

Fungsi:

```text
Menerima Alert
↓
Kirim ke AI API
↓
Menerima Probabilitas
↓
Menentukan Response
↓
Menjalankan Playbook
```

---

# Workflow

```text
Wazuh Alert
      ↓
AI API
      ↓
Decision Engine
      ↓
Playbook
      ↓
Response
```

---

# 10. Threshold AI

## High Confidence

```text
Probability >= 0.80
```

Action:

```text
Auto Response
```

---

## Manual Review

```text
0.50 - 0.79
```

Action:

```text
SOC Analyst Review
```

---

## Likely False Positive

```text
< 0.50
```

Action:

```text
No Automatic Action
```

---

# 11. Mapping Alert ke Response

| Alert | Response |
|---------|---------|
| DDoS | Block Source IP |
| Malware | Isolate Host |
| Brute Force | Lock User |

---

# 12. DDoS Playbook

## Simulasi

VM Attacker:

```bash
sudo hping3 -S -p 80 --flood IP_FRONTEND
```

---

Response:

```bash
iptables -A INPUT -s ATTACKER_IP -j DROP
```

---

Verifikasi:

```bash
sudo iptables -L
```

---

# 13. Malware Playbook

Simulasi:

```bash
curl -O https://secure.eicar.org/eicar.com.txt
```

---

Response:

```bash
iptables -P INPUT DROP
iptables -P OUTPUT DROP
```

---

Verifikasi:

```bash
ping google.com
```

Harus gagal.

---

# 14. Credential Abuse Playbook

Simulasi:

```bash
hydra
```

atau

```bash
multiple ssh login failure
```

---

Response:

```bash
passwd -l victim
```

---

Verifikasi:

```bash
sudo passwd -S victim
```

---

# 15. Integrasi dengan Wazuh

Metode paling sederhana:

```text
Wazuh Alert JSON
↓
Export Alert
↓
SOAR Engine
↓
AI API
↓
Response
```

Alert yang diterima Wazuh akan diproses oleh:

```text
/home/azureuser/soc-project/local-soar/soar_engine.py
```

---

# 16. Benchmark Sebelum AI

Kondisi:

```text
Wazuh Only
```

Catat:

| Metric | Value |
|----------|----------|
| Total Alert | |
| True Positive | |
| False Positive | |
| Precision | |
| Recall | |
| F1 Score | |
| MTTR | |

---

# 17. Benchmark Sesudah AI

Kondisi:

```text
Wazuh + AI + Local SOAR
```

Catat:

| Metric | Value |
|----------|----------|
| Total Alert | |
| True Positive | |
| False Positive | |
| Precision | |
| Recall | |
| F1 Score | |
| MTTR | |

---

# 18. Rumus

## Precision

```text
TP / (TP + FP)
```

---

## Recall

```text
TP / (TP + FN)
```

---

## F1 Score

```text
2 × Precision × Recall
-----------------------
Precision + Recall
```

---

## MTTR

```text
Total Response Time
-------------------
Jumlah Insiden
```

---

# 19. Output yang Dikumpulkan

Screenshot:

```text
AI API Running
SOAR Engine Running
DDoS Response
Malware Response
Credential Abuse Response
Benchmark Result
```

---

File:

```text
app.py
soar_engine.py
playbook_actions.sh

alert_tp_fp_model.joblib
metrics.json

benchmark.xlsx
```

---

# 20. Kesimpulan

1. False Positive berhasil dikurangi menggunakan AI Classifier.
2. Precision meningkat setelah filtering AI.
3. Jumlah alert yang masuk ke analyst berkurang.
4. MTTR menurun karena response otomatis.
5. Sistem SOAR berhasil diimplementasikan menggunakan Local SOAR Engine berbasis Python tanpa memerlukan platform SOAR eksternal.
6. Arsitektur lebih ringan dan sesuai dengan resource VM yang tersedia.