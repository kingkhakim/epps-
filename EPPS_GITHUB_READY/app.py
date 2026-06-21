"""
app.py

Streamlit UI linier untuk aplikasi psikotes EPPS
(Edwards Personal Preference Schedule).

File ini mengikuti alur proyek yang sudah dibuat sebelumnya:

1. item_bank.json
2. scoring_engine.py
3. interpretation_engine.py
4. norms_male.csv / norms_female.csv
5. results/

Cara menjalankan:

streamlit run app.py

Struktur folder yang disarankan:

EPPS_PROJECT/
│
├── app.py
├── item_bank.json
├── scoring_engine.py
├── interpretation_engine.py
├── norms_male.csv
├── norms_female.csv
└── results/
"""

import json
import csv
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from scoring_engine import score_epps
from interpretation_engine import interpret_epps_result


# ============================================================
# KONFIGURASI DASAR
# ============================================================

APP_TITLE = "EPPS Psychological Test System"

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"

ITEM_BANK_PATH = BASE_DIR / "item_bank.json"

# Prioritas:
# 1. corrected_norms_male.csv jika ada
# 2. norms_male.csv jika corrected file tidak ada
NORMS_MALE_PATH = (
    BASE_DIR / "corrected_norms_male.csv"
    if (BASE_DIR / "corrected_norms_male.csv").exists()
    else BASE_DIR / "norms_male.csv"
)

NORMS_FEMALE_PATH = (
    BASE_DIR / "corrected_norms_female.csv"
    if (BASE_DIR / "corrected_norms_female.csv").exists()
    else BASE_DIR / "norms_female.csv"
)

DIMENSIONS = [
    "ach",
    "def",
    "ord",
    "exh",
    "aut",
    "aff",
    "int",
    "suc",
    "dom",
    "aba",
    "nur",
    "cha",
    "end",
    "het",
    "agg",
]

DIMENSION_NAMES = {
    "ach": "Achievement",
    "def": "Deference",
    "ord": "Order",
    "exh": "Exhibition",
    "aut": "Autonomy",
    "aff": "Affiliation",
    "int": "Intraception",
    "suc": "Succorance",
    "dom": "Dominance",
    "aba": "Abasement",
    "nur": "Nurturance",
    "cha": "Change",
    "end": "Endurance",
    "het": "Heterosexuality",
    "agg": "Aggression",
}


# ============================================================
# HELPER: FILE DAN DATA
# ============================================================

def ensure_results_dir():
    """
    Membuat folder results jika belum ada.
    """
    RESULTS_DIR.mkdir(exist_ok=True)


