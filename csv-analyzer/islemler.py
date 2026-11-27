"""CSV okuma, veri temizleme ve analiz. Bu dosya arayüzden bağımsızdır."""

import csv
from io import StringIO

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_integer_dtype, is_numeric_dtype

MAX_BOYUT = 10 * 1024 * 1024
MAX_SATIR = 100_000
MAX_SUTUN = 150


def csv_oku(veri: bytes, ayrac="Otomatik", kodlama="Otomatik"):
    """CSV'yi oku. Kimliklerdeki sıfırları korumak için sütunlar önce metindir."""
    if not veri or not veri.strip():
        raise ValueError("Dosya boş. Başlık ve veri satırları içeren bir CSV seç.")
    if len(veri) > MAX_BOYUT:
        raise ValueError("En fazla 10 MB büyüklüğünde bir CSV seç.")

    adaylar = [kodlama] if kodlama != "Otomatik" else ["utf-8-sig", "cp1254"]
    if kodlama == "Otomatik" and veri[:2] in (b"\xff\xfe", b"\xfe\xff"):
        adaylar = ["utf-16"]
    metin = None
    for aday in adaylar:
        try:
            metin = veri.decode(aday).lstrip("\ufeff\r\n")
            kullanilan_kodlama = aday
            break
        except UnicodeError:
            continue
    if metin is None:
        raise ValueError("Metin okunamadı. Okuma ayarlarından dosyanın kodlamasını seç.")
    if not metin.strip() or "\x00" in metin:
        raise ValueError("Geçerli bir CSV metni bulunamadı. Dosya biçimini ve kodlamayı kontrol et.")

    if ayrac == "Otomatik":
        try:
            ayrac = csv.Sniffer().sniff(metin[:65536], delimiters=",;\t|").delimiter
        except csv.Error:
            # Düzensiz veri satırlarında en olası başlık ayıracını kullan.
            ilk_satir = metin.splitlines()[0]
            ayrac = max(",;\t|", key=lambda x: len(next(csv.reader([ilk_satir], delimiter=x))))
    if ayrac not in (",", ";", "\t", "|"):
        raise ValueError("Desteklenen ayraçlar: virgül, noktalı virgül, sekme ve dikey çizgi.")

    # Pandas bazı fazla alanlı satırları örtük indeks gibi yorumlayabilir.
    # Her kaydın başlıkla aynı sayıda alan taşıdığını önceden doğrula.
    try:
        okuyucu = csv.reader(StringIO(metin), delimiter=ayrac, strict=True)
        basliklar = next(okuyucu)
        satir_sayisi = 0
        for satir in okuyucu:
            if not satir:
                continue
            if len(satir) != len(basliklar):
                raise ValueError(f"{okuyucu.line_num}. satırın sütun sayısı başlıkla uyuşmuyor. Ayıracı ve tırnakları kontrol et.")
            satir_sayisi += 1
            if satir_sayisi > MAX_SATIR:
                raise ValueError("En fazla 100.000 satırlı bir CSV seç.")
    except csv.Error as hata:
        raise ValueError("CSV tırnakları veya satırları okunamadı. Dosyanın metin biçimini kontrol et.") from hata
    basliklar = [ad.strip() or f"sutun_{i + 1}" for i, ad in enumerate(basliklar)]
    if len(basliklar) > MAX_SUTUN:
        raise ValueError("En fazla 150 sütunlu bir CSV seç.")
    if len(basliklar) != len(set(basliklar)):
        raise ValueError("Sütun adları tekrarlanıyor. CSV başlıklarını benzersiz olacak şekilde düzenle.")
    try:
        tablo = pd.read_csv(
            StringIO(metin), sep=ayrac, names=basliklar, header=0,
            dtype="string", keep_default_na=False, na_values=[""],
            nrows=MAX_SATIR + 1, on_bad_lines="error",
        )
    except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as hata:
        raise ValueError("CSV sütunları okunamadı. Ayıracı, tırnakları ve satır uzunluklarını kontrol et.") from hata
    if len(tablo) > MAX_SATIR:
        raise ValueError("En fazla 100.000 satırlı bir CSV seç.")
    return tablo, {"kodlama": kullanilan_kodlama, "ayrac": ayrac}


