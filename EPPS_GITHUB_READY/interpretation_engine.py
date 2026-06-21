"""
interpretation_engine.py

Engine interpretasi untuk sistem psikotes EPPS
(Edwards Personal Preference Schedule) berbasis Python.

Tujuan:
- Mengubah output scoring_engine.py menjadi interpretasi deskriptif.
- Mudah diintegrasikan ke Streamlit.
- Tanpa class/OOP.
- Tanpa framework.
- Aman UTF-8.

Input utama yang diharapkan:
{
  "raw_scores": {"ach": 10, "def": 7, ...},
  "percentiles": {"ach": 55, "def": 21, ...},
  "categories": {"ach": "Average", "def": "Low", ...},
  "consistency_score": 13
}

Output utama:
{
  "validity": {},
  "summary": {},
  "dimension_interpretations": {},
  "short_report": "..."
}
"""

import json


# 15 dimensi EPPS.
DIMENSIONS = [
    "ach", "def", "ord", "exh", "aut",
    "aff", "int", "suc", "dom", "aba",
    "nur", "cha", "end", "het", "agg",
]


# Nama panjang dimensi.
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


# Label Indonesia untuk laporan.
DIMENSION_LABELS_ID = {
    "ach": "Kebutuhan Berprestasi",
    "def": "Kebutuhan Mengikuti Arahan",
    "ord": "Kebutuhan Keteraturan",
    "exh": "Kebutuhan Menampilkan Diri",
    "aut": "Kebutuhan Kemandirian",
    "aff": "Kebutuhan Berafiliasi",
    "int": "Kebutuhan Memahami Perasaan Orang Lain",
    "suc": "Kebutuhan Mendapat Dukungan",
    "dom": "Kebutuhan Memimpin",
    "aba": "Kebutuhan Merendahkan Diri",
    "nur": "Kebutuhan Merawat dan Menolong",
    "cha": "Kebutuhan Perubahan",
    "end": "Kebutuhan Ketekunan",
    "het": "Kebutuhan Relasi dengan Lawan Jenis",
    "agg": "Kebutuhan Agresi",
}


# Definisi ringkas setiap dimensi.
DIMENSION_DEFINITIONS = {
    "ach": "dorongan untuk mencapai hasil terbaik, menyelesaikan tugas sulit, dan menunjukkan prestasi",
    "def": "kecenderungan mengikuti arahan, menghormati figur otoritas, dan menyesuaikan diri dengan aturan",
    "ord": "kebutuhan terhadap keteraturan, kerapian, perencanaan, dan sistem kerja yang terstruktur",
    "exh": "dorongan untuk tampil, menarik perhatian, bercerita, atau menunjukkan diri di hadapan orang lain",
    "aut": "kebutuhan untuk mandiri, bebas menentukan pilihan, dan tidak terlalu bergantung pada orang lain",
    "aff": "kebutuhan untuk menjalin hubungan sosial, berteman, dan berada dalam kelompok yang hangat",
    "int": "kecenderungan memahami perasaan, motif, dan perilaku diri sendiri maupun orang lain",
    "suc": "kebutuhan untuk menerima bantuan, dukungan, perhatian, simpati, atau afeksi dari orang lain",
    "dom": "dorongan untuk memimpin, mengarahkan, memengaruhi, dan mengambil kendali dalam situasi sosial",
    "aba": "kecenderungan merasa bersalah, mengalah, menerima kritik, atau menilai diri secara rendah",
    "nur": "kebutuhan untuk menolong, merawat, memberi dukungan, dan bersikap simpatik kepada orang lain",
    "cha": "kebutuhan terhadap variasi, pengalaman baru, perubahan, dan stimulasi dari lingkungan",
    "end": "kecenderungan untuk tekun, bertahan, menyelesaikan tugas, dan bekerja sampai tuntas",
    "het": "kebutuhan untuk berinteraksi, tertarik, atau terlibat dalam aktivitas sosial dengan lawan jenis",
    "agg": "dorongan untuk mengkritik, menentang, menyerang pendapat, atau mengekspresikan kemarahan",
}


