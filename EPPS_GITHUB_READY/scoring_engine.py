"""
scoring_engine.py

Engine scoring utama untuk aplikasi psikotes EPPS
(Edwards Personal Preference Schedule) berbasis Python.

File yang dibaca:
1. item_bank.json
2. responses.json
3. norms_male.csv
4. norms_female.csv

Contoh format responses.json yang disarankan:

{
  "gender": "male",
  "answers": {
    "1": "A",
    "2": "B",
    "3": "A"
  }
}

Catatan:
- Key jawaban boleh string ("1") atau integer (1).
- Gender hanya boleh "male" atau "female".
- Jawaban hanya boleh "A" atau "B".
"""

import json
import csv
from collections import defaultdict


# 15 dimensi EPPS yang dipakai sebagai key skor.
DIMENSIONS = [
    "ach",  # Achievement
    "def",  # Deference
    "ord",  # Order
    "exh",  # Exhibition
    "aut",  # Autonomy
    "aff",  # Affiliation
    "int",  # Intraception
    "suc",  # Succorance
    "dom",  # Dominance
    "aba",  # Abasement
    "nur",  # Nurturance
    "cha",  # Change
    "end",  # Endurance
    "het",  # Heterosexual
    "agg",  # Aggression
]


# Field minimal yang harus ada pada setiap item EPPS.
REQUIRED_ITEM_FIELDS = [
    "id",
    "page",
    "a_text",
    "b_text",
    "need_a",
    "need_b",
    "row_need",
    "column_need",
    "dimension_a",
    "dimension_b",
    "pair_group",
    "consistency_role",
]


