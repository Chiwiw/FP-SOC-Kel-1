# Handover Anggota 1 → Anggota 2 dan Seterusnya
## Proyek: Reducing SOC False Alarms through Human-AI Collaboration
**Wazuh v4.7.5 | Microsoft Azure | Resource Group: SOC-Project**

---

## Daftar Isi

1. [Ringkasan Proyek](#1-ringkasan-proyek)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Infrastruktur — Spesifikasi VM](#3-infrastruktur--spesifikasi-vm)
4. [Konfigurasi Wazuh — Rules dan Mekanisme Deteksi](#4-konfigurasi-wazuh--rules-dan-mekanisme-deteksi)
5. [Apa yang Telah Dikerjakan Anggota 1](#5-apa-yang-telah-dikerjakan-anggota-1)
6. [Hasil Dataset Per Skenario](#6-hasil-dataset-per-skenario)
7. [Panduan Labeling untuk Anggota 2](#7-panduan-labeling-untuk-anggota-2)
8. [File yang Diserahkan](#8-file-yang-diserahkan)
9. [Catatan Teknis Penting untuk Laporan](#9-catatan-teknis-penting-untuk-laporan)

---

## 1. Ringkasan Proyek

Tugas ini membangun sistem SOC berbasis Human-AI Collaboration yang mampu **mengurangi false alarm tanpa mengorbankan akurasi deteksi**. Secara konseptual, sistem ini beroperasi di level **Semi-Autonomous (Level 2 / HOtL — Human-on-the-Loop)**:

- **AI** bertugas memproses alert Wazuh secara masif, mengklasifikasikan setiap alert sebagai True Positive (TP) atau False Positive (FP), dan meneruskan hasilnya ke SOAR bila confidence tinggi.
- **Manusia** tetap memegang keputusan akhir, terutama untuk alert dengan confidence rendah atau ambiguous.

Pekerjaan Anggota 1 adalah menyediakan seluruh **infrastruktur dan data mentah** yang menjadi fondasi seluruh proyek ini.

---

## 2. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MICROSOFT AZURE                                  │
│                     Resource Group: SOC-Project                         │
│                        Region: East Asia & SE Asia                      │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  wazuh-agent-    │    │  wazuh-agent-    │    │  wazuh-agent-   │  │
│  │     attack       │    │     webapp       │    │     victim      │  │
│  │  20.6.131.20     │    │  20.255.63.52    │    │  20.24.81.16   │  │
│  │  Standard_B2ats  │    │  Standard_B2ats  │    │  Standard_B2ats│  │
│  │                  │    │                  │    │                 │  │
│  │ [Tool Serangan]  │    │ [Target Webapp]  │    │ [Korban Phish] │  │
│  │ - hping3         │    │ - Node.js HTTP   │    │ - SSH target   │  │
│  │ - Apache Bench   │    │   server:3000    │    │ - user corpuser│  │
│  │ - sshpass        │    │ - Wazuh Agent    │    │ - Wazuh Agent  │  │
│  │ - GoPhish        │    │ - FIM aktif di   │    │                 │  │
│  │ - Wazuh Agent    │    │   /uploads       │    │                 │  │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬────────┘  │
│           │                       │                        │            │
│           │  Log & Alert (OSSEC)  │                        │            │
│           └───────────────────────┴────────────┬───────────┘            │
│                                                 │                        │
│                                    ┌────────────▼────────────┐          │
│                                    │     wazuh-manager       │          │
│                                    │    20.198.176.191       │          │
│                                    │    Standard_B2ls_v2     │          │
│                                    │    Region: SE Asia      │          │
│                                    │                         │          │
│                                    │  ┌─────────────────┐   │          │
│                                    │  │  Wazuh Manager  │   │          │
│                                    │  │  Wazuh Indexer  │   │          │
│                                    │  │  Wazuh Dashboard│   │          │
│                                    │  │  (OpenSearch)   │   │          │
│                                    │  └────────┬────────┘   │          │
│                                    │           │             │          │
│                                    │  ┌────────▼────────┐   │          │
│                                    │  │   alerts.json   │   │          │
│                                    │  │ /var/ossec/logs │   │          │
│                                    │  │ /alerts/        │   │          │
│                                    │  └─────────────────┘   │          │
│                                    └────────────┬────────────┘          │
└─────────────────────────────────────────────────│───────────────────────┘
                                                  │
                          ┌───────────────────────▼───────────────────────┐
                          │              PIPELINE SELANJUTNYA             │
                          │                                               │
                          │  [Anggota 2]        [Anggota 3]              │
                          │  Labeling &    →    AI/ML Model   →  SOAR    │
                          │  Dataset Final      Training           [A4]  │
                          └───────────────────────────────────────────────┘
```

### Alur Data Lengkap Per Skenario

```
SKENARIO MALWARE
─────────────────
wazuh-agent-webapp
  │
  ├─ File EICAR ditambahkan ke /home/azureuser/uploads/
  │  (FIM realtime monitoring aktif via check_all="yes")
  │
  ├─ Wazuh Agent menghitung MD5 → kirim ke Manager
  │
  └─ Wazuh Manager:
       ├─ Rule 554  → "File added to the system" (level 5)
       └─ Rule 100110 → Cek MD5 di CDB List malware-hashes
            ├─ COCOK (EICAR) → Alert level 12 "Malware terdeteksi" [TP]
            └─ TIDAK COCOK  → Hanya rule 554 saja [FP]

SKENARIO DDoS
──────────────
wazuh-agent-attack
  │
  ├─ Apache Bench → kirim ribuan HTTP request ke webapp:3000
  │
wazuh-agent-webapp (Node.js server)
  │
  ├─ Tiap request → tulis JSON log ke /var/log/webapp/access.log
  │
  └─ Wazuh Agent baca log (logcollector format json)
       └─ Wazuh Manager:
            ├─ Rule 100002 → "NodeJS HTTP Request" (level 3) [setiap request]
            ├─ Rule 100003 → "Possible HTTP Flood" (level 8)  [≥5 req/20 detik dari IP sama]
            └─ Rule 100004 → "Severe HTTP Flood"  (level 12) [≥20 req/20 detik dari IP sama]
                 └─ 100002 saja (tanpa 100003/100004) = traffic normal [FP]
                    100003 atau 100004 menyala = DDoS terdeteksi [TP]

SKENARIO SOCIAL ENGINEERING
─────────────────────────────
GoPhish (di wazuh-agent-attack)
  │
  ├─ Kirim email phishing via Mailtrap → target membuka link & submit kredensial
  │
  └─ Simulasi pemakaian kredensial hasil phishing:
       sshpass → SSH login ke wazuh-agent-attack
         │
         └─ Wazuh Agent monitor /var/log/auth.log
              └─ Wazuh Manager:
                   ├─ Rule 5715 → "authentication success" (level 3) [TP]
                   ├─ Rule 5760 → "authentication failed" (level 5)  [FP kandidat]
                   └─ Rule 5710 → "non-existent user" (level 5)      [FP kandidat]
```

---

## 3. Infrastruktur — Spesifikasi VM

| VM Name | IP Publik | Ukuran | Region | OS | Peran |
|---|---|---|---|---|---|
| `wazuh-manager` | 20.198.176.191 | Standard_B2ls_v2 | Southeast Asia | Linux (Ubuntu) | Manager + Indexer + Dashboard |
| `wazuh-agent-webapp` | 20.255.63.52 | Standard_B2ats | East Asia | Linux (Ubuntu) | Target webapp + FIM malware |
| `wazuh-agent-attack` | 20.6.131.20 | Standard_B2ats | East Asia | Linux (Ubuntu) | Mesin penyerang (DDoS + Social Eng) |
| `wazuh-agent-victim` | 20.24.81.16 | Standard_B2ats | East Asia | Linux (Ubuntu) | Korban phishing |

**Wazuh Version:** v4.7.5
**Penyimpanan alert:** `/var/ossec/logs/alerts/alerts.json` (di Manager)

---

## 4. Konfigurasi Wazuh — Rules dan Mekanisme Deteksi

### 4.1 Custom Rules (`/var/ossec/etc/rules/local_rules.xml`)

```xml
<!-- Social Engineering: SSH ke IP spesifik -->
<group name="local,syslog,sshd,">
  <rule id="100001" level="5">
    <if_sid>5716</if_sid>
    <srcip>1.1.1.1</srcip>
    <description>sshd: authentication failed from IP 1.1.1.1.</description>
    <group>authentication_failed,pci_dss_10.2.4,pci_dss_10.2.5,</group>
  </rule>
</group>

<!-- DDoS Detection via NodeJS HTTP Log -->
<group name="nodejs,web,ddos">
  <rule id="100002" level="3">
    <decoded_as>json</decoded_as>
    <description>NodeJS HTTP Request</description>
    <group>nodejs,http,web</group>
  </rule>

  <rule id="100003" level="8" frequency="5" timeframe="20">
    <if_matched_sid>100002</if_matched_sid>
    <same_srcip />
    <description>Possible HTTP Flood Activity</description>
    <group>ddos,http_flood</group>
  </rule>

  <rule id="100004" level="12" frequency="20" timeframe="20" ignore="60">
    <if_matched_sid>100002</if_matched_sid>
    <same_srcip />
    <description>Severe HTTP Flood / DDoS attack detected</description>
    <group>ddos,http_flood,severe</group>
  </rule>
</group>

<!-- Malware: Hash-based Detection -->
<group name="local,malware,">
  <rule id="100110" level="12">
    <if_sid>554, 550</if_sid>
    <list field="md5" lookup="match_key">etc/lists/malware-hashes</list>
    <description>File dengan hash dikenal sebagai malware terdeteksi: $(file)</description>
  </rule>
</group>
```

### 4.2 CDB List Malware Hash (`/var/ossec/etc/lists/malware-hashes`)

```
44d88612fea8a8f36de82e1278abb02f:eicar-test-file
```

Hash ini adalah MD5 resmi dari EICAR Standard Antivirus Test File. File apapun dengan hash ini akan memicu rule 100110 level 12.

**Catatan kritis:** Hash ini hanya cocok jika file EICAR dibuat menggunakan `echo -n` (tanpa newline). Penggunaan `echo` biasa (tanpa `-n`) menambahkan satu byte newline yang menghasilkan hash berbeda (`69630e4574ec6798239b091cda43dca0`) dan tidak akan terdeteksi. Tiga percobaan pertama (sample_doc_1, 2, 3) mengalami masalah ini dan dikecualikan dari dataset.

### 4.3 Konfigurasi FIM di `wazuh-agent-webapp`

Lokasi: `/var/ossec/etc/ossec.conf`

```xml
<syscheck>
  <directories check_all="yes" realtime="yes">/home/azureuser/uploads</directories>
</syscheck>
```

`check_all="yes"` wajib ada agar Wazuh menghitung checksum MD5/SHA1/SHA256 dari setiap file — tanpa ini, rule 100110 tidak bisa membandingkan hash.

### 4.4 Konfigurasi Logcollector DDoS di `wazuh-agent-webapp`

Lokasi: `/var/ossec/etc/ossec.conf`

```xml
<localfile>
  <log_format>json</log_format>
  <location>/var/log/webapp/access.log</location>
</localfile>
```

Log ini dihasilkan oleh Node.js HTTP server yang berjalan di port 3000 pada VM `wazuh-agent-webapp`.

### 4.5 Wazuh Default Rules yang Relevan (Tidak Perlu Diubah)

| Rule ID | Level | Deskripsi | Relevansi |
|---|---|---|---|
| 554 | 5 | File added to the system | FIM — file baru ditambahkan |
| 550 | 7 | Integrity checksum changed | FIM — isi file berubah |
| 5715 | 3 | sshd: authentication success | Login SSH berhasil |
| 5760 | 5 | sshd: authentication failed | Login SSH gagal (password salah) |
| 5710 | 5 | sshd: Attempt to login using a non-existent user | Login dengan username tidak ada |
| 5503 | 5 | PAM: User login failed | Kegagalan autentikasi PAM |

---

## 5. Apa yang Telah Dikerjakan Anggota 1

Bagian ini menjelaskan urutan kronologis pekerjaan Anggota 1, termasuk hambatan yang ditemui dan cara mengatasinya.

### 5.1 Setup Infrastruktur Azure

Dibuat 4 VM di Azure Student subscription:
- `wazuh-manager` dipasang dengan Wazuh Manager, Wazuh Indexer, dan Wazuh Dashboard (OpenSearch)
- 3 VM agent (`wazuh-agent-attack`, `wazuh-agent-webapp`, `wazuh-agent-victim`) dipasang Wazuh Agent dan didaftarkan ke Manager

Semua VM menggunakan OS Ubuntu Linux. VM dibuat dengan status "stop/deallocate" saat tidak digunakan untuk menghemat kredit Azure Student.

### 5.2 Skenario Malware (21 Juni 2026)

**Mekanisme:** FIM (File Integrity Monitoring) Wazuh + CDB List Hash Matching

**Kronologi permasalahan:**

Percobaan pertama menggunakan `echo 'string EICAR' > file.txt` menghasilkan hash MD5 `69630e4574ec6798239b091cda43dca0` — berbeda dari hash EICAR standar `44d88612fea8a8f36de82e1278abb02f`. Penyebabnya adalah perintah `echo` secara default menambahkan satu karakter newline (`\n`) di akhir output, menambah ukuran file dari 68 byte (standar EICAR) menjadi 69 byte. Perbedaan satu byte ini sepenuhnya mengubah hash MD5.

Tiga file pertama (sample_doc_1, 2, 3) gagal terdeteksi oleh rule 100110 karena alasan ini, dan dikecualikan dari dataset.

**Solusi:** Gunakan `echo -n` untuk menghilangkan newline. File dibuat ulang dan menghasilkan hash yang tepat, sehingga rule 100110 terpicu.

**Hasil akhir:**
- 8 file TP: `sample_doc_4.txt` sampai `sample_doc_11.txt`
- 8 file FP: `file_normal.txt`, `file_normal_1.txt` s/d `file_normal_5.txt`, `report_draft_1.txt` s/d `report_draft_3.txt`
- 3 file dikecualikan: `sample_doc_1.txt`, `sample_doc_2.txt`, `sample_doc_3.txt` (hash salah)

### 5.3 Skenario Social Engineering (21 Juni 2026)

**Mekanisme:** GoPhish → simulasi phishing → pemakaian kredensial hasil phishing → SSH login → Wazuh SSH auth monitoring

**Kronologi:**
1. GoPhish diinstall di `wazuh-agent-attack`
2. Konfigurasi GoPhish: Sending Profile via Mailtrap (SMTP testing), Email Template "Reset Password", Landing Page berisi form kredensial palsu
3. Campaign diluncurkan, email phishing masuk ke Mailtrap inbox
4. Simulasi korban mengklik link dan mengisi kredensial di landing page
5. Simulasi penyerang memakai kredensial tersebut: `sshpass -p 'Passw0rd123' ssh corpuser@<webapp>` — menghasilkan alert `rule 5715` (login berhasil) [TP]
6. Simulasi login gagal biasa (FP): `sshpass -p 'password-salah' ssh azureuser@<webapp>` — menghasilkan alert `rule 5760` / `5710` [FP]

### 5.4 Skenario DDoS (22 Juni 2026)

**Mekanisme:** Apache Bench → Node.js HTTP server → JSON log → Wazuh logcollector → Rules 100002/100003/100004

**Kronologi permasalahan:**

Percobaan DDoS dengan `hping3` tidak pernah menghasilkan alert di Wazuh. Penyebabnya: `hping3` bekerja di level paket TCP/SYN (layer 4), sehingga tidak ada request HTTP yang masuk ke aplikasi, tidak ada log yang ditulis, dan Wazuh tidak punya data untuk diproses. Rule 100002 bergantung pada `<decoded_as>json</decoded_as>`, artinya harus ada JSON log yang masuk dari aplikasi yang berjalan.

**Solusi:**
1. Install Node.js di `wazuh-agent-webapp`
2. Buat HTTP server sederhana yang menulis JSON log per request ke `/var/log/webapp/access.log`
3. Daftarkan log file tersebut ke Wazuh logcollector dengan `log_format: json`
4. Ganti tool DDoS dari `hping3` ke Apache Bench (`ab`) yang mengirim request HTTP level 7

Setelah Node.js server aktif, `ab -n 10000 -c 200` berhasil memicu rule 100003 (level 8) dan 100004 (level 12).

**Hasil akhir:**
- 689 alert TP: rule 100003 dan 100004 dari sesi ab flood
- 2.618+ alert FP kandidat: rule 100002 saja (request normal yang tidak mencapai threshold flood)

---

## 6. Hasil Dataset Per Skenario

### 6.1 Skenario Malware

**File:** `malware-alerts-final.json`
**Tanggal pengambilan data:** 21 Juni 2026

| No | File | Timestamp | Rule Menyala | Label | Keterangan |
|---|---|---|---|---|---|
| 1 | file_normal.txt | 2026-06-21T10:39:46 | 554 | **FP** | File teks biasa |
| 2 | eicar_test.txt | 2026-06-21T10:39:11 | 554 | **FP** | EICAR tapi `echo` biasa — hash salah |
| 3 | eicar_test_1.txt s/d 5.txt | 2026-06-21T11:53:39 - 11:54:19 | 554 | **FP** | Loop EICAR tapi masih `echo` biasa |
| 4 | file_normal_1.txt s/d 5.txt | 2026-06-21T11:54:54 - 11:55:34 | 554 | **FP** | File teks biasa dengan timestamp |
| 5 | sample_doc_1.txt s/d 3.txt | 2026-06-21T13:06:39 - 13:06:59 | 554 | **EXCLUDED** | EICAR dengan `echo` biasa — hash salah, dikecualikan |
| 6 | report_draft_1.txt s/d 3.txt | 2026-06-21T13:08:06 - 13:08:26 | 554 | **FP** | File teks biasa |
| 7 | **sample_doc_4.txt** | 2026-06-21T13:24:06 | **554 + 100110** | **TP** | EICAR dengan `echo -n` — hash cocok ✓ |
| 8 | **sample_doc_5.txt s/d 11.txt** | 2026-06-21T13:35:28 - 13:36:16 | **554 + 100110** | **TP** | EICAR dengan `echo -n` — hash cocok ✓ |
| 9 | report_draft_4.txt s/d 8.txt | 2026-06-21T13:37:46 - 13:38:18 | 554 | **FP** | File teks biasa |

**Ringkasan valid:**
- **TP:** 8 entri (sample_doc_4 s/d sample_doc_11) — identifikasi: `rule.id == "100110"`
- **FP:** 8 entri (file_normal.txt + file_normal_1-5 + report_draft_1-3) — identifikasi: `rule.id == "554"` DAN `syscheck.path` tidak punya pasangan rule 100110
- **EXCLUDED:** 6 entri (eicar_test_1-5 dan sample_doc_1-3) — jangan dipakai karena ambigu/hash salah

### 6.2 Skenario DDoS

**File:** `ddos-alerts-final.json`
**Tanggal pengambilan data:** 22 Juni 2026
**Rentang waktu:** 06:03:38 - 06:28:17 UTC

| Rule ID | Level | Deskripsi | Jumlah Alert | Label Kandidat |
|---|---|---|---|---|
| 100002 | 3 | NodeJS HTTP Request | 3.307 | Baseline (FP jika berdiri sendiri) |
| 100003 | 8 | Possible HTTP Flood Activity | 686 | **TP** |
| 100004 | 12 | Severe HTTP Flood / DDoS attack detected | 3 | **TP** |

**Total TP:** 689 (rule 100003 + 100004)
**Total FP kandidat:** ~2.618 (rule 100002 yang tidak disertai 100003/100004 di timewindow yang sama)

### 6.3 Skenario Social Engineering

**File:** `socialeng-alerts-final.json`
**Tanggal pengambilan data:** 21 Juni 2026
**Rentang waktu:** 09:27:04 - 15:00:36 UTC

| Rule ID | Level | Deskripsi | Jumlah | Label Kandidat |
|---|---|---|---|---|
| 5715 | 3 | sshd: authentication success | 7 | **TP** — login berhasil pasca phishing |
| 5760 | 5 | sshd: authentication failed | 1.056 | **FP** — login gagal biasa |
| 5710 | 5 | sshd: Attempt login non-existent user | 4.638 | **FP** — username tidak ada |
| 5503 | 5 | PAM: User login failed | 2.666 | **FP** — kegagalan autentikasi PAM |

**Catatan penting:** Alert 5710 dan 5503 dalam jumlah besar di file ini sebagian besar bukan dari simulasi yang dikendalikan — ini adalah brute force otomatis dari internet yang terjadi secara organik pada VM yang memiliki port SSH terbuka. Ini sebenarnya sangat representatif dari kondisi SOC nyata: banyak alert SSH yang secara teknis valid tapi bukan bagian dari skenario serangan yang sedang diinvestigasi (ini adalah FP dari perspektif "apakah ini terkait skenario phishing yang sedang diuji?"). Gunakan field `agent.name` dan timestamp untuk membedakan mana yang dihasilkan dari eksperimen terkendalikan.

---

## 7. Panduan Labeling untuk Anggota 2

### 7.1 Cara Membaca File JSON

Setiap baris di ketiga file adalah satu alert JSON. Field yang paling penting:

```json
{
  "timestamp": "2026-06-21T13:24:06.489+0000",
  "rule": {
    "id": "100110",
    "level": 12,
    "description": "File dengan hash dikenal sebagai malware terdeteksi",
    "groups": ["local", "malware"]
  },
  "agent": {
    "name": "webapp-agent",
    "ip": "10.0.0.4"
  },
  "syscheck": {
    "path": "/home/azureuser/uploads/sample_doc_4.txt",
    "md5_after": "44d88612fea8a8f36de82e1278abb02f",
    "event": "added"
  },
  "full_log": "...",
  "decoder": { "name": "syscheck_new_entry" }
}
```

### 7.2 Kriteria Labeling Eksak

#### SKENARIO MALWARE

**True Positive (TP) — Label: 1**
```
rule.id == "100110"
```
Artinya: file yang ditambahkan ke sistem memiliki hash MD5 yang cocok dengan database malware (CDB list). Ini adalah deteksi yang benar karena file memang mengandung signature EICAR.

**False Positive (FP) — Label: 0**
```
rule.id == "554" AND syscheck.path TIDAK PUNYA entry rule.id "100110" 
pada timestamp yang berdekatan (dalam 1 detik)
```
Artinya: file baru terdeteksi ditambahkan, tapi hash-nya tidak cocok dengan database malware — hanya alert FIM generik tanpa konfirmasi konten berbahaya.

**EXCLUDED — Jangan dipakai:**
```
syscheck.path mengandung "sample_doc_1" ATAU "sample_doc_2" ATAU "sample_doc_3"
```

---

#### SKENARIO DDoS

**True Positive (TP) — Label: 1**
```
rule.id == "100003" OR rule.id == "100004"
```
Artinya: threshold frekuensi request terpenuhi (≥5 request dalam 20 detik dari IP yang sama), mengindikasikan pola banjir traffic yang abnormal.

**False Positive (FP) — Label: 0**
```
rule.id == "100002" AND tidak ada rule.id "100003" atau "100004" 
dalam rentang timestamp ±20 detik yang sama
```
Artinya: request HTTP biasa yang masuk ke server, frekuensinya belum mencapai threshold untuk dianggap serangan.

**Catatan implementasi:** Untuk efisiensi labeling dengan jumlah data yang besar (>3.000 baris), pertimbangkan menggunakan pandas dengan logika window-based grouping:
```python
import pandas as pd
df = pd.read_json('ddos-alerts-final.json', lines=True)
df_ddos = df[df['rule.id'].isin(['100002', '100003', '100004'])]
df_ddos['label'] = df_ddos['rule.id'].apply(lambda x: 1 if x in ['100003','100004'] else 0)
```

---

#### SKENARIO SOCIAL ENGINEERING

**True Positive (TP) — Label: 1**
```
rule.id == "5715" AND agent.name == "attack-agent" 
AND timestamp BETWEEN "2026-06-21T14:00:00" AND "2026-06-21T15:00:00"
```
Artinya: login SSH berhasil dari mesin penyerang dalam rentang waktu eksperimen — mengindikasikan penggunaan kredensial hasil phishing.

**False Positive (FP) — Label: 0**
```
(rule.id == "5760" OR rule.id == "5710" OR rule.id == "5503") 
AND timestamp BETWEEN "2026-06-21T14:00:00" AND "2026-06-21T15:00:00"
```
Artinya: percobaan login gagal dari mesin penyerang — simulasi user salah ketik password atau username tidak ada.

**Alert di luar rentang 14:00-15:00 (09:27 - 14:00):** Ini adalah brute force otomatis dari internet yang tidak terkontrol. Bisa dimasukkan sebagai data tambahan FP yang realistis, tapi tandai dengan field tambahan seperti `source: "organic"` agar Anggota 3 bisa memisahkan jika diperlukan.

---

### 7.3 Feature Engineering Rekomendasi untuk Anggota 3

Berikut fitur yang bisa diekstrak dari alert JSON untuk training model:

| Nama Fitur | Field Sumber | Keterangan |
|---|---|---|
| `rule_level` | `rule.level` | Tingkat keparahan Wazuh (integer 3-12) |
| `rule_id` | `rule.id` | ID rule numerik (encode sebagai kategori) |
| `agent_name` | `agent.name` | Nama agent sumber (encode sebagai kategori) |
| `hour_of_day` | `timestamp` | Jam kejadian (0-23), untuk deteksi anomali waktu |
| `decoder_name` | `decoder.name` | Jenis decoder yang dipakai |
| `log_length` | `full_log` | Panjang karakter full_log |
| `syscheck_event` | `syscheck.event` | Jenis event FIM: added/modified/deleted (untuk malware) |
| `has_md5` | `syscheck.md5_after` | Boolean: apakah alert punya field hash MD5 |
| `rule_group_ddos` | `rule.groups` | Boolean: apakah `ddos` ada di groups |
| `rule_group_auth` | `rule.groups` | Boolean: apakah `authentication_failed` ada di groups |

---

## 8. File yang Diserahkan

| File | Skenario | Ukuran | Keterangan |
|---|---|---|---|
| `malware-alerts-final.json` | Malware | ~8.531 baris | Semua alert 21 Juni 2026, gunakan panduan labeling 7.2 |
| `socialeng-alerts-final.json` | Social Engineering | ~9.347 baris | Semua alert 21 Juni 2026, filter agent dan timestamp |
| `ddos-alerts-final.json` | DDoS | ~6.276 baris | Semua alert 22 Juni 2026 pagi |

**Catatan:** Ketiga file berisi SEMUA alert dari Manager pada hari tersebut — termasuk alert background noise (SSH brute force dari internet, dsb). Gunakan panduan kriteria labeling di Bagian 7.2 sebagai ground truth untuk memilah mana yang merupakan bagian dari eksperimen terkendalikan.

---

## 9. Catatan Teknis Penting untuk Laporan

### 9.1 Keterbatasan yang Harus Disebutkan di Laporan

**Malware — Label Leakage Awal:** Tiga file pertama (sample_doc_1/2/3) tidak terdeteksi bukan karena sistem gagal, melainkan karena kesalahan pembuatan file (perintah `echo` tanpa flag `-n` menambahkan newline yang mengubah hash MD5). Ini mendokumentasikan sifat exact-match dari deteksi berbasis hash — perbedaan 1 byte membuat file sepenuhnya tidak dikenali.

**DDoS — Tool Mismatch Awal:** Percobaan awal menggunakan `hping3` tidak menghasilkan alert apapun karena `hping3` bekerja di layer 4 (TCP SYN), sedangkan pipeline deteksi Wazuh bergantung pada log aplikasi layer 7 (HTTP request JSON). Ini penting dicatat: Wazuh tidak secara native mendeteksi DDoS layer 4 tanpa integrasi tambahan (seperti iptables log atau netflow).

**Social Engineering — Alert Organik:** Sebagian besar volume alert di file social engineering berasal dari brute force otomatis internet, bukan dari eksperimen terkontrol. Ini realistis (kondisi SOC nyata), tapi harus diakui di laporan sebagai batasan kontrol eksperimen.

### 9.2 Poin Kuat untuk Laporan

1. **CDB List Hash Matching** adalah fitur native Wazuh yang valid secara industri — bukan workaround — dan memberikan sinyal deteksi yang berbasis konten (bukan nama file).
2. **Dua fase deteksi Malware** (sebelum dan sesudah integrasi hash) bisa disajikan sebagai perbandingan baseline vs improved system yang meyakinkan.
3. **Volume alert DDoS** (689 TP vs 2.618+ FP) memberikan ilustrasi konkret dari masalah false alarm yang disebutkan di latar belakang tugas.
4. **Alert SSH organik** di skenario Social Engineering bisa dijadikan argumen kenapa threshold dan konteks diperlukan — alert tidak bisa dievaluasi secara terisolasi.

---

*Dokumen ini dibuat berdasarkan pekerjaan Anggota 1 yang selesai pada 22 Juni 2026.*
*Untuk pertanyaan teknis tentang infrastruktur atau konfigurasi rule, hubungi Anggota 1.*
