"""Temel algoritma doğruluğu ve hatalı veri durumları için küçük testler."""

import csv
import io
import math
import unittest

import numpy as np
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

from kmeans_manuel import kmeans, kumelere_ata, uzaklik_kare
from kmeans_optimize import hazir_kmeans
from veri_indir import VERI, veriyi_dogrula, veriyi_oku


class KMeansTestleri(unittest.TestCase):
    def test_elle_hesaplanabilen_ornek(self):
        noktalar = [(0, 0), (0, 2), (10, 0), (10, 2)]
        sonuc = kmeans(noktalar, k=2, baslangic=[(0, 0), (10, 0)])
        self.assertEqual(sonuc["etiketler"], [0, 0, 1, 1])
        self.assertEqual(sonuc["merkezler"], [(0, 1), (10, 1)])
        self.assertEqual(sonuc["inertia"], 4)
        self.assertTrue(sonuc["yakinsadi"])

    def test_bos_kume_merkezi_korunur(self):
        sonuc = kmeans([(0, 0), (1, 0), (10, 0)], k=3,
                       baslangic=[(0, 0), (10, 0), (100, 100)])
        self.assertEqual(sonuc["merkezler"][2], (100, 100))
        self.assertTrue(math.isfinite(sonuc["inertia"]))

    def test_seed_tekrarlanabilir(self):
        noktalar = [(il["x"], il["y"]) for il in veriyi_oku()]
        self.assertEqual(kmeans(noktalar), kmeans(noktalar))

    def test_iterasyon_sinirinda_son_merkezlere_atama(self):
        noktalar = [(0, 0), (2, 0), (3, 0), (10, 0)]
        sonuc = kmeans(noktalar, k=2, baslangic=[(0, 0), (2, 0)], max_iter=1)
        self.assertEqual(sonuc["iterasyon"], 1)
        self.assertFalse(sonuc["yakinsadi"])
        self.assertEqual(sonuc["etiketler"], kumelere_ata(noktalar, sonuc["merkezler"]))
        self.assertAlmostEqual(sonuc["inertia"], sum(
            uzaklik_kare(p, sonuc["merkezler"][e]) for p, e in zip(noktalar, sonuc["etiketler"])))

    def test_gecersiz_parametreler(self):
        for ayar in [{"k": 0}, {"k": 3}, {"k": 1, "max_iter": 0},
                     {"k": 1, "baslangic": []}]:
            with self.subTest(ayar=ayar), self.assertRaises(ValueError):
                kmeans([(0, 0), (1, 1)], **ayar)
        with self.assertRaises(ValueError):
            kmeans([(math.nan, 1)], k=1)

    def test_sklearn_ile_ayni_baslangic_ayni_cozum(self):
        noktalar = [(il["x"], il["y"]) for il in veriyi_oku()]
        sonuc = kmeans(noktalar)
        with threadpool_limits(limits=1):
            model = hazir_kmeans(np.array(noktalar), baslangic=np.array(sonuc["baslangic"]), n_init=1)
        self.assertAlmostEqual(sonuc["inertia"], model.inertia_, places=9)
        self.assertEqual(adjusted_rand_score(sonuc["etiketler"], model.labels_), 1)
        np.testing.assert_allclose(sonuc["merkezler"], model.cluster_centers_)


class VeriTestleri(unittest.TestCase):
    def setUp(self):
        with VERI.open(encoding="utf-8-sig", newline="") as dosya:
            okuyucu = csv.DictReader(dosya)
            self.alanlar = okuyucu.fieldnames
            self.satirlar = list(okuyucu)

    def dogrula(self):
        metin = io.StringIO()
        yazici = csv.DictWriter(metin, fieldnames=self.alanlar)
        yazici.writeheader()
        yazici.writerows(self.satirlar)
        return veriyi_dogrula(csv.DictReader(io.StringIO(metin.getvalue())))

    def test_81_il_ve_plaka_sirasi(self):
        self.satirlar.reverse()
        iller = self.dogrula()
        self.assertEqual([il["plaka"] for il in iller], list(range(1, 82)))

    def test_eksik_ve_tekrarlanan_il(self):
        self.satirlar[-1] = self.satirlar[0].copy()
        with self.assertRaises(ValueError):
            self.dogrula()

    def test_eksik_satir(self):
        self.satirlar.pop()
        with self.assertRaises(ValueError):
            self.dogrula()

    def test_hatali_alanlar(self):
        for alan, deger in [("latitude", ""), ("latitude", "NaN"),
                            ("longitude", "inf"), ("longitude", "180"),
                            ("latitude", "koordinat"), ("region", "bilinmiyor"),
                            ("province_name", "Yanlış İl"), ("plate_code", "82")]:
            eski = self.satirlar[0][alan]
            self.satirlar[0][alan] = deger
            with self.subTest(alan=alan, deger=deger), self.assertRaises(ValueError):
                self.dogrula()
            self.satirlar[0][alan] = eski

    def test_eksik_sutun(self):
        with self.assertRaises(ValueError):
            veriyi_dogrula(csv.DictReader(io.StringIO("province_name\nAdana\n")))


if __name__ == "__main__":
    unittest.main()
