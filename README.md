# 81 İl ile K-Means Kümeleme Ödevi

Türkiye'nin 81 ili, enlem ve boylam koordinatları kullanılarak K-Means yöntemiyle 7 kümeye ayrılır. İlk sürüm algoritmayı döngülerle kendimiz uygular; ikinci sürüm `scikit-learn` ile çözümü karşılaştırır ve 2–12 arasındaki K değerlerini Silhouette Score kullanarak değerlendirir.

## Dosyalar

- `veri_indir.py`: 81 ilin CSV verisini indirir.
- `kmeans_manuel.py`: K-Means'i temel `for` döngüleriyle uygular.
- `kmeans_optimize.py`: Hazır KMeans, Silhouette, Elbow ve gerçek coğrafi bölgelerle ARI karşılaştırması.
- `veri_setleri.md`: Sınıflandırma, kümeleme, tahminleme veri seti araştırması.
- `data/iller.csv`: Veri indirme sonrasında oluşur.
- `sonuclar/`: Üretilen CSV ve PNG grafik dosyaları.

## Kurulum

Python 3 yüklü olmalıdır. Proje klasöründe terminal açın:

```bash
python -m pip install -r requirements.txt
python veri_indir.py
python kmeans_manuel.py
python kmeans_optimize.py
```

Windows'ta `python` komutu çalışmazsa `py` deneyebilirsiniz.

## Nasıl çalışır?

1. Rastgele 7 başlangıç merkezi seçilir (`random_state/seed = 42`).
2. Her il en yakın merkeze atanır.
3. Her merkez, kendisine atanmış illerin koordinat ortalamasına taşınır.
4. Merkezler değişmeyene kadar işlemler yinelenir.
5. Aynı veri hazır KMeans ile tekrar denenir.
6. Farklı K değerleri test edilip en yüksek ortalama Silhouette Score veren K raporlanır.

## Neden sonuçlar birebir yedi coğrafi bölge olmaz?

K-Means yalnızca koordinat yakınlığını kullanır. Resmî/yerleşik coğrafi bölge ayrımında yüzey şekilleri, iklim ve diğer coğrafi etkenler de bulunur. İllerin koordinatı olarak il yönetim merkezlerinin konumu kullanılır; illerin bütün sınırları kullanılmaz.

**Yöntemsel sınırlama:** Enlem ve boylam derecelerine doğrudan Öklid uzaklığı uygulanmıştır. Bu, ilk ders uygulaması için kolaydır; dereceler gerçek kilometre uzaklıklarıyla tam aynı değildir. Sonraki geliştirmelerde Türkiye için uygun bir projeksiyona dönüştürülmüş x-y koordinatları kullanılabilir.

## Veri kaynağı

[brkunver/turkiye-provinces-dataset](https://github.com/brkunver/turkiye-provinces-dataset) — 81 il, açık veri, CC BY 4.0. Kaynağa atıf verilmiştir.
