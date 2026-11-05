"""K-Means'i hazır kümeleme fonksiyonu kullanmadan, döngülerle uygular."""

import csv
import math
import random
from time import perf_counter

from veri_indir import SONUC, veriyi_oku

K = 7
SEED = 42
MAKSIMUM_TEKRAR = 300


def uzaklik_kare(nokta1, nokta2):
    """Karekök almak en yakın merkezi değiştirmez; WCSS'de de kare kullanılır."""
    return (nokta1[0] - nokta2[0]) ** 2 + (nokta1[1] - nokta2[1]) ** 2


def baslangic_merkezlerini_sec(noktalar, k=K, seed=SEED):
    if not 1 <= k <= len(set(noktalar)):
        raise ValueError("K, 1 ile farklı nokta sayısı arasında olmalı.")
    return random.Random(seed).sample(noktalar, k)


def kumelere_ata(noktalar, merkezler):
    etiketler = []
    for nokta in noktalar:
        uzakliklar = [uzaklik_kare(nokta, merkez) for merkez in merkezler]
        etiketler.append(uzakliklar.index(min(uzakliklar)))
    return etiketler


def merkezleri_guncelle(noktalar, etiketler, merkezler):
    yeni_merkezler = []
    for kume_no, eski_merkez in enumerate(merkezler):
        kume = [nokta for nokta, etiket in zip(noktalar, etiketler) if etiket == kume_no]
        if kume:
            yeni_merkezler.append((sum(p[0] for p in kume) / len(kume),
                                   sum(p[1] for p in kume) / len(kume)))
        else:
            # Boş kümede sıfıra bölmek yerine eski merkezi koruyoruz.
            yeni_merkezler.append(eski_merkez)
    return yeni_merkezler


def kmeans(noktalar, k=K, seed=SEED, baslangic=None, max_iter=MAKSIMUM_TEKRAR):
    """Etiketleri (0'dan başlayarak), merkezleri, iterasyonu ve WCSS'yi döndürür."""
    noktalar = [tuple(nokta) for nokta in noktalar]
    if not noktalar or any(len(p) != 2 or not all(math.isfinite(x) for x in p)
                           for p in noktalar):
        raise ValueError("Noktalar, sonlu iki koordinattan oluşmalı.")
    if not isinstance(max_iter, int) or max_iter < 1:
        raise ValueError("max_iter pozitif bir tam sayı olmalı.")
    if not isinstance(k, int) or not 1 <= k <= len(set(noktalar)):
        raise ValueError("K, 1 ile farklı nokta sayısı arasında bir tam sayı olmalı.")
    merkezler = (baslangic_merkezlerini_sec(noktalar, k, seed) if baslangic is None
                 else [tuple(merkez) for merkez in baslangic])
    if len(merkezler) != k or any(len(m) != 2 or not all(math.isfinite(x) for x in m)
                                 for m in merkezler):
        raise ValueError("K adet geçerli başlangıç merkezi verilmeli.")
    ilk_merkezler = merkezler.copy()
    onceki_etiketler = None
    yakinsadi = False
    for tekrar in range(1, max_iter + 1):
        etiketler = kumelere_ata(noktalar, merkezler)
        yeni_merkezler = merkezleri_guncelle(noktalar, etiketler, merkezler)
        # tol=0: scikit-learn ile aynı atama/merkez kararlılığı hedeflenir.
        if etiketler == onceki_etiketler or yeni_merkezler == merkezler:
            merkezler = yeni_merkezler
            yakinsadi = True
            break
        merkezler = yeni_merkezler
        onceki_etiketler = etiketler
    # İterasyon sınırında dahi etiketler son merkezlere ait olmalı.
    etiketler = kumelere_ata(noktalar, merkezler)
    inertia = sum(uzaklik_kare(p, merkezler[e]) for p, e in zip(noktalar, etiketler))
    return {"etiketler": etiketler, "merkezler": merkezler, "iterasyon": tekrar,
            "inertia": inertia, "baslangic": ilk_merkezler, "yakinsadi": yakinsadi}


def sonucu_kaydet(iller, sonuc, dosya_adi):
    SONUC.mkdir(parents=True, exist_ok=True)
    with (SONUC / f"{dosya_adi}.csv").open("w", encoding="utf-8-sig", newline="") as dosya:
        yazici = csv.writer(dosya)
        yazici.writerow(["il", "enlem", "boylam", "gercek_bolge", "atanan_kume"])
        for il, etiket in zip(iller, sonuc["etiketler"]):
            yazici.writerow([il["ad"], il["y"], il["x"], il["gercek_bolge"], int(etiket) + 1])
    with (SONUC / f"{dosya_adi}_merkezler.csv").open("w", encoding="utf-8-sig", newline="") as dosya:
        yazici = csv.writer(dosya)
        yazici.writerow(["kume", "boylam", "enlem"])
        for no, merkez in enumerate(sonuc["merkezler"], start=1):
            yazici.writerow([no, *merkez])


def kumeleri_yazdir(iller, sonuc):
    for no, merkez in enumerate(sonuc["merkezler"]):
        adlar = [il["ad"] for il, e in zip(iller, sonuc["etiketler"]) if e == no]
        print(f"Küme {no + 1} ({len(adlar)} il), merkez (boylam, enlem) = "
              f"({merkez[0]:.5f}, {merkez[1]:.5f}): {', '.join(adlar)}")


def main():
    from gorsellestirme import kume_grafigi

    iller = veriyi_oku()
    noktalar = [(il["x"], il["y"]) for il in iller]
    basla = perf_counter()
    sonuc = kmeans(noktalar)
    sure = perf_counter() - basla
    print("Başlangıç merkezleri (boylam, enlem):", sonuc["baslangic"])
    print(f"Manuel: {sonuc['iterasyon']} iterasyon, WCSS={sonuc['inertia']:.6f}, "
          f"süre={sure * 1000:.3f} ms, yakınsadı={sonuc['yakinsadi']}")
    kumeleri_yazdir(iller, sonuc)
    sonucu_kaydet(iller, sonuc, "manuel_kumeler")
    kume_grafigi(iller, sonuc, "Manuel K-Means (K=7)", "manuel_7_kume.png")


if __name__ == "__main__":
    main()