@st.cache_data
def load_item_bank():
    """
    Membaca item_bank.json.

    Data ini di-cache agar aplikasi tidak membaca file berulang-ulang.
    """
    with open(ITEM_BANK_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def check_required_files():
    """
    Mengecek apakah file wajib tersedia.

    Jika ada file yang hilang, aplikasi akan berhenti dan memberi pesan jelas.
    """
    required_files = [
        ITEM_BANK_PATH,
        BASE_DIR / "scoring_engine.py",
        BASE_DIR / "interpretation_engine.py",
        NORMS_MALE_PATH,
        NORMS_FEMALE_PATH,
    ]

    missing_files = [file for file in required_files if not file.exists()]

    if missing_files:
        st.error("Ada file wajib yang belum ditemukan:")
        for file in missing_files:
            st.write(f"- `{file.name}`")
        st.stop()


def init_session_state():
    """
    Menyiapkan state awal aplikasi.

    Alur dibuat linier:
    1. identity
    2. instruction
    3. test
    4. review
    5. result
    """
    if "step" not in st.session_state:
        st.session_state.step = "identity"

    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    if "participant" not in st.session_state:
        st.session_state.participant = {}

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if "scoring_result" not in st.session_state:
        st.session_state.scoring_result = None

    if "interpretation_result" not in st.session_state:
        st.session_state.interpretation_result = None

    if "result_files" not in st.session_state:
        st.session_state.result_files = {}


def reset_test():
    """
    Menghapus seluruh state pengerjaan dan kembali ke halaman identitas.
    """
    st.session_state.step = "identity"
    st.session_state.current_page = 1
    st.session_state.participant = {}
    st.session_state.answers = {}
    st.session_state.scoring_result = None
    st.session_state.interpretation_result = None
    st.session_state.result_files = {}


def get_items_by_page(item_bank, page):
    """
    Mengambil 15 item pada halaman tertentu.
    """
    return [item for item in item_bank if item["page"] == page]


def count_answered_items():
    """
    Menghitung jumlah item yang sudah dijawab.
    """
    return len(st.session_state.answers)


def page_is_complete(items):
    """
    Mengecek apakah seluruh item pada halaman aktif sudah dijawab.
    """
    for item in items:
        if item["id"] not in st.session_state.answers:
            return False
    return True


def all_answers_complete():
    """
    Mengecek apakah seluruh 225 item sudah dijawab.
    """
    return len(st.session_state.answers) == 225


def build_responses_payload():
    """
    Membuat payload responses.json sesuai kebutuhan scoring_engine.py.
    """
    participant = st.session_state.participant

    return {
        "participant": participant,
        "gender": participant["gender"],
        "answers": {
            str(item_id): answer
            for item_id, answer in sorted(st.session_state.answers.items())
        },
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def make_result_basename():
    """
    Membuat nama file hasil agar rapi dan tidak bentrok.

    Format:
    EPPS_NamaPeserta_YYYYMMDD_HHMMSS
    """
    participant_name = st.session_state.participant.get("name", "participant")
    clean_name = (
        participant_name.strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"EPPS_{clean_name}_{timestamp}"


def save_json_file(data, path):
    """
    Menyimpan dictionary ke JSON UTF-8.
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def save_summary_csv(scoring_result, interpretation_result, path):
    """
    Menyimpan ringkasan hasil ke CSV.
    """
    participant = st.session_state.participant

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "participant_name",
            "age",
            "gender",
            "test_date",
            "need",
            "dimension_name",
            "raw_score",
            "percentile",
            "category",
            "interpretation",
        ])

        for need in DIMENSIONS:
            dimension_data = interpretation_result["dimension_interpretations"][need]

            writer.writerow([
                participant.get("name", ""),
                participant.get("age", ""),
                participant.get("gender", ""),
                participant.get("test_date", ""),
                need,
                DIMENSION_NAMES[need],
                scoring_result["raw_scores"][need],
                scoring_result["percentiles"][need],
                scoring_result["categories"][need],
                dimension_data["interpretation"],
            ])


def run_scoring_and_interpretation():
    """
    Menjalankan proses scoring dan interpretasi.

    Alur:
    1. Simpan responses.json ke folder results.
    2. Jalankan score_epps dari scoring_engine.py.
    3. Jalankan interpret_epps_result dari interpretation_engine.py.
    4. Simpan semua output ke folder results.
    """
    ensure_results_dir()

    base_name = make_result_basename()

    responses_path = RESULTS_DIR / f"{base_name}_responses.json"
    scoring_path = RESULTS_DIR / f"{base_name}_scoring_result.json"
    interpretation_path = RESULTS_DIR / f"{base_name}_interpretation_result.json"
    csv_path = RESULTS_DIR / f"{base_name}_summary.csv"

    responses_payload = build_responses_payload()
    save_json_file(responses_payload, responses_path)

    scoring_result = score_epps(
        item_bank_path=str(ITEM_BANK_PATH),
        responses_path=str(responses_path),
        norms_male_path=str(NORMS_MALE_PATH),
        norms_female_path=str(NORMS_FEMALE_PATH),
    )

    interpretation_result = interpret_epps_result(scoring_result)

    save_json_file(scoring_result, scoring_path)
    save_json_file(interpretation_result, interpretation_path)
    save_summary_csv(scoring_result, interpretation_result, csv_path)

    st.session_state.scoring_result = scoring_result
    st.session_state.interpretation_result = interpretation_result
    st.session_state.result_files = {
        "responses": responses_path,
        "scoring_result": scoring_path,
        "interpretation_result": interpretation_path,
        "summary_csv": csv_path,
    }


# ============================================================
# HELPER: UI
# ============================================================

def render_header():
    """
    Header utama aplikasi.
    """
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("EPPS Psychological Test System")
    st.caption("Aplikasi psikotes EPPS berbasis Python dan Streamlit")


def render_sidebar():
    """
    Sidebar berisi status pengerjaan.
    """
    st.sidebar.header("Status Pengerjaan")

    answered = count_answered_items()
    progress = answered / 225

    st.sidebar.progress(progress)
    st.sidebar.write(f"Item terjawab: **{answered}/225**")

    if st.session_state.step == "identity":
        active_step = "1. Identitas"
    elif st.session_state.step == "instruction":
        active_step = "2. Instruksi"
    elif st.session_state.step == "test":
        active_step = f"3. Tes Halaman {st.session_state.current_page}/15"
    elif st.session_state.step == "review":
        active_step = "4. Review Jawaban"
    else:
        active_step = "5. Hasil"

    st.sidebar.write(f"Tahap aktif: **{active_step}**")

    st.sidebar.divider()

    st.sidebar.write("Alur linier:")
    st.sidebar.write("1. Identitas")
    st.sidebar.write("2. Instruksi")
    st.sidebar.write("3. Tes 15 halaman")
    st.sidebar.write("4. Review")
    st.sidebar.write("5. Hasil")

    st.sidebar.divider()

    if st.sidebar.button("Reset Tes"):
        reset_test()
        st.rerun()


def render_identity_page():
    """
    Halaman 1: input identitas peserta.
    """
    st.subheader("1. Identitas Peserta")

    with st.form("identity_form"):
        name = st.text_input("Nama peserta")
        age = st.number_input("Usia", min_value=18, max_value=100, value=18)
        gender_label = st.selectbox(
            "Jenis kelamin",
            options=["Laki-laki", "Perempuan"],
        )
        education = st.text_input("Pendidikan", placeholder="Contoh: S1 Psikologi")
        test_date = st.date_input("Tanggal tes")

        submitted = st.form_submit_button("Lanjut ke Instruksi")

    if submitted:
        if not name.strip():
            st.warning("Nama peserta wajib diisi.")
            return

        gender = "male" if gender_label == "Laki-laki" else "female"

        st.session_state.participant = {
            "name": name.strip(),
            "age": int(age),
            "gender": gender,
            "gender_label": gender_label,
            "education": education.strip(),
            "test_date": str(test_date),
        }

        st.session_state.step = "instruction"
        st.rerun()


def render_instruction_page():
    """
    Halaman 2: instruksi pengerjaan.
    """
    st.subheader("2. Instruksi Tes")

    st.info(
        "Pada setiap nomor terdapat dua pernyataan, yaitu A dan B. "
        "Pilih satu pernyataan yang paling sesuai atau paling Anda sukai. "
        "Tidak ada jawaban benar atau salah."
    )

    st.write(
        "Tes ini terdiri dari **225 item** yang dibagi menjadi **15 halaman**. "
        "Setiap halaman berisi **15 item**. Anda harus menyelesaikan seluruh item pada "
        "satu halaman sebelum dapat lanjut ke halaman berikutnya."
    )

    st.warning(
        "Kerjakan secara jujur dan spontan. Jangan terlalu lama memikirkan satu item."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Kembali ke Identitas"):
            st.session_state.step = "identity"
            st.rerun()

    with col2:
        if st.button("Mulai Tes"):
            st.session_state.step = "test"
            st.session_state.current_page = 1
            st.rerun()


def render_test_page(item_bank):
    """
    Halaman 3: pengerjaan tes per halaman.

    Desain dibuat linier:
    - Hanya menampilkan 15 item sesuai halaman aktif.
    - Tombol lanjut aktif secara logika hanya jika semua item pada halaman dijawab.
    """
    page = st.session_state.current_page
    items = get_items_by_page(item_bank, page)

    st.subheader(f"3. Tes EPPS - Halaman {page} dari 15")

    st.write(
        "Pilih salah satu pernyataan pada setiap nomor. "
        "Seluruh item pada halaman ini harus dijawab sebelum lanjut."
    )

    st.divider()

    for item in items:
        item_id = item["id"]

        st.markdown(f"**Nomor {item_id}**")

        options = {
            "A": f"A. {item['a_text']}",
            "B": f"B. {item['b_text']}",
        }

        current_answer = st.session_state.answers.get(item_id)
        index = None

        if current_answer == "A":
            index = 0
        elif current_answer == "B":
            index = 1

        selected = st.radio(
            label="Pilih jawaban:",
            options=["A", "B"],
            format_func=lambda option: options[option],
            index=index,
            key=f"item_{item_id}",
            horizontal=False,
        )

        if selected in ["A", "B"]:
            st.session_state.answers[item_id] = selected

        st.divider()

    complete = page_is_complete(items)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if page > 1:
            if st.button("Sebelumnya"):
                st.session_state.current_page -= 1
                st.rerun()

    with col2:
        st.write(f"Progress halaman: **{sum(1 for item in items if item['id'] in st.session_state.answers)}/15**")

    with col3:
        if page < 15:
            if st.button("Lanjut"):
                if not complete:
                    st.warning("Lengkapi seluruh 15 item pada halaman ini terlebih dahulu.")
                else:
                    st.session_state.current_page += 1
                    st.rerun()
        else:
            if st.button("Selesai dan Review"):
                if not complete:
                    st.warning("Lengkapi seluruh 15 item pada halaman ini terlebih dahulu.")
                else:
                    st.session_state.step = "review"
                    st.rerun()


def render_review_page(item_bank):
    """
    Halaman 4: review sebelum scoring.

    Peserta dapat melihat apakah semua item sudah dijawab.
    """
    st.subheader("4. Review Jawaban")

    answered = count_answered_items()
    missing_items = [
        item_id
        for item_id in range(1, 226)
        if item_id not in st.session_state.answers
    ]

    st.write(f"Jumlah item terjawab: **{answered}/225**")

    if missing_items:
        st.error("Masih ada item yang belum dijawab.")
        st.write("Item belum dijawab:")
        st.write(missing_items)

        first_missing = missing_items[0]
        target_page = ((first_missing - 1) // 15) + 1

        if st.button(f"Kembali ke Halaman {target_page}"):
            st.session_state.current_page = target_page
            st.session_state.step = "test"
            st.rerun()

        return

    st.success("Semua item sudah dijawab. Data siap discoring.")

    with st.expander("Lihat ringkasan jawaban"):
        answers_df = pd.DataFrame(
            [
                {"id": item_id, "answer": answer}
                for item_id, answer in sorted(st.session_state.answers.items())
            ]
        )
        st.dataframe(answers_df, use_container_width=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Kembali ke Tes"):
            st.session_state.current_page = 15
            st.session_state.step = "test"
            st.rerun()

    with col2:
        if st.button("Hitung Hasil EPPS"):
            try:
                run_scoring_and_interpretation()
                st.session_state.step = "result"
                st.rerun()
            except Exception as error:
                st.error("Terjadi error saat scoring.")
                st.code(str(error))


def build_result_dataframe(scoring_result):
    """
    Membuat DataFrame hasil agar mudah ditampilkan di Streamlit.
    """
    rows = []

    for need in DIMENSIONS:
        rows.append({
            "Need": need,
            "Dimension": DIMENSION_NAMES[need],
            "Raw Score": scoring_result["raw_scores"][need],
            "Percentile": scoring_result["percentiles"][need],
            "Category": scoring_result["categories"][need],
        })

    return pd.DataFrame(rows)


def render_score_chart(result_df):
    """
    Membuat grafik raw score sederhana.

    Catatan:
    Tidak menggunakan warna khusus agar tetap sederhana.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(result_df["Need"], result_df["Raw Score"])
    ax.set_title("Raw Score EPPS")
    ax.set_xlabel("Need")
    ax.set_ylabel("Raw Score")
    ax.set_ylim(0, max(result_df["Raw Score"].max() + 2, 10))

    st.pyplot(fig)


def render_download_button(label, path, mime_type):
    """
    Membuat tombol download untuk file hasil.
    """
    with open(path, "rb") as file:
        st.download_button(
            label=label,
            data=file,
            file_name=path.name,
            mime=mime_type,
        )


def render_result_page():
    """
    Halaman 5: hasil scoring dan interpretasi.
    """
    st.subheader("5. Hasil EPPS")

    scoring_result = st.session_state.scoring_result
    interpretation_result = st.session_state.interpretation_result

    if scoring_result is None or interpretation_result is None:
        st.error("Hasil belum tersedia. Silakan lakukan scoring dari halaman Review.")
        if st.button("Kembali ke Review"):
            st.session_state.step = "review"
            st.rerun()
        return

    participant = st.session_state.participant

    st.markdown("### Identitas Peserta")
    col1, col2, col3 = st.columns(3)
    col1.write(f"Nama: **{participant.get('name', '')}**")
    col2.write(f"Usia: **{participant.get('age', '')}**")
    col3.write(f"Jenis Kelamin: **{participant.get('gender_label', '')}**")

    st.divider()

    consistency = interpretation_result["validity"]

    st.markdown("### Consistency")
    st.metric(
        label="Consistency Score",
        value=f"{consistency['score']} / 15",
        help="Skor minimal yang disarankan biasanya 10.",
    )

    if consistency["status"] == "Valid":
        st.success(consistency["interpretation"])
    else:
        st.warning(consistency["interpretation"])

    st.write(consistency["recommendation"])

    st.divider()

    result_df = build_result_dataframe(scoring_result)

    st.markdown("### Tabel Skor")
    st.dataframe(result_df, use_container_width=True)

    st.markdown("### Grafik Raw Score")
    render_score_chart(result_df)

    st.divider()

    st.markdown("### Ringkasan Interpretasi")
    st.text(interpretation_result["short_report"])

    with st.expander("Interpretasi per Dimensi"):
        for need in DIMENSIONS:
            data = interpretation_result["dimension_interpretations"][need]

            st.markdown(
                f"#### {need.upper()} - {data['name']} "
                f"({data['category']}, Percentile {data['percentile']})"
            )

            st.write(data["definition"])
            st.write(data["interpretation"])

    st.divider()

    st.markdown("### Download Hasil")

    files = st.session_state.result_files

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_download_button(
            "Download Responses JSON",
            files["responses"],
            "application/json",
        )

    with col2:
        render_download_button(
            "Download Scoring JSON",
            files["scoring_result"],
            "application/json",
        )

    with col3:
        render_download_button(
            "Download Interpretation JSON",
            files["interpretation_result"],
            "application/json",
        )

    with col4:
        render_download_button(
            "Download Summary CSV",
            files["summary_csv"],
            "text/csv",
        )


# ============================================================
# MAIN APP
# ============================================================

def main():
    """
    Function utama aplikasi.
    """
    render_header()
    check_required_files()
    init_session_state()
    render_sidebar()

    item_bank = load_item_bank()

    if st.session_state.step == "identity":
        render_identity_page()

    elif st.session_state.step == "instruction":
        render_instruction_page()

    elif st.session_state.step == "test":
        render_test_page(item_bank)

    elif st.session_state.step == "review":
        render_review_page(item_bank)

    elif st.session_state.step == "result":
        render_result_page()

    else:
        st.error("State aplikasi tidak dikenal. Klik Reset Tes.")
        if st.button("Reset"):
            reset_test()
            st.rerun()


if __name__ == "__main__":
    main()
