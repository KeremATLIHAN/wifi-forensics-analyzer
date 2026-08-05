# CyberLab Desktop Suite
## Yazılım Tasarım ve Mimari Dokümanı

**Belge sürümü:** 0.1  
**Ürün durumu:** Geliştirme aşamasında  
**Ana geliştirici:** KeremATLIHAN  
**Teknolojiler:** Python, PySide6, Qt, TShark  
**Slogan:** From data to insight.

---

## 1. Proje vizyonu

CyberLab Desktop Suite, siber güvenlik eğitimi sırasında öğrenilen
konuların bağımsız modüller halinde uygulanabildiği, geliştirilebildiği
ve raporlanabildiği masaüstü tabanlı bir eğitim ve analiz platformudur.

Proje yalnızca tek bir ağ analiz aracına dönüşmek için değil, zaman
içerisinde yeni laboratuvar konularının eklenebileceği genişletilebilir
bir çalışma ortamı olarak tasarlanmıştır.

İlk çalışan modül, Wi-Fi yakalama dosyalarını inceleyen
Wi-Fi Forensics modülüdür.

---

## 2. Temel amaçlar

CyberLab Desktop Suite aşağıdaki amaçları taşır:

- Siber güvenlik laboratuvar dosyalarını düzenli biçimde analiz etmek
- Öğrenilen yeni konuları bağımsız modüller halinde uygulamaya eklemek
- Analiz sonuçlarını görsel ve anlaşılır biçimde sunmak
- Laboratuvar geçmişini kayıt altında tutmak
- JSON, CSV ve HTML raporları oluşturmak
- Python, PySide6, Git ve yazılım mimarisi pratiği kazandırmak
- Eğitim ve izinli laboratuvar ortamlarında kullanılmak
- Modüller arasında ortak bir tasarım ve raporlama standardı sağlamak

---

## 3. Kullanım kapsamı

Uygulama yalnızca aşağıdaki ortamlarda kullanılmak üzere tasarlanır:

- Kullanıcıya ait sistemler
- Açıkça izin verilmiş laboratuvar ağları
- Eğitim kurumlarının kontrollü çalışma ortamları
- CTF ve uygulamalı eğitim senaryoları
- Kullanıcı tarafından oluşturulmuş test verileri

Yetkisiz sistemlere erişim, parola kırma otomasyonu veya saldırı
zincirlerinin yürütülmesi projenin kapsamı dışındadır.

---

## 4. Ürün yapısı

Ana ürün:

```text
CyberLab Desktop Suite
```

İlk modül:

```text
Wi-Fi Forensics
```

Planlanan modüller:

```text
CyberLab Desktop Suite
├── Dashboard
├── Lab Workspace
├── Wi-Fi Forensics
├── Network Analysis
├── Log Analysis
├── File Integrity
├── IOC Analysis
├── Training Notes
├── Reports
└── Settings
```

Her modül bağımsız geliştirilebilmeli ve ana uygulamaya kayıt sistemi
üzerinden eklenebilmelidir.

---

## 5. Yüksek seviyeli mimari

```text
┌───────────────────────────────────────────┐
│          CyberLab Desktop Suite           │
│              PySide6 GUI                  │
└────────────────────┬──────────────────────┘
                     │
                     ▼
┌───────────────────────────────────────────┐
│             Module Registry               │
│ Modül keşfi, yükleme ve yaşam döngüsü     │
└──────────────┬────────────────────────────┘
               │
      ┌────────┴─────────┐
      ▼                  ▼
┌───────────────┐  ┌───────────────────────┐
│ Wi-Fi Module  │  │ Gelecekteki Modüller  │
└───────┬───────┘  └───────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│          Analysis Service Layer           │
└────────────────────┬──────────────────────┘
                     │
                     ▼
┌───────────────────────────────────────────┐
│ Parser / TShark Integration / Data Model  │
└───────────────────────────────────────────┘
```

---

## 6. Mimari ilkeler

### 6.1 Arayüz ve analiz motoru ayrımı

GUI doğrudan TShark komutu çalıştırmamalıdır.

Doğru akış:

```text
GUI
→ Controller veya Worker
→ Analysis Service
→ Parser
→ TShark
```

GUI yalnızca kullanıcı girdisini alır, analizi başlatır ve dönen sonucu
görüntüler.

### 6.2 Tek sorumluluk

