"""Arayüz: dosyayı al, Pandas işlemlerini çağır, sonucu göster."""

from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from islemler import csv_oku, csv_olustur, grup_ozeti, kalite_raporu, veri_filtrele, veriyi_temizle

KLASOR = Path(__file__).parent
st.set_page_config(page_title="CSV Analyzer", page_icon="▦", layout="wide")
st.markdown(f"<style>{(KLASOR / 'stil.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def anahtarlari_sil(*onekler):
    """Yeni dosyada eski dosyanın sütun seçimlerini kullanma."""
    for anahtar in list(st.session_state):
        if anahtar.startswith(onekler):
            del st.session_state[anahtar]


def sonucu_sifirla():
    st.session_state.calisma = st.session_state.orijinal.copy()
    st.session_state.gecmis = pd.DataFrame(columns=["İşlem", "Sonuç"])
    st.session_state.uygulandi = False
    st.session_state.form_surum = st.session_state.get("form_surum", 0) + 1
    anahtarlari_sil("k_", "f_", "a_")


def filtreleri_sifirla():
    anahtarlari_sil("f_")


# 1. Başlık ve veri kaynağı.
baslik, indirme = st.columns([5, 1.5], vertical_alignment="center")
with baslik:
    st.markdown('<div class="brand">CSV Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<p class="intro">Verini incele, düzenle ve temiz bir dosyayla devam et.</p>', unsafe_allow_html=True)
with indirme:
    indirme_yeri = st.empty()
st.divider()

with st.sidebar:
    st.markdown('<p class="side-heading">Veri kaynağı</p>', unsafe_allow_html=True)
    ornek = st.toggle("Örnek veriyi kullan", key="ornek")
    dosya = st.file_uploader("CSV dosyanı seç", type=["csv", "tsv"], disabled=ornek, key="dosya", help="İlk satır sütun başlıkları olmalı.")
    with st.expander("Okuma ayarları"):
        ayrac_adi = st.selectbox("Sütun ayıracı", ["Otomatik", "Virgül", "Noktalı virgül", "Sekme", "Dikey çizgi"], key="okuma_ayrac")
        kodlama = st.selectbox("Dosya kodlaması", ["Otomatik", "utf-8-sig", "cp1254", "utf-16"], key="okuma_kodlama")
    st.caption("CSV / TSV · En fazla 10 MB, 100.000 satır, 150 sütun.")

if ornek:
    veri = (KLASOR / "ornek_veri.csv").read_bytes()
    dosya_adi = "ornek_harcamalar"
elif dosya is not None:
    veri = dosya.getvalue()
    dosya_adi = Path(dosya.name).stem
else:
    st.markdown('''
    <section class="empty-workspace">
      <svg width="44" height="44" viewBox="0 0 44 44" fill="none" aria-hidden="true">
        <rect x="5" y="6" width="34" height="32" rx="3" stroke="currentColor" stroke-width="1.4"/>
        <path d="M5 17H39M5 27H39M17 6V38M29 6V38" stroke="currentColor" stroke-width="1.4"/>
      </svg>
      <h2>Bir tabloyla başla.</h2>
      <p>Menüden CSV dosyanı seç veya örnek veriyi aç.<br>
      Eksikleri incele, temizleme kurallarını seç ve sonucu indir.</p>
      <span>Dosyalar bu uygulamanın belleğinde işlenir.</span>
    </section>
    ''', unsafe_allow_html=True)
    st.stop()

ayrac = {"Otomatik": "Otomatik", "Virgül": ",", "Noktalı virgül": ";", "Sekme": "\t", "Dikey çizgi": "|"}[ayrac_adi]
kimlik = sha256(veri + str((ayrac, kodlama)).encode()).hexdigest()
if st.session_state.get("kaynak_kimligi") != kimlik:
    try:
        orijinal, okuma_bilgisi = csv_oku(veri, ayrac=ayrac, kodlama=kodlama)
    except ValueError as hata:
        st.error(str(hata))
        st.stop()
    anahtarlari_sil("k_", "f_", "a_")
    st.session_state.kaynak_kimligi = kimlik
    st.session_state.orijinal = orijinal
    st.session_state.okuma_bilgisi = okuma_bilgisi
    st.session_state.calisma = orijinal.copy()
    st.session_state.gecmis = pd.DataFrame(columns=["İşlem", "Sonuç"])
    st.session_state.uygulandi = False

orijinal = st.session_state.orijinal
sutunlar = orijinal.columns.tolist()
form_kimligi = f"{kimlik[:12]}_{st.session_state.get('form_surum', 0)}"

# 2. Temizleme kuralları. Form gönderilene kadar veri değişmez.
with st.sidebar:
    st.divider()
    st.markdown('<p class="side-heading">Temizleme kuralları</p>', unsafe_allow_html=True)
    st.caption("Kurallar her uygulamada orijinal verinin kopyasına uygulanır.")
    with st.form(f"temizleme_formu_{form_kimligi}"):
        with st.expander("Metin ve veri tipleri"):
            bosluk = st.checkbox("Metinlerin kenar boşluklarını temizle", value=True, key=f"k_bosluk_{form_kimligi}")
            sayilar = st.multiselect("Sayıya çevir", sutunlar, default=["tutar"] if ornek else [], key=f"k_sayilar_{form_kimligi}")
            ondalik = st.selectbox("Ondalık ayıracı", [".", ","], key=f"k_ondalik_{form_kimligi}")
            binlik_adi = st.selectbox("Binlik ayıracı", ["Yok", ".", ","], key=f"k_binlik_{form_kimligi}")
            tarihler = st.multiselect("Tarihe çevir", sutunlar, default=["tarih"] if ornek else [], key=f"k_tarihler_{form_kimligi}")
            tarih_bicimi = st.selectbox("Tarih biçimi", ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"], key=f"k_tarih_bicimi_{form_kimligi}")
        with st.expander("Tekrarlı kayıtlar"):
            tekrar_sil = st.checkbox("Tekrarlı kayıtları çıkar", value=ornek, key=f"k_tekrar_sil_{form_kimligi}")
            tekrar_sutunlar = st.multiselect("Tekrarı belirleyen sütunlar", sutunlar, default=["islem_id"] if ornek else [], key=f"k_tekrar_sutunlar_{form_kimligi}", help="Boş bırakırsan bütün sütunlar birlikte karşılaştırılır.")
            tekrar_tut = st.selectbox("Tekrarda tutulacak kayıt", ["İlk kayıt", "Son kayıt"], key=f"k_tekrar_tut_{form_kimligi}")
        with st.expander("Eksik değerler"):
            eksik_yontem_adi = st.selectbox("Eksik değerlere uygulanacak işlem", ["Koru", "Satırı çıkar", "Medyanla doldur", "Sabit değerle doldur"], index=1 if ornek else 0, key=f"k_eksik_yontem_{form_kimligi}")
            eksik_sutunlar = st.multiselect("Eksik işlemine dahil sütunlar", sutunlar, default=["tarih", "tutar"] if ornek else [], key=f"k_eksik_sutunlar_{form_kimligi}")
            sabit = st.text_input("Sabit doldurma değeri", key=f"k_sabit_{form_kimligi}", help="Yalnızca 'Sabit değerle doldur' seçeneğinde kullanılır.")
        uygula = st.form_submit_button("Temizliği uygula", type="primary", width="stretch", key=f"uygula_{form_kimligi}")

if uygula:
    ayarlar = dict(
        bosluk=bosluk, sayilar=sayilar, tarihler=tarihler,
        ondalik=ondalik, binlik="" if binlik_adi == "Yok" else binlik_adi,
        tarih_bicimi=tarih_bicimi, tekrar_sil=tekrar_sil,
        tekrar_sutunlar=tekrar_sutunlar, tekrar_tut="first" if tekrar_tut == "İlk kayıt" else "last",
        eksik_yontem={"Koru": "koru", "Satırı çıkar": "sil", "Medyanla doldur": "medyan", "Sabit değerle doldur": "sabit"}[eksik_yontem_adi],
        eksik_sutunlar=eksik_sutunlar, sabit=sabit,
    )
    try:
        sonuc, gecmis = veriyi_temizle(orijinal, ayarlar)
    except (ValueError, TypeError, OverflowError) as hata:
        st.error(str(hata))
        st.caption("Kurallar uygulanmadı; önceki çalışma tablosu korunuyor.")
    else:
        st.session_state.calisma = sonuc
        st.session_state.gecmis = gecmis
        st.session_state.uygulandi = True
        anahtarlari_sil("f_", "a_")
        st.success("Temizleme kuralları uygulandı.")

st.sidebar.button("Orijinale dön", on_click=sonucu_sifirla, width="stretch", disabled=not st.session_state.uygulandi, key="orijinale_don")
calisma = st.session_state.calisma
st.caption(f"{dosya_adi}.csv · {len(orijinal):,} kaynak satırı · {st.session_state.okuma_bilgisi['kodlama']}")
if not st.session_state.uygulandi:
    st.info("Alanlar önce metin olarak okunur; böylece kimliklerdeki sıfırlar korunur. Hesaplanacak sütunları menüden sayıya çevirip temizliği uygula.")

# 3. Filtreler yalnızca görüntüyü değiştirir; temizlenmiş kaynak saklanır.
gorunum = calisma
with st.expander("Filtrele ve sırala", expanded=False):
    sol, sag = st.columns(2)
    with sol:
        filtre_sutun = st.selectbox("Filtre sütunu", ["Filtre yok"] + sutunlar, key="f_sutun")
        if filtre_sutun != "Filtre yok":
            seri = calisma[filtre_sutun]
            dolu = seri.dropna()
            if is_numeric_dtype(seri):
                if not dolu.empty:
                    alt = st.number_input("En az", value=float(dolu.min()), key=f"f_alt_{filtre_sutun}")
                    ust = st.number_input("En çok", value=float(dolu.max()), key=f"f_ust_{filtre_sutun}")
                    if alt > ust:
                        st.warning("Alt sınır üst sınırdan büyük; bu filtre sonuç üretmez.")
                    gorunum = veri_filtrele(calisma, filtre_sutun, alt=alt, ust=ust)
                else:
                    st.caption("Bu sütunda geçerli sayısal ölçüm bulunmuyor.")
            elif is_datetime64_any_dtype(seri):
                if not dolu.empty:
                    aralik = st.date_input("Tarih aralığı", value=(dolu.min().date(), dolu.max().date()), key=f"f_tarih_{filtre_sutun}")
                    if isinstance(aralik, (tuple, list)) and len(aralik) == 2:
                        gorunum = veri_filtrele(calisma, filtre_sutun, baslangic=aralik[0], bitis=aralik[1])
                    else:
                        st.caption("Aralığın başlangıç ve bitişini seç.")
                else:
                    st.caption("Bu sütunda geçerli tarih bulunmuyor.")
            else:
                aranan = st.text_input("İçerdiği metin", key=f"f_metin_{filtre_sutun}", help="Büyük/küçük harf duyarsız düz metin araması.")
                gorunum = veri_filtrele(calisma, filtre_sutun, aranan=aranan)
    with sag:
        siralama = st.selectbox("Sıralama sütunu", ["Sıralama yok"] + sutunlar, key="f_siralama")
        azalan = st.checkbox("Büyükten küçüğe sırala", key="f_azalan")
        if siralama != "Sıralama yok":
            gorunum = gorunum.sort_values(siralama, ascending=not azalan, na_position="last", kind="stable")
        gorunen_sutunlar = st.multiselect("Gösterilecek ve indirilecek sütunlar", sutunlar, default=sutunlar, key="f_gorunen")
        st.button("Filtreleri sıfırla", on_click=filtreleri_sifirla, key="filtre_sifirla")

if not gorunen_sutunlar:
    st.warning("Tabloyu göstermek ve indirmek için en az bir sütun seç.")
    st.stop()
gorunum = gorunum[gorunen_sutunlar]
with indirme_yeri:
    st.download_button("CSV indir", csv_olustur(gorunum), file_name=f"{dosya_adi}_duzenlendi.csv", mime="text/csv", width="stretch", type="primary", disabled=gorunum.empty, key="csv_indir")

sayaclar = st.columns(4)
sayaclar[0].metric("Görüntülenen satır", f"{len(gorunum):,}")
sayaclar[1].metric("Seçili sütun", len(gorunum.columns))
sayaclar[2].metric("Eksik hücre", int(gorunum.isna().sum().sum()))
sayaclar[3].metric("Tam tekrar", int(gorunum.duplicated().sum()))

tablo_sekme, kalite_sekme, analiz_sekme, gecmis_sekme = st.tabs(["Çalışma tablosu", "Veri kalitesi", "Analiz", "İşlem geçmişi"])

with tablo_sekme:
    if gorunum.empty:
        st.info("Bu kurallar veya filtrelerle kayıt kalmadı. Filtreleri sıfırlayabilir ya da orijinal veriye dönebilirsin.")
    st.dataframe(gorunum.head(1000), hide_index=True, width="stretch", height=560, row_height=46)
    st.caption(f"Önizleme ilk {min(len(gorunum), 1000):,} satırı gösterir. CSV indirme, filtrelenmiş sonucun tamamını içerir.")
    with st.expander("Orijinal veriyi incele"):
        st.dataframe(orijinal.head(1000), hide_index=True, width="stretch", row_height=44)

with kalite_sekme:
    st.caption("Kalite karşılaştırması filtrelerden önceki çalışma tablosu ile orijinal dosyayı karşılaştırır.")
    once, sonra = st.columns(2)
    with once:
        st.markdown("**Orijinal**")
        st.dataframe(kalite_raporu(orijinal), hide_index=True, width="stretch", row_height=44)
    with sonra:
        st.markdown("**Çalışma tablosu**")
        st.dataframe(kalite_raporu(calisma), hide_index=True, width="stretch", row_height=44)
    st.caption("Tam tekrar bütün sütunları aynı olan satırları sayar. Kimliğe göre tekrar temizliği için menüden ilgili kimlik sütununu seç.")

with analiz_sekme:
    st.caption("Analizler görüntülenen satırları ve seçili sütunları kullanır.")
    sayisal = [ad for ad in gorunum.columns if is_numeric_dtype(gorunum[ad])]
    if not sayisal:
        st.info("Analiz için en az bir sütunu menüden sayıya çevirip temizliği uygula.")
    elif gorunum.empty:
        st.info("Analiz edilecek satır bulunmuyor.")
    else:
        st.markdown("**Gruplama**")
        a, b, c = st.columns(3)
        grup_adaylari = gorunum.columns.tolist()
        varsayilan_grup = "kategori" if "kategori" in grup_adaylari else next((ad for ad in grup_adaylari if ad not in sayisal), grup_adaylari[0])
        grup = a.selectbox("Grup sütunu", grup_adaylari, index=grup_adaylari.index(varsayilan_grup), key="a_grup")
        olcum = b.selectbox("Sayısal ölçüm", sayisal, key="a_olcum")
        metrik = c.selectbox("Grafikte göster", ["Toplam", "Ortalama", "En yüksek", "Kayıt", "Bilinen"], key="a_metrik")
        if grup == olcum:
            st.info("Gruplamak ve hesaplamak için farklı sütunlar seç.")
        else:
            ozet = grup_ozeti(gorunum, grup, olcum)
            st.dataframe(ozet.head(1000), hide_index=True, width="stretch", row_height=44)
            grafik = ozet.dropna(subset=[metrik]).nlargest(20, metrik).copy()
            grafik["Grup"] = grafik["Grup"].astype("string").fillna("(Eksik değer)")
            if not grafik.empty:
                st.bar_chart(grafik, x="Grup", y=metrik, color="#454545", height=420)
            st.caption("Grafik seçilen ölçüye göre en yüksek 20 grubu gösterir. Bilinmeyen toplamlar sıfır sayılmaz.")
            st.download_button("Özet CSV indir", csv_olustur(ozet), file_name=f"{dosya_adi}_ozet.csv", mime="text/csv", key="ozet_indir")

        st.divider()
        st.markdown("**İki sayısal sütunun ilişkisi**")
        if len(sayisal) < 2:
            st.caption("Dağılım grafiği için iki sayısal sütun gerekli.")
        else:
            sol, sag = st.columns(2)
            x = sol.selectbox("Yatay eksen", sayisal, key="a_x")
            y = sag.selectbox("Dikey eksen", sayisal, index=1, key="a_y")
            if x == y:
                st.info("İlişkiyi incelemek için farklı sütunlar seç.")
            else:
                noktalar = gorunum[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
                gosterilen = noktalar.sample(5000, random_state=42) if len(noktalar) > 5000 else noktalar
                if noktalar.empty:
                    st.info("İki sütunun da geçerli olduğu ortak bir ölçüm bulunmuyor.")
                else:
                    st.scatter_chart(gosterilen, x=x, y=y, color="#454545", height=420)
                    korelasyon = noktalar[x].corr(noktalar[y]) if len(noktalar) >= 2 and noktalar[x].nunique() > 1 and noktalar[y].nunique() > 1 else np.nan
                    yorum = f"Pearson korelasyonu: {korelasyon:.3f}." if pd.notna(korelasyon) else "Korelasyon için yeterli değişken ölçüm yok."
                    st.caption(f"{len(noktalar):,} ortak ölçüm; grafikte {len(gosterilen):,} nokta. {yorum} Korelasyon nedensellik göstermez.")

with gecmis_sekme:
    st.caption("Son uygulanan temizliğin adımları. Yeni kurallar önceki temizliğin üzerine eklenmez; orijinalden tekrar hesaplanır.")
    if st.session_state.gecmis.empty:
        st.info("Henüz bir temizleme işlemi uygulanmadı.")
    else:
        st.dataframe(st.session_state.gecmis, hide_index=True, width="stretch", row_height=46)
    st.caption(f"Orijinal: {len(orijinal):,} satır · Çalışma tablosu: {len(calisma):,} satır · Filtrelenmiş görünüm: {len(gorunum):,} satır.")
