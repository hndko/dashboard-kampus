import re
import difflib
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional, Dict, List, Tuple

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
    'Ruang Kelas/Kerja': [
        'Ruang kelas bersih & rapi',
        'Ventilasi & pencahayaan baik',
        'Kursi & meja nyaman',
        'LCD/Proyektor berfungsi baik',
        'Pendingin ruangan (AC/kipas) memadai',
        'Sarana tulis (papan/marker) tersedia'
    ],
    'Laboratorium': [
        'Peralatan lab lengkap & berfungsi',
        'Kebersihan laboratorium terjaga',
        'Petugas lab membantu',
        'Aturan keselamatan jelas',
        'Akses lab sesuai kebutuhan'
    ],
    'Perpustakaan': [
        'Apakah koleksi buku perpustakaan cukup lengkap ?',
        'Suasana perpustakaan kondusif',
        'Tempat duduk perpustakaan memadai',
        'Sistem peminjaman buku efisien',
        'Apakah petugas perpustakaan ramah',
        'Tersedia internet/komputer',
        'Akses jurnal digital mudah'
    ],
    'Teknologi & Internet': [
        'Wi-Fi mudah diakses',
        'Kecepatan internet stabil',
        'Sistem akademik mudah digunakan',
        'Bantuan tim IT responsif.'
    ],
    'Kebersihan & Kesehatan': [
        'Tempat sampah tersedia dan memadai',
        'Toilet bersih',
        'Pembersihan dilakukan secara rutin',
        'Tersedia P3K',
        'Lingkungan higienis dan bersih'
    ],
    'Kantin': [
        'Harga makanan terjangkau',
        'Pilihan menu bervariasi',
        'Kebersihan area kantin baik',
        'Area makan nyaman',
        'Pelayanan ramah & cepat.'
    ],
    'Keamanan & Parkir': [
        'Sistem keamanan efektif.',
        'Petugas ramah & membantu',
        'Parkir memadai & aman',
        'Penerangan cukup',
        'Tidak ada area rawan.',
        'Akses masuk terkontrol',
        'Evakuasi & jalur Darurat jelas'
    ]
}

# -----------------
# UTIL & NORMALISASI
# -----------------
USIA_ORDER = ["< 20", "20–30", "31–40", "> 40"]

def normalize_label(s: str) -> str:
    """Normalisasi label untuk pemetaan kolom (hilangkan variasi minor)."""
    if s is None:
        return ""
    t = str(s).strip().lower()
    t = t.replace("&", " dan ")
    t = t.replace("/", " ")
    t = re.sub(r"[\(\)\[\]\.\,\:;!\?\"'`]+", " ", t)   # buang tanda baca umum
    t = re.sub(r"\s+", " ", t).strip()
    return t

def normalize_prodi(x: str) -> str:
    if pd.isna(x):
        return x
    s = str(x).strip()
    s_low = s.lower().replace("_", " ").replace("-", "").replace("  ", " ").strip()
    s_low = re.sub(r"\bs\s*1\b", "s1", s_low)
    s_low = re.sub(r"\bs\s*2\b", "s2", s_low)
    s_low = re.sub(r"\bs\s*3\b", "s3", s_low)
    pretty = s_low.title()
    pretty = re.sub(r"\bLppm\b", "LPPM", pretty)
    pretty = re.sub(r"\bLpm\b", "LPM", pretty)
    pretty = re.sub(r"\bS1\b", "S1", pretty)
    pretty = re.sub(r"\bS2\b", "S2", pretty)
    pretty = re.sub(r"\bS3\b", "S3", pretty)
    pretty = re.sub(r"\bTi\b", "TI", pretty)
    pretty = re.sub(r"\bSi\b", "SI", pretty)
    pretty = pretty.replace("Ilmu Hukum", "Hukum")
    return pretty

