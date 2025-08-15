
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------
# PENGATURAN HALAMAN
# -----------------
st.set_page_config(
    page_title="Dashboard Kepuasan Fasilitas Kampus",
    page_icon="🎓",
    layout="wide"
)

# -----------------
# DATA & KONFIGURASI
# -----------------
# Mendefinisikan kolom untuk setiap kategori fasilitas
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
# FUNGSI UNTUK MEMUAT DAN MEMBERSIHKAN DATA
# -----------------
@st.cache_data
def load_data(file_path):
    # Encoding fallback agar tahan file dengan BOM/variasi encoding
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        df = pd.read_csv(file_path)  # biarkan error terlihat jika tetap gagal

    # Bersihkan nama kolom
    df.columns = df.columns.astype(str).str.replace("\ufeff", "", regex=False).str.strip()

    # --- PERBAIKAN DIMULAI DI SINI ---
    # Mengambil semua kolom penilaian dari semua kategori menjadi satu daftar
    kolom_penilaian = [col for sublist in kategori_fasilitas.values() for col in sublist]

    # Loop melalui setiap kolom penilaian
    for col in kolom_penilaian:
        # Jika kolom ada di dataframe, paksa menjadi numerik.
        # Nilai yang tidak bisa diubah (seperti teks) akan menjadi NaN (kosong).
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # --- PERBAIKAN SELESAI ---

    return df

# Memuat data dari file
df = load_data('data_preprocessed.csv')

# -----------------
# SIDEBAR UNTUK FILTER
# -----------------
st.sidebar.header("Filter Responden")

# Helper aman untuk membangun opsi filter
def build_options(df, col_name):
    if col_name in df.columns:
        opts = ['Semua'] + sorted([str(x) for x in df[col_name].dropna().unique().tolist()])
    else:
        opts = ['Semua']
    return opts

# Filter berdasarkan Status
status_list = build_options(df, 'Status Anda')
status_filter = st.sidebar.selectbox('Status Anda', status_list)

# Filter berdasarkan Jenis Kelamin
gender_list = ['Semua', 'laki-laki', 'perempuan']
gender_filter = st.sidebar.selectbox('Jenis Kelamin', gender_list)

# Filter berdasarkan Usia
age_list = build_options(df, 'Usia')
age_filter = st.sidebar.selectbox('Usia', age_list)

# Menerapkan filter ke DataFrame (cek eksistensi kolom sebelum filter)
df_filtered = df.copy()
if status_filter != 'Semua' and 'Status Anda' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Status Anda'] == status_filter]
if gender_filter != 'Semua' and 'Jenis Kelamin' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Jenis Kelamin'] == gender_filter]
if age_filter != 'Semua' and 'Usia' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Usia'] == age_filter]

# -----------------
# TAMPILAN UTAMA DASHBOARD
# -----------------
st.title("🎓 Dashboard Analisis Kepuasan Fasilitas Kampus")
st.markdown("Gunakan filter di sebelah kiri untuk menganalisis data kepuasan berdasarkan demografi responden.")

st.metric(label="Jumlah Responden Sesuai Filter", value=len(df_filtered))

if df_filtered.empty:
    st.warning("Tidak ada data yang cocok dengan filter yang Anda pilih.")
else:
    # -----------------
    # VISUALISASI UTAMA: RATA-RATA KATEGORI
    # -----------------
    st.header("Ringkasan Skor Kepuasan per Kategori Fasilitas")

    avg_scores = []
    for kategori, kolom in kategori_fasilitas.items():
        valid_cols = [col for col in kolom if col in df_filtered.columns]
        if valid_cols:
            # .mean().mean() sekarang akan berjalan lancar karena nilai non-numerik sudah menjadi NaN
            avg_score = df_filtered[valid_cols].mean().mean()
            avg_scores.append({'Kategori': kategori, 'Rata-rata Skor': avg_score})
        else:
            # Jika tidak ada kolom valid untuk kategori tersebut, simpan NaN agar tidak error saat plotting
            avg_scores.append({'Kategori': kategori, 'Rata-rata Skor': float('nan')})

    df_scores = pd.DataFrame(avg_scores)

    fig_bar = px.bar(
        df_scores.sort_values('Rata-rata Skor', ascending=True),
        x='Rata-rata Skor',
        y='Kategori',
        orientation='h',
        title='Rata-rata Skor Kepuasan (Skala 1-5)',
        text='Rata-rata Skor',
        range_x=[1, 5]
    )
    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_bar.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig_bar, use_container_width=True)

    # -----------------
    # TAMPILAN DETAIL PER KATEGORI
    # -----------------
    st.header("Detail Skor per Pertanyaan")

    kategori_pilihan = st.selectbox("Pilih kategori untuk melihat detail:", list(kategori_fasilitas.keys()))

    if kategori_pilihan:
        detail_cols = kategori_fasilitas[kategori_pilihan]
        # Pastikan hanya menghitung kolom yang valid
        valid_detail_cols = [col for col in detail_cols if col in df_filtered.columns]

        if len(valid_detail_cols) > 0:
            df_detail = df_filtered[valid_detail_cols].mean().reset_index()
            df_detail.columns = ['Pertanyaan', 'Rata-rata Skor']

            fig_detail = px.bar(
                df_detail.sort_values('Rata-rata Skor', ascending=False),
                x='Rata-rata Skor',
                y='Pertanyaan',
                orientation='h',
                title=f'Detail Skor untuk Kategori: {kategori_pilihan}',
                text='Rata-rata Skor',
                range_x=[1, 5]
            )
            fig_detail.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_detail.update_layout(
                yaxis={'title': ''},
                height=400
            )
            st.plotly_chart(fig_detail, use_container_width=True)
        else:
            # Tidak menambahkan teks baru agar "text lainnya" tidak berubah; cukup skip plot jika tidak ada kolom valid
            pass

st.sidebar.markdown("---")
st.sidebar.info("Dashboard ini dibuat menggunakan data survei kepuasan fasilitas kampus.")