def kalite_raporu(tablo):
    """Her sütunun tipini, eksiklerini ve farklı değer sayısını göster."""
    return pd.DataFrame({
        "Sütun": tablo.columns,
        "Tür": tablo.dtypes.astype(str).tolist(),
        "Eksik": tablo.isna().sum().tolist(),
        "Dolu": tablo.notna().sum().tolist(),
        "Farklı": tablo.nunique(dropna=True).tolist(),
    })


def veriyi_temizle(orijinal, ayarlar):
    """Kuralları her seferinde orijinalin kopyasına uygula ve işlem raporu üret."""
    temiz = orijinal.copy()
    kayit = []
    sayilar = ayarlar.get("sayilar", [])
    tarihler = ayarlar.get("tarihler", [])
    eksik_sutunlar = ayarlar.get("eksik_sutunlar", [])
    tekrar_sutunlar = ayarlar.get("tekrar_sutunlar", [])
    for alanlar in (sayilar, tarihler, eksik_sutunlar, tekrar_sutunlar):
        if any(ad not in temiz.columns for ad in alanlar):
            raise ValueError("Seçilen sütunlardan biri bu dosyada bulunmuyor.")
    if set(sayilar) & set(tarihler):
        raise ValueError("Bir sütun hem sayı hem tarih olarak seçilemez.")
    ondalik = ayarlar.get("ondalik", ".")
    binlik = ayarlar.get("binlik", "")
    if sayilar and binlik and ondalik == binlik:
        raise ValueError("Ondalık ve binlik ayıracı farklı olmalı.")

    if ayarlar.get("bosluk", False):
        degisen = 0
        for ad in temiz.select_dtypes(include=["string", "str", "object"]).columns:
            eski = temiz[ad].astype("string")
            yeni = eski.str.strip().replace("", pd.NA)
            degisen += int(eski.fillna("").ne(yeni.fillna("")).sum())
            temiz[ad] = yeni
        kayit.append({"İşlem": "Metin temizliği", "Sonuç": f"{degisen} hücrede kenar boşluğu kaldırıldı."})

    for ad in sayilar:
        kaynak = temiz[ad].astype("string")
        duzenli = kaynak
        if binlik:
            duzenli = duzenli.str.replace(binlik, "", regex=False)
        if ondalik != ".":
            duzenli = duzenli.str.replace(ondalik, ".", regex=False)
        sonuc = pd.to_numeric(duzenli, errors="coerce")
        sonuc = sonuc.mask(np.isinf(sonuc), pd.NA)
        hatali = int((kaynak.notna() & sonuc.isna()).sum())
        temiz[ad] = sonuc
        kayit.append({"İşlem": f"Sayı · {ad}", "Sonuç": f"{hatali} geçersiz değer eksik yapıldı."})

    for ad in tarihler:
        kaynak = temiz[ad]
        try:
            sonuc = pd.to_datetime(kaynak, format=ayarlar.get("tarih_bicimi", "%Y-%m-%d"), errors="coerce")
        except (ValueError, TypeError) as hata:
            raise ValueError(f"{ad}: tarih biçimi bu sütuna uygulanamadı. Seçilen biçimi kontrol et.") from hata
        hatali = int((kaynak.notna() & sonuc.isna()).sum())
        temiz[ad] = sonuc
        kayit.append({"İşlem": f"Tarih · {ad}", "Sonuç": f"{hatali} geçersiz tarih eksik yapıldı."})

    if ayarlar.get("tekrar_sil", False):
        once = len(temiz)
        temiz = temiz.drop_duplicates(
            subset=tekrar_sutunlar or None, keep=ayarlar.get("tekrar_tut", "first")
        ).copy()
        kayit.append({"İşlem": "Tekrarlı kayıtlar", "Sonuç": f"{once - len(temiz)} satır çıkarıldı."})

    yontem = ayarlar.get("eksik_yontem", "koru")
    if yontem != "koru" and not eksik_sutunlar:
        raise ValueError("Eksik değer işlemi için en az bir sütun seç.")
    if yontem == "sil":
        once = len(temiz)
        temiz = temiz.dropna(subset=eksik_sutunlar).copy()
        kayit.append({"İşlem": "Eksik kayıtlar", "Sonuç": f"{once - len(temiz)} satır çıkarıldı."})
    elif yontem == "medyan":
        for ad in eksik_sutunlar:
            if not is_numeric_dtype(temiz[ad]):
                raise ValueError(f"{ad}: medyan için önce sütunu sayıya dönüştür.")
            medyan = temiz[ad].median()
            if pd.isna(medyan):
                raise ValueError(f"{ad}: medyan hesaplanacak geçerli değer yok.")
            adet = int(temiz[ad].isna().sum())
            if is_integer_dtype(temiz[ad]) and not float(medyan).is_integer():
                temiz[ad] = temiz[ad].astype("Float64")
            temiz[ad] = temiz[ad].fillna(medyan)
            kayit.append({"İşlem": f"Medyan · {ad}", "Sonuç": f"{adet} eksik hücre {medyan:g} ile dolduruldu."})
    elif yontem == "sabit":
        deger = ayarlar.get("sabit", "")
        if not str(deger).strip():
            raise ValueError("Doldurmak için boş olmayan bir sabit değer yaz.")
        for ad in eksik_sutunlar:
            adet = int(temiz[ad].isna().sum())
            uygun = deger
            if is_numeric_dtype(temiz[ad]):
                try:
                    uygun = float(str(deger).replace(",", "."))
                except ValueError as hata:
                    raise ValueError(f"{ad}: sayısal bir doldurma değeri gerekli.") from hata
                if not np.isfinite(uygun):
                    raise ValueError("Doldurma değeri sonlu bir sayı olmalı.")
                if is_integer_dtype(temiz[ad]) and not uygun.is_integer():
                    temiz[ad] = temiz[ad].astype("Float64")
            elif is_datetime64_any_dtype(temiz[ad]):
                try:
                    uygun = pd.to_datetime(deger, format=ayarlar.get("tarih_bicimi", "%Y-%m-%d"))
                except (ValueError, TypeError) as hata:
                    raise ValueError(f"{ad}: seçilen biçime uygun bir tarih yaz.") from hata
            temiz[ad] = temiz[ad].fillna(uygun)
            kayit.append({"İşlem": f"Sabit değer · {ad}", "Sonuç": f"{adet} eksik hücre dolduruldu."})
    elif yontem not in ("koru", "sil", "medyan", "sabit"):
        raise ValueError("Bilinmeyen eksik değer yöntemi.")
    if not kayit:
        kayit.append({"İşlem": "Değişiklik yok", "Sonuç": "Orijinal veri korunuyor."})
    return temiz.reset_index(drop=True), pd.DataFrame(kayit)