def normalize_usia(x: str) -> str:
    if pd.isna(x):
        return x
    s = str(x).strip().lower()
    s = s.replace("tahun", "").replace("th", "").strip()
    s = s.replace("–", "-").replace("—", "-")
    m = re.match(r"^(\d+)\s*-\s*(\d+)$", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a <= 20 and b <= 20:
            return "< 20"
        if a <= 20 and b <= 30 or (a >= 20 and b <= 30):
            return "20–30"
        if a <= 31 and b <= 40:
            return "31–40"
    if re.search(r"(lebih dari|di atas|>)\s*40", s):
        return "> 40"
    if re.search(r"(kurang dari|di bawah|<)\s*20", s):
        return "< 20"
    m2 = re.match(r"^(\d+)$", s)
    if m2:
        age = int(m2.group(1))
        if age < 20: return "< 20"
        if 20 <= age <= 30: return "20–30"
        if 31 <= age <= 40: return "31–40"
        return "> 40"
    if "40" in s: return "> 40"
    if any(x in s for x in list("313233343536373839")): return "31–40"
    if "20" in s or "30" in s: return "20–30"
    if any(x in s for x in ["19","18","17"]): return "< 20"
    return s

def normalize_gender(x: str) -> str:
    if pd.isna(x):
        return "Lainnya/Unknown"
    s = str(x).strip().lower()
    if s in ["laki-laki", "laki laki", "pria", "male", "m"]: return "Laki-laki"
    if s in ["perempuan", "wanita", "female", "f"]: return "Perempuan"
    return "Lainnya/Unknown"

def usia_sort_key(label: str) -> int:
    try:
        return USIA_ORDER.index(label)
    except ValueError:
        return len(USIA_ORDER) + 1

def to_float(x) -> Optional[float]:
    try:
        if pd.isna(x): return None
        return float(x)
    except Exception:
        return None

def build_dfcol_map(df_cols: List[str]) -> Tuple[Dict[str,str], List[str]]:
    """Bangun peta: normalized_col -> original_col, juga sediakan daftar normalized untuk fuzzy match."""
    mapping: Dict[str, str] = {}
    normalized_list: List[str] = []
    for c in df_cols:
        n = normalize_label(c)
        if n and n not in mapping:  # pertama menang
            mapping[n] = c
            normalized_list.append(n)
    return mapping, normalized_list

def resolve_question_columns(question_labels: List[str], df_cols: List[str]) -> Tuple[List[str], List[str]]:
    """
    Kembalikan: ([kolom_df_yang_ditemukan], [pertanyaan_yang_tidak_ketemu])
    Cocokkan pakai normalisasi; jika tidak ketemu, coba difflib.get_close_matches.
    """
    mapping, normalized_df = build_dfcol_map(df_cols)
    found: List[str] = []
    missing: List[str] = []

    for q in question_labels:
        nq = normalize_label(q)
        if nq in mapping:
            found.append(mapping[nq])
            continue
        # fuzzy
        candidates = difflib.get_close_matches(nq, normalized_df, n=1, cutoff=0.85)
        if candidates:
            found.append(mapping[candidates[0]])
        else:
            missing.append(q)
    # unik dan urutan sesuai urutan pertanyaan input
    uniq_ordered = []
    seen = set()
    for q in question_labels:
        nq = normalize_label(q)
        # pilih kolom yang match tepat atau fuzzy yang sudah kita tambahkan
        if nq in mapping:
            col = mapping[nq]
        else:
            cand = difflib.get_close_matches(nq, normalized_df, n=1, cutoff=0.85)
            col = mapping[cand[0]] if cand else None
        if col and col not in seen:
            uniq_ordered.append(col)
            seen.add(col)

    return uniq_ordered, missing

# -----------------
# MEMUAT DATA
# -----------------
@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    # Alias Program Studi bila tidak ada —> treat as Program Studi/Unit Kerja
    if "Program Studi" not in df.columns:
        for c in df.columns:
            cname = c.strip().lower()
            if "program studi" in cname or "prodi" in cname or ("unit kerja" in cname) or ("lppm" in cname):
                df["Program Studi"] = df[c]
                break

    if "Program Studi" in df.columns:
        df["Program Studi (Norm)"] = df["Program Studi"].apply(normalize_prodi)
    if "Usia" in df.columns:
        df["Usia (Norm)"] = df["Usia"].apply(normalize_usia)
    if "Jenis Kelamin" in df.columns:
        df["JK (Norm)"] = df["Jenis Kelamin"].apply(normalize_gender)

    # Pastikan kolom pertanyaan numerik float built-in
    kolom_penilaian = [col for sublist in kategori_fasilitas.values() for col in sublist]
    for col in kolom_penilaian:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').apply(to_float)

    return df

df = load_data('data_preprocessed.csv')

# -----------------
# SIDEBAR FILTER
# -----------------
st.sidebar.header("Filter Responden")

status_list = ['Semua'] + (df['Status Anda'].dropna().unique().tolist() if 'Status Anda' in df.columns else [])
gender_list = ['Semua', 'Laki-laki', 'Perempuan']

usia_source_col = "Usia (Norm)" if "Usia (Norm)" in df.columns else "Usia"
prodi_source_col = "Program Studi (Norm)" if "Program Studi (Norm)" in df.columns else "Program Studi"

usia_unique = []
if usia_source_col in df.columns:
    usia_unique = sorted(df[usia_source_col].dropna().unique().tolist(), key=usia_sort_key)
prodi_unique = []
if prodi_source_col in df.columns:
    prodi_unique = sorted(set([str(x) for x in df[prodi_source_col].dropna().tolist()]), key=lambda s: s.lower())

usia_list = ['Semua'] + usia_unique
prodi_list = ['Semua'] + prodi_unique if prodi_unique else ['Semua']

status_filter = st.sidebar.selectbox("Status", status_list)
gender_filter = st.sidebar.selectbox("Jenis Kelamin", gender_list)
usia_filter = st.sidebar.selectbox("Usia", usia_list)

# Label sebagai "Program Studi/Unit Kerja"
if prodi_source_col in df.columns:
    prodi_filter = st.sidebar.selectbox("Program Studi/Unit Kerja", prodi_list)
else:
    prodi_filter = 'Semua'
    st.sidebar.caption("ℹ️ Kolom **Program Studi/Unit Kerja** tidak ditemukan—filter disembunyikan.")

# Terapkan filter
df_filtered = df.copy()
if 'Status Anda' in df_filtered.columns and status_filter != 'Semua':
    df_filtered = df_filtered[df_filtered['Status Anda'] == status_filter]
if 'Jenis Kelamin' in df_filtered.columns and gender_filter != 'Semua':
    df_filtered = df_filtered[df_filtered['Jenis Kelamin'].astype(str).str.lower() == gender_filter.lower()]
if usia_source_col in df_filtered.columns and usia_filter != 'Semua':
    df_filtered = df_filtered[df_filtered[usia_source_col] == usia_filter]
if (prodi_source_col in df_filtered.columns) and prodi_filter != 'Semua':
    df_filtered = df_filtered[df_filtered[prodi_source_col] == prodi_filter]

# -----------------
# HEADER + LOGO
# -----------------
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title("Dashboard Analisis Kepuasan Fasilitas STHM")
    st.markdown("Gunakan filter di sebelah kiri untuk menganalisis data.")
with col_logo:
    try:
        st.image("logo.jpeg", width=120)
    except Exception:
        pass

st.markdown("---")

if df_filtered.empty:
    st.warning("Tidak ada data yang cocok dengan filter yang Anda pilih.")
else:
    # --- KARTU METRIK ---
    avg_scores = []
    for kategori, kolom in kategori_fasilitas.items():
        # Petakan kolom berdasarkan isi DataFrame (toleran terhadap variasi nama)
        resolved_cols, _ = resolve_question_columns(kolom, df_filtered.columns.tolist())
        if resolved_cols:
            sub = df_filtered[resolved_cols].apply(pd.to_numeric, errors='coerce').astype(float)
            avg_score = float(sub.mean(skipna=True).mean(skipna=True))
            avg_scores.append({'Kategori': str(kategori), 'Rata-rata Skor': avg_score})
    df_scores = pd.DataFrame(avg_scores)

    if not df_scores.empty:
        df_scores['Rata-rata Skor'] = pd.to_numeric(df_scores['Rata-rata Skor'], errors='coerce').astype(float)

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
        st.metric(label="👥 Total Responden", value=int(total_responden))
    with col2:
        st.metric(label="⭐ Rata-rata Kepuasan", value=f"{float(avg_satisfaction):.2f}")
    with col3:
        st.metric(label="👍 Kategori Tertinggi", value=str(hr_cat), delta=f"{float(hr_score):.2f}")
    with col4:
        st.metric(label="👎 Kategori Terendah", value=str(lr_cat), delta=f"{float(lr_score):.2f}", delta_color="inverse")

    st.markdown("---")

    # --- DONUT CHART DEMOGRAFI ---
    st.header("Distribusi Demografi Responden")
    col_demo1, col_demo2, col_demo3 = st.columns(3)

    with col_demo1:
        if 'Status Anda' in df_filtered.columns:
            df_status = (
                df_filtered['Status Anda']
                .value_counts(dropna=False)
                .rename_axis('Status Anda')
                .reset_index(name='count')
            )
            fig_status = px.pie(
                df_status, names='Status Anda', values='count',
                title='Distribusi Status', hole=0.4
            )
            fig_status.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_status, use_container_width=True)

    with col_demo2:
        if 'JK (Norm)' in df_filtered.columns or 'Jenis Kelamin' in df_filtered.columns:
            jk_col = 'JK (Norm)' if 'JK (Norm)' in df_filtered.columns else 'Jenis Kelamin'
            jk_series = df_filtered[jk_col].astype(str)
            if gender_filter == 'Semua':
                jk_series = jk_series[jk_series.isin(['Laki-laki', 'Perempuan'])]
            df_gender = (
                jk_series
                .value_counts(dropna=False)
                .rename_axis('Jenis Kelamin')
                .reset_index(name='count')
            )
            if not df_gender.empty:
                fig_gender = px.ppie = px.pie(
                    df_gender, names='Jenis Kelamin', values='count',
                    title='Distribusi Jenis Kelamin', hole=0.4
                )
                fig_gender.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_gender, use_container_width=True)

    with col_demo3:
        usia_col = 'Usia (Norm)' if 'Usia (Norm)' in df_filtered.columns else ('Usia' if 'Usia' in df_filtered.columns else None)
        if usia_col is not None:
            df_age = (
                df_filtered[usia_col]
                .value_counts(dropna=False)
                .rename_axis('Usia')
                .reset_index(name='count')
            )
            df_age['order'] = df_age['Usia'].apply(usia_sort_key)
            df_age = df_age.sort_values('order').drop(columns='order')
            fig_age = px.pie(
                df_age, names='Usia', values='count',
                title='Distribusi Usia', hole=0.4
            )
            fig_age.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")

    # --- RINGKASAN SKOR PER KATEGORI ---
    st.header("Ringkasan Skor Kepuasan per Kategori Fasilitas")
    if not df_scores.empty:
        df_scores_plot = df_scores.copy()
        df_scores_plot['Rata-rata Skor'] = pd.to_numeric(df_scores_plot['Rata-rata Skor'], errors='coerce').astype(float)
        df_plot_sorted = df_scores_plot.sort_values('Rata-rata Skor', ascending=True)

        fig_bar = px.bar(
            df_plot_sorted,
            x='Rata-rata Skor',
            y='Kategori',
            orientation='h',
            title='Rata-rata Skor Kepuasan (Skala 1–5)',
            text='Rata-rata Skor',
            range_x=(1.0, 5.0)
        )
        fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_bar.update_layout(yaxis={'title': ''}, height=500)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # --- DETAIL SKOR PER PERTANYAAN (SELECT TANPA "LABORATORIUM") ---
    st.header("Detail Skor per Pertanyaan")
    opsi_kategori_detail = [k for k in kategori_fasilitas.keys() if k.lower() != 'laboratorium']
    # default ke "Ruang Kelas/Kerja" bila ada
    index_default = 0
    if 'Ruang Kelas/Kerja' in opsi_kategori_detail:
        index_default = opsi_kategori_detail.index('Ruang Kelas/Kerja')
    kategori_pilihan = st.selectbox("Pilih Kategori (tanpa Laboratorium)", opsi_kategori_detail, index=index_default)

    # PETA KOLON PERTANYAAN → KOLON DATAFRAME (toleran)
    question_labels = kategori_fasilitas[kategori_pilihan]
    resolved_cols, missing_cols = resolve_question_columns(question_labels, df_filtered.columns.tolist())

    if missing_cols:
        st.warning("Beberapa pertanyaan belum ditemukan di kolom CSV: " + ", ".join(missing_cols))

    if resolved_cols:
        df_detail = (
            df_filtered[resolved_cols]
            .apply(pd.to_numeric, errors='coerce')
            .astype(float)
            .mean()
            .reset_index()
        )
        df_detail.columns = ['Pertanyaan (CSV)', 'Rata-rata Skor']
        # Tampilkan label yang ramah (pakai urutan dari question_labels)
        # bangun peta: df_col -> label pertanyaan yang dipilih
        df_map = {}
        mp_df, _ = build_dfcol_map(df_filtered.columns.tolist())
        for q in question_labels:
            n = normalize_label(q)
            # temukan col yang dipakai
            if n in mp_df:
                df_map[mp_df[n]] = q
            else:
                cand = difflib.get_close_matches(n, list(mp_df.keys()), n=1, cutoff=0.85)
                if cand:
                    df_map[mp_df[cand[0]]] = q

        df_detail['Pertanyaan'] = df_detail['Pertanyaan (CSV)'].map(lambda c: df_map.get(c, c))
        df_detail = df_detail[['Pertanyaan', 'Rata-rata Skor']]

        df_detail['Rata-rata Skor'] = pd.to_numeric(df_detail['Rata-rata Skor'], errors='coerce').astype(float)
        df_det_sorted = df_detail.sort_values('Rata-rata Skor', ascending=False)

        fig_detail = px.bar(
            df_det_sorted,
            x='Rata-rata Skor',
            y='Pertanyaan',
            orientation='h',
            title=f'Detail Skor untuk Kategori: {kategori_pilihan}',
            text='Rata-rata Skor',
            range_x=(1.0, 5.0)
        )
        fig_detail.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_detail.update_layout(yaxis={'title': ''}, height=420)
        st.plotly_chart(fig_detail, use_container_width=True)
    else:
        st.info("Kolom pertanyaan untuk kategori ini belum ditemukan di file data. Cek nama kolom CSV-nya ya.")

st.sidebar.markdown("---")
st.sidebar.info("Dashboard ini dibuat menggunakan data survei kepuasan fasilitas STHM.")
