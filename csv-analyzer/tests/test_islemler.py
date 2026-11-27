"""Kullanıcı verisinin okuma, temizleme ve indirme boyunca korunmasını denetler."""

from io import BytesIO
from pathlib import Path
import sys
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from islemler import csv_oku, csv_olustur, grup_ozeti, kalite_raporu, veri_filtrele, veriyi_temizle


class CsvAnalizTestleri(unittest.TestCase):
    def test_csv_turkce_kimlik_ve_bilinmeyen_metin(self):
        veri = 'kod;urun\n001;"Kalem; mavi"\n002;NA\n003;\n'.encode("utf-8-sig")
        df, bilgi = csv_oku(veri)
        self.assertEqual(bilgi["ayrac"], ";")
        self.assertEqual(df["kod"].tolist(), ["001", "002", "003"])
        self.assertEqual(df["urun"].iloc[:2].tolist(), ["Kalem; mavi", "NA"])
        self.assertTrue(pd.isna(df["urun"].iloc[2]))

    def test_csv_kodlamalari_ve_tsv(self):
        for kodlama in ("cp1254", "utf-16"):
            df, _ = csv_oku("isim\tadet\nÇağrı\t2\n".encode(kodlama))
            self.assertEqual(df.iloc[0, 0], "Çağrı")
            self.assertEqual(df.iloc[0, 1], "2")

    def test_csv_bozuk_girdiler(self):
        for veri in (b"", b"a,a\n1,2", b"a,b\n1,2,3", b'a,b\n"unclosed,2', b"a,b\n1"):
            with self.subTest(veri=veri), self.assertRaises(ValueError):
                csv_oku(veri)
        df, _ = csv_oku(b"a,b\n")
        self.assertEqual(df.shape, (0, 2))

    def test_ornek_dosyanin_temizligi_ve_kaynagin_korunmasi(self):
        kaynak, _ = csv_oku((Path(__file__).parents[1] / "ornek_veri.csv").read_bytes())
        once = kaynak.copy(deep=True)
        temiz, gecmis = veriyi_temizle(kaynak, dict(
            bosluk=True, sayilar=["tutar"], tarihler=["tarih"],
            tekrar_sil=True, tekrar_sutunlar=["islem_id"],
            eksik_yontem="sil", eksik_sutunlar=["tarih", "tutar"],
        ))
        pd.testing.assert_frame_equal(kaynak, once)
        self.assertEqual(temiz["islem_id"].tolist(), ["001", "002", "003"])
        self.assertEqual(temiz["tutar"].sum(), 200)
        self.assertEqual(len(gecmis), 5)
        rapor = grup_ozeti(temiz, "kategori", "tutar").set_index("Grup")
        self.assertEqual(rapor.loc["Yemek", "Toplam"], 160)
        self.assertEqual(rapor.loc["Ulaşım", "Toplam"], 40)
        geri, _ = csv_oku(csv_olustur(temiz))
        self.assertEqual(geri["islem_id"].tolist(), ["001", "002", "003"])

    def test_yerel_sayi_bicimi_ve_gecersiz_degerler(self):
        df = pd.DataFrame({"tutar": pd.Series(["1.234,50", "boş", "inf", None], dtype="string")})
        sonuc, _ = veriyi_temizle(df, dict(sayilar=["tutar"], ondalik=",", binlik="."))
        self.assertEqual(sonuc["tutar"].iloc[0], 1234.5)
        self.assertEqual(sonuc["tutar"].isna().sum(), 3)

    def test_medyan_kesirli_dolgu_ve_tamamen_eksik_sutun(self):
        df = pd.DataFrame({"adet": pd.Series(["1", "2", None], dtype="string")})
        sonuc, _ = veriyi_temizle(df, dict(sayilar=["adet"], eksik_yontem="medyan", eksik_sutunlar=["adet"]))
        self.assertEqual(sonuc["adet"].tolist(), [1, 2, 1.5])
        with self.assertRaises(ValueError):
            veriyi_temizle(pd.DataFrame({"adet": [None]}), dict(sayilar=["adet"], eksik_yontem="medyan", eksik_sutunlar=["adet"]))
        with self.assertRaises(ValueError):
            veriyi_temizle(df, dict(eksik_yontem="medyan", eksik_sutunlar=["adet"]))

    def test_sabit_doldurma_ve_kurallarin_denetimi(self):
        df = pd.DataFrame({"adet": pd.Series(["1", None], dtype="string")})
        sonuc, _ = veriyi_temizle(df, dict(sayilar=["adet"], eksik_yontem="sabit", eksik_sutunlar=["adet"], sabit="2,5"))
        self.assertEqual(sonuc["adet"].tolist(), [1, 2.5])
        for ayar in [dict(sayilar=["adet"], tarihler=["adet"]), dict(eksik_yontem="sil"), dict(sayilar=["yok"])]:
            with self.subTest(ayar=ayar), self.assertRaises(ValueError):
                veriyi_temizle(df, ayar)

    def test_filtreler_ve_sifir_eslesme(self):
        df = pd.DataFrame({"ad": pd.Series(["Elma", "Armut", None], dtype="string"), "tutar": [10, 20, 30]})
        self.assertEqual(veri_filtrele(df, "ad", aranan="EL")["ad"].tolist(), ["Elma"])
        self.assertEqual(veri_filtrele(df, "tutar", alt=15, ust=25)["tutar"].tolist(), [20])
        self.assertTrue(veri_filtrele(df, "tutar", alt=100).empty)
        self.assertEqual(len(df), 3)

    def test_bilinmeyen_grup_toplami_sifir_yapilmaz(self):
        df = pd.DataFrame({"grup": ["A", "A", "B", None], "deger": [10, None, None, 30]})
        ozet = grup_ozeti(df, "grup", "deger")
        b = ozet.loc[ozet["Grup"] == "B"].iloc[0]
        self.assertTrue(pd.isna(b["Toplam"]))
        self.assertEqual(b["Kayıt"], 1)
        self.assertEqual(b["Bilinen"], 0)
        self.assertEqual(len(ozet), 3)
        self.assertEqual(kalite_raporu(df)["Eksik"].tolist(), [1, 2])


if __name__ == "__main__":
    unittest.main()
