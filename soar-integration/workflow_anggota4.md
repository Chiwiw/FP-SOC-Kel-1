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
```

Tambahan yang akan dipasang:

```text
Shuffle SOAR
AI Scoring Service
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
```

Target:

```text
DDoS
Malware
Login Abuse
```

---

## VM-3 : wazuh-agent-attacker

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

# 3. File yang Diterima dari Anggota 3

## Artifact

```text
ai-model/artifacts/

├── alert_tp_fp_model.joblib
├── metrics.json
└── top_features.json
```

## Script

```text
ai-model/

├── score_alert.py
├── train_model.py
└── src/
```

---

# 4. Struktur Folder Anggota 4

Di VM Manager:

```text
/home/azureuser/soc-project

├── ai-model
│
│   ├── artifacts
│   │
│   │   ├── alert_tp_fp_model.joblib
│   │   ├── metrics.json
│   │   └── top_features.json
│   │
│   ├── score_alert.py
│   ├── app.py
│   └── requirements.txt
│
├── soar
│   └── Shuffle
│
└── benchmark
```

---

# 5. Setup Shuffle SOAR

## Login ke VM Manager

```bash
ssh azureuser@IP_MANAGER
```

---

## Install Docker

```bash
sudo apt update

curl -fsSL https://get.docker.com | sudo bash
```

Verifikasi:

```bash
docker --version
```

---

## Install Docker Compose

```bash
sudo apt install docker-compose-plugin -y
```

---

## Clone Shuffle

```bash
mkdir -p ~/soc-project/soar

cd ~/soc-project/soar

git clone https://github.com/Shuffle/Shuffle.git
```

Masuk:

```bash
cd Shuffle
```

---

## Jalankan Shuffle

```bash
docker compose up -d
```

---

## Verifikasi

```bash
docker ps
```

Pastikan container Shuffle aktif.

---

## Akses Dashboard

```text
http://IP_MANAGER
```

Buat akun administrator.

---

# 6. Integrasi Pipeline AI

Tujuan:

Mengubah model Logistic Regression menjadi REST API yang bisa dipanggil oleh Shuffle.

---

# Install Dependency

Masuk:

```bash
cd ~/soc-project/ai-model
```

Install:

```bash
pip install flask
pip install pandas
pip install joblib
pip install scikit-learn
```

---

# Membuat File app.py

Lokasi:

```text
/home/azureuser/soc-project/ai-model/app.py
```

Fungsi:

```text
Menerima alert JSON Wazuh
↓
Menjalankan score_alert.py
↓
Mengembalikan probabilitas TP
```

---

# Menjalankan API

```bash
cd ~/soc-project/ai-model

python3 app.py
```

Port:

```text
5000
```

Test:

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

# 7. Integrasi Wazuh dan Shuffle

Masuk ke:

```text
Shuffle
```

Install App:

```text
Wazuh
```

Isi:

```text
Host:
https://IP_MANAGER:55000

Username:
wazuh

Password:
*******
```

Test Connection.

Status:

```text
Connected
```

---

# 8. Workflow AI Pipeline

Workflow:

```text
Alert Generated
        ↓
Wazuh
        ↓
Shuffle
        ↓
HTTP Request
        ↓
AI Scoring API
        ↓
Probability TP
        ↓
Decision Node
        ↓
Playbook
```

---

# 9. Threshold AI

Gunakan:

```text
TP Probability >= 0.80
```

Maka:

```text
High Confidence
```

---

```text
0.50 - 0.79
```

Maka:

```text
Manual Review
```

---

```text
< 0.50
```

Maka:

```text
Likely False Positive
```

---

# 10. Playbook DDoS

## Trigger

Rule:

```text
High Traffic
SYN Flood
HTTP Flood
```

---

## Workflow

```text
Alert
 ↓
AI Score
 ↓
>= 0.80
 ↓
Block IP
```

---

## Action

Frontend VM:

```bash
sudo iptables -A INPUT \
-s ATTACKER_IP \
-j DROP
```

---

## Expected Result

```text
Traffic attacker berhenti
```

---

# 11. Playbook Malware

## Trigger

```text
Malware Detection
EICAR Detection
Suspicious File
```

---

## Workflow

```text
Alert
 ↓
AI Score
 ↓
>= 0.80
 ↓
Isolate Host
```

---

## Action

Frontend VM:

```bash
sudo iptables -P INPUT DROP

sudo iptables -P OUTPUT DROP
```

---

## Expected Result

```text
Host terisolasi
```

---

# 12. Playbook Credential Abuse

## Trigger

```text
Multiple Failed Login
Bruteforce Login
Credential Abuse
```

---

## Workflow

```text
Alert
 ↓
AI Score
 ↓
>= 0.80
 ↓
Lock User
```

---

## Action

```bash
sudo passwd -l victim
```

---

## Expected Result

```text
Akun terkunci
```

---

# 13. Pengujian End-to-End

Minta Anggota 1 melakukan ulang:

```text
DDoS Simulation
Malware Simulation
Credential Abuse Simulation
```

Saat:

```text
AI + SOAR aktif
```

---

# 14. Benchmark Sebelum AI

Kondisi:

```text
Wazuh Only
```

Catat:

| Metric         | Value |
| -------------- | ----- |
| Total Alert    |       |
| True Positive  |       |
| False Positive |       |
| Precision      |       |
| Recall         |       |
| MTTR           |       |

---

# 15. Benchmark Sesudah AI

Kondisi:

```text
Wazuh + AI + SOAR
```

Catat:

| Metric         | Value |
| -------------- | ----- |
| Total Alert    |       |
| True Positive  |       |
| False Positive |       |
| Precision      |       |
| Recall         |       |
| MTTR           |       |

---

# 16. Perhitungan

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
----------------------
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

# 17. Output yang Dikumpulkan

## Screenshot

```text
Shuffle Dashboard
Workflow AI
Workflow DDoS
Workflow Malware
Workflow Credential Abuse
AI API Running
Benchmark Results
```

---

## File

```text
workflow-ddos.json
workflow-malware.json
workflow-login-abuse.json

alert_tp_fp_model.joblib

metrics.json

comparison.xlsx
```

---

# 18. Kesimpulan yang Diharapkan

1. False Positive turun signifikan.
2. Precision meningkat.
3. Recall tetap tinggi.
4. Jumlah alert yang perlu ditinjau manusia berkurang.
5. MTTR menurun karena respons otomatis.
6. AI berhasil menjadi lapisan penyaring sebelum SOAR dijalankan.

```
```