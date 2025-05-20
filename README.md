Gönderdiğiniz `.txt` dosyası, bir **Python uygulamasının**, **Docker** ve **Azure Event Hubs** kullanarak ZIP içindeki CSV verilerini işleyip Fabric EventStream’e (Event Hubs) göndermesine olanak tanıyan bir çözümü açıklıyor. Ayrıca, bu çözümün yapılandırılması için gerekli olan `docker-compose.yml`, `Dockerfile`, `requirements.txt`, ortam değişkenleri ve çalıştırmaya dair örnekler yer alıyor.

Aşağıda bu bilgileri temel alan **README.md** dosyasını markdown formatında bulabilirsiniz. Bu README dosyası hem teknik detayları içerir hem de kullanım kılavuzu niteliğindedir:

---

# 🚀 Fabric EventStream'e ZIP İçindeki CSV Verilerini Gönderme Çözümü

Bu proje, Azure Fabric EventStream (Event Hubs) üzerinde ZIP dosyalarından çıkarılan CSV verilerini etkili bir şekilde göndermek için hazırlanmış bir çözümdür. Özellikle büyük miktarda veriyi işlemeniz gerektiğinde yüksek performanslı toplu ve paralel işlemeye olanak tanır.

## ✅ Özellikler

- 🔧 ZIP dosyalarını otomatik olarak açar ve içindeki tüm CSV dosyalarını işler.
- 📦 Toplu işleme: 1000'er satırlık batch’ler halinde veri gönderimi.
- ⚙️ Gönderim hızı kontrolü (saniye cinsinden aralıklarla).
- 🔁 Hata durumunda tekrar deneme mekanizması.
- 📁 Farklı klasörlerden gelen ZIP dosyalarını aynı anda işler (paralel işleme).
- 📄 Her satıra meta veri eklenir: hangi ZIP ve CSV dosyasından geldiğini belirtir.
- 🐳 Kolay dağıtım için Docker desteği.

---

## 📁 Dosya Yapısı

Proje aşağıdaki ana dosyalardan oluşur:

| Dosya               | Açıklama |
|---------------------|----------|
| `streamer.py`       | Ana Python kodu - ZIP açma, CSV işleme ve Event Hubs'a veri gönderme. |
| `Dockerfile`        | Docker konteyner yapılandırma dosyası. |
| `requirements.txt`  | Gerekli Python bağımlılıkları. |
| `docker-compose.yml`| Docker Compose ile çalıştırma için yapılandırma. |
| `run_docker.sh`     | (İsteğe bağlı) Docker komutlarını içeren betik. |

---

## 🛠️ Ortam Değişkenleri

Çözüm şu ortam değişkenlerini desteklemektedir:

| Değişken                     | Açıklama |
|------------------------------|----------|
| `FABRIC_EVENTHUB_CONNECTION_STRING` | Azure Event Hubs bağlantı dizesi |
| `FABRIC_EVENTHUB_NAME`              | Gönderilecek Event Hub adı |
| `ZIP_FILES`                         | İşlenecek ZIP dosyalarının yolu ve deseni (örn: `/app/data/trip_*.zip`) |
| `SEND_INTERVAL`                     | Her gönderim arasında bekleme süresi (saniye) |
| `MAX_RETRIES`                       | Hata durumunda maksimum tekrar sayısı |
| `RETRY_DELAY`                       | Tekrar denemeler arası bekleme süresi (saniye) |
| `BATCH_SIZE`                        | Kaç satır birlikte gönderilsin (varsayılan: 1000) |
| `MAX_CONCURRENT_FILES`              | Aynı anda kaç ZIP dosyası işlensin (varsayılan: 10) |

---

## 📦 Kullanım Talimatları

### 1. Dosyaları Projeye Ekleyin
Aşağıdaki dosyaları projenizin kök dizinine ekleyin:
- `streamer.py`
- `Dockerfile`
- `requirements.txt`
- `docker-compose.yml` (tercih edilen yöntem)

### 2. Ortam Değişkenlerini Ayarlayın

#### Örnek `.env` dosyası:
```env
FABRIC_EVENTHUB_CONNECTION_STRING=Endpoint=sb://...
FABRIC_EVENTHUB_NAME=your-eventhub-name
ZIP_FILES=/app/data1/trip_*.zip,/app/data2/trip_*.zip
BATCH_SIZE=1000
SEND_INTERVAL=0.1
MAX_RETRIES=3
RETRY_DELAY=5
MAX_CONCURRENT_FILES=10
```

### 3. Docker ile Çalıştırma

#### Docker Build ve Run Komutları:
```bash
docker build -t fabric-eventhub-streamer .
docker run -it --rm \
  -e FABRIC_EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
  -e FABRIC_EVENTHUB_NAME="your-eventhub-name" \
  -e ZIP_FILES="/app/data/trip_*.zip" \
  -e BATCH_SIZE=1000 \
  -v /path/to/your/zip/files:/app/data \
  fabric-eventhub-streamer
```

### 4. Docker Compose ile Çalıştırma (Önerilir)

#### Örnek `docker-compose.yml`:
```yaml
version: '3'
services:
  streamer:
    build: .
    environment:
      - FABRIC_EVENTHUB_CONNECTION_STRING=Endpoint=sb://...
      - FABRIC_EVENTHUB_NAME=your-eventhub-name
      - ZIP_FILES=/app/data1/trip_*.zip,/app/data2/trip_*.zip
      - BATCH_SIZE=1000
      - SEND_INTERVAL=0.1
      - MAX_CONCURRENT_FILES=10
    volumes:
      - ./data1:/app/data1
      - ./data2:/app/data2
```

#### Çalıştırma:
```bash
docker-compose up
```

---

## 🔄 Yeni Özellikler

### 1. Batch Gönderimi (1000'er Satır)
Veriler artık tek tek değil, 1000'er satırlık gruplar halinde gönderilir. Bu sayede daha az istekle daha fazla veri aktarımı yapılır.

### 2. Paralel İşleme
- **ZIP seviyesinde:** Aynı anda birden fazla ZIP dosyası işlenir.
- **CSV seviyesinde:** Bir ZIP içindeki tüm CSV dosyaları paralel olarak işlenir.
- **Klasör bazlı:** Birden fazla klasördeki ZIP dosyaları eş zamanlı olarak işlenebilir.

---

## 📈 Performans ve Kaynak Yönetimi

- Daha yüksek `BATCH_SIZE` = daha hızlı veri akışı ama daha fazla bellek kullanımı.
- Daha yüksek `MAX_CONCURRENT_FILES` = daha hızlı işlenen dosyalar ama CPU/I/O kaynakları artar.
- Uygun değerler seçerek sistem kaynaklarını optimize edebilirsiniz.

---

## 📝 Lisans & Katkı

Bu proje açık kaynak olup, katkılar herkes için açıktır. Lisans bilgisi gerekiyorsa MIT veya Apache lisansları gibi yaygın lisanslardan birini ekleyebilirsiniz.

---

## 📬 Destek veya Sorular?

Herhangi bir sorunuz varsa, özelleştirme ihtiyacınız varsa lütfen bana yazmaktan çekinmeyin!

--- 

> 💡 Not: Markdown formatındaki bu README dosyasını GitHub, GitLab veya VSCode gibi platformlarda düzgün görüntülemek için `.md` uzantılı bir dosya olarak kaydetmeniz gerekmektedir. Örneğin: `README.md`.

Hazır haliyle kopyalayıp projenize ekleyebileceğiniz bu README dosyası, takım arkadaşlarınız ya da kullanıcılar için açıklayıcı ve kolay anlaşılır bir rehber sunar.