Her sınıf ve modül mümkün olduğunca tek bir sorumluluğa sahip olmalıdır.

Örnek:

- `tshark_parser.py`: Paket alanlarını okur
- `analyzer.py`: Veriyi analiz eder
- `reporters.py`: Rapor üretir
- `worker.py`: Uzun işlemleri arka planda çalıştırır
- `main_window.py`: Ana pencereyi yönetir

### 6.3 Genişletilebilirlik

Yeni bir modül eklemek için ana pencerenin kaynak kodunun değiştirilmesi
gerekmemelidir. Modül kayıt sistemine eklenmesi yeterli olmalıdır.

### 6.4 Arka plan işlemleri

Uzun süren analizler ana GUI iş parçacığında çalıştırılmamalıdır.
PySide6 `QThread`, `QRunnable` veya `QThreadPool` yapısı kullanılmalıdır.

### 6.5 Veri odaklı arayüz

Analiz sonucu GUI bileşenlerine doğrudan bağlı olmamalıdır.
Sonuçlar sözlükler veya veri modelleri üzerinden taşınmalıdır.

---

## 7. Önerilen klasör yapısı

```text
cyberlab-desktop-suite/
├── app/
│   ├── application.py
│   ├── main_window.py
│   └── settings.py
│
├── gui/
│   ├── pages/
│   ├── widgets/
│   ├── dialogs/
│   ├── workers/
│   └── themes/
│
├── modules/
│   ├── base.py
│   ├── registry.py
│   └── wifi_forensics/
│       ├── module.py
│       ├── page.py
│       ├── controller.py
│       └── models.py
│
├── core/
│   ├── events.py
│   ├── exceptions.py
│   ├── logging.py
│   └── paths.py
│
├── services/
│   ├── report_service.py
│   └── project_service.py
│
├── src/
│   ├── analyzer.py
│   ├── tshark_parser.py
│   ├── reporters.py
│   ├── config.py
│   └── utils.py
│
├── resources/
│   ├── icons/
│   ├── images/
│   ├── styles/
│   └── translations/
│
├── captures/
├── reports/
├── projects/
├── tests/
├── docs/
├── gui_app.py
├── main.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── LICENSE
```

Mevcut proje bu yapıya tek seferde taşınmayacaktır. Taşıma küçük ve
kontrollü sürümler halinde yapılacaktır.

---

## 8. Modül sistemi

Her CyberLab modülü en az aşağıdaki bilgileri sağlamalıdır:

```python
module_id
display_name
description
version
icon
create_page()
```

Örnek modül arayüzü:

```python
class CyberLabModule:
    module_id = "example"
    display_name = "Example Module"
    description = ""
    version = "0.1.0"

    def create_page(self):
        raise NotImplementedError
```

İlerleyen sürümlerde şu yaşam döngüsü metotları eklenebilir:

```python
initialize()
activate()
deactivate()
shutdown()
```

---

## 9. Wi-Fi Forensics modülü

İlk modül şu görevlerden sorumludur:

- `.cap`, `.pcap` ve `.pcapng` dosyalarını seçmek
- TShark alanlarını otomatik algılamak
- SSID ve BSSID bilgilerini çıkarmak
- İstemci adaylarını göstermek
- Kanal ve sinyal bilgilerini okumak
- EAPOL paketlerini tespit etmek
- 802.11 çerçeve türlerini sınıflandırmak
- JSON, CSV ve HTML raporları üretmek

Modül doğrudan GUI’ye veri yazmamalıdır. Analiz sonucu standart bir
model aracılığıyla döndürülmelidir.

Örnek veri modeli:

```python
{
    "capture": {
        "file_name": "example.pcapng",
        "total_packets": 155025
    },
    "summary": {
        "networks": 1,
        "clients": 296,
        "eapol_packets": 0
    },
    "networks": [],
    "frame_statistics": {},
    "warnings": []
}
```

---

## 10. Ana arayüz tasarımı

Ana pencere iki temel bölüme ayrılır:

```text
┌────────────────┬──────────────────────────────────┐
│ Sol Navigasyon │          İçerik Alanı            │
│                │                                  │
│ Dashboard      │ Modüle ait sayfa                 │
│ Labs           │                                  │
│ Wi-Fi          │                                  │
│ Reports        │                                  │
│ Settings       │                                  │
└────────────────┴──────────────────────────────────┘
```

