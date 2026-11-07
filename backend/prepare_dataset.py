
import requests
import pandas as pd
import zipfile
import io
from pathlib import Path

# Đường dẫn thư mục dataset ở thư mục gốc
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "dataset"
DATA_DIR.mkdir(exist_ok=True)

print("=== PHISHGUARD AI - DATA COLLECTION ===")

# --------------------------------
# 1. Thu thập URL phishing
# --------------------------------

print("\n[1] Dang tai URL phishing...")

phishing_source = "https://openphish.com/feed.txt"

response = requests.get(
    phishing_source,
    timeout=30
)
response.raise_for_status()

phishing_urls = list(dict.fromkeys(
    line.strip()
    for line in response.text.splitlines()
    if line.strip().startswith(("http://", "https://"))
))

print("So URL phishing:", len(phishing_urls))

# --------------------------------
# 2. Thu thập tên miền Tranco
# --------------------------------

print("\n[2] Dang tai danh sach Tranco...")

tranco_source = "https://tranco-list.eu/top-1m.csv.zip"

response = requests.get(
    tranco_source,
    timeout=60
)
response.raise_for_status()

with zipfile.ZipFile(io.BytesIO(response.content)) as archive:

    csv_file = next(
        name for name in archive.namelist()
        if name.endswith(".csv")
    )

    with archive.open(csv_file) as file:
        tranco_df = pd.read_csv(
            file,
            header=None,
            names=["rank", "domain"]
        )

benign_urls = [
    "https://" + domain
    for domain in tranco_df["domain"].dropna()
    if isinstance(domain, str)
]

# --------------------------------
# 3. Cân bằng dữ liệu
# --------------------------------

print("\n[3] Dang xu ly du lieu...")

# Loại bỏ URL trùng lặp
phishing_urls = list(dict.fromkeys(phishing_urls))
benign_urls = list(dict.fromkeys(benign_urls))

# Giới hạn mỗi lớp tối đa 300 URL
number = min(
    300,
    len(phishing_urls),
    len(benign_urls)
)

if number < 50:
    raise ValueError(
        "Du lieu qua it. Hay kiem tra lai nguon tai du lieu."
    )

# Lấy mẫu dữ liệu
phishing_urls = phishing_urls[:number]
benign_urls = benign_urls[:number]

# Tạo DataFrame
phishing_df = pd.DataFrame({
    "url": phishing_urls,
    "label": 1,
    "source": "OpenPhish"
})

benign_df = pd.DataFrame({
    "url": benign_urls[:number],
    "label": 0,
    "source": "Tranco"
})

dataset = pd.concat(
    [phishing_df, benign_df],
    ignore_index=True
)

dataset = dataset.drop_duplicates(
    subset=["url"]
)

dataset = dataset.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# --------------------------------
# 4. Lưu dữ liệu
# --------------------------------

output_file = DATA_DIR / "url_dataset.csv"

dataset.to_csv(
    output_file,
    index=False,
    encoding="utf-8"
)

print("\n=== HOAN THANH ===")
print("Tong so URL:", len(dataset))
print("\nThong ke nhan:")
print(dataset["label"].value_counts())
print("\nFile da luu:", output_file)