def load_json(file_path):
    """
    Membaca file JSON dengan encoding UTF-8.

    Parameter:
        file_path (str): path file JSON.

    Return:
        object Python dari isi JSON.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_item_bank(file_path="item_bank.json"):
    """
    Membaca item_bank.json.
    """
    return load_json(file_path)


def load_responses(file_path="responses.json"):
    """
    Membaca responses.json.

    Format yang disarankan:
    {
      "gender": "male",
      "answers": {
        "1": "A",
        "2": "B"
      }
    }

    Return:
        tuple: (gender, answers)
    """
    data = load_json(file_path)

    if not isinstance(data, dict):
        raise ValueError("responses.json harus berupa object/dictionary JSON.")

    if "gender" not in data:
        raise ValueError("responses.json harus memiliki field 'gender'.")

    if "answers" not in data:
        raise ValueError("responses.json harus memiliki field 'answers'.")

    gender = str(data["gender"]).strip().lower()
    answers = data["answers"]

    return gender, answers


def load_norms(file_path):
    """
    Membaca file norms CSV.

    Format CSV wajib:
    need,raw_score,percentile,category

    Return:
        dict dengan format:
        {
          "ach": {
            0: {"percentile": 1, "category": "Very Low"},
            1: {"percentile": 2, "category": "Very Low"}
          }
        }
    """
    norms = defaultdict(dict)

    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        required_columns = ["need", "raw_score", "percentile", "category"]
        if reader.fieldnames != required_columns:
            raise ValueError(
                f"Kolom {file_path} harus {required_columns}, "
                f"tetapi ditemukan {reader.fieldnames}."
            )

        for row_number, row in enumerate(reader, start=2):
            need = row["need"].strip()
            category = row["category"].strip()

            try:
                raw_score = int(row["raw_score"])
                percentile = int(row["percentile"])
            except ValueError:
                raise ValueError(
                    f"Data numerik tidak valid pada {file_path}, baris {row_number}."
                )

            if need not in DIMENSIONS:
                raise ValueError(
                    f"Need tidak valid pada {file_path}, baris {row_number}: {need}"
                )

            if raw_score < 0:
                raise ValueError(
                    f"raw_score tidak boleh negatif pada {file_path}, baris {row_number}."
                )

            if percentile < 1 or percentile > 99:
                raise ValueError(
                    f"percentile harus 1-99 pada {file_path}, baris {row_number}."
                )

            key = (need, raw_score)
            if raw_score in norms[need]:
                raise ValueError(
                    f"Duplicate norm row pada {file_path}: need={need}, raw_score={raw_score}"
                )

            norms[need][raw_score] = {
                "percentile": percentile,
                "category": category,
            }

    validate_norms(norms, file_path)

    return norms


def validate_item_bank(item_bank):
    """
    Validasi item_bank agar aman dipakai scoring.

    Yang dicek:
    1. item_bank berupa list
    2. total item 225
    3. id lengkap 1 sampai 225
    4. semua field wajib ada
    5. dimension_a dan dimension_b valid
    6. pair_group consistency valid
    """
    if not isinstance(item_bank, list):
        raise ValueError("item_bank.json harus berupa list.")

    if len(item_bank) != 225:
        raise ValueError(f"Total item harus 225, ditemukan {len(item_bank)} item.")

    ids = [item.get("id") for item in item_bank]
    if sorted(ids) != list(range(1, 226)):
        raise ValueError("ID item harus lengkap dan unik dari 1 sampai 225.")

    for item in item_bank:
        item_id = item.get("id")

        for field in REQUIRED_ITEM_FIELDS:
            if field not in item:
                raise ValueError(f"Item {item_id} tidak memiliki field '{field}'.")

        if item["dimension_a"] not in DIMENSIONS:
            raise ValueError(
                f"Item {item_id} memiliki dimension_a tidak valid: {item['dimension_a']}"
            )

        if item["dimension_b"] not in DIMENSIONS:
            raise ValueError(
                f"Item {item_id} memiliki dimension_b tidak valid: {item['dimension_b']}"
            )

        role = item["consistency_role"]
        if role not in [None, "original", "mirror"]:
            raise ValueError(
                f"Item {item_id} memiliki consistency_role tidak valid: {role}"
            )

    validate_pair_groups(item_bank)

    return True


def validate_pair_groups(item_bank):
    """
    Validasi pasangan consistency berdasarkan pair_group.

    Aturan:
    - pair_group non-null harus ada 15 kelompok.
    - setiap pair_group muncul tepat 2 kali.
    - setiap pair_group memiliki 1 original dan 1 mirror.
    """
    pair_groups = defaultdict(list)

    for item in item_bank:
        group = item["pair_group"]
        if group is not None:
            pair_groups[group].append(item)

    if len(pair_groups) != 15:
        raise ValueError(
            f"Jumlah pair_group harus 15, ditemukan {len(pair_groups)}."
        )

    for group, items in pair_groups.items():
        if len(items) != 2:
            raise ValueError(
                f"{group} harus muncul tepat 2 kali, ditemukan {len(items)} kali."
            )

        roles = [item["consistency_role"] for item in items]

        if roles.count("original") != 1 or roles.count("mirror") != 1:
            raise ValueError(
                f"{group} harus memiliki 1 original dan 1 mirror."
            )

    return True


def validate_norms(norms, file_path):
    """
    Validasi isi norms CSV.

    Yang dicek:
    1. Semua 15 dimensi ada.
    2. Setiap dimensi memiliki raw_score 0 sampai 28.
    3. Percentile monotonic atau tidak menurun.
    """
    missing_needs = [need for need in DIMENSIONS if need not in norms]
    if missing_needs:
        raise ValueError(f"{file_path} tidak memiliki need: {missing_needs}")

    for need in DIMENSIONS:
        raw_scores = sorted(norms[need].keys())

        if raw_scores != list(range(0, 29)):
            raise ValueError(
                f"{file_path} need '{need}' harus memiliki raw_score lengkap 0-28."
            )

        percentiles = [norms[need][raw]["percentile"] for raw in raw_scores]

        for i in range(len(percentiles) - 1):
            if percentiles[i] > percentiles[i + 1]:
                raise ValueError(
                    f"Percentile {file_path} need '{need}' tidak monotonic."
                )

    return True


def validate_gender(gender):
    """
    Validasi gender untuk pemilihan norma.
    """
    if gender not in ["male", "female"]:
        raise ValueError("Gender hanya boleh 'male' atau 'female'.")

    return gender


def validate_answers(answers):
    """
    Validasi jawaban peserta.

    Aturan:
    - answers harus dictionary.
    - jumlah jawaban harus 225.
    - id jawaban harus 1 sampai 225.
    - jawaban hanya boleh A atau B.

    Return:
        dict dengan key integer dan value huruf besar.
    """
    if not isinstance(answers, dict):
        raise ValueError("answers harus berupa dictionary.")

    normalized_answers = {}

    for key, value in answers.items():
        try:
            item_id = int(key)
        except (TypeError, ValueError):
            raise ValueError(f"ID jawaban tidak valid: {key}")

        if not isinstance(value, str):
            raise ValueError(f"Jawaban item {item_id} harus berupa string 'A' atau 'B'.")

        answer = value.strip().upper()

        if answer not in ["A", "B"]:
            raise ValueError(
                f"Jawaban item {item_id} tidak valid: {value}. "
                "Jawaban hanya boleh 'A' atau 'B'."
            )

        normalized_answers[item_id] = answer

    missing_ids = [item_id for item_id in range(1, 226) if item_id not in normalized_answers]
    extra_ids = [item_id for item_id in normalized_answers if item_id < 1 or item_id > 225]

    if missing_ids:
        raise ValueError(
            f"Ada jawaban yang belum diisi. ID item hilang: {missing_ids}"
        )

    if extra_ids:
        raise ValueError(
            f"Ada ID jawaban di luar rentang 1-225: {extra_ids}"
        )

    if len(normalized_answers) != 225:
        raise ValueError(f"Jumlah jawaban harus 225, ditemukan {len(normalized_answers)}.")

    return normalized_answers


def calculate_raw_scores(item_bank, answers):
    """
    Menghitung raw score setiap dimensi EPPS.

    Aturan scoring:
    - Jika jawaban A, tambah skor ke dimension_a.
    - Jika jawaban B, tambah skor ke dimension_b.
    - Item dengan consistency_role == "original" tidak dihitung ke raw score.
      Item original hanya dipakai untuk consistency checking.
    """
    raw_scores = {dimension: 0 for dimension in DIMENSIONS}

    for item in item_bank:
        # Item original consistency tidak masuk skor utama.
        if item["consistency_role"] == "original":
            continue

        item_id = item["id"]
        answer = answers[item_id]

        if answer == "A":
            selected_dimension = item["dimension_a"]
        else:
            selected_dimension = item["dimension_b"]

        raw_scores[selected_dimension] += 1

    return raw_scores

def calculate_consistency_score(item_bank, answers):
    """
    Menghitung consistency score berdasarkan pair_group.

    Aturan:
    - Setiap pair_group berisi 2 item:
      1 original dan 1 mirror.
    - Sistem melihat dimensi yang dipilih peserta pada original dan mirror.
    - Jika dimensi yang dipilih berbeda, maka inconsistency bertambah 1.
    - Jika dimensi yang dipilih sama, maka pasangan dianggap konsisten.
    """
    pair_groups = defaultdict(list)

    for item in item_bank:
        group = item["pair_group"]

        if group is not None:
            pair_groups[group].append(item)

    inconsistency = 0

    for group, items in pair_groups.items():
        if len(items) != 2:
            raise ValueError(f"{group} tidak valid karena tidak berisi 2 item.")

        original_item = None
        mirror_item = None

        for item in items:
            if item["consistency_role"] == "original":
                original_item = item
            elif item["consistency_role"] == "mirror":
                mirror_item = item

        if original_item is None or mirror_item is None:
            raise ValueError(
                f"{group} harus memiliki 1 original dan 1 mirror."
            )

        original_answer = answers[original_item["id"]]
        mirror_answer = answers[mirror_item["id"]]

        if original_answer == "A":
            original_selected_dimension = original_item["dimension_a"]
        else:
            original_selected_dimension = original_item["dimension_b"]

        if mirror_answer == "A":
            mirror_selected_dimension = mirror_item["dimension_a"]
        else:
            mirror_selected_dimension = mirror_item["dimension_b"]

        if original_selected_dimension != mirror_selected_dimension:
            inconsistency += 1

    total_pairs = len(pair_groups)
    consistency_score = total_pairs - inconsistency

    return consistency_score

def convert_scores_to_norms(raw_scores, norms):
    """
    Mengubah raw score menjadi percentile dan category berdasarkan norms.

    Return:
        tuple: (percentiles, categories)
    """
    percentiles = {}
    categories = {}

    for dimension, raw_score in raw_scores.items():
        if dimension not in norms:
            raise ValueError(f"Norma untuk dimensi '{dimension}' tidak ditemukan.")

        if raw_score not in norms[dimension]:
            raise ValueError(
                f"Norma untuk dimensi '{dimension}' raw_score {raw_score} tidak ditemukan."
            )

        percentiles[dimension] = norms[dimension][raw_score]["percentile"]
        categories[dimension] = norms[dimension][raw_score]["category"]

    return percentiles, categories


def choose_norms_by_gender(gender, norms_male, norms_female):
    """
    Memilih norma berdasarkan gender peserta.
    """
    if gender == "male":
        return norms_male

    if gender == "female":
        return norms_female

    raise ValueError("Gender hanya boleh 'male' atau 'female'.")


def score_epps(
    item_bank_path="item_bank.json",
    responses_path="responses.json",
    norms_male_path="norms_male.csv",
    norms_female_path="norms_female.csv",
):
    """
    Function utama scoring EPPS.

    Langkah:
    1. Baca item_bank.json
    2. Baca responses.json
    3. Baca norms_male.csv dan norms_female.csv
    4. Validasi semua input
    5. Hitung raw score
    6. Hitung consistency score
    7. Konversi raw score menjadi percentile dan category
    8. Return dictionary final

    Output:
    {
      "raw_scores": {},
      "percentiles": {},
      "categories": {},
      "consistency_score": 0
    }
    """
    item_bank = load_item_bank(item_bank_path)
    gender, answers = load_responses(responses_path)
    norms_male = load_norms(norms_male_path)
    norms_female = load_norms(norms_female_path)

    validate_item_bank(item_bank)
    gender = validate_gender(gender)
    answers = validate_answers(answers)

    selected_norms = choose_norms_by_gender(gender, norms_male, norms_female)

    raw_scores = calculate_raw_scores(item_bank, answers)
    consistency_score = calculate_consistency_score(item_bank, answers)
    percentiles, categories = convert_scores_to_norms(raw_scores, selected_norms)

    return {
        "raw_scores": raw_scores,
        "percentiles": percentiles,
        "categories": categories,
        "consistency_score": consistency_score,
    }


# Contoh penggunaan langsung dari terminal:
# python scoring_engine.py
if __name__ == "__main__":
    try:
        result = score_epps(
            item_bank_path="item_bank.json",
            responses_path="responses.json",
            norms_male_path="norms_male.csv",
            norms_female_path="norms_female.csv",
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as error:
        print("Terjadi error saat scoring EPPS:")
        print(error)
