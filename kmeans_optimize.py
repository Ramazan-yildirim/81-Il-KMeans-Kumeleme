"""Aynı başlangıçla KMeans karşılaştırması, K araştırması ve bölge analizi."""

import os
import platform
from datetime import datetime, timedelta, timezone
from statistics import median
from time import perf_counter

# Küçük deneyde tek çekirdek yeterli; Windows'ta gereksiz çekirdek sorgusunu önler.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from threadpoolctl import threadpool_limits

from gorsellestirme import (bolge_grafigi, bolge_karsilastirma_grafigi,
                            dagilim_grafigi, k_grafikleri, kume_grafigi)
from kmeans_manuel import (K, MAKSIMUM_TEKRAR, SEED, baslangic_merkezlerini_sec,
                           kmeans, kumeleri_yazdir, sonucu_kaydet)
from veri_indir import BOLGELER, SONUC, veriyi_oku

OLCUM_TEKRARI = 15


def hazir_kmeans(noktalar, k=K, baslangic="k-means++", n_init=20):
    return KMeans(n_clusters=k, init=baslangic, n_init=n_init, random_state=SEED,
                  max_iter=MAKSIMUM_TEKRAR, tol=0.0, algorithm="lloyd").fit(noktalar)


def sure_olc(islem):
    """Bir ısınma çalıştırması sonrası 15 ölçümün medyanını alır (yalnız hesap)."""
    islem()
    sureler = []
    for _ in range(OLCUM_TEKRARI):
        basla = perf_counter()
        sonuc = islem()
        sureler.append(perf_counter() - basla)
    return sonuc, median(sureler) * 1000


def model_sonucu(model):
    return {"etiketler": model.labels_, "merkezler": model.cluster_centers_,
            "iterasyon": model.n_iter_, "inertia": model.inertia_}


def dirsek_adayi(olcumler):
    """Normalize WCSS eğrisinde, uçları birleştiren doğrudan en uzak K: bir öneri."""
    kler = olcumler["K"].to_numpy()
    wcss = olcumler["inertia"].to_numpy()
    if wcss[0] == wcss[-1]:
        return int(kler[0])
    x = (kler - kler[0]) / (kler[-1] - kler[0])
    y = (wcss - wcss[-1]) / (wcss[0] - wcss[-1])
    uzakliklar = np.abs(x + y - 1) / np.sqrt(2)
    return int(kler[np.argmax(uzakliklar)])


def bolge_tablosu(iller, etiketler):
    tablo = pd.crosstab(pd.Series([il["gercek_bolge"] for il in iller], name="bolge"),
                        pd.Series(np.array(etiketler) + 1, name="kume"))
    return tablo.reindex(index=list(BOLGELER.values()), columns=range(1, K + 1), fill_value=0)