def veri_filtrele(tablo, sutun=None, *, aranan="", alt=None, ust=None, baslangic=None, bitis=None):
    """Bir sütuna filtre uygula. Kaynak tabloyu değiştirme."""
    if sutun is None:
        return tablo
    if sutun not in tablo.columns:
        raise ValueError("Filtre sütunu bulunamadı.")
    seri = tablo[sutun]
    maske = pd.Series(True, index=tablo.index)
    if is_numeric_dtype(seri):
        if alt is not None:
            maske &= seri >= alt
        if ust is not None:
            maske &= seri <= ust
    elif is_datetime64_any_dtype(seri):
        if baslangic is not None:
            maske &= seri.dt.date >= baslangic
        if bitis is not None:
            maske &= seri.dt.date <= bitis
    elif aranan:
        maske &= seri.astype("string").str.contains(aranan, case=False, regex=False, na=False)
    return tablo.loc[maske.fillna(False)]


def grup_ozeti(tablo, grup, olcum):
    """Grup başına kayıt sayısı ve sayısal özetler; bilinmeyen toplamı sıfır sayma."""
    if grup == olcum:
        raise ValueError("Grup ve ölçüm için farklı sütunlar seç.")
    if grup not in tablo or olcum not in tablo or not is_numeric_dtype(tablo[olcum]):
        raise ValueError("Geçerli bir grup ve sayısal ölçüm sütunu seç.")
    return tablo.groupby(grup, dropna=False, observed=True)[olcum].agg(
        Kayıt="size", Bilinen="count", Toplam=lambda s: s.sum(min_count=1),
        Ortalama="mean", **{"En yüksek": "max"},
    ).rename_axis("Grup").reset_index()


def csv_olustur(tablo):
    """İndeksi sütun olarak eklemeden, Excel'de Türkçe açılabilen UTF-8 CSV üret."""
    return tablo.to_csv(index=False).encode("utf-8-sig")
