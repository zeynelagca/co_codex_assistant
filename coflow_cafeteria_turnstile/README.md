# Coflow Catering Turnstile (ZKTeco K70)

- Kart/UID yönetimi (müşteri bağlantılı)
- Geçiş kayıtları ve bakiye takibi
- Aylık fatura sihirbazı
- Partner formunda catering kart sekmesi
- ZKTeco K70 entegrasyonuna hazır cron şablonları

## Kurulum
1. Bu klasörü `addons` altına kopyalayın: `coflow_cafeteria_turnstile`
2. Uygulamalar menüsünde **Catering Turnike Yazılımı** modülünü arayıp yükleyin.

## ZKTeco K70 Entegrasyon İpuçları
Python tarafında `pyzk` (veya uygun SDK) kullanılabilir. Örnek pseudo kod:

```python
from pyzk.zk import ZK

def fetch(ip, port=4370):
    zk = ZK(ip, port=port, timeout=5)
    conn = zk.connect()
    for record in conn.get_attendance() or []:
        yield {'uid': record.user_id, 'ts': record.timestamp}
    conn.disconnect()
```

Alınan `uid` değeri ile `cafeteria.card(name == uid)` bulunur; eşleşirse `cafeteria.transaction` kaydı oluşturulur.

## Faturalama
- Sihirbaz üzerinden müşteri ve tarih aralığı seçilir.
- Ürün seçilirse: tek satır, adet = geçiş sayısı, birim fiyat = ürün liste fiyatı.
- Ürün seçilmezse: kart bazlı toplam tutar satırları (`transaction.price` toplamı).

## Notlar
- Güvenlik/roller ve liste görünümleri temel seviye tanımlıdır.
- İhtiyaca göre bakiye yönetimi, online tahsilat, rapor/export geliştirmeleri yapılabilir.
