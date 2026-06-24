# Reducing SOC False Alarms through Human-AI Collaboration
### Final Project — Security Operations Center (SOC)
**Wazuh v4.7.5 | Microsoft Azure | Logistic Regression | Custom Local SOAR**

---

## Daftar Isi

1. [Latar Belakang](#1-latar-belakang)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Infrastruktur Azure](#3-infrastruktur-azure)
4. [Struktur Repositori](#4-struktur-repositori)
5. [Anggota Tim & Pembagian Tugas](#5-anggota-tim--pembagian-tugas)
6. [Alur Kerja Sistem (End-to-End)](#6-alur-kerja-sistem-end-to-end)
7. [Skenario Serangan](#7-skenario-serangan)
8. [Dataset](#8-dataset)
9. [AI Model](#9-ai-model)
10. [SOAR Integration](#10-soar-integration)
11. [Hasil Benchmark](#11-hasil-benchmark)
12. [Cara Menjalankan Ulang Sistem](#12-cara-menjalankan-ulang-sistem)
13. [Catatan Teknis & Limitations](#13-catatan-teknis--limitations)

---

## 1. Latar Belakang

SOC modern menggunakan pendekatan **"Better Safe Than Sorry"** — sistem deteksi dibuat sangat sensitif agar tidak ada serangan yang lolos (recall tinggi). Konsekuensinya, sebagian besar alert yang dihasilkan adalah **False Positive (FP)**: peringatan yang terlihat seperti ancaman tetapi sebenarnya bukan. Analis SOC menghabiskan waktu besar untuk menyaring alert ini secara manual, memicu kelelahan dan meningkatkan risiko melewatkan serangan nyata.

**Solusi yang dibangun:** Sistem kolaborasi Human-AI yang menempatkan model AI sebagai lapisan filtrasi sebelum alert sampai ke analis manusia. AI mengklasifikasikan setiap alert sebagai True Positive (TP) atau False Positive (FP), lalu SOAR engine menentukan respons otomatis berdasarkan confidence score.

Sistem ini beroperasi di level **Semi-Autonomous (HOtL — Human-on-the-Loop)**:
- Alert dengan confidence tinggi (≥ 0.80) → respons otomatis via SOAR
- Alert dengan confidence menengah (0.50 – 0.79) → ditandai untuk review manual analis
- Alert dengan confidence rendah (< 0.50) → dikategorikan sebagai False Positive, tidak diteruskan

---

## 2. Arsitektur Sistem

### Arsitektur AI-Driven SOAR

```text
                    ┌──────────────────────┐
                    │   Attacker VM        │
                    │  (DDoS Simulation)   │
                    └──────────┬───────────┘
                               │
                               │ HTTP Flood
                               ▼
                    ┌──────────────────────┐
                    │   Frontend VM        │
                    │  NodeJS Web Server   │
                    │  Port 3000           │
                    └──────────┬───────────┘
                               │
                               │ access.log
                               ▼
                    ┌──────────────────────┐
                    │   Wazuh Agent        │
                    │ (Web Server Agent)   │
                    └──────────┬───────────┘
                               │
                               │ Log Forwarding
                               ▼
                    ┌──────────────────────┐
                    │   Wazuh Manager      │
                    │ Detection Engine     │
                    └──────────┬───────────┘
                               │
                               │ local_rules.xml
                               ▼
                    ┌──────────────────────┐
                    │ Custom Rule 100004   │
                    │ HTTP Flood Detection │
                    └──────────┬───────────┘
                               │
                               │ Alert Generated
                               ▼
                    ┌──────────────────────┐
                    │ alerts.json          │
                    │ Wazuh Alert Storage  │
                    └──────────┬───────────┘
                               │
                               │ Real-Time Monitoring
                               ▼
                    ┌──────────────────────┐
                    │ SOAR Engine          │
                    │ soar_engine.py       │
                    └──────────┬───────────┘
                               │
                               │ JSON Alert
                               ▼
                    ┌──────────────────────┐
                    │ AI Scoring API       │
                    │ Flask + RandomForest │
                    └──────────┬───────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
                   ▼                       ▼

       Likely False Positive       High Confidence
                │                        │
                │                        │
                ▼                        ▼

        Manual Review          ┌─────────────────┐
                               │ Playbook Engine │
                               └────────┬────────┘
                                        │
                                        ▼
                            playbook_actions.sh
                                        │
                                        ▼
                             SSH to Frontend VM
                                        │
                                        ▼
                           sudo ufw deny <srcip>
                                        │
                                        ▼
                             Attacker Blocked
`

### Infrastruktur Keseluruhan


```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MICROSOFT AZURE                                   │
│                       Resource Group: SOC-Project                           │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ wazuh-agent-    │  │ wazuh-agent-    │  │ wazuh-agent-   │             │
│  │    attack       │  │    webapp       │  │    victim      │             │
│  │ 20.6.131.20     │  │ 20.255.63.52    │  │ 20.24.81.16   │             │
│  │                 │  │                 │  │                │             │
│  │ [Attack Tools]  │  │ [Target Server] │  │ [Phish Target] │             │
│  │ - Apache Bench  │  │ - Node.js :3000 │  │ - SSH target   │             │
│  │ - GoPhish       │  │ - FIM aktif     │  │ - user corpuser│             │
│  │ - sshpass       │  │ - Wazuh Agent   │  │ - Wazuh Agent  │             │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘             │
│           │                    │                    │                        │
│           └────────────────────┴────────────┬───────┘                        │
│                            Log & Alert (OSSEC)                               │
│                                             │                                │
│                            ┌────────────────▼────────────────┐               │
│                            │         wazuh-manager           │               │
│                            │        20.198.176.191           │               │
│                            │        Standard_B2ls_v2         │               │
│                            │                                 │               │
│                            │  ┌──────────────────────────┐  │               │
│                            │  │     Wazuh Manager        │  │               │
│                            │  │     Wazuh Indexer        │  │               │
│                            │  │     Wazuh Dashboard      │  │               │
│                            │  └────────────┬─────────────┘  │               │
│                            │               │                 │               │
│                            │  ┌────────────▼─────────────┐  │               │
│                            │  │   AI Scoring API         │  │               │
│                            │  │   (Flask :5000)          │  │               │
│                            │  │   alert_tp_fp_model      │  │               │
│                            │  │   .joblib                │  │               │
│                            │  └────────────┬─────────────┘  │               │
│                            │               │                 │               │
│                            │  ┌────────────▼─────────────┐  │               │
│                            │  │   Local SOAR Engine      │  │               │
│                            │  │   (soar_engine.py)       │  │               │
│                            │  └────────────┬─────────────┘  │               │
│                            └───────────────│─────────────────┘               │
└───────────────────────────────────────────│─────────────────────────────────┘
                                            │
                              ┌─────────────▼──────────────┐
                              │      RESPONS OTOMATIS      │
                              │  - Block IP (DDoS)         │
                              │  - Isolate Host (Malware)  │
                              │  - Lock User (SocEng)      │
                              └────────────────────────────┘
```

### Alur Data Per Skenario

```
MALWARE
  webapp-agent: File ditambahkan ke /uploads/
        ↓ FIM realtime (check_all=yes → hitung MD5)
  Wazuh Manager: Rule 554 (file added)
        ↓ Cek MD5 di CDB list malware-hashes
  Rule 100110 menyala → Alert level 12 [TP]   ← hash cocok EICAR
  Rule 554 saja       → Alert level 5  [FP]   ← hash tidak cocok

DDOS
  attack-agent: Apache Bench → ribuan HTTP request ke webapp:3000
        ↓ Node.js server tulis JSON log per request
  Wazuh Agent baca /var/log/webapp/access.log (format: json)
  Rule 100002 (setiap request)   → level 3  [baseline]
  Rule 100003 (≥5 req/20 detik)  → level 8  [TP - flood terdeteksi]
  Rule 100004 (≥20 req/20 detik) → level 12 [TP - severe]
  100002 tanpa 100003/100004     →           [FP - traffic normal]

SOCIAL ENGINEERING
  GoPhish → email phishing → korban submit kredensial di landing page
        ↓ Penyerang pakai kredensial hasil phishing untuk SSH
  Rule 5715 (auth success, jam eksperimen) → [TP - login berhasil pasca-phishing]
  Rule 5760/5710 (auth failed)            → [FP - login gagal biasa]
```

---

## 3. Infrastruktur Azure

| VM | IP Publik | Ukuran | Region | Peran |
|---|---|---|---|---|
| `wazuh-manager` | 20.198.176.191 | Standard_B2ls_v2 | Southeast Asia | Manager + Indexer + Dashboard + AI API + SOAR Engine |
| `wazuh-agent-webapp` | 20.255.63.52 | Standard_B2ats | East Asia | Target webapp, FIM monitoring |
| `wazuh-agent-attack` | 20.6.131.20 | Standard_B2ats | East Asia | Mesin penyerang |
| `wazuh-agent-victim` | 20.24.81.16 | Standard_B2ats | East Asia | Korban phishing |

**Wazuh Version:** v4.7.5  
**OS:** Ubuntu 22.04 LTS  
**Platform:** Microsoft Azure for Students

---

## 4. Struktur Repositori

```
FP-SOC-Kel-1/
├── wazuh-config/
│   ├── local_rules.xml          ← Custom detection rules (DDoS + Malware)
│   ├── ossec.conf-agent.xml     ← Konfigurasi FIM + logcollector (webapp agent)
│   └── malware-hashes           ← CDB List: hash MD5 EICAR test file
│
├── dataset/
│   ├── malware-alerts-final.json    ← Raw alert Wazuh skenario Malware
│   ├── socialeng-alerts-final.json  ← Raw alert Wazuh skenario Social Engineering
│   ├── ddos-alerts-final.json       ← Raw alert Wazuh skenario DDoS
│   ├── malware_labeled.csv          ← Dataset berlabel per skenario
│   ├── socialeng_labeled.csv
│   ├── ddos_labeled.csv
│   ├── final_dataset.csv            ← Dataset gabungan (dipakai training)
│   └── handover_report.json         ← Statistik labeling per skenario
│
├── ai-model/
│   ├── src/
│   │   └── alert_model.py           ← Feature engineering + pipeline definition
│   ├── train_model.py               ← Script training + evaluasi
│   ├── score_alert.py               ← Script scoring alert baru
│   ├── requirements.txt
│   └── artifacts/
│       ├── alert_tp_fp_model.joblib ← Model terlatih (siap pakai)
│       ├── metrics.json             ← Hasil evaluasi model
│       ├── classification_report.json
│       └── top_features.json        ← Fitur paling berpengaruh
│
├── soar-integration/
│   ├── app.py                       ← Flask API wrapper untuk model AI
│   ├── soar_engine.py               ← Engine routing alert → playbook
│   ├── playbook_actions.sh          ← Aksi respons otomatis (bash)
│   └── workflow_anggota4.md         ← Dokumentasi alur kerja SOAR
│
└── docs/
    ├── handover-anggota1-ke-anggota2.md
    ├── handover_anggota2_ke_anggota3.md
    └── handover_anggota3_ke_anggota4.md
```

---

## 5. Anggota Tim & Pembagian Tugas

| Anggota | Peran | Deliverable |
|---|---|---|
| **Evan Christian Nainggolan** | Infrastruktur & Skenario Serangan | 4 VM Azure, 3 skenario serangan, raw dataset JSON, konfigurasi Wazuh |
| **Hanif Mawla Faizi** | Analisis Data & Labeling | `final_dataset.csv`, 3 CSV per skenario, kriteria false alarm |
| **Yasykur Khalis Jati Maulana** | AI/ML Developer | Model terlatih, pipeline scoring, metrics & feature analysis |
| **Rizqi Akbar Sukirman Putra** | SOAR & Integrasi Otomasi | Flask API, SOAR engine, playbook bash, dokumentasi benchmark |

---

## 6. Alur Kerja Sistem (End-to-End)

```
[Serangan Masuk]
       │
       ▼
[Wazuh Agent] ──── monitor log & file ────▶ [Wazuh Manager]
                                                    │
                                         alert.json tersimpan di
                                    /var/ossec/logs/alerts/alerts.json
                                                    │
                                                    ▼
                                        [AI Scoring API - Flask :5000]
                                         app.py memanggil model
                                         alert_tp_fp_model.joblib
                                                    │
                                         ┌──────────▼──────────┐
                                         │  tp_probability     │
                                         │  ≥ 0.80 → High     │
                                         │  0.50-0.79 → Medium│
                                         │  < 0.50 → Low FP   │
                                         └──────────┬──────────┘
                                                    │
                                        [SOAR Engine - soar_engine.py]
                                                    │
                          ┌─────────────────────────┼─────────────────────────┐
                          ▼                         ▼                         ▼
                   High Confidence           Manual Review              Likely FP
                  Auto Response             SOC Analyst               No Action
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         ddos_block  malware_    lock_user
        (iptables)   isolate    (passwd -l)
                    (iptables)
```

---

## 7. Skenario Serangan

### 7.1 Malware Detection

**Tool:** EICAR Standard Antivirus Test File + Wazuh FIM + CDB List Hash Matching  
**Mekanisme:** File Integrity Monitoring dengan `check_all="yes"` menghitung MD5 setiap file. Hash dibandingkan dengan CDB list malware signature.

| File | Isi | Hash MD5 | Rule Menyala | Label |
|---|---|---|---|---|
| `sample_doc_4.txt` s/d `sample_doc_11.txt` | String EICAR | `44d88612fea8a8f36de82e1278abb02f` | 554 + **100110** | **TP** |
| `report_draft_*.txt`, `file_normal_*.txt` | Teks biasa | Hash berbeda | 554 saja | FP |

**Catatan teknis:** File EICAR harus dibuat dengan `echo -n` (tanpa newline) agar hash MD5-nya tepat 68 byte sesuai standar. Penggunaan `echo` biasa menambah 1 byte newline dan menghasilkan hash berbeda yang tidak akan cocok dengan CDB list.

### 7.2 DDoS Detection

**Tool:** Apache Bench (`ab`) → Node.js HTTP server → Wazuh JSON logcollector  
**Mekanisme:** Node.js server menulis JSON log per request ke `/var/log/webapp/access.log`. Wazuh membaca log ini dan menerapkan rule berbasis frekuensi.

| Rule | Level | Kondisi | Label |
|---|---|---|---|
| 100002 | 3 | Setiap request HTTP masuk | Baseline |
| 100003 | 8 | ≥ 5 request dari IP sama dalam 20 detik | **TP** |
| 100004 | 12 | ≥ 20 request dari IP sama dalam 20 detik | **TP** |
| 100002 tanpa 100003/100004 | 3 | Traffic normal di bawah threshold | **FP** |

**Catatan teknis:** `hping3` tidak dapat digunakan karena bekerja di layer 4 (TCP SYN) dan tidak menghasilkan log HTTP. Rule DDoS ini bergantung pada log aplikasi layer 7.

### 7.3 Social Engineering Detection

**Tool:** GoPhish → simulasi phishing → SSH login dengan kredensial hasil phishing  
**Mekanisme:** Wazuh memonitor `/var/log/auth.log` secara default untuk semua aktivitas autentikasi SSH.

| Rule | Level | Kondisi | Label |
|---|---|---|---|
| 5715 | 3 | Login SSH berhasil (jam eksperimen, dari attack-agent) | **TP** |
| 5760 | 5 | Login SSH gagal — password salah | FP |
| 5710 | 5 | Login SSH gagal — username tidak ada | FP |

---

## 8. Dataset

### Statistik Per Skenario

| Skenario | Total Alert | True Positive | False Positive | % TP | % FP |
|---|---|---|---|---|---|
| DDoS | 6.276 | 689 | 5.587 | 10.98% | 89.02% |
| Malware | 8.531 | 8 | 8.523 | 0.09% | 99.91% |
| Social Engineering | 9.347 | 3 | 9.344 | 0.03% | 99.97% |
| **Total Gabungan** | **24.154** | **700** | **23.454** | **2.9%** | **97.1%** |

### Kriteria Labeling

**Malware:**
- TP: `rule.id == "100110"` (hash MD5 cocok dengan CDB list)
- FP: `rule.id == "554"` tanpa pasangan rule 100110

**DDoS:**
- TP: `rule.id in ["100003", "100004"]`
- FP: `rule.id == "100002"` tanpa disertai 100003/100004 dalam window 20 detik

**Social Engineering:**
- TP: `rule.id == "5715"` dari `agent.name == "attack-agent"` pada rentang waktu eksperimen
- FP: `rule.id in ["5760", "5710", "5503"]`

### Ketidakseimbangan Kelas

Dataset sangat imbalanced (97.1% FP vs 2.9% TP) — ini representatif dari kondisi SOC nyata. Model AI mengatasi ini dengan parameter `class_weight="balanced"` pada LogisticRegression.

---

## 9. AI Model

### Algoritma

**Logistic Regression** dengan feature engineering kustom. Dipilih karena:
- Ringan dan cepat dilatih untuk dataset tabular skala kecil-menengah
- Koefisien model dapat dijelaskan (interpretable) — penting untuk kepercayaan SOC analyst
- Tidak memerlukan GPU atau infrastruktur komputasi berat
- Tidak menggunakan API pihak ketiga (sesuai spesifikasi tugas)

### Pipeline

```
Raw Wazuh Alert (JSON)
       │
       ▼
[AlertFeatureBuilder]
  Ekstrak 30+ fitur dari alert:
  - Numerik: rule.level, jam kejadian, panjang log, frekuensi IP, keyword flags
  - Kategorikal: rule.id, agent.name, decoder.name, syscheck.event
  - Teks: rule.groups (CountVectorizer binary)
       │
       ▼
[ColumnTransformer]
  - Numerik → StandardScaler (setelah SimpleImputer median)
  - Kategorikal → OneHotEncoder (handle_unknown=ignore)
  - Groups → CountVectorizer binary
       │
       ▼
[LogisticRegression]
  max_iter=2000, class_weight="balanced", solver="liblinear"
       │
       ▼
  tp_probability (0.0 – 1.0) + prediction (0 atau 1)
```

### Fitur Paling Berpengaruh

**Mendorong prediksi TP (True Positive):**

| Fitur | Bobot | Interpretasi |
|---|---|---|
| `groups__http_flood` | +1.643 | Alert dari grup DDoS |
| `groups__ddos` | +1.643 | Alert berlabel DDoS |
| `rule.id_100003` | +1.642 | Rule HTTP Flood aktif |
| `rule.level` | +1.507 | Level alert tinggi |
| `has_http_keyword` | +0.964 | Log mengandung kata kunci HTTP |
| `rule.id_5715` | +0.480 | Auth success terdeteksi |

**Mendorong prediksi FP (False Positive):**

| Fitur | Bobot | Interpretasi |
|---|---|---|
| `syscheck.event_missing` | -1.673 | Alert tanpa event FIM (bukan file) |
| `groups__syslog` | -1.670 | Alert dari syslog biasa |
| `rule.id_100002` | -1.562 | HTTP request biasa (di bawah threshold) |
| `agent.name_wazuh-manager` | -1.385 | Alert dari manager sendiri (noise) |
| `groups__authentication_failures` | -0.921 | Login gagal berulang (brute force organik) |

### Hasil Evaluasi (Test Set — 20% dari 24.154 data)

| Metrik | Nilai |
|---|---|
| **Accuracy** | **99.98%** |
| **Precision** | **99.29%** |
| **Recall** | **100.00%** |
| **F1-Score** | **99.64%** |

**Confusion Matrix (test set: 4.831 baris):**

```
                  Predicted FP    Predicted TP
Actual FP  (TN)      4690             1         ← 1 FP lolos sebagai TP
Actual TP  (FN)         0           140         ← 0 TP terlewat
```

**Interpretasi:** Model tidak pernah melewatkan serangan nyata (Recall = 100%), dan hanya 1 dari 4.691 FP yang salah diklasifikasi sebagai TP.

---

## 10. SOAR Integration

### Arsitektur Local SOAR

Implementasi menggunakan **Local SOAR Engine berbasis Python**, bukan platform SOAR eksternal (Shuffle/TheHive). Keputusan ini diambil karena keterbatasan RAM VM Azure Student (3.8GB) yang tidak cukup untuk menjalankan Shuffle (Docker dengan 5+ container) bersamaan dengan Wazuh Indexer.

### Komponen

**1. AI Scoring API (`app.py` — Flask :5000)**

Menerima alert Wazuh dalam format JSON via POST `/score`, mengembalikan:
```json
{
  "tp_probability": 0.95,
  "prediction": 1,
  "decision": "High Confidence"
}
```

Endpoint tambahan:
- `GET /health` → status check

**2. SOAR Engine (`soar_engine.py`)**

Membaca alert → kirim ke AI API → routing berdasarkan decision:

```
decision = "High Confidence" (prob ≥ 0.80)
    └── rule 100003/100004 → ddos_block (iptables DROP source IP)
    └── rule 100110        → malware_isolate (iptables DROP semua traffic)
    └── rule 5715          → lock_user (passwd -l <username>)

decision = "Manual Review" (prob 0.50-0.79)
    └── Log untuk review analis, tidak ada aksi otomatis

decision = "Likely False Positive" (prob < 0.50)
    └── Tidak ada aksi
```

**3. Playbook Actions (`playbook_actions.sh`)**

```bash
# Blokir IP penyerang DDoS
./playbook_actions.sh ddos_block <ATTACKER_IP>
# → sudo iptables -A INPUT -s <IP> -j DROP

# Isolasi host terinfeksi malware
./playbook_actions.sh malware_isolate host
# → iptables DROP semua koneksi kecuali SSH

# Kunci user akibat credential abuse
./playbook_actions.sh lock_user <USERNAME>
# → sudo passwd -l <USERNAME>
```

### Threshold Decision

| Probabilitas AI | Keputusan | Tindakan |
|---|---|---|
| ≥ 0.80 | High Confidence | Respons otomatis via playbook |
| 0.50 – 0.79 | Manual Review | Ditandai untuk analis SOC |
| < 0.50 | Likely False Positive | Tidak ada tindakan |

---

## 11. Hasil Benchmark & Evaluasi

### Tabel 1. Perbandingan Performa Deteksi
| Metric | Wazuh Only | AI + SOAR |
|---|---:|---:|
| Total Alert | 24,154 | 24,154 |
| True Positive (TP) | 700 | 700 |
| False Positive (FP) | 23,454 | ~5 |
| False Negative (FN) | 0 | 0 |
| Accuracy | N/A | 99.98% |
| Precision | 2.90% | 99.29% |
| Recall | 100% | 100% |
| F1-Score | 5.64% | 99.64% |

### Tabel 2. Perbandingan Beban Kerja Analis
| Parameter | Sebelum AI | Sesudah AI |
|---|---:|---:|
| Total Alert Masuk | 24,154 | 24,154 |
| Alert yang Harus Dicek Manual | 24,154 | ~705 |
| Alert Noise (False Positive) | 23,454 | ~5 |
| Persentase Noise | 97.10% | 0.71% |
| Pengurangan Beban Kerja | - | 97.08% |

*(Estimasi alert yang perlu diperiksa analis: 700 TP + 5 FP ≈ 705 alert)*

### Tabel 3. Hasil Evaluasi Model AI
| Metric | Nilai |
|---|---:|
| Accuracy | 99.98% |
| Precision | 99.29% |
| Recall | 100% |
| F1-Score | 99.64% |
| False Positive yang Lolos | 1 dari 4,691 |
| False Negative | 0 dari 140 |
| False Positive Reduction | 99.98% |

### Tabel 4. Benchmark Sistem AI + SOAR
![Benchmark Sistem](img/benchmark.png)

| Parameter | Nilai |
|---|---:|
| Rata-rata AI Inference Time | 31 ms |
| Rata-rata Keputusan AI | 0.031 detik |
| Rata-rata Eksekusi Playbook | 7 - 10 detik |
| Rata-rata End-to-End Response| 8.5 detik |
| Mitigasi | Otomatis |

### Tabel 5. Contoh Benchmark Aktual
![SOAR and Benchmark](img/SOARnBenchmark.png)

| Alert ID | Rule ID | Decision | AI Time (s) | Total Time (s) |
|---|---|---|---:|---:|
| 1782298969.12582573 | 5503 | Likely False Positive | 0.0321 | 0.0322 |
| 1782298975.12584277 | 5503 | Likely False Positive | 0.0312 | 0.0313 |
| 1782299015.12585368 | 5503 | Likely False Positive | 0.0315 | 0.0316 |
| 1782299017.12587002 | 5503 | Likely False Positive | 0.0324 | 0.0324 |
| 1782299017.12596892 | 100004 | High Confidence | 0.0301 | 9.5042 |
| 1782299138.13368896 | 100004 | High Confidence | 0.0322 | 7.4205 |

### Tabel 6. Ringkasan Hasil Penelitian
| Aspek | Wazuh Only | AI + SOAR |
|---|---|---|
| Deteksi Serangan | Ya | Ya |
| Penyaringan False Positive | Tidak | Ya |
| Precision | 2.90% | 99.29% |
| Recall | 100% | 100% |
| F1-Score | 5.64% | 99.64% |
| Mitigasi Otomatis | Tidak | Ya |
| Waktu Respons | Bergantung Analis | ± 8.5 detik |
| Alert ke Analis | 24,154 | ~705 |
| False Positive Reduction | 0% | 99.98% |
| Beban Kerja Analis | Sangat Tinggi | Rendah |

### Kesimpulan
Implementasi AI dan SOAR berhasil meningkatkan precision deteksi dari 2.90% menjadi 99.29% tanpa menurunkan recall yang tetap berada pada 100%. Model mampu mengurangi false positive sebesar 99.98%, sehingga jumlah alert yang harus dianalisis secara manual berkurang dari 24,154 alert menjadi sekitar 705 alert. Selain itu, sistem SOAR mampu melakukan mitigasi otomatis dengan rata-rata waktu respons end-to-end sebesar 8.5 detik sejak alert diterima hingga playbook dijalankan.

---

## 12. Cara Menjalankan Ulang Sistem

### Prerequisites

- Akses SSH ke keempat VM Azure
- Python 3.10+
- Wazuh v4.7.5 terinstall dan berjalan

### Step 1 — Start VM di Azure Portal

Start keempat VM dari Azure Portal:
- `wazuh-manager`, `wazuh-agent-webapp`, `wazuh-agent-attack`, `wazuh-agent-victim`

### Step 2 — Kloning Repo di VM Manager

```bash
ssh azureuser@20.198.176.191
git clone https://github.com/<repo-url>/FP-SOC-Kel-1.git
cd FP-SOC-Kel-1
```

### Step 3 — Install Dependencies AI

```bash
cd ai-model
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4 — Jalankan AI Scoring API

```bash
# Masih di dalam venv
python app.py &
# Verifikasi
curl http://localhost:5000/health
```

### Step 5 — Training Ulang Model (Opsional)

```bash
python train_model.py --data ../dataset/final_dataset.csv
# Model baru tersimpan di artifacts/
```

### Step 6 — Test Scoring Alert Baru

```bash
# Score dari file JSON Wazuh langsung
python score_alert.py \
  --model artifacts/alert_tp_fp_model.joblib \
  --input ../dataset/ddos-alerts-final.json
```

### Step 7 — Jalankan SOAR Engine

```bash
cd ../soar-integration
python soar_engine.py
```

### Step 8 — Setup Wazuh Config (Jika VM baru/reset)

```bash
# Copy custom rules ke Manager
sudo cp ../wazuh-config/local_rules.xml /var/ossec/etc/rules/local_rules.xml
sudo cp ../wazuh-config/malware-hashes /var/ossec/etc/lists/malware-hashes

# Di webapp agent:
ssh azureuser@20.255.63.52
sudo cp ossec.conf-agent.xml /var/ossec/etc/ossec.conf
sudo systemctl restart wazuh-agent
```

---

## 13. Catatan Teknis & Limitations

### Keterbatasan yang Diakui

**1. Malware — Label Leakage Awal (Sudah Diselesaikan)**
Tiga file pertama (sample_doc_1/2/3) tidak terdeteksi karena perintah `echo` tanpa flag `-n` menambahkan 1 byte newline, menghasilkan hash MD5 berbeda dari EICAR standar. File-file ini dikecualikan dari dataset. Ini mendokumentasikan sifat exact-match dari deteksi berbasis hash.

**2. DDoS — Layer 4 vs Layer 7**
`hping3` (TCP SYN flood, layer 4) tidak dapat dideteksi oleh pipeline ini karena rule DDoS bergantung pada log aplikasi HTTP (layer 7). Wazuh secara native tidak mendeteksi DDoS layer 4 tanpa integrasi netflow atau iptables logging tambahan.

**3. Social Engineering — Volume TP Sangat Kecil**
Hanya 3 TP dari 9.347 total alert social engineering (0.03%). Sebagian besar alert SSH (5710, 5503) berasal dari brute force otomatis internet yang tidak terkontrol, bukan dari eksperimen. Volume TP yang kecil ini membatasi kemampuan model untuk belajar pola social engineering secara spesifik.

**4. SOAR — Local Implementation**
Shuffle SOAR gagal dijalankan di VM Manager (RAM 3.8GB tidak cukup untuk 5+ Docker container bersamaan dengan Wazuh Indexer). Implementasi beralih ke Local SOAR Engine berbasis Python, yang lebih ringan tapi lebih terbatas dalam hal workflow management dan audit trail.

**5. Potensi Overfitting pada Test Set**
Metrik model sangat tinggi (99.98% accuracy) sebagian karena dataset berasal dari lingkungan yang sama dengan yang dipakai training. Generalisasi ke environment SOC yang berbeda perlu divalidasi lebih lanjut.

### Wazuh Custom Rules

```xml
<!-- DDoS Detection -->
<rule id="100002" level="3">
  <decoded_as>json</decoded_as>
  <description>NodeJS HTTP Request</description>
</rule>

<rule id="100003" level="8" frequency="5" timeframe="20">
  <if_matched_sid>100002</if_matched_sid>
  <same_srcip />
  <description>Possible HTTP Flood Activity</description>
</rule>

<rule id="100004" level="12" frequency="20" timeframe="20" ignore="60">
  <if_matched_sid>100002</if_matched_sid>
  <same_srcip />
  <description>Severe HTTP Flood / DDoS attack detected</description>
</rule>

<!-- Malware Detection -->
<rule id="100110" level="12">
  <if_sid>554, 550</if_sid>
  <list field="md5" lookup="match_key">etc/lists/malware-hashes</list>
  <description>File dengan hash dikenal sebagai malware terdeteksi</description>
</rule>
```

### Referensi

- [Wazuh Documentation v4.7](https://documentation.wazuh.com/4.7/)
- [Wazuh CDB Lists](https://documentation.wazuh.com/4.7/user-manual/ruleset/cdb-list.html)
- [Scikit-learn LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
- [EICAR Test File Standard](https://www.eicar.org/download-anti-malware-testfile/)
- [GoPhish Documentation](https://docs.getgophish.com/)

---

*Final Project — Security Operations Center | Wazuh v4.7.5 | Azure Student Subscription*
