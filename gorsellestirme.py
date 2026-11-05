"""Grafikleri pencere açmadan PNG olarak kaydeder."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from veri_indir import BOLGELER, SONUC, veriyi_oku

GRAFIK = SONUC / "grafikler"


def grafigi_kaydet(fig, dosya_adi):
    GRAFIK.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(GRAFIK / dosya_adi, dpi=160, bbox_inches="tight")
    plt.close(fig)


def koordinat_ekseni(baslik):
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set(title=baslik, xlabel="Boylam (°)", ylabel="Enlem (°)")
    ax.set_xlim(25.5, 45)
    ax.set_ylim(35.7, 42.6)
    ax.grid(alpha=0.2)
    ax.set_axisbelow(True)
    return fig, ax


def dagilim_grafigi(iller):
    fig, ax = koordinat_ekseni("Türkiye'nin 81 İl Merkezinin Koordinat Dağılımı")
    ax.scatter([il["x"] for il in iller], [il["y"] for il in iller], s=25, color="#176a91")
    # Plaka kodları, yakın noktaların uzun il adlarıyla örtüşmesini azaltır.
    for il in iller:
        ax.annotate(str(il["plaka"]), (il["x"], il["y"]), xytext=(3, 4),
                    textcoords="offset points", fontsize=7)
    ax.text(0, -0.13, "Sayılar plaka kodlarıdır. Noktalar il merkezleridir; il sınırları çizilmemiştir.",
            transform=ax.transAxes, fontsize=9)
    grafigi_kaydet(fig, "il_dagilimi.png")


def kume_grafigi(iller, sonuc, baslik, dosya_adi):
    fig, ax = koordinat_ekseni(baslik)
    renkler = plt.get_cmap("tab10")
    for no, merkez in enumerate(sonuc["merkezler"]):
        grup = [il for il, e in zip(iller, sonuc["etiketler"]) if e == no]
        ax.scatter([il["x"] for il in grup], [il["y"] for il in grup], s=36,
                   color=renkler(no), label=f"Küme {no + 1} ({len(grup)} il)")
        ax.scatter(*merkez, marker="X", s=160, color=renkler(no), edgecolors="black",
                   linewidths=1.3, zorder=4)
        ax.annotate(str(no + 1), merkez, xytext=(6, 7), textcoords="offset points",
                    fontsize=10, weight="bold")
    ax.scatter([], [], marker="X", color="white", edgecolors="black", s=100, label="Küme merkezi")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=9)
    grafigi_kaydet(fig, dosya_adi)


def bolge_grafigi(iller):
    fig, ax = koordinat_ekseni("Karşılaştırma: Mevcut 7 Coğrafi Bölge")
    for no, bolge in enumerate(BOLGELER.values()):
        grup = [il for il in iller if il["gercek_bolge"] == bolge]
        ax.scatter([il["x"] for il in grup], [il["y"] for il in grup],
                   color=plt.get_cmap("tab10")(no), s=36, label=f"{bolge} ({len(grup)} il)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=9)
    grafigi_kaydet(fig, "gercek_bolgeler.png")


def k_grafikleri(olcumler, en_iyi_k, dirsek_k):
    for sutun, baslik, y_adi, dosya, secim in [
        ("inertia", "Elbow Yöntemi: K ile WCSS Değişimi", "WCSS (derece²)", "elbow.png", dirsek_k),
        ("silhouette", "Silhouette Score ile K Araştırması", "Ortalama Silhouette Score", "k_secimi.png", en_iyi_k),
    ]:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(olcumler["K"], olcumler[sutun], marker="o", color="#176a91")
        ax.axvline(secim, color="#ba4d25", linestyle="--", label=f"Aday K={secim}")
        ax.axvline(7, color="gray", linestyle=":", label="Coğrafi bölge sayısı: 7")
        ax.set(title=baslik, xlabel="K (küme sayısı)", ylabel=y_adi, xticks=olcumler["K"])
        ax.grid(alpha=0.2)
        ax.legend()
        grafigi_kaydet(fig, dosya)


def bolge_karsilastirma_grafigi(tablolar):
    fig, axes = plt.subplots(1, len(tablolar), figsize=(6 * len(tablolar), 5.5), squeeze=False)
    for ax, (ad, tablo) in zip(axes[0], tablolar.items()):
        ax.imshow(tablo.values, cmap="Blues", vmin=0, vmax=18)
        ax.set(title=ad, xlabel="Küme numarası", xticks=range(7), xticklabels=range(1, 8),
               yticks=range(7), yticklabels=[b.replace(" Bölgesi", "") for b in tablo.index])
        for i, satir in enumerate(tablo.values):
            for j, adet in enumerate(satir):
                ax.text(j, i, str(adet), ha="center", va="center",
                        color="white" if adet > 9 else "black", fontsize=9)
    fig.suptitle("Coğrafi Bölge – Küme Dağılımı (hücreler il sayısıdır)")
    grafigi_kaydet(fig, "bolge_karsilastirma.png")


def main():
    iller = veriyi_oku()
    dagilim_grafigi(iller)
    bolge_grafigi(iller)
    # Kaydedilmiş küme sonuçları varsa onları da yeniden çizer.
    for kok, baslik, dosya in [
        ("manuel_kumeler", "Manuel K-Means (K=7)", "manuel_7_kume.png"),
        ("optimize_7_kume", "scikit-learn: Aynı Başlangıç (K=7)", "optimize_7_kume.png"),
        ("optimize_iyilestirilmis", "scikit-learn: k-means++ / 20 Başlangıç (K=7)", "iyilestirilmis_7_kume.png"),
    ]:
        yol = SONUC / f"{kok}.csv"
        merkez_yolu = SONUC / f"{kok}_merkezler.csv"
        if yol.exists() and merkez_yolu.exists():
            veri = pd.read_csv(yol).set_index("il").loc[[il["ad"] for il in iller]]
            merkezler = pd.read_csv(merkez_yolu)[["boylam", "enlem"]].values
            kume_grafigi(iller, {"etiketler": veri["atanan_kume"].values - 1,
                                "merkezler": merkezler}, baslik, dosya)
    if (SONUC / "k_karsilastirma.csv").exists():
        from kmeans_optimize import dirsek_adayi

        olcumler = pd.read_csv(SONUC / "k_karsilastirma.csv")
        en_iyi_k = int(olcumler.loc[olcumler["silhouette"].idxmax(), "K"])
        k_grafikleri(olcumler, en_iyi_k, dirsek_adayi(olcumler))
    if (SONUC / "bolge_karsilastirma.csv").exists():
        veri = pd.read_csv(SONUC / "bolge_karsilastirma.csv")
        tablolar = {ad: grup.set_index("bolge").drop(columns="yontem")
                    for ad, grup in veri.groupby("yontem", sort=False)}
        bolge_karsilastirma_grafigi(tablolar)
    print(f"Grafikler kaydedildi: {GRAFIK}")


if __name__ == "__main__":
    main()