# Makna umum kategori normatif.
CATEGORY_MEANINGS = {
    "Very Low": {
        "level_id": "sangat rendah",
        "description": "Kecenderungan pada dimensi ini tampak sangat rendah dibandingkan norma.",
    },
    "Low": {
        "level_id": "rendah",
        "description": "Kecenderungan pada dimensi ini relatif rendah dibandingkan norma.",
    },
    "Average": {
        "level_id": "rata-rata",
        "description": "Kecenderungan pada dimensi ini berada pada taraf wajar atau umum.",
    },
    "High": {
        "level_id": "tinggi",
        "description": "Kecenderungan pada dimensi ini relatif menonjol dibandingkan norma.",
    },
    "Very High": {
        "level_id": "sangat tinggi",
        "description": "Kecenderungan pada dimensi ini sangat menonjol dibandingkan norma.",
    },
}


# Fokus interpretasi untuk skor tinggi.
HIGH_FOCUS = {
    "ach": "kuat untuk berhasil, unggul, dan menyelesaikan tugas menantang",
    "def": "kuat untuk mengikuti arahan, aturan, atau figur yang dihormati",
    "ord": "kuat untuk menjaga kerapian, struktur, dan perencanaan",
    "exh": "kuat untuk tampil dan memperoleh perhatian sosial",
    "aut": "kuat untuk mandiri dan menentukan cara sendiri",
    "aff": "kuat untuk menjalin relasi sosial dan kebersamaan",
    "int": "kuat untuk memahami emosi, motif, dan dinamika psikologis orang lain",
    "suc": "kuat untuk memperoleh dukungan, perhatian, atau simpati",
    "dom": "kuat untuk memimpin, mengarahkan, dan memengaruhi orang lain",
    "aba": "kuat untuk mengalah, merasa bersalah, atau merendahkan diri",
    "nur": "kuat untuk membantu, merawat, dan memberi dukungan kepada orang lain",
    "cha": "kuat untuk mencari variasi, pengalaman baru, dan perubahan",
    "end": "kuat untuk tekun, bertahan, dan menyelesaikan tugas sampai tuntas",
    "het": "kuat dalam perhatian terhadap interaksi atau relasi dengan lawan jenis",
    "agg": "kuat untuk menentang, mengkritik, atau mengekspresikan kemarahan",
}


# Fokus interpretasi untuk skor rendah.
LOW_FOCUS = {
    "ach": "kurang menekankan pencapaian, kompetisi, atau target menantang",
    "def": "kurang bergantung pada arahan, aturan, atau figur otoritas",
    "ord": "kurang menekankan kerapian, struktur, atau perencanaan rinci",
    "exh": "kurang terdorong untuk tampil atau menjadi pusat perhatian",
    "aut": "kurang menonjolkan kebebasan pribadi atau kemandirian ekstrem",
    "aff": "kurang terdorong mencari kebersamaan atau kedekatan sosial intensif",
    "int": "kurang terdorong menganalisis emosi, motif, atau perilaku orang lain",
    "suc": "kurang menunjukkan kebutuhan meminta bantuan, simpati, atau perhatian",
    "dom": "kurang terdorong memimpin, mengatur, atau memengaruhi orang lain",
    "aba": "kurang mudah menyalahkan diri, mengalah, atau merasa inferior",
    "nur": "kurang menonjolkan peran merawat, membantu, atau melindungi orang lain",
    "cha": "kurang terdorong mencari perubahan, variasi, atau pengalaman baru",
    "end": "kurang menekankan ketekunan atau penyelesaian tugas jangka panjang",
    "het": "kurang menonjolkan perhatian terhadap interaksi atau relasi dengan lawan jenis",
    "agg": "kurang terdorong untuk mengkritik, menentang, atau berkonfrontasi",
}


VALID_CATEGORIES = ["Very Low", "Low", "Average", "High", "Very High"]


