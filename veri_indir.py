"""İl verisini okur, doğrular ve istenirse kaynağından yeniden indirir."""

import csv
import io
import math
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

KLASOR = Path(__file__).resolve().parent
VERI = KLASOR / "data" / "iller.csv"
SONUC = KLASOR / "sonuclar"
URL = ("https://raw.githubusercontent.com/brkunver/turkiye-provinces-dataset/"
       "027db5990f8d220edde133d8e958ed37200ef0c2/data/provinces.csv")

BOLGELER = {
    "Marmara": "Marmara Bölgesi",
    "Aegean": "Ege Bölgesi",
    "Mediterranean": "Akdeniz Bölgesi",
    "Central Anatolia": "İç Anadolu Bölgesi",
    "Black Sea": "Karadeniz Bölgesi",
    "Eastern Anatolia": "Doğu Anadolu Bölgesi",
    "Southeastern Anatolia": "Güneydoğu Anadolu Bölgesi",
}

# Plaka sırası, satırların gerçekten Türkiye'nin 81 iline ait olduğunu denetler.
IL_ADLARI = (
    "Adana|Adıyaman|Afyonkarahisar|Ağrı|Amasya|Ankara|Antalya|Artvin|Aydın|"
    "Balıkesir|Bilecik|Bingöl|Bitlis|Bolu|Burdur|Bursa|Çanakkale|Çankırı|Çorum|"
    "Denizli|Diyarbakır|Edirne|Elazığ|Erzincan|Erzurum|Eskişehir|Gaziantep|"
    "Giresun|Gümüşhane|Hakkari|Hatay|Isparta|Mersin|İstanbul|İzmir|Kars|"
    "Kastamonu|Kayseri|Kırklareli|Kırşehir|Kocaeli|Konya|Kütahya|Malatya|"
    "Manisa|Kahramanmaraş|Mardin|Muğla|Muş|Nevşehir|Niğde|Ordu|Rize|Sakarya|"
    "Samsun|Siirt|Sinop|Sivas|Tekirdağ|Tokat|Trabzon|Tunceli|Şanlıurfa|Uşak|"
    "Van|Yozgat|Zonguldak|Aksaray|Bayburt|Karaman|Kırıkkale|Batman|Şırnak|"
    "Bartın|Ardahan|Iğdır|Yalova|Karabük|Kilis|Osmaniye|Düzce"
).split("|")


def veriyi_dogrula(okuyucu):
    """CSV okuyucusunu denetler, kullanılan alanları sayısal biçime çevirir."""
    gerekli = {"province_name", "plate_code", "latitude", "longitude", "region"}
    if not gerekli.issubset(okuyucu.fieldnames or []):
        raise ValueError("CSV sütunları eksik: " + ", ".join(sorted(gerekli)))
    iller = []
    for sira, satir in enumerate(okuyucu, start=2):
        if any(not (satir.get(alan) or "").strip() for alan in gerekli):
            raise ValueError(f"CSV satır {sira}: kullanılan alanlarda eksik değer var.")
        try:
            plaka = int(satir["plate_code"])
            enlem = float(satir["latitude"])
            boylam = float(satir["longitude"])
        except ValueError as hata:
            raise ValueError(f"CSV satır {sira}: plaka veya koordinat sayısal değil.") from hata
        ad = satir["province_name"].strip()
        bolge = satir["region"].strip()
        if not 1 <= plaka <= 81 or IL_ADLARI[plaka - 1] != ad:
            raise ValueError(f"CSV satır {sira}: il adı ile plaka eşleşmiyor ({ad}).")
        if bolge not in BOLGELER:
            raise ValueError(f"CSV satır {sira}: bilinmeyen coğrafi bölge ({bolge}).")
        if not (math.isfinite(enlem) and math.isfinite(boylam)
                and 35.5 <= enlem <= 42.5 and 25.5 <= boylam <= 45):
            raise ValueError(f"CSV satır {sira}: Türkiye sınırları dışında/geçersiz koordinat.")
        iller.append({"ad": ad, "plaka": plaka, "x": boylam, "y": enlem,
                      "gercek_bolge": BOLGELER[bolge]})
    if len(iller) != 81 or len({il["plaka"] for il in iller}) != 81:
        raise ValueError("Veride 1–81 plaka kodlarıyla 81 farklı il bulunmalı.")
    if len({(il["x"], il["y"]) for il in iller}) != 81:
        raise ValueError("Birden fazla il için aynı koordinat verilmiş.")
    if {il["gercek_bolge"] for il in iller} != set(BOLGELER.values()):
        raise ValueError("Veride 7 coğrafi bölgenin tamamı bulunmalı.")
    return sorted(iller, key=lambda il: il["plaka"])


def veriyi_oku(yol=VERI):
    try:
        with Path(yol).open(encoding="utf-8-sig", newline="") as dosya:
            return veriyi_dogrula(csv.DictReader(dosya))
    except FileNotFoundError as hata:
        raise FileNotFoundError("Veri bulunamadı. Önce python veri_indir.py çalıştırın.") from hata


def veri_indir():
    istek = Request(URL, headers={"User-Agent": "81-Il-KMeans/1.0"})
    try:
        with urlopen(istek, timeout=30) as yanit:
            icerik = yanit.read()
    except URLError as hata:
        raise RuntimeError("Veri indirilemedi. İnternet bağlantısını/kaynak adresini kontrol edin.") from hata
    # İndirme hatalıysa mevcut, çalışan CSV'nin üzerine yazma.
    iller = veriyi_dogrula(csv.DictReader(io.StringIO(icerik.decode("utf-8-sig"))))
    VERI.parent.mkdir(parents=True, exist_ok=True)
    VERI.write_bytes(icerik)
    print(f"Doğrulandı ve kaydedildi: {len(iller)} il, 7 bölge -> {VERI}")


if __name__ == "__main__":
    veri_indir()
