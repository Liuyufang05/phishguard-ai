import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "dataset"
PHISHING_FEED_URL = "https://openphish.com/feed.txt"
TRANCO_ARCHIVE_URL = "https://tranco-list.eu/top-1m.csv.zip"
MAX_PER_CLASS = 300
MIN_PER_CLASS = 50


def build_dataset(phishing_urls, benign_urls, collected_at=None):
    phishing_urls = list(dict.fromkeys(
        str(url).strip()
        for url in phishing_urls
        if str(url).strip().startswith(("http://", "https://"))
    ))
    benign_urls = list(dict.fromkeys(
        str(url).strip()
        for url in benign_urls
        if str(url).strip()
    ))

    sample_size = min(
        MAX_PER_CLASS,
        len(phishing_urls),
        len(benign_urls),
    )
    if sample_size < MIN_PER_CLASS:
        raise ValueError(
            "Du lieu qua it. Can toi thieu 50 URL cho moi nhan."
        )

    collected_at = collected_at or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )
    phishing_df = pd.DataFrame({
        "url": phishing_urls[:sample_size],
        "label": 1,
        "source": "OpenPhish",
        "collected_at": collected_at,
    })
    benign_df = pd.DataFrame({
        "url": benign_urls[:sample_size],
        "label": 0,
        "source": "Tranco",
        "collected_at": collected_at,
    })
    dataset = pd.concat([phishing_df, benign_df], ignore_index=True)

    conflicting_urls = dataset.groupby("url")["label"].nunique().gt(1)
    if conflicting_urls.any():
        raise ValueError(
            "Nguon du lieu gan nhan mau thuan cho cung mot URL."
        )

    return (
        dataset.drop_duplicates(subset=["url"])
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )


def main():
    print("=== PHISHGUARD AI - DATA COLLECTION ===")
    print("\n[1] Dang tai URL phishing...")
    phishing_response = requests.get(PHISHING_FEED_URL, timeout=30)
    phishing_response.raise_for_status()
    phishing_urls = [
        line.strip()
        for line in phishing_response.text.splitlines()
        if line.strip().startswith(("http://", "https://"))
    ]
    print("So URL phishing:", len(phishing_urls))

    print("\n[2] Dang tai danh sach Tranco...")
    tranco_response = requests.get(TRANCO_ARCHIVE_URL, timeout=60)
    tranco_response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(tranco_response.content)) as archive:
        csv_file = next(
            name for name in archive.namelist()
            if name.endswith(".csv")
        )
        with archive.open(csv_file) as file:
            tranco_df = pd.read_csv(
                file,
                header=None,
                names=["rank", "domain"],
            )

    benign_urls = [
        "https://" + domain
        for domain in tranco_df["domain"].dropna()
        if isinstance(domain, str)
    ]

    print("\n[3] Dang lam sach va gan provenance...")
    dataset = build_dataset(phishing_urls, benign_urls)
    DATA_DIR.mkdir(exist_ok=True)
    output_file = DATA_DIR / "url_dataset.csv"
    dataset.to_csv(output_file, index=False, encoding="utf-8")

    print("\n=== HOAN THANH ===")
    print("Tong so URL:", len(dataset))
    print("\nThong ke nhan:")
    print(dataset["label"].value_counts())
    print("\nThong ke nguon:")
    print(pd.crosstab(dataset["source"], dataset["label"]))
    print("\nFile da luu:", output_file)


if __name__ == "__main__":
    main()