def load_json(file_path):
    """
    Membaca file JSON dengan encoding UTF-8.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, file_path):
    """
    Menyimpan dictionary ke file JSON UTF-8.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def validate_scoring_result(scoring_result):
    """
    Validasi dictionary hasil scoring_engine.py.
    """
    if not isinstance(scoring_result, dict):
        raise ValueError("scoring_result harus berupa dictionary.")

    required_fields = ["raw_scores", "percentiles", "categories", "consistency_score"]
    for field in required_fields:
        if field not in scoring_result:
            raise ValueError(f"scoring_result tidak memiliki field '{field}'.")

    raw_scores = scoring_result["raw_scores"]
    percentiles = scoring_result["percentiles"]
    categories = scoring_result["categories"]

    for field_name, value in [
        ("raw_scores", raw_scores),
        ("percentiles", percentiles),
        ("categories", categories),
    ]:
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} harus berupa dictionary.")

        missing = [dimension for dimension in DIMENSIONS if dimension not in value]
        if missing:
            raise ValueError(f"{field_name} tidak memiliki dimensi: {missing}")

    for dimension in DIMENSIONS:
        raw_score = raw_scores[dimension]
        percentile = percentiles[dimension]
        category = categories[dimension]

        if not isinstance(raw_score, int):
            raise ValueError(f"raw_scores['{dimension}'] harus integer.")

        if not isinstance(percentile, int):
            raise ValueError(f"percentiles['{dimension}'] harus integer.")

        if percentile < 1 or percentile > 99:
            raise ValueError(f"percentiles['{dimension}'] harus berada pada rentang 1-99.")

        if category not in VALID_CATEGORIES:
            raise ValueError(f"categories['{dimension}'] tidak valid: {category}")

    consistency_score = scoring_result["consistency_score"]

    if not isinstance(consistency_score, int):
        raise ValueError("consistency_score harus integer.")

    if consistency_score < 0 or consistency_score > 15:
        raise ValueError("consistency_score harus berada pada rentang 0-15.")

    return True


def interpret_consistency(consistency_score):
    """
    Membuat interpretasi consistency score.

    Dalam praktik EPPS, skor konsistensi di bawah 10 biasanya dianggap meragukan.
    """
    if consistency_score >= 10:
        return {
            "score": consistency_score,
            "max_score": 15,
            "status": "Valid",
            "is_interpretable": True,
            "interpretation": (
                "Skor konsistensi berada pada batas yang dapat diterima. "
                "Hasil dapat dilanjutkan untuk interpretasi dengan tetap memperhatikan konteks pemeriksaan."
            ),
            "recommendation": (
                "Interpretasi profil dapat dilakukan. Tetap gunakan data observasi, wawancara, "
                "dan konteks pemeriksaan sebagai pendukung."
            ),
        }

    return {
        "score": consistency_score,
        "max_score": 15,
        "status": "Questionable",
        "is_interpretable": False,
        "interpretation": (
            "Skor konsistensi berada di bawah batas yang disarankan. "
            "Pola jawaban menunjukkan inkonsistensi sehingga hasil perlu ditafsirkan dengan sangat hati-hati."
        ),
        "recommendation": (
            "Disarankan untuk tidak menjadikan hasil sebagai dasar interpretasi utama. "
            "Pertimbangkan pengulangan tes atau klarifikasi melalui wawancara."
        ),
    }


def build_dimension_sentence(dimension, category):
    """
    Membuat kalimat interpretasi ringkas untuk satu dimensi.
    """
    level_id = CATEGORY_MEANINGS[category]["level_id"]

    if category in ["High", "Very High"]:
        focus = HIGH_FOCUS[dimension]
        return f"Kecenderungan {DIMENSION_NAMES[dimension]} berada pada taraf {level_id}; individu tampak {focus}."

    if category in ["Low", "Very Low"]:
        focus = LOW_FOCUS[dimension]
        return f"Kecenderungan {DIMENSION_NAMES[dimension]} berada pada taraf {level_id}; individu tampak {focus}."

    return (
        f"Kecenderungan {DIMENSION_NAMES[dimension]} berada pada taraf rata-rata; "
        f"individu menunjukkan {DIMENSION_DEFINITIONS[dimension]} secara cukup proporsional."
    )


def interpret_dimension(dimension, raw_score, percentile, category):
    """
    Membuat interpretasi satu dimensi EPPS.
    """
    return {
        "dimension": dimension,
        "name": DIMENSION_NAMES[dimension],
        "label_id": DIMENSION_LABELS_ID[dimension],
        "raw_score": raw_score,
        "percentile": percentile,
        "category": category,
        "definition": DIMENSION_DEFINITIONS[dimension],
        "category_meaning": CATEGORY_MEANINGS[category]["description"],
        "interpretation": build_dimension_sentence(dimension, category),
    }


def get_profile_groups(categories):
    """
    Mengelompokkan dimensi menjadi tinggi, rata-rata, dan rendah.
    """
    high_needs = []
    average_needs = []
    low_needs = []

    for dimension in DIMENSIONS:
        category = categories[dimension]

        if category in ["High", "Very High"]:
            high_needs.append(dimension)
        elif category in ["Low", "Very Low"]:
            low_needs.append(dimension)
        else:
            average_needs.append(dimension)

    return high_needs, average_needs, low_needs


