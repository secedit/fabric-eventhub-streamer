import asyncio
import os
import json
import csv
import time
import zipfile
import io
import glob
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData, EventDataBatch

# Fabric Eventstream'den (Event Hubs) alınan bağlantı bilgileri
EVENTHUB_CONNECTION_STRING = os.environ.get("FABRIC_EVENTHUB_CONNECTION_STRING")
EVENTHUB_NAME = os.environ.get("FABRIC_EVENTHUB_NAME")

# ZIP dosyalarının yolları (Docker içindeki yollar) - Birden fazla klasör deseni
ZIP_FILE_PATTERNS = os.environ.get("ZIP_FILES", "/app/data1/trip_*.zip,/app/data2/trip_*.zip").split(',')
ZIP_FILE_PATHS = []
for pattern in ZIP_FILE_PATTERNS:
    ZIP_FILE_PATHS.extend(glob.glob(pattern.strip()))

# Her batch gönderimdeki satır sayısı
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "1000"))  # 1000 satırlık gruplar

# Her olay gönderimi arasında beklenecek saniye (isteğe bağlı)
SEND_INTERVAL = float(os.environ.get("SEND_INTERVAL", "0.1"))  # Saniyede 10 olay varsayılan

# Başarısız olunca tekrar deneme parametreleri
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", "1.0"))  # saniye

# Paralel işleme ayarları
MAX_CONCURRENT_FILES = int(os.environ.get("MAX_CONCURRENT_FILES", "10"))  # Aynı anda işlenecek maksimum dosya sayısı

async def send_csv_data_to_eventhub(producer, csv_content, source_zip, csv_name):
    """CSV içeriğini 1000'er satırlık batch'ler halinde Event Hub'a gönderir."""
    print(f"'{source_zip}' içindeki '{csv_name}' verileri okunuyor ve gönderiliyor...")
    
    try:
        # CSV içeriğini satırlara ayır
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        batch = []
        total_sent = 0
        batch_count = 0
        
        for row_number, row_dict in enumerate(reader):
            # Veriye kaynak dosya bilgisini ekleyelim
            row_dict["_source_zip"] = os.path.basename(source_zip)
            row_dict["_source_csv"] = csv_name
            row_dict["_row_number"] = row_number + 1  # 1-tabanlı satır numarası
            
            # Satırı batch'e ekle
            batch.append(row_dict)
            
            # Batch dolduysa veya son satırsa gönder
            if len(batch) >= BATCH_SIZE or row_number == total_sent + len(batch) - 1:
                batch_count += 1
                
                # Yeniden deneme mantığı
                retries = 0
                while retries <= MAX_RETRIES:
                    try:
                        # Batch'i oluştur
                        event_data_batch = await producer.create_batch()
                        
                        # Batch'deki tüm kayıtları ekle
                        for record in batch:
                            event_data = EventData(json.dumps(record))
                            # Eğer batch doluysa, yeni bir batch oluştur ve gönder
                            if not event_data_batch.try_add(event_data):
                                # Mevcut batch'i gönder
                                await producer.send_batch(event_data_batch)
                                # Yeni batch oluştur
                                event_data_batch = await producer.create_batch()
                                # Bu kaydı yeni batch'e ekle
                                event_data_batch.try_add(event_data)
                        
                        # Kalan batch'i gönder
                        if len(event_data_batch) > 0:
                            await producer.send_batch(event_data_batch)
                            
                        total_sent += len(batch)
                        print(f"  Gönderildi ({csv_name} - Batch {batch_count}, {len(batch)} satır, Toplam: {total_sent})")
                        
                        # Batch'ler arası bekleme
                        if SEND_INTERVAL > 0:
                            await asyncio.sleep(SEND_INTERVAL)
                        
                        # Batch'i temizle
                        batch = []
                        break  # Başarılı gönderim, döngüden çık
                        
                    except Exception as e:
                        retries += 1
                        if retries > MAX_RETRIES:
                            print(f"  Son deneme başarısız oldu (Batch {batch_count}): {e}")
                            raise
                        print(f"  Deneme {retries}/{MAX_RETRIES} başarısız (Batch {batch_count}): {e}, {RETRY_DELAY}s sonra tekrar denenecek")
                        await asyncio.sleep(RETRY_DELAY)
                
        print(f"'{source_zip}' içindeki '{csv_name}' dosyasındaki {total_sent} satır gönderildi. ({batch_count} batch)")
        
    except Exception as e:
        print(f"Hata ('{source_zip}' içindeki '{csv_name}' işlenirken): {e}")
        raise

