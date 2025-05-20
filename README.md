Fabric EventStream'e ZIP İçindeki CSV Verilerini Gönderme ÇözümüBu çözüm, ZIP dosyalarından CSV verilerini çıkarıp Azure Fabric EventStream'e (Event Hubs) göndermek için tasarlanmıştır. Özellikle büyük veri setlerini paralel ve verimli bir şekilde işlemek için optimize edilmiştir.Çözümün ÖzellikleriOtomatik ZIP Açma: ZIP dosyalarını otomatik olarak açar ve içindeki tüm CSV dosyalarını işler.Toplu İşleme: ZIP dosyası deseni ile toplu işleme yapar (örn. /app/data/trip_*.zip).Hata Tekrar Deneme Mekanizması: Hata durumunda yapılandırılabilir tekrar deneme mekanizması içerir.Meta Veri Ekleme: Her satırın geldiği ZIP ve CSV dosyasını belirtmek için meta verileri ekler.Gönderim Hızı Kontrolü: Gönderim hızını ayarlamak için zaman aralığı kontrolü sunar.Docker Entegrasyonu: Docker ile kolay çalıştırma ve dağıtım imkanı sağlar.Batch Gönderimi: Verileri 1000'er satırlık gruplar halinde göndererek performansı artırır.Paralel İşleme:Farklı klasörlerdeki ZIP dosyalarını aynı anda (paralel olarak) işler.Bir ZIP dosyasının içindeki birden fazla CSV dosyasını paralel olarak işler.Dosya YapısıÇözüm aşağıdaki dosyalardan oluşmaktadır:streamer.py: Ana Python kodu.Dockerfile: Docker konteyner yapılandırması.requirements.txt: Gerekli Python kütüphaneleri.run_docker.sh: Docker'ı çalıştırmak için örnek betik (isteğe bağlı, Docker Compose tercih edilir).docker-compose.yml: Docker Compose ile çalıştırma yapılandırması.Kullanım Talimatları1. Dosyaları KaydetmeYukarıdaki dosyaları projenizin ana dizinine kaydedin.2. Gerekli Ortam Değişkenlerini AyarlamaÇözümün çalışması için aşağıdaki ortam değişkenlerinin ayarlanması gerekmektedir:FABRIC_EVENTHUB_CONNECTION_STRING: EventHub bağlantı dizesi.FABRIC_EVENTHUB_NAME: EventHub adı.ZIP_FILES: İşlenecek ZIP dosyası desenleri (örn. /app/data/trip_*.zip veya /app/data1/trip_*.zip,/app/data2/trip_*.zip paralel işleme için).SEND_INTERVAL: Her gönderim arasındaki bekleme süresi (saniye).MAX_RETRIES: Hata durumunda tekrar deneme sayısı.RETRY_DELAY: Tekrar denemeler arası bekleme süresi (saniye).BATCH_SIZE: Her gönderimde kaç satır birleştirilecek (varsayılan: 1000).MAX_CONCURRENT_FILES: Aynı anda işlenecek maksimum ZIP dosyası sayısı (varsayılan: 10).3. Docker ile Çalıştırmadocker build -t fabric-eventhub-streamer .
docker run -it --rm \
  -e FABRIC_EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
  -e FABRIC_EVENTHUB_NAME="your-eventhub-name" \
  -e ZIP_FILES="/app/data/trip_*.zip" \
  -e BATCH_SIZE=1000 \
  -e SEND_INTERVAL=0.1 \
  -e MAX_CONCURRENT_FILES=10 \
  -v /path/to/your/zip/files:/app/data \
  fabric-eventhub-streamer
Not: /path/to/your/zip/files yerine ZIP dosyalarınızın bulunduğu gerçek yolu belirtmelisiniz.4. Docker Compose ile Çalıştırma (Önerilen)docker-compose.yml dosyasını aşağıdaki gibi yapılandırın ve çalıştırın:version: '3'
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
Ardından, terminalde docker-compose.yml dosyasının bulunduğu dizinde aşağıdaki komutu çalıştırın:docker-compose up
Bu örnekte, data1 ve data2 adında iki klasörünüz olduğu ve bu klasörlerin içinde trip_*.zip desenine uyan ZIP dosyaları bulunduğu varsayılmıştır.Yeni Özellikler Detayları1. Batch Gönderimi (1000'er Satır)Veriler artık tek tek satır yerine, BATCH_SIZE (varsayılan 1000) kadar satırlık gruplar halinde EventStream'e gönderilmektedir. Bu, veri gönderim hızını önemli ölçüde artırır ve EventStream'in toplu işleme yeteneklerinden daha iyi faydalanır. Her batch gönderiminde kaç satır gönderildiği ve toplam gönderilen satır sayısı konsola raporlanır.2. Paralel İşlemeİki seviyeli paralel işleme eklenmiştir:ZIP Dosyası Seviyesinde Paralellik: MAX_CONCURRENT_FILES parametresi ile aynı anda kaç ZIP dosyasının işlenebileceği kontrol edilir. ZIP_FILES ortam değişkenine virgülle ayrılmış birden fazla dosya deseni (örn. /app/data1/trip_*.zip,/app/data2/trip_*.zip) vererek farklı klasörlerdeki dosyaları aynı anda işleyebilirsiniz.CSV Dosyası Seviyesinde Paralellik: Bir ZIP dosyasının içindeki tüm CSV dosyaları paralel olarak işlenir. Her CSV dosyası için ayrı asenkron görevler oluşturulur, bu da ZIP içeriği işlemesini hızlandırır.SonuçBu güncellemelerle sistemin önemli ölçüde daha hızlı çalışmasını bekleyebilirsiniz. İhtiyacınıza göre BATCH_SIZE ve MAX_CONCURRENT_FILES değerlerini ayarlayarak performansı optimize edebilirsiniz. Daha büyük batch boyutu ve daha fazla paralel işleme daha hızlı veri gönderimi sağlar, ancak sistem kaynaklarını da daha fazla kullanabilir.
