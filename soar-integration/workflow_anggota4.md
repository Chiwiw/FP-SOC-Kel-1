# PERBAIKAN DAN PENAMBAHAN DOKUMENTASI ANGGOTA 4

## Struktur Final VM

### VM-1 : wazuh-manager

IP:

```text
20.198.176.191
```

Service:

```text
Wazuh Manager
Wazuh Dashboard
Wazuh API
Shuffle SOAR
AI Scoring API
```

Folder:

```text
/home/azureuser/soc-project

├── ai-model
│   ├── artifacts
│   ├── src
│   ├── score_alert.py
│   └── app.py
│
├── soar
│   └── Shuffle
│
└── benchmark
```

---

### VM-2 : wazuh-agent-fe

IP:

```text
20.255.63.52
```

Service:

```text
Frontend Application
Wazuh Agent
Playbook Executor
```

Folder:

```text
/home/azureuser/playbooks

└── playbook_actions.sh
```

---

### VM-3 : wazuh-agent-attacker

IP:

```text
20.6.131.20
```

Service:

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

# PERSIAPAN PORT

Sebelum install Shuffle dan AI API:

```bash
sudo ss -tulpn
```

Catat port yang sudah digunakan.

Biasanya:

```text
443     Wazuh Dashboard
55000   Wazuh API
```

Pastikan:

```text
5000
3001
```

belum digunakan.

---

# DEPLOY AI SCORING API

Masuk ke VM Manager:

```bash
ssh azureuser@20.198.176.191
```

---

## Membuat Folder AI

```bash
mkdir -p ~/soc-project/ai-model
```

---

## Upload Artifact

Dari laptop:

```bash
scp -r ai-model \
azureuser@20.198.176.191:/home/azureuser/soc-project/
```

Verifikasi:

```bash
ls ~/soc-project/ai-model/artifacts
```

Harus muncul:

```text
alert_tp_fp_model.joblib
metrics.json
top_features.json
```

---

## Install Dependency

```bash
sudo apt update

sudo apt install python3-pip -y

pip3 install flask pandas scikit-learn joblib
```

---

## Menjalankan API

```bash
cd ~/soc-project/ai-model

python3 app.py
```

Output:

```text
Running on http://0.0.0.0:5000
```

---

## Test API

Health Check:

```bash
curl http://localhost:5000/health
```

Expected:

```json
{
  "status":"ok"
}
```

---

## Test Endpoint Score

```bash
curl -X POST \
http://localhost:5000/score \
-H "Content-Type: application/json" \
-d '{}'
```

Jika model aktif:

```json
{
  "decision":"Manual Review"
}
```

---

# MEMBUAT AI API SEBAGAI SERVICE

Supaya API tidak mati saat logout SSH.

File:

```text
/etc/systemd/system/ai-api.service
```

Isi:

```ini
[Unit]
Description=AI Scoring API

[Service]
User=azureuser
WorkingDirectory=/home/azureuser/soc-project/ai-model
ExecStart=/usr/bin/python3 app.py

Restart=always

[Install]
WantedBy=multi-user.target
```

Aktifkan:

```bash
sudo systemctl daemon-reload

sudo systemctl enable ai-api

sudo systemctl start ai-api
```

Cek:

```bash
sudo systemctl status ai-api
```

---

# DEPLOY SHUFFLE

Masuk ke VM Manager:

```bash
cd ~/soc-project
```

---

## Install Docker

```bash
curl -fsSL https://get.docker.com | sudo bash
```

---

## Install Docker Compose

```bash
sudo apt install docker-compose-plugin -y
```

---

## Clone Shuffle

```bash
mkdir soar

cd soar

git clone https://github.com/Shuffle/Shuffle.git
```

---

## Menentukan Port Shuffle

Edit file:

```bash
cd Shuffle

nano docker-compose.yml
```

Cari:

```yaml
ports:
  - "3001:3001"
```

Jika bentrok:

```yaml
ports:
  - "8080:3001"
```

---

## Menjalankan Shuffle

```bash
docker compose up -d
```

---

## Verifikasi

```bash
docker ps
```

Pastikan container status:

```text
Up
```

---

## Akses Dashboard

Jika menggunakan:

```yaml
3001:3001
```

akses:

```text
http://20.198.176.191:3001
```

Jangan menggunakan:

```text
http://20.198.176.191
```

karena biasanya akan membuka Wazuh Dashboard.

---

# INTEGRASI WAZUH KE SHUFFLE

Masuk:

```text
Shuffle Dashboard
```

---

## Install Wazuh App

```text
Apps
↓
Search
↓
Wazuh
↓
Install
```

---

## Konfigurasi

Host:

```text
https://20.198.176.191:55000
```

Username:

```text
wazuh
```

Password:

```text
********
```

---

## Test Connection

Expected:

```text
Connection Successful
```

---

# MEMBUAT PLAYBOOK EXECUTOR

Masuk ke VM Frontend.

```bash
ssh azureuser@20.255.63.52
```

---

## Folder

```bash
mkdir -p ~/playbooks
```

---

## Upload File

```bash
scp playbook_actions.sh \
azureuser@20.255.63.52:/home/azureuser/playbooks/
```

---

## Permission

```bash
chmod +x ~/playbooks/playbook_actions.sh
```

---

## Test Manual

Block IP:

```bash
./playbook_actions.sh ddos_block 1.1.1.1
```

Lock User:

```bash
./playbook_actions.sh lock_user testuser
```

---

# WORKFLOW SHUFFLE

Workflow:

```text
Alert
↓
HTTP Request
↓
AI API
↓
Decision
↓
SSH Action
```

---

## Node 1

Trigger:

```text
Wazuh Alert
```

---

## Node 2

HTTP Request

URL:

```text
http://20.198.176.191:5000/score
```

Method:

```text
POST
```

Body:

```json
{
  "$exec.alert"
}
```

---

## Node 3

Decision

Rule:

```text
decision == "High Confidence"
```

---

## Node 4

SSH Command

Host:

```text
20.255.63.52
```

Command:

```bash
/home/azureuser/playbooks/playbook_actions.sh ddos_block 20.6.131.20
```

---

# BENCHMARKING

## Sebelum AI

Matikan AI API dan Shuffle.

```text
Wazuh Only
```

Lakukan:

```text
DDoS
Malware
Credential Abuse
```

Catat:

```text
Jumlah Alert
Jumlah False Positive
Waktu Respon
```

Simpan:

```text
benchmark/before_ai.xlsx
```

---

## Sesudah AI

Aktifkan:

```text
AI API
Shuffle
```

Ulangi skenario yang sama.

Catat:

```text
Jumlah Alert Diteruskan
Jumlah False Positive
Waktu Respon
```

Simpan:

```text
benchmark/after_ai.xlsx
```

---

# HASIL YANG DIHARAPKAN

| Metric         | Before | After |
| -------------- | ------ | ----- |
| Total Alert    |        |       |
| False Positive |        |       |
| Precision      |        |       |
| Recall         |        |       |
| F1 Score       |        |       |
| MTTR           |        |       |

Kesimpulan:

1. False Positive berkurang.
2. Alert yang masuk ke analis lebih sedikit.
3. Respon insiden lebih cepat.
4. AI berhasil menjadi filter sebelum SOAR menjalankan playbook.

```
```