async def process_zip_file(producer, zip_path):
    """ZIP dosyasını açar ve içindeki her CSV dosyasını işler."""
    try:
        print(f"ZIP dosyası açılıyor: {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # ZIP içindeki tüm dosyaları listele
            file_list = zip_ref.namelist()
            csv_files = [f for f in file_list if f.lower().endswith('.csv')]
            
            if not csv_files:
                print(f"Uyarı: '{zip_path}' içinde CSV dosyası bulunamadı.")
                return
                
            print(f"'{zip_path}' içinde {len(csv_files)} CSV dosyası bulundu: {csv_files}")
            
            # Her CSV dosyasını işle - burada paralellik ekleyebiliriz
            tasks = []
            for csv_name in csv_files:
                try:
                    # CSV dosyasını okuma
                    with zip_ref.open(csv_name) as csv_file:
                        # Binary içeriği text'e çevir
                        csv_content = csv_file.read().decode('utf-8')
                        
                        # Her CSV için asenkron görev oluştur
                        task = asyncio.create_task(
                            send_csv_data_to_eventhub(producer, csv_content, zip_path, csv_name)
                        )
                        tasks.append(task)
                        
                except Exception as e:
                    print(f"Hata: '{zip_path}' içindeki '{csv_name}' dosyası açılırken: {e}")
                    continue
            
            # Tüm CSV dosyaları için görevleri bekle
            if tasks:
                await asyncio.gather(*tasks)
                    
    except zipfile.BadZipFile:
        print(f"Hata: '{zip_path}' geçerli bir ZIP dosyası değil.")
    except Exception as e:
        print(f"Hata: '{zip_path}' işlenirken: {e}")

async def main():
    """Ana program fonksiyonu - paralel dosya işleme ile."""
    if not EVENTHUB_CONNECTION_STRING or not EVENTHUB_NAME:
        print("Hata: FABRIC_EVENTHUB_CONNECTION_STRING ve FABRIC_EVENTHUB_NAME ortam değişkenleri ayarlanmalıdır.")
        return
        
    if not ZIP_FILE_PATHS:
        print(f"Hata: Gönderilecek ZIP dosyası bulunamadı. Patterns: {ZIP_FILE_PATTERNS}")
        return
        
    print(f"İşlenecek {len(ZIP_FILE_PATHS)} ZIP dosyası bulundu.")
    
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENTHUB_CONNECTION_STRING, 
        eventhub_name=EVENTHUB_NAME
    )
    
    async with producer:
        try:
            # Dosyaları paralel işleme için semaforu oluştur
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_FILES)
            
            # Semaforu kullanan yardımcı fonksiyon
            async def process_with_semaphore(zip_path):
                async with semaphore:
                    return await process_zip_file(producer, zip_path)
            
            # Tüm ZIP dosyaları için görevler oluştur
            tasks = [
                asyncio.create_task(process_with_semaphore(zip_path)) 
                for zip_path in ZIP_FILE_PATHS
            ]
            
            # Tüm görevleri bekle
            await asyncio.gather(*tasks)
                
            print("Tüm ZIP dosyalarının gönderimi tamamlandı.")
            
        except KeyboardInterrupt:
            print("\nGönderim kullanıcı tarafından durduruldu.")
        except Exception as e:
            print(f"Ana programda bir hata oluştu: {e}")

if __name__ == "__main__":
    asyncio.run(main())
