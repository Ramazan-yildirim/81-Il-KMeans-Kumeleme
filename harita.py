"""Mevcut küme sonuçlarını il sınırları boyalı ek Türkiye haritalarında gösterir."""

import json
import math

from gorsellestirme import grafigi_kaydet

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path
import pandas as pd

from veri_indir import BOLGELER, KLASOR, SONUC, veriyi_oku

SINIR_DOSYASI = KLASOR / "data" / "il_sinirlari.geojson"


def sinirlari_oku(iller):
    with SINIR_DOSYASI.open(encoding="utf-8") as dosya:
        veri = json.load(dosya)
    ozellikler = veri.get("features", [])
    if veri.get("type") != "FeatureCollection" or len(ozellikler) != 81:
        raise ValueError("Sınır dosyasında 81 il geometrisi bulunmalı.")
    il_adlari = {il["plaka"]: il["ad"] for il in iller}
    sinirlar = {}
    for ozellik in ozellikler:
        bilgi = ozellik["properties"]
        iso = bilgi.get("shapeISO", "")
        if not iso.startswith("TR-") or not iso[3:].isdigit():
            raise ValueError(f"Sınır dosyasında geçersiz il kodu: {iso}")
        plaka = int(iso[3:])
        # Kaynakta Hakkâri yazılır; il CSV'sindeki karşılığı Hakkari'dir.
        ad = bilgi.get("shapeName", "").replace("â", "a")
        if plaka in sinirlar or il_adlari.get(plaka) != ad:
            raise ValueError(f"Sınır dosyasında tekrarlanan/eşleşmeyen il: {iso}, {ad}")
        geometri = ozellik.get("geometry") or {}
        if geometri.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"Desteklenmeyen il geometrisi: {ad}")
        sinirlar[plaka] = geometri
    if set(sinirlar) != set(il_adlari):
        raise ValueError("Sınır verisiyle il CSV'sinin plaka kodları eşleşmiyor.")
    return sinirlar


def poligon_yollari(geometri):
    """Adaları ve göl gibi iç boşlukları koruyarak Matplotlib yolları oluşturur."""
    poligonlar = geometri["coordinates"]
    if geometri["type"] == "Polygon":
        poligonlar = [poligonlar]
    yollar = []
    for poligon in poligonlar:
        noktalar, kodlar = [], []
        for no, halka in enumerate(poligon):
            if len(halka) < 4 or halka[0] != halka[-1]:
                raise ValueError("İl sınırı kapalı bir koordinat halkası olmalı.")
            if any(len(p) != 2 or not all(math.isfinite(v) for v in p)
                   or not (25 <= p[0] <= 45.5 and 35 <= p[1] <= 43) for p in halka):
                raise ValueError("İl sınırında geçersiz koordinat var.")
            alan = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(halka, halka[1:]))
            # Dış sınır saat yönünün tersine, iç boşluk saat yönünde çizilir.
            if (no == 0 and alan < 0) or (no > 0 and alan > 0):
                halka = list(reversed(halka))
            noktalar.extend(halka)
            kodlar.extend([Path.MOVETO] + [Path.LINETO] * (len(halka) - 2) + [Path.CLOSEPOLY])
        yollar.append(Path(noktalar, kodlar))
    if not yollar:
        raise ValueError("İl geometrisi boş olamaz.")
    return yollar