def main():
    iller = veriyi_oku()
    noktalar = [(il["x"], il["y"]) for il in iller]
    x = np.array(noktalar, dtype=float)
    gercek = [il["gercek_bolge"] for il in iller]
    baslangic = baslangic_merkezlerini_sec(noktalar)
    SONUC.mkdir(parents=True, exist_ok=True)
    print("Veri doğrulandı: 81 farklı il, 7 coğrafi bölge.")
    print("Ortak başlangıç illeri:", ", ".join(
        il["ad"] for merkez in baslangic for il in iller if (il["x"], il["y"]) == merkez))

    # Bu küçük veri için iş parçacığı başlatma maliyetini azaltır; ölçümde sabit tutulur.
    with threadpool_limits(limits=1):
        manuel, sure_manuel = sure_olc(lambda: kmeans(noktalar, baslangic=baslangic))
        ayni_model, sure_ayni = sure_olc(
            lambda: hazir_kmeans(x, baslangic=np.array(baslangic), n_init=1))
        iyi_model, sure_iyi = sure_olc(lambda: hazir_kmeans(x))
        sonuclar = {"Manuel": manuel, "Aynı başlangıç": model_sonucu(ayni_model),
                    "k-means++ (20 başlangıç)": model_sonucu(iyi_model)}
        sureler = [sure_manuel, sure_ayni, sure_iyi]

        kayitlar = []
        for ad, sonuc in sonuclar.items():
            kayitlar.append({"yontem": ad, "K": K,
                             "baslangic_sayisi": 20 if ad.startswith("k-means++") else 1,
                             "sure_medyan_ms": sureler[len(kayitlar)],
                             "iterasyon": sonuc["iterasyon"], "inertia": sonuc["inertia"],
                             "silhouette": silhouette_score(x, sonuc["etiketler"]),
                             "ARI": adjusted_rand_score(gercek, sonuc["etiketler"])})
        karsilastirma = pd.DataFrame(kayitlar)

        olcumler = []
        for k in range(2, 13):
            model = hazir_kmeans(x, k=k)
            olcumler.append({"K": k, "inertia": model.inertia_,
                             "silhouette": silhouette_score(x, model.labels_),
                             "iterasyon": model.n_iter_})
        olcumler = pd.DataFrame(olcumler)

    karsilastirma.to_csv(SONUC / "yontem_karsilastirma.csv", index=False, encoding="utf-8-sig")
    olcumler.to_csv(SONUC / "k_karsilastirma.csv", index=False, encoding="utf-8-sig")
    for (ad, sonuc), kok, png in zip(sonuclar.items(),
            ["manuel_kumeler", "optimize_7_kume", "optimize_iyilestirilmis"],
            ["manuel_7_kume.png", "optimize_7_kume.png", "iyilestirilmis_7_kume.png"]):
        sonucu_kaydet(iller, sonuc, kok)
        kume_grafigi(iller, sonuc, f"{ad} K-Means (K=7)", png)
        print(f"\n{ad}:")
        kumeleri_yazdir(iller, sonuc)

    tablolar = {ad: bolge_tablosu(iller, sonuc["etiketler"]) for ad, sonuc in sonuclar.items()}
    pd.concat([tablo.reset_index().assign(yontem=ad) for ad, tablo in tablolar.items()],
              ignore_index=True).to_csv(SONUC / "bolge_karsilastirma.csv",
                                        index=False, encoding="utf-8-sig")
    en_iyi = olcumler.loc[olcumler["silhouette"].idxmax()]
    dirsek_k = dirsek_adayi(olcumler)
    dagilim_grafigi(iller)
    bolge_grafigi(iller)
    k_grafikleri(olcumler, int(en_iyi["K"]), dirsek_k)
    bolge_karsilastirma_grafigi(tablolar)

    iki_yontem_ari = adjusted_rand_score(manuel["etiketler"], ayni_model.labels_)
    rapor = ["81 İL K-MEANS DENEY SONUÇLARI", "",
             f"Python {platform.python_version()}, NumPy {np.__version__}, "
             f"pandas {pd.__version__}, scikit-learn {sklearn.__version__}",
             f"seed={SEED}, max_iter={MAKSIMUM_TEKRAR}, tol=0, algorithm=lloyd",
             f"Süre: 1 ısınma + {OLCUM_TEKRARI} tekrarın medyanı; iş parçacığı sınırı=1.",
             "Dosya okuma, grafik ve ARI/silhouette hesabı süreye dahil değildir.",
             "20 başlangıcın süresi bütün başlangıçları; iterasyonu yalnız kazananı kapsar.",
             "", karsilastirma.to_string(index=False, float_format=lambda v: f"{v:.6f}"),
             "", f"Manuel / aynı başlangıç scikit-learn küme benzerliği (ARI): {iki_yontem_ari:.6f}",
             "", olcumler.to_string(index=False, float_format=lambda v: f"{v:.6f}"),
             "", f"Silhouette'a göre en iyi K={int(en_iyi['K'])}, skor={en_iyi['silhouette']:.6f}",
             f"Normalize Elbow eğrisinde doğruya uzaklıkla dirsek adayı: K={dirsek_k}.",
             "Dirsek adayı sezgiseldir; grafikle birlikte yorumlanmalıdır.",
             "K=7 en iyi olmak zorunda değildir; K-Means K değerini kendisi öğrenmez.",
             "ARI küme numaralarını bölge adlarıyla eşleştirmez; 1 tam uyum, 0 rastgele düzeydir.",
             "Bölgeler sadece uzaklıkla belirlenmez; iklim ve yer şekilleri de etkilidir.",
             "Her il tek bölge etiketiyle temsil edilmiştir; coğrafi sınırlar il sınırı değildir.",
             "Ham derece koordinatları ve Öklid uzaklığı kullanıldı; WCSS birimi derece²dir.",
             "81 noktalı ölçüm genel bir hız üstünlüğü kanıtlamaz; süreler makineye göre değişir."]
    for ad, tablo in tablolar.items():
        rapor.extend(["", f"{ad}: bölge-küme il sayıları", tablo.to_string()])
    rapor_metni = "\n".join(rapor)
    rapor_metni = "\n".join(satir.rstrip() for satir in rapor_metni.splitlines()) + "\n"
    (SONUC / "rapor.txt").write_text(rapor_metni, encoding="utf-8")
    # Markdown raporu da her deneyde gerçek ölçümlerden yeniden üretilir.
    zaman = datetime.now(timezone(timedelta(hours=3))).strftime("%d.%m.%Y %H:%M:%S")
    markdown = ["# 81 İl K-Means Deney Sonuçları", "",
                f"Çalıştırma zamanı: **{zaman} (Türkiye saati)**.", "",
                "## Veri ve deney koşulları", "",
                "81 farklı il ve yedi coğrafi bölge doğrulandı. Kullanılan alanlarda eksik değer yok.",
                "Girdiler il merkezlerinin boylam/enlem çiftleridir; bölge etiketleri eğitime katılmadı.",
                rapor[2], "", f"`seed={SEED}`, `max_iter={MAKSIMUM_TEKRAR}`, `tol=0`, `algorithm=lloyd`.",
                "İlk iki yönteme aynı yedi il başlangıç merkezi olarak verildi: " + ", ".join(
                    il["ad"] for merkez in baslangic for il in iller
                    if (il["x"], il["y"]) == merkez) + ".", "",
                f"Süreler bir ısınma çalıştırmasından sonra {OLCUM_TEKRARI} tekrarın medyanıdır. "
                "İş parçacığı sınırı 1; dosya okuma, çizim ve değerlendirme metrikleri ölçüm dışındadır.",
                "", "## K=7: yöntemlerin karşılaştırılması", ""]
    for kayit in kayitlar:
        markdown.extend([
            f"### {kayit['yontem']}", "",
            f"- Başlangıç sayısı: **{kayit['baslangic_sayisi']}**.",
            f"- Medyan süre: **{kayit['sure_medyan_ms']:.4f} ms**.",
            f"- İterasyon: **{kayit['iterasyon']}**.",
            f"- WCSS: **{kayit['inertia']:.6f}** derece².",
            f"- Silhouette: **{kayit['silhouette']:.6f}**.",
            f"- Gerçek bölgelere karşı ARI: **{kayit['ARI']:.6f}**.", ""])
    markdown.extend([
        f"Manuel ve aynı başlangıçlı scikit-learn çözümlerinin birbirine karşı ARI'si "
        f"**{iki_yontem_ari:.6f}** oldu. Bu ölçü küme numaralarının adlandırılmasından etkilenmez.", "",
        "20 başlangıçlı deney daha düşük WCSS arar; süre bütün denemeleri, iterasyon sayısı "
        "yalnız kazanan denemeyi kapsar. Farklı başlangıç stratejisiyle elde edilen kazanç, "
        "yalnızca uygulama hızına bağlanamaz. 81 noktalık süreler genel performans kanıtı değildir.",
        "", "## K=2–12 araştırması", "",
        "Her K için k-means++, 20 başlangıç ve aynı seed/durma ayarları kullanıldı.", ""])
    for olcum in olcumler.to_dict("records"):
        markdown.append(f"- **K={olcum['K']}**: WCSS={olcum['inertia']:.6f}; "
                        f"Silhouette={olcum['silhouette']:.6f}; iterasyon={olcum['iterasyon']}.")
    markdown.extend([
        "", f"Silhouette'a göre seçim **K={int(en_iyi['K'])}** "
        f"(skor **{en_iyi['silhouette']:.6f}**); Elbow dirsek adayı **K={dirsek_k}**.", "",
        "Dirsek, normalize WCSS eğrisinin uçlarını birleştiren doğruya en uzak noktayla önerilir; "
        "kesin optimum değildir. K=7, mevcut yedi bölgeyle karşılaştırmak için kullanılır. "
        "Bu veri ve ölçütlerle yedinin en iyi değer olması gerekmez; K-Means K'yi kendisi öğrenmez.",
        "", "## Coğrafi bölgelerle karşılaştırma", "",
        f"Manuel çözümde ARI **{kayitlar[0]['ARI']:.6f}**, 20 başlangıçlı çözümde "
        f"**{kayitlar[2]['ARI']:.6f}** bulundu. ARI bir doğruluk yüzdesi değildir; "
        "1 tam uyum, 0 rastgele etiketlemeye göre beklenen düzeydir; negatif de olabilir.", "",
        "İklim ve yer şekilleri gibi etkenler K-Means girdisinde bulunmaz. Her il, kaynak verinin "
        "tek bölge etiketiyle temsil edilir; coğrafi bölge ve il sınırları tam örtüşmez. "
        "Derece koordinatlarıyla Öklid uzaklığı kullanılması da yöntemin sınırıdır.", "",
        "[Bölge–küme il sayıları](bolge_karsilastirma.csv) ayrıntılı dağılımı gösterir.", "",
        "## Grafikler", ""])
    for ad, dosya in [("81 ilin dağılımı", "il_dagilimi.png"),
                     ("Manuel K-Means", "manuel_7_kume.png"),
                     ("Aynı başlangıçla scikit-learn", "optimize_7_kume.png"),
                     ("20 başlangıçlı scikit-learn", "iyilestirilmis_7_kume.png"),
                     ("Elbow", "elbow.png"), ("Silhouette", "k_secimi.png"),
                     ("Mevcut coğrafi bölgeler", "gercek_bolgeler.png"),
                     ("Bölge–küme dağılımı", "bolge_karsilastirma.png")]:
        markdown.extend([f"![{ad}](grafikler/{dosya})", ""])
    markdown.extend(["## Küme üyeleri ve merkezler", ""])
    for (ad, sonuc), kok in zip(sonuclar.items(),
            ["manuel_kumeler", "optimize_7_kume", "optimize_iyilestirilmis"]):
        markdown.extend([f"### {ad}", "",
                         f"[Üyelik CSV'si]({kok}.csv) · [Merkez CSV'si]({kok}_merkezler.csv)", ""])
        for no, merkez in enumerate(sonuc["merkezler"]):
            adlar = [il["ad"] for il, e in zip(iller, sonuc["etiketler"]) if e == no]
            markdown.append(f"- **Küme {no + 1} ({len(adlar)} il)**; merkez (boylam, enlem) "
                            f"= ({merkez[0]:.5f}, {merkez[1]:.5f}): {', '.join(adlar)}.")
        markdown.append("")
    markdown.extend(["## Diğer çıktılar", "",
                     "- [Yöntem ölçümleri](yontem_karsilastirma.csv)",
                     "- [K araştırmasının ölçümleri](k_karsilastirma.csv)",
                     "- [Düz metin raporu](rapor.txt)",
                     "- [Kurulum, yorumlar ve veri kaynakları](../README.md)"])
    (SONUC / "rapor.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print("\n" + "\n".join(rapor[:20]))
    print(f"\nTüm sonuçlar: {SONUC}")


if __name__ == "__main__":
    main()