### Sol menü

- Marka ve logo
- Dashboard
- Lab Workspace
- Etkin modüller
- Reports
- Settings
- Uygulama sürümü

### İçerik alanı

- Sayfa başlığı
- Açıklama
- İşlem kontrolleri
- Özet kartları
- Tablo veya grafikler
- Durum bilgisi

---

## 11. Tasarım sistemi

### Ana renkler

```text
Ana arka plan     #111827
Yan panel         #0B1220
Kart              #182235
Çerçeve           #29364B
Ana vurgu         #22D3A6
İkincil vurgu     #3B82F6
Metin             #F9FAFB
İkincil metin     #9CA3AF
Uyarı             #F59E0B
Hata               #EF4444
Başarı             #10B981
```

### Tasarım özellikleri

- Koyu tema varsayılan olacaktır
- Kart köşeleri yuvarlatılmış olacaktır
- Gereksiz animasyonlardan kaçınılacaktır
- Veri tabloları okunabilir ve filtrelenebilir olacaktır
- Kritik uyarılar yalnızca renkle ifade edilmeyecektir
- Açık tema ileriki sürümlerde eklenecektir

---

## 12. Marka kimliği

Geçici ürün adı:

```text
CyberLab Desktop Suite
```

Geçici slogan:

```text
From data to insight.
```

İlk modül adı:

```text
Wi-Fi Forensics
```

Logo aşağıdaki kavramları birleştirmelidir:

- Siber güvenlik
- Analiz
- Eğitim
- Modülerlik
- Veri ve ağ görünürlüğü

Logo uygulamada, README dosyasında ve HTML raporlarında kullanılacaktır.

---

## 13. Laboratuvar çalışma alanı

İlerleyen sürümlerde her laboratuvar çalışması proje olarak saklanacaktır.

Önerilen bilgiler:

```text
Lab adı
Tarih ve saat
Konu
Amaç
Yetki kapsamı
Kullanılan araçlar
Çalıştırılan komutlar
Eklenen dosyalar
Analiz sonuçları
Kullanıcı notları
Öğrenilen konular
Raporlar
```

Önerilen proje yapısı:

```text
projects/
└── lab-2026-001/
    ├── project.json
    ├── notes.md
    ├── captures/
    ├── reports/
    └── attachments/
```

---

## 14. Hata yönetimi

Uygulama teknik hataları kullanıcıya ham Python traceback olarak
göstermemelidir.

Hatalar şu seviyelerde yönetilecektir:

```text
INFO
WARNING
ERROR
CRITICAL
```

Kullanıcıya açıklayıcı mesaj gösterilirken teknik ayrıntılar log
dosyasına yazılacaktır.

Örnek:

```text
Kullanıcı mesajı:
Yakalama dosyası okunamadı.

Teknik log:
TsharkError: The file appears to have been cut short...
```

---

## 15. Log sistemi

Log dosyaları şu dizinde tutulabilir:

```text
logs/cyberlab.log
```

Loglarda şu bilgiler bulunmalıdır:

- Uygulamanın başlangıç ve kapanış zamanı
- Modül yükleme sonuçları
- Analiz başlangıç ve bitiş zamanı
- Kullanılan dosya yolu
- Oluşan raporlar
- Hata ve uyarılar

Yakalama dosyasındaki hassas içerik loglara doğrudan yazılmamalıdır.

---

## 16. Test stratejisi

### Birim testleri

- SSID çözümleme
- MAC doğrulama
- TShark alan eşleştirme
- Ağ gruplama
- Rapor üretimi

### Entegrasyon testleri

- TShark ile örnek dosya okuma
- Analiz motorundan rapor üretme
- Worker ve GUI sinyal iletişimi

### Arayüz testleri

- Modüllerin yüklenmesi
- Dosya seçme
- Analiz butonunun etkinleşmesi
- Hata mesajlarının gösterilmesi
- Tablo verilerinin güncellenmesi

Testlerde gerçek kullanıcı yakalamaları yerine anonim ve küçük test
dosyaları kullanılmalıdır.

---

## 17. Git stratejisi

Kararlı dal:

```text
main
```

Özellik dalları:

```text
feature/pyside6-gui
feature/module-registry
feature/wifi-frame-analysis
feature/lab-workspace
```