def build_profile_summary(scoring_result):
    """
    Membuat ringkasan profil berdasarkan percentile dan category.
    """
    categories = scoring_result["categories"]
    percentiles = scoring_result["percentiles"]

    high_needs, average_needs, low_needs = get_profile_groups(categories)

    high_needs_sorted = sorted(
        high_needs,
        key=lambda dimension: percentiles[dimension],
        reverse=True,
    )

    low_needs_sorted = sorted(
        low_needs,
        key=lambda dimension: percentiles[dimension],
    )

    top_3 = high_needs_sorted[:3]
    bottom_3 = low_needs_sorted[:3]

    if high_needs_sorted:
        dominant_text = "Kebutuhan yang menonjol: " + ", ".join(
            f"{DIMENSION_NAMES[dim]} ({percentiles[dim]})" for dim in high_needs_sorted
        ) + "."
    else:
        dominant_text = "Tidak ada dimensi yang masuk kategori High atau Very High."

    if low_needs_sorted:
        low_text = "Kebutuhan yang relatif rendah: " + ", ".join(
            f"{DIMENSION_NAMES[dim]} ({percentiles[dim]})" for dim in low_needs_sorted
        ) + "."
    else:
        low_text = "Tidak ada dimensi yang masuk kategori Low atau Very Low."

    return {
        "high_needs": high_needs_sorted,
        "average_needs": average_needs,
        "low_needs": low_needs_sorted,
        "top_3_needs": top_3,
        "bottom_3_needs": bottom_3,
        "dominant_text": dominant_text,
        "low_text": low_text,
    }


def build_short_report_text(interpretation_result):
    """
    Membuat teks laporan singkat untuk Streamlit/PDF.
    """
    validity = interpretation_result["validity"]
    summary = interpretation_result["summary"]

    lines = []
    lines.append("INTERPRETASI SINGKAT EPPS")
    lines.append("")
    lines.append(f"Consistency Score: {validity['score']}/{validity['max_score']} ({validity['status']})")
    lines.append(validity["interpretation"])
    lines.append("")
    lines.append(summary["dominant_text"])
    lines.append(summary["low_text"])
    lines.append("")
    lines.append(
        "Catatan: Interpretasi ini bersifat deskriptif, bukan diagnosis. "
        "Hasil perlu dipadukan dengan observasi, wawancara, dan konteks pemeriksaan."
    )

    return "\n".join(lines)


def interpret_epps_result(scoring_result):
    """
    Function utama untuk membuat interpretasi EPPS.

    Parameter:
        scoring_result (dict): output dari scoring_engine.py

    Return:
        dict interpretasi lengkap.
    """
    validate_scoring_result(scoring_result)

    raw_scores = scoring_result["raw_scores"]
    percentiles = scoring_result["percentiles"]
    categories = scoring_result["categories"]
    consistency_score = scoring_result["consistency_score"]

    dimension_interpretations = {}

    for dimension in DIMENSIONS:
        dimension_interpretations[dimension] = interpret_dimension(
            dimension=dimension,
            raw_score=raw_scores[dimension],
            percentile=percentiles[dimension],
            category=categories[dimension],
        )

    result = {
        "validity": interpret_consistency(consistency_score),
        "summary": build_profile_summary(scoring_result),
        "dimension_interpretations": dimension_interpretations,
    }

    result["short_report"] = build_short_report_text(result)

    return result


def interpret_from_file(scoring_result_path, output_path=None):
    """
    Membaca hasil scoring dari file JSON, lalu membuat interpretasi.

    Parameter:
        scoring_result_path (str): path file JSON hasil scoring.
        output_path (str | None): jika diisi, hasil interpretasi akan disimpan.

    Return:
        dict interpretasi lengkap.
    """
    scoring_result = load_json(scoring_result_path)
    interpretation_result = interpret_epps_result(scoring_result)

    if output_path is not None:
        save_json(interpretation_result, output_path)

    return interpretation_result


# Contoh penggunaan terminal:
# python interpretation_engine.py
if __name__ == "__main__":
    try:
        result = interpret_from_file(
            scoring_result_path="scoring_result.json",
            output_path="interpretation_result.json",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as error:
        print("Terjadi error saat membuat interpretasi EPPS:")
        print(error)
