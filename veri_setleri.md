# Makine Öğrenmesi İçin Veri Setleri

Bu araştırma sınıflandırma, kümeleme ve regresyon için üç farklı veri seti önerir. Kaynak sayfaları 5 Kasım 2026 tarihinde kontrol edilmiştir. Bu üç veri setinde model eğitimi yapılmamıştır; uygulanan deneyler yalnızca Türkiye'nin 81 ili üzerindedir.

## 1. Sınıflandırma: Iris

- **Kaynak ve erişim:** [UCI Machine Learning Repository — Iris](https://archive.ics.uci.edu/dataset/53/iris).
- **Amaç:** Çiçeğin ölçülerinden türünü belirlemek.
- **Veri sayısı:** 150 çiçek; üç türün her birinden 50 örnek.
- **Özellikler:** Çanak yaprağı uzunluğu/genişliği ve taç yaprağı uzunluğu/genişliği; toplam dört sayısal girdi, santimetre cinsinden.
- **Hedef:** Setosa, Versicolour veya Virginica tür etiketi.
- **Problem türü:** Denetimli sınıflandırma; çıktı bir kategoridir.
- **Örnek algoritmalar:** K-En Yakın Komşu (KNN), karar ağacı, lojistik regresyon ve destek vektör makineleri (SVM).
- **Örnek çalışma:** Eğitim/test ayrımı yapılarak tür tahmini ve doğruluk ölçümü. Ölçekleyici kullanılacaksa yalnız eğitim verisinde öğrenilmelidir.

## 2. Kümeleme: Online Retail

- **Kaynak ve erişim:** [UCI Machine Learning Repository — Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail).
- **Amaç:** Bir çevrim içi mağazanın müşterilerini alışveriş alışkanlıklarına göre gruplamak.
- **Veri sayısı:** 541.909 işlem satırı. Bu sayı müşteri sayısı değildir; müşteri bazında birleştirilince değişir.
- **Özellikler:** Fatura numarası, ürün kodu/açıklaması, miktar, işlem tarihi, birim fiyat, müşteri kimliği ve ülke. Kümelemede müşteri kimliği sayısal özellik olarak kullanılmaz.
- **Hazırlama:** İade/iptal kayıtları ve geçersiz miktar/fiyatlar incelenir; müşteri kimliği eksikleri kontrol edilir. Müşteri başına son alışverişten geçen süre, alışveriş sıklığı ve toplam harcama (RFM) çıkarılır. Ölçekleme ve aykırı değer incelemesi yapılır.
- **Hedef:** Önceden verilmiş müşteri grubu etiketi yoktur; gruplar veriden bulunur.
- **Problem türü:** Denetimsiz kümeleme.
- **Örnek algoritmalar:** K-Means, DBSCAN ve hiyerarşik kümeleme.
- **Örnek çalışma:** Düşük/yüksek harcama ve sık/seyrek alışveriş yapan müşteri gruplarını incelemek; Silhouette ile ayrışmayı değerlendirmek.

## 3. Regresyon: Wine Quality — beyaz şarap alt kümesi

- **Kaynak ve erişim:** [UCI Machine Learning Repository — Wine Quality](https://archive.ics.uci.edu/dataset/186/wine+quality); bu öneride `winequality-white.csv` kullanılır.
- **Amaç:** Fizikokimyasal ölçümlerden şarabın kalite puanını tahmin etmek.
- **Veri sayısı:** Beyaz şarap alt kümesinde 4.898 örnek vardır. Kaynakta ayrı kırmızı şarap dosyası da bulunur; bu sayı iki dosyanın toplamı değildir.
- **Özellikler:** Sabit/uçucu asitlik, sitrik asit, artık şeker, klorürler, serbest/toplam kükürt dioksit, yoğunluk, pH, sülfatlar ve alkol; toplam 11 sayısal girdi.
- **Hedef:** Duyusal değerlendirmeyle verilen `quality` puanı (0–10 ölçeği).
- **Problem türü:** Denetimli regresyon; sayısal puan tahmini. Hedef sıralı ve kesiklidir; sınıflandırma olarak da ele alınabilir.
- **Örnek algoritmalar:** Doğrusal regresyon, Random Forest Regressor ve destek vektör regresyonu (SVR).
- **Örnek çalışma:** Eğitim/test ayrımıyla puan tahmini; MAE veya RMSE ile hata değerlendirmesi.

## 4. Bu projede uygulanan kümeleme verisi: Türkiye'nin 81 ili

- **Kaynak:** [brkunver — Turkish Provinces Dataset](https://github.com/brkunver/turkiye-provinces-dataset).
- **Veri sayısı:** 81 il; il başına bir satır.
- **Amaç:** İl merkezi konumlarına göre yakınlık grupları oluşturmak.
- **Özellikler:** Yalnız boylam ve enlem; il adı ve plaka kayıt tanımlama/doğrulama için kullanılır.
- **Karşılaştırma bilgisi:** `region` algoritmaya verilmez; sonuçları yedi coğrafi bölgeyle ARI üzerinden karşılaştırmak için saklanır.
- **Problem türü ve algoritmalar:** Kümeleme; manuel K-Means ve scikit-learn KMeans bu projede uygulanmıştır.

Sınıflandırma kategori, regresyon sayısal değer tahmin eder; kümeleme önceden verilmiş hedef etiketi olmadan benzer gözlemleri gruplar. Veri setinin hangi görevde kullanılacağı, seçilen girdiye ve hedefe bağlıdır.

## Lisans ve atıf

UCI'deki üç kaynak sayfası ve Türkiye il veri seti CC BY 4.0 lisansı belirtir. Yeniden dağıtımda kaynaklara ve veri üreticilerine atıf verilmelidir. Projedeki il CSV'sinin sabit sürümü ve lisans bağlantıları [README](README.md) içindedir.
