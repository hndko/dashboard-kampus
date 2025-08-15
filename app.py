import re
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# -----------------
# PENGATURAN HALAMAN
# -----------------
st.set_page_config(
    page_title="Dashboard Analisis Kepuasan Fasilitas STHM",
    page_icon="logo.jpeg",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.75rem; }
</style>
""", unsafe_allow_html=True)

# -----------------
# DEFINISI KATEGORI & PERTANYAAN
# -----------------
kategori_fasilitas = {
    'Ruang Kelas': [
        'Ruang kelas bersih & rapi', 'Ventilasi & pencahayaan baik', 'Kursi & meja nyaman',
        'LCD/Proyektor berfungsi baik', 'Pendingin ruangan (AC/kipas) memadai', 'Sarana tulis (papan/marker) tersedia'
    ],
    'Laboratorium': [
        'Peralatan lab lengkap & berfungsi', 'Kebersihan laboratorium terjaga',
        'Petugas lab membantu', 'Aturan keselamatan jelas', 'Akses lab sesuai kebutuhan'
    ],
    'Perpustakaan': [
        'Apakah koleksi buku perpustakaan cukup lengkap ?', 'Suasana perpustakaan kondusif',
        'Tempat duduk perpustakaan memadai', 'Sistem peminjaman buku efisien',
        'Apakah petugas perpustakaan ramah', 'Tersedia internet/komputer', 'Akses jurnal digital mudah'
    ],
    'Teknologi & Internet': [
        'Wi-Fi mudah diakses', 'Kecepatan internet stabil', 'Sistem akademik mudah digunakan',
        'Bantuan tim IT responsif.'
    ],
    'Kebersihan & Kesehatan': [
        'Tempat sampah tersedia dan memadai', 'Toilet bersih', 'Pembersihan dilakukan secara rutin',
        'Tersedia P3K', 'Lingkungan higienis dan bersih'
    ],
    'Kantin': [
        'Harga makanan terjangkau', 'Pilihan menu bervariasi', 'Kebersihan area kantin baik',
        'Area makan nyaman', 'Pelayanan ramah & cepat.'
    ],
    'Keamanan & Parkir': [
        'Sistem keamanan efektif.', 'Petugas ramah & membantu', 'Parkir memadai & aman',
        'Penerangan cukup', 'Tidak ada area rawan.', 'Akses masuk terkontrol',
        'Evakuasi & jalur Darurat jelas'
    ]
}

# -----------------
# UTIL: NORMALISASI NILAI
# -----------------
ABBR_UPPER = {"lppm", "lpm", "sthm", "s1", "s2", "s3", "ti", "si", "mi", "mh", "ilmu hukum", "hukum"}  # set dasar

def normalize_prodi(x: str) -> str:
    if pd.isna(x):
        return x
    s = str(x).strip()
    # satukan variasi s1/s-1/s 1
    s_low = s.lower().replace("_", " ").replace("-", "").replace("  ", " ").strip()
    s_low = re.sub(r"\bs\s*1\b", "s1", s_low)
    s_low = re.sub(r"\bs\s*2\b", "s2", s_low)
    s_low = re.sub(r"\bs\s*3\b", "s3", s_low)

    # title-case default
    pretty = s_low.title()

    # kapitalisasi singkatan umum
    pretty = re.sub(r"\bLppm\b", "LPPM", pretty)
    pretty = re.sub(r"\bLpm\b", "LPM", pretty)
    pretty = re.sub(r"\bS1\b", "S1", pretty)
    pretty = re.sub(r"\bS2\b", "S2", pretty)
    pretty = re.sub(r"\bS3\b", "S3", pretty)
    pretty = re.sub(r"\bTi\b", "TI", pretty)
    pretty = re.sub(r"\bSi\b", "SI", pretty)

    # benahi variasi lazim
    pretty = pretty.replace("Ilmu Hukum", "Hukum")
    return pretty

USIA_ORDER = ["< 20", "20–30", "31–40", "> 40"]

def normalize_usia(x: str) -> str:
    if pd.isna(x):
        return x
    s = str(x).strip().lower()
    s = s.replace("tahun", "").replace("th", "").strip()
    s = s.replace("–", "-").replace("—", "-")  # satukan dash
    # pola rentang: 20-30, 31 - 40
    m = re.match(r"^(\d+)\s*-\s*(\d+)$", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a <= 20 and b <= 20:
            return "< 20"
        if a <= 20 and b <= 30 or (a >= 20 and b <= 30):
            return "20–30"
        if a <= 31 and b <= 40:
            return "31–40"
    # lebih dari / di atas
    if re.search(r"(lebih dari|di atas|>)\s*40", s):
        return "> 40"
    # kurang dari / di bawah
    if re.search(r"(kurang dari|di bawah|<)\s*20", s):
        return "< 20"
    # angka tunggal
    m2 = re.match(r"^(\d+)$", s)
    if m2:
        age = int(m2.group(1))
        if age < 20:
            return "< 20"
        if 20 <= age <= 30:
            return "20–30"
        if 31 <= age <= 40:
            return "31–40"
        return "> 40"

    # fallback ke kategori paling mendekati
    if "40" in s:
        return "> 40"
    if "31" in s or "32" in s or "33" in s or "34" in s or "35" in s or "36" in s or "37" in s or "38" in s or "39" in s:
        return "31–40"
    if "20" in s or "30" in s:
        return "20–30"
    if "19" in s or "18" in s or "17" in s:
        return "< 20"
    return s  # biarkan apa adanya bila tidak terdeteksi

def usia_sort_key(label: str) -> int:
    try:
        return USIA_ORDER.index(label)
    except ValueError:
        return len(USIA_ORDER) + 1

# -----------------
# MEMUAT DATA
# -----------------
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    # Alias kolom Program Studi (nama panjang di data asli)
    if "Program Studi" not in df.columns:
        for c in df.columns:
            cname = c.strip().lower()
            if "program studi" in cname and ("unit kerja" in cname or "lppm" in cname or "contoh" in cname):
                df["Program Studi"] = df[c]
                break

    # Normalisasi kolom Program Studi & Usia untuk dipakai di filter
    if "Program Studi" in df.columns:
        df["Program Studi (Norm)"] = df["Program Studi"].apply(normalize_prodi)
    if "Usia" in df.columns:
        df["Usia (Norm)"] = df["Usia"].apply(normalize_usia)

    # Pastikan kolom pertanyaan bernilai numerik
    kolom_penilaian = [col for sublist in kategori_fasilitas.values() for col in sublist]
    for col in kolom_penilaian:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

df = load_data('data_preprocessed.csv')

# -----------------
# SIDEBAR FILTER
# -----------------
st.sidebar.header("Filter Responden")

status_list = ['Semua'] + (df['Status Anda'].dropna().unique().tolist() if 'Status Anda' in df.columns else [])
gender_list = ['Semua', 'Laki-laki', 'Perempuan']

# Pakai kolom normalisasi untuk Usia & Program Studi
usia_source_col = "Usia (Norm)" if "Usia (Norm)" in df.columns else "Usia"
prodi_source_col = "Program Studi (Norm)" if "Program Studi (Norm)" in df.columns else "Program Studi"

usia_unique = []
if usia_source_col in df.columns:
    usia_unique = sorted(df[usia_source_col].dropna().unique().tolist(), key=usia_sort_key)
prodi_unique = []
if prodi_source_col in df.columns:
    # sort case-insensitive, unik
    prodi_unique = sorted(set([str(x) for x in df[prodi_source_col].dropna().tolist()]), key=lambda s: s.lower())

usia_list = ['Semua'] + usia_unique
prodi_list = ['Semua'] + prodi_unique

status_filter = st.sidebar.selectbox("Status", status_list)
gender_filter = st.sidebar.selectbox("Jenis Kelamin", gender_list)
usia_filter = st.sidebar.selectbox("Usia", usia_list)
prodi_filter = st.sidebar.selectbox("Program Studi", prodi_list)

# Terapkan filter ke DataFrame (gunakan kolom norm untuk usia & prodi)
df_filtered = df.copy()
if 'Status Anda' in df_filtered.columns and status_filter != 'Semua':
    df_filtered = df_filtered[df_filtered['Status Anda'] == status_filter]
if 'Jenis Kelamin' in df_filtered.columns and gender_filter != 'Semua':
    df_filtered = df_filtered[df_filtered['Jenis Kelamin'].str.lower() == gender_filter.lower()]
if usia_source_col in df_filtered.columns and usia_filter != 'Semua':
    df_filtered = df_filtered[df_filtered[usia_source_col] == usia_filter]
if prodi_source_col in df_filtered.columns and prodi_filter != 'Semua':
    df_filtered = df_filtered[df_filtered[prodi_source_col] == prodi_filter]

# -----------------
# HEADER + LOGO
# -----------------
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title("Dashboard Analisis Kepuasan Fasilitas STHM")
    st.markdown("Gunakan filter di sebelah kiri untuk menganalisis data.")
with col_logo:
    st.image("logo.jpeg", width=120)

st.markdown("---")

if df_filtered.empty:
    st.warning("Tidak ada data yang cocok dengan filter yang Anda pilih.")
else:
    # --- KARTU METRIK ---
    avg_scores = []
    for kategori, kolom in kategori_fasilitas.items():
        valid_cols = [col for col in kolom if col in df_filtered.columns]
        if valid_cols:
            avg_score = float(df_filtered[valid_cols].mean(skipna=True).mean(skipna=True))
            avg_scores.append({'Kategori': kategori, 'Rata-rata Skor': avg_score})
    df_scores = pd.DataFrame(avg_scores)

    total_responden = int(len(df_filtered))
    avg_satisfaction = float(df_scores['Rata-rata Skor'].mean()) if not df_scores.empty else 0.0

    if not df_scores.empty:
        idx_max = int(df_scores['Rata-rata Skor'].idxmax())
        idx_min = int(df_scores['Rata-rata Skor'].idxmin())
        hr_cat = str(df_scores.loc[idx_max, 'Kategori'])
        hr_score = float(df_scores.loc[idx_max, 'Rata-rata Skor'])
        lr_cat = str(df_scores.loc[idx_min, 'Kategori'])
        lr_score = float(df_scores.loc[idx_min, 'Rata-rata Skor'])
    else:
        hr_cat, hr_score = "N/A", 0.0
        lr_cat, lr_score = "N/A", 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="👥 Total Responden", value=total_responden)
    with col2:
        st.metric(label="⭐ Rata-rata Kepuasan", value=f"{avg_satisfaction:.2f}")
    with col3:
        st.metric(label="👍 Kategori Tertinggi", value=hr_cat, delta=f"{hr_score:.2f}")
    with col4:
        st.metric(label="👎 Kategori Terendah", value=lr_cat, delta=f"{lr_score:.2f}", delta_color="inverse")

    st.markdown("---")

    # --- DONUT CHART DEMOGRAFI ---
    st.header("Distribusi Demografi Responden")
    col_demo1, col_demo2, col_demo3 = st.columns(3)

    with col_demo1:
        if 'Status Anda' in df_filtered.columns:
            df_status = (
                df_filtered['Status Anda']
                .value_counts()
                .reset_index(name='count')
                .rename(columns={'index': 'Status Anda'})
            )
            fig_status = px.pie(df_status, names='Status Anda', values='count', title='Distribusi Status', hole=0.4)
            fig_status.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_status, use_container_width=True)

    with col_demo2:
        if 'Jenis Kelamin' in df_filtered.columns:
            df_gender = (
                df_filtered['Jenis Kelamin']
                .value_counts()
                .reset_index(name='count')
                .rename(columns={'index': 'Jenis Kelamin'})
            )
            fig_gender = px.pie(df_gender, names='Jenis Kelamin', values='count', title='Distribusi Jenis Kelamin', hole=0.4)
            fig_gender.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_gender, use_container_width=True)

    with col_demo3:
        if usia_source_col in df_filtered.columns:
            df_age = (
                df_filtered[usia_source_col]
                .value_counts()
                .rename_axis('Usia')
                .reset_index(name='count')
            )
            # urutkan sesuai kategori yang rapi
            df_age['order'] = df_age['Usia'].apply(usia_sort_key)
            df_age = df_age.sort_values('order').drop(columns='order')
            fig_age = px.pie(df_age, names='Usia', values='count', title='Distribusi Usia', hole=0.4)
            fig_age.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")

    # --- RINGKASAN SKOR PER KATEGORI ---
    st.header("Ringkasan Skor Kepuasan per Kategori Fasilitas")
    if not df_scores.empty:
        fig_bar = px.bar(
            df_scores.sort_values('Rata-rata Skor', ascending=True),
            x='Rata-rata Skor', y='Kategori', orientation='h',
            title='Rata-rata Skor Kepuasan (Skala 1-5)', text='Rata-rata Skor', range_x=[1, 5]
        )
        fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_bar.update_layout(yaxis={'title': ''}, height=500)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # --- DETAIL SKOR PER PERTANYAAN ---
    st.header("Detail Skor per Pertanyaan")
    kategori_pilihan = st.selectbox("Pilih Kategori", list(kategori_fasilitas.keys()))

    valid_detail_cols = [col for col in kategori_fasilitas[kategori_pilihan] if col in df_filtered.columns]
    if valid_detail_cols:
        df_detail = df_filtered[valid_detail_cols].mean().reset_index()
        df_detail.columns = ['Pertanyaan', 'Rata-rata Skor']

        fig_detail = px.bar(
            df_detail.sort_values('Rata-rata Skor', ascending=False),
            x='Rata-rata Skor', y='Pertanyaan', orientation='h',
            title=f'Detail Skor untuk Kategori: {kategori_pilihan}', text='Rata-rata Skor', range_x=[1, 5]
        )
        fig_detail.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_detail.update_layout(yaxis={'title': ''}, height=400)
        st.plotly_chart(fig_detail, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("Dashboard ini dibuat menggunakan data survei kepuasan fasilitas STHM.")