def il_haritasi(iller, yollar, gruplar, adlar, baslik, dosya_adi, merkezler=None):
    fig, ax = plt.subplots(figsize=(15, 7.5))
    renkler = plt.get_cmap("tab10")
    for il in iller:
        grup = gruplar[il["plaka"]]
        for yol in yollar[il["plaka"]]:
            ax.add_patch(PathPatch(yol, facecolor=renkler(grup), edgecolor="#ffffff",
                                   linewidth=0.65, joinstyle="round"))
        ax.text(il["x"], il["y"], str(il["plaka"]), ha="center", va="center",
                fontsize=7, color="#202b33", weight="bold", zorder=3,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1})

    aciklamalar = [Patch(facecolor=renkler(i), label=f"{ad} ({sum(g == i for g in gruplar.values())} il)")
                   for i, ad in enumerate(adlar)]
    if merkezler is not None:
        ax.scatter(merkezler[:, 0], merkezler[:, 1], marker="X", s=120,
                   color="#172c3a", edgecolors="white", linewidths=1, zorder=4)
        aciklamalar.append(Line2D([], [], marker="X", linestyle="none", color="#172c3a",
                                 markeredgecolor="white", markersize=10, label="Küme merkezleri"))
    ax.legend(handles=aciklamalar, loc="upper left", bbox_to_anchor=(1.01, 0.9),
              frameon=False, fontsize=9, labelspacing=1.1)
    ax.set(xlim=(25.4, 45.1), ylim=(35.6, 42.5))
    # 39° referans enlemiyle eş dikdörtgen gösterim: boylamın görsel ölçeği düzeltilir.
    ax.set_aspect(1 / math.cos(math.radians(39)))
    ax.set_title(baslik, loc="left", fontsize=16, weight="bold", pad=18)
    ax.axis("off")
    ax.text(34, 42.15, "K A R A D E N İ Z", fontsize=10, color="#7b939e", ha="center")
    ax.text(31, 35.85, "A K D E N İ Z", fontsize=10, color="#7b939e", ha="center")
    ax.text(25.7, 38, "EGE DENİZİ", fontsize=9, rotation=90, color="#7b939e", ha="center")
    not_metni = ("İl merkezi için hesaplanan küme, ilin tamamına uygulanır." if merkezler is not None
                 else "İller kaynak verinin bölge etiketiyle boyanır; coğrafi bölge sınırları farklı olabilir.")
    ax.text(0, -0.04, "Sayılar plaka kodlarıdır. " + not_metni + "\n"
            "Sınırlar: geoBoundaries / © OpenStreetMap contributors · 2021 · Sadeleştirilmiş ADM1 geometrileri.",
            transform=ax.transAxes, fontsize=8, color="#536771", linespacing=1.6)
    grafigi_kaydet(fig, dosya_adi)


def haritalari_uret(iller=None):
    iller = veriyi_oku() if iller is None else iller
    sinirlar = sinirlari_oku(iller)
    yollar = {plaka: poligon_yollari(geometri) for plaka, geometri in sinirlar.items()}
    bolgeler = list(BOLGELER.values())
    il_haritasi(iller, yollar,
                {il["plaka"]: bolgeler.index(il["gercek_bolge"]) for il in iller}, bolgeler,
                "Mevcut 7 Coğrafi Bölge · İl Alanları", "harita_gercek_bolgeler.png")
    for kok, baslik, png in [
        ("manuel_kumeler", "Manuel K-Means · K=7", "harita_manuel_7_kume.png"),
        ("optimize_7_kume", "scikit-learn · Aynı Başlangıç · K=7", "harita_optimize_7_kume.png"),
        ("optimize_iyilestirilmis", "scikit-learn · k-means++ / 20 Başlangıç · K=7", "harita_iyilestirilmis_7_kume.png"),
    ]:
        dosya = SONUC / f"{kok}.csv"
        merkez_dosyasi = SONUC / f"{kok}_merkezler.csv"
        if not dosya.exists() or not merkez_dosyasi.exists():
            raise FileNotFoundError("Küme sonuçları eksik. Önce python main.py çalıştırın.")
        veri = pd.read_csv(dosya)
        if len(veri) != 81 or veri["il"].duplicated().any() or set(veri["il"]) != {il["ad"] for il in iller}:
            raise ValueError(f"{dosya.name}: 81 il ile küme sonuçları eşleşmiyor.")
        veri = veri.set_index("il").loc[[il["ad"] for il in iller]]
        etiketler = veri["atanan_kume"]
        if etiketler.isna().any() or not etiketler.isin(range(1, 8)).all():
            raise ValueError(f"{dosya.name}: küme numaraları 1–7 arasında olmalı.")
        merkezler = pd.read_csv(merkez_dosyasi).sort_values("kume")[["boylam", "enlem"]].to_numpy()
        gruplar = {il["plaka"]: int(etiket) - 1 for il, etiket in zip(iller, etiketler)}
        il_haritasi(iller, yollar, gruplar, [f"Küme {no}" for no in range(1, 8)],
                    baslik, png, merkezler)
    print("İl sınırları boyalı 4 ek harita sonuclar/grafikler klasörüne kaydedildi.")


if __name__ == "__main__":
    haritalari_uret()
