# Final Project SOC (Security Operations Center)

Repositori ini berisi struktur project template untuk Tugas Akhir / Final Project mata kuliah **Security Operations Center (SOC)**.

## 📁 Struktur Repositori

Berikut adalah folder dan berkas yang tersedia beserta penjelasannya:

* 🛠️ **[wazuh-config/](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/wazuh-config)**
  * [local_rules.xml](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/wazuh-config/local_rules.xml) - Aturan kustom (copy dari Manager).
  * [ossec.conf-agent.xml](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/wazuh-config/ossec.conf-agent.xml) - Konfigurasi syscheck & localfile untuk webapp agent.
  * [malware-hashes](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/wazuh-config/malware-hashes) - CDB List berisi hash malware.
* 📊 **[dataset/](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/dataset)**
  * [malware-alerts-final.json](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/dataset/malware-alerts-final.json) - Dataset alert final untuk deteksi malware.
  * [socialeng-alerts-final.json](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/dataset/socialeng-alerts-final.json) - Dataset alert final untuk social engineering.
  * [ddos-alerts-final.json](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/dataset/ddos-alerts-final.json) - Dataset alert final untuk serangan DDoS.
* 📝 **[docs/](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/docs)**
  * [handover-anggota1-ke-anggota2.md](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/docs/handover-anggota1-ke-anggota2.md) - Dokumentasi serah terima tugas dari Anggota 1 ke Anggota 2.
* 🤖 **[ai-model/](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/ai-model)**
  * [README.md](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/ai-model/README.md) - Modul AI/ML (Dikerjakan oleh **Anggota 3**).
* 🔄 **[soar-integration/](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/soar-integration)**
  * [README.md](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/soar-integration/README.md) - Modul integrasi SOAR (Dikerjakan oleh **Anggota 4**).

---

## 👥 Anggota Tim & Pembagian Tugas
* **Anggota 1**: `[Nama/NRP]` - Webapp Agent & Konfigurasi Awal
* **Anggota 2**: `[Nama/NRP]` - Analisis Log, Rules, & Handover dari Anggota 1
* **Anggota 3**: `[Nama/NRP]` - Pengembangan AI/ML Model ([ai-model/](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/ai-model))
* **Anggota 4**: `[Nama/NRP]` - Integrasi Otomatisasi SOAR ([soar-integration/](file:///d:/Kuliah/SMT%204/SOC/FP%20SOC/soar-integration))