Hata düzeltme dalları:

```text
fix/report-directory-name
fix/tshark-field-resolution
```

Commit mesajları kısa ve açıklayıcı olmalıdır:

```text
Add CyberLab desktop shell
Connect Wi-Fi analyzer to GUI worker
Fix report directory configuration
Add module registry tests
```

---

## 18. Sürüm planı

### v0.1 — Wi-Fi analiz çekirdeği

- TShark entegrasyonu
- Temel paket analizi
- JSON, CSV ve HTML raporları
- Komut satırı arayüzü

### v0.2 — CyberLab masaüstü kabuğu

- PySide6 ana pencere
- Koyu tema
- Modül kayıt sistemi
- Wi-Fi modülü için temel sayfa
- Worker altyapısı

### v0.3 — Wi-Fi modül entegrasyonu

- Mevcut analiz motorunun GUI’ye bağlanması
- Arka plan analiz işlemi
- Özet kartları
- Ağ tablosu
- Rapor erişimi

### v0.4 — Laboratuvar çalışma alanı

- Laboratuvar oluşturma
- Notlar
- Dosya ve rapor yönetimi
- Analiz geçmişi

### v0.5 — Gelişmiş analiz

- Frame istatistikleri
- Kanal analizi
- RSSI grafikleri
- OUI üretici bilgileri

### v1.0 — İlk kararlı sürüm

- Testler
- Dokümantasyon
- Paketleme
- Kararlı modül sistemi
- GitHub release

---

## 19. Kod standartları

- Python tür ipuçları kullanılmalıdır
- Fonksiyonlar mümkün olduğunca kısa tutulmalıdır
- Kullanıcıya gösterilen metinlerle iç kod ayrılmalıdır
- Dosya ve sınıf adları tek bir standarda uymalıdır
- Sabit değerler merkezi yapılandırma dosyalarında tutulmalıdır
- İşlevsiz veya kullanılmayan kod repoda bırakılmamalıdır
- Gizli bilgiler ve gerçek yakalama dosyaları GitHub’a gönderilmemelidir

Kod kontrolü için ileride şu araçlar değerlendirilebilir:

```text
ruff
black
mypy
pytest
```

---

## 20. Güvenlik ve gizlilik

Aşağıdaki dosyalar varsayılan olarak Git dışında tutulmalıdır:

```gitignore
.venv/
captures/
reports/
projects/
logs/
*.cap
*.pcap
*.pcapng
```

Uygulama:

- Yakalama dosyalarını otomatik olarak internete göndermemelidir
- Analizleri varsayılan olarak yerel ortamda gerçekleştirmelidir
- Kullanıcı onayı olmadan dosya silmemelidir
- Gerçek ağ bilgilerini örnek dokümanlara eklememelidir
- Hassas verileri hata mesajlarında göstermemelidir

---

## 21. Başarı ölçütleri

İlk kararlı sürüm başarılı kabul edilecektir, eğer:

- Uygulama Kali Linux üzerinde güvenilir biçimde açılıyorsa
- Modüller bağımsız olarak yüklenebiliyorsa
- Wi-Fi yakalama dosyaları GUI üzerinden analiz edilebiliyorsa
- Arayüz analiz sırasında donmuyorsa
- Raporlar doğru biçimde üretilebiliyorsa
- Hatalar anlaşılır biçimde gösteriliyorsa
- Yeni bir modül mevcut sistemi bozmadan eklenebiliyorsa

---

## 22. Açık kararlar

Aşağıdaki kararlar sonraki tasarım oturumlarında netleştirilecektir:

- Ürünün kesin adı
- Nihai logo
- Uygulama ikonları
- Açık tema
- SQLite kullanım zamanı
- Paketleme yöntemi
- Windows ve macOS desteğinin kapsamı
- Modüllerin dinamik mi statik mi yükleneceği
- Eklenti sisteminin dış geliştiricilere açılıp açılmayacağı

---

## 23. Sonuç

CyberLab Desktop Suite, sabit özelliklere sahip tek amaçlı bir program
değil; siber güvenlik eğitimiyle birlikte gelişen, yeni bilgiler ve
laboratuvar senaryolarıyla genişletilen modüler bir öğrenme ve analiz
platformu olacaktır.

Bu belge, projenin gelişimi boyunca güncellenecek yaşayan bir tasarım
dokümanıdır.
