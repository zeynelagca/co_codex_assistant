# Coflow Cafeteria Turnstile (ZKTeco K70)
- Kart/UID yönetimi (müşteri bağlantılı)
- Geçiş (transaction) kayıtları
- Aylık fatura üretimi (wizard)
- Partner formuna kart sekmesi
- Cron placeholder (ZKTeco K70 entegrasyonuna hazır)

## Kurulum
1) Bu klasörü `addons` altına atın: `coflow_cafeteria_turnstile`
2) Uygulamalar > Modül adı ile arayıp yükleyin.

## ZKTeco K70 Entegrasyon İpuçları
Python tarafında `pyzk` (veya uygun SDK) kullanılabilir. Örnek pseudo:
```python
from pyzk.zk import ZK
def fetch(ip, port=4370):
    zk = ZK(ip, port=port, timeout=5)
    conn = zk.connect()
    for a in conn.get_attendance() or []:
        yield {'uid': a.user_id, 'ts': a.timestamp}
    conn.disconnect()
```

Alınan `uid` ile `cafeteria.card(name==uid)` bulunur; eşleşirse `cafeteria.transaction` oluşturulur.

## Faturalama
- Wizard üzerinden müşteri ve tarih aralığı seçilir.
- Ürün seçilirse: tek satır, adet = geçiş sayısı, birim fiyat = ürün liste fiyatı.
- Ürün seçilmezse: kart bazlı toplam tutar satırları (transaction.price toplamı).

## Notlar
- Güvenlik/roller ve liste görünümleri temel seviye tanımlıdır.
- İhtiyaca göre bakiye yönetimi, online tahsilat, rapor/export eklentileri yapılabilir.