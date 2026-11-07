
from feature_extractor import extract_features

url = "https://example.com/login"

result = extract_features(url)

print("URL:", url)
print("\nCÁC ĐẶC TRƯNG ĐÃ TRÍCH XUẤT:")

for feature, value in result.items():
    print(f"{feature}: {value}")
