import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# -----------------
# PENGATURAN HALAMAN
# -----------------
# Menggunakan logo sebagai ikon halaman dan menghapus ikon toga
st.set_page_config(
    page_title="Dashboard Kepuasan STHM",
    page_icon="logo.jpeg",
    layout="wide"
)

# Menambahkan CSS kustom untuk mengecilkan font di dalam kartu metrik
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 1.75rem;
}
</style>
""", unsafe_allow_html=True)


# -----------------
# DATA & KONFIGURASI
# -----------------
kategori_fasilitas = {
    'Ruang Kelas & Belajar': [
        'Ruang kelas/kerja bersih & tertata.', 'Meja & kursi nyaman.', 'Pencahayaan cukup.',
        'Ventilasi/AC berfungsi dengan baik.', 'Papan tulis & spidol/ alat tulis memadai.',
        'Proyektor & alat ajar berfungsi.', 'Terdapat colokan listrik', 'Ruang cukup luas',
        'Kebisingan dari luar tidak mengganggu.', 'Saya nyaman belajar/mengajar/kerja'
    ],
    'Perpustakaan': [
        'Apakah koleksi buku perpustakaan cukup lengkap ?', 'Suasana perpustakaan kondusif',
        'Tempat duduk perpustakaan memadai', 'Sistem peminjaman buku efisien',
        'Apakah petugas perpustakaan ramah', 'Tersedia internet/komputer', 'Akses jurnal digital mudah'
    ],
    'Teknologi & Internet': [
        'Wi‑Fi mudah diakses', 'Kecepatan internet stabil', 'Sistem akademik mudah digunakan',
        'Bantuan tim IT responsif.'
    ],
    'Kebersihan & Kesehatan': [
        'Tempat sampah tersedia dan memadai', 'Toilet bersih', 'Pembersihan dilakukan secara rutin',
        'Tersedia P3K', 'Lingkungan higienis dan bersih'
    ],
    'Kantin': [
        'Menu cukup bervariasi.', 'Harga terjangkau.', 'Kualitas makanan baik',
        'Area makan nyaman', 'Pelayanan ramah & cepat.'
    ],
    'Keamanan & Parkir': [
        'Sistem keamanan efektif.', 'Petugas ramah & membantu', 'Parkir memadai & aman',
        'Penerangan cukup', 'Tidak ada area rawan.', 'Akses masuk terkontrol',
        'Evakuasi & jalur Darurat jelas'
    ]
}

# -----------------
# FUNGSI UNTUK MEMUAT DATA
# -----------------
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    kolom_penilaian = [col for sublist in kategori_fasilitas.values() for col in sublist]
    for col in kolom_penilaian:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# Memuat data dari file
df = load_data('data_preprocessed.csv')

# -----------------
# SIDEBAR UNTUK FILTER
# -----------------
st.sidebar.header("Filter Responden")
status_list = ['Semua'] + df['Status Anda'].unique().tolist()
status_filter = st.sidebar.selectbox('Status Anda', status_list)

gender_list = ['Semua'] + df['Jenis Kelamin'].unique().tolist()
gender_filter = st.sidebar.selectbox('Jenis Kelamin', gender_list)

age_list = ['Semua'] + df['Usia'].unique().tolist()
age_filter = st.sidebar.selectbox('Usia', age_list)

# Menerapkan filter ke DataFrame
df_filtered = df.copy()
if status_filter != 'Semua':
    df_filtered = df_filtered[df_filtered['Status Anda'] == status_filter]
if gender_filter != 'Semua':
    df_filtered = df_filtered[df_filtered['Jenis Kelamin'] == gender_filter]
if age_filter != 'Semua':
    df_filtered = df_filtered[df_filtered['Usia'] == age_filter]


# -----------------
# TAMPILAN UTAMA DASHBOARD
# -----------------

# --- PERUBAHAN JUDUL & LOGO ---
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
            avg_score = df_filtered[valid_cols].mean(skipna=True).mean(skipna=True)
            avg_scores.append({'Kategori': kategori, 'Rata-rata Skor': avg_score})
    df_scores = pd.DataFrame(avg_scores)

    total_responden = len(df_filtered)
    avg_satisfaction = df_scores['Rata-rata Skor'].mean()

    if not df_scores.empty:
        highest_rated = df_scores.loc[df_scores['Rata-rata Skor'].idxmax()]
        lowest_rated = df_scores.loc[df_scores['Rata-rata Skor'].idxmin()]
    else:
        highest_rated = {'Kategori': 'N/A', 'Rata-rata Skor': 0}
        lowest_rated = {'Kategori': 'N/A', 'Rata-rata Skor': 0}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="👥 Total Responden", value=total_responden)
    with col2:
        st.metric(label="⭐ Rata-rata Kepuasan", value=f"{avg_satisfaction:.2f} / 5")
    with col3:
        st.metric(label="👍 Kategori Tertinggi", value=highest_rated['Kategori'], delta=f"{highest_rated['Rata-rata Skor']:.2f}")
    with col4:
        st.metric(label="👎 Kategori Terendah", value=lowest_rated['Kategori'], delta=f"{lowest_rated['Rata-rata Skor']:.2f}", delta_color="inverse")

    st.markdown("---")

    # --- PENAMBAHAN GRAFIK DONAT UNTUK DEMOGRAFI ---
    st.header("Distribusi Demografi Responden")
    col_demo1, col_demo2, col_demo3 = st.columns(3)

    with col_demo1:
        df_status = df_filtered['Status Anda'].value_counts().reset_index()
        fig_status = px.pie(df_status, names='Status Anda', values='count', title='Distribusi Status', hole=0.4)
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)

    with col_demo2:
        df_gender = df_filtered['Jenis Kelamin'].value_counts().reset_index()
        fig_gender = px.pie(df_gender, names='Jenis Kelamin', values='count', title='Distribusi Jenis Kelamin', hole=0.4)
        fig_gender.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_gender, use_container_width=True)

    with col_demo3:
        df_age = df_filtered['Usia'].value_counts().reset_index()
        fig_age = px.pie(df_age, names='Usia', values='count', title='Distribusi Usia', hole=0.4)
        fig_age.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")

    # --- GRAFIK YANG SUDAH ADA (TETAP DIPERTAHANKAN) ---
    st.header("Ringkasan Skor Kepuasan per Kategori Fasilitas")
    fig_bar = px.bar(
        df_scores.sort_values('Rata-rata Skor', ascending=True),
        x='Rata-rata Skor', y='Kategori', orientation='h',
        title='Rata-rata Skor Kepuasan (Skala 1-5)', text='Rata-rata Skor', range_x=[1, 5]
    )
    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    st.plotly_chart(fig_bar, use_container_width=True)

    st.header("Detail Skor per Pertanyaan")
    kategori_pilihan = st.selectbox("Pilih kategori untuk melihat detail:", list(kategori_fasilitas.keys()))
    if kategori_pilihan:
        detail_cols = kategori_fasilitas[kategori_pilihan]
        valid_detail_cols = [col for col in detail_cols if col in df_filtered.columns]
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