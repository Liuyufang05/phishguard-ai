# 🛡️ PhishGuard AI

> **Hệ thống phát hiện website lừa đảo (phishing) sử dụng Machine Learning**

PhishGuard AI là một dự án nghiên cứu sử dụng trí tuệ nhân tạo và Machine Learning để phân tích các đặc trưng của URL và phát hiện các website giả mạo, lừa đảo trực tuyến. Dự án bao gồm backend API (FastAPI) và frontend (React + Vite).

---

## 📋 Mục lục

- [Tính năng chính](#-tính-năng-chính)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt và chạy dự án](#-cài-đặt-và-chạy-dự-án)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [API Endpoints](#-api-endpoints)
- [Huấn luyện mô hình](#-huấn-luyện-mô-hình)
- [Đóng góp](#-đóng-góp)
- [Giấy phép](#-giấy-phép)

---

## ✨ Tính năng chính

### 🔍 Phân tích URL thông minh
- Trích xuất 14 đặc trưng từ URL (độ dài, số lượng dấu chấm, từ khóa đáng ngờ, IP trong hostname, v.v.)
- Phân tích không cần truy cập trực tiếp vào website (an toàn, nhanh chóng)

### 🤖 Machine Learning
- So sánh 4 thuật toán: **Logistic Regression**, **Decision Tree**, **Random Forest**, **SVM**
- Tự động chọn mô hình tốt nhất dựa trên Recall và F1-score
- Đánh giá rủi ro 3 mức: **High** (≥70%), **Medium** (40-69%), **Low** (<40%)

### 📊 Dashboard trực quan
- Thống kê tổng số lượt quét, phân bố mức độ rủi ro
- Biểu đồ phân bố rủi ro (High/Medium/Low)
- Lịch sử quét URL với xuất file CSV

### 🎨 Giao diện người dùng
- Thiết kế responsive, hiện đại
- Lưu lịch sử quét vào localStorage
- Hỗ trợ tiếng Việt

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐     HTTP/JSON      ┌─────────────────┐
│   Frontend      │ ◄────────────────► │    Backend      │
│   (React/Vite)  │   Port 5173        │   (FastAPI)     │
│   Port 5173     │                    │   Port 8000     │
└─────────────────┘                    └────────┬────────┘
                                                 │
                                        ┌────────▼────────┐
                                        │  ML Model       │
                                        │  (scikit-learn) │
                                        │  phishguard_    │
                                        │  model.pkl      │
                                        └─────────────────┘
```

---

## 🛠️ Công nghệ sử dụng

### Backend
| Công nghệ | Phiên bản | Mô tả |
|-----------|-----------|-------|
| **FastAPI** | 0.162+ | Framework API hiện đại, nhanh |
| **scikit-learn** | 1.5+ | Thư viện Machine Learning |
| **pandas** | 3.1+ | Xử lý dữ liệu |
| **joblib** | 1.6+ | Lưu/tải mô hình ML |
| **python-dotenv** | 1.0+ | Quản lý biến môi trường |
| **uvicorn** | 0.54+ | ASGI server |

### Frontend
| Công nghệ | Phiên bản | Mô tả |
|-----------|-----------|-------|
| **React** | 19.3+ | Thư viện UI |
| **Vite** | 8.3+ | Build tool nhanh |
| **Chart.js** | 4.6+ | Biểu đồ thống kê |
| **react-chartjs-2** | 5.3+ | Wrapper Chart.js cho React |
| **ESLint** | 10.14+ | Linting code |

### Nguồn dữ liệu huấn luyện
- **Phishing URLs**: [OpenPhish](https://openphish.com/) - Feed URL lừa đảo thực tế
- **Benign URLs**: [Tranco List](https://tranco-list.eu/) - Top 1M tên miền phổ biến

---

## 💻 Yêu cầu hệ thống

- **Python** 3.10 trở lên
- **Node.js** 18 trở lên
- **npm** hoặc **yarn**
- **Git** (tùy chọn)

---

## 🚀 Cài đặt và chạy dự án

### 1. Clone repository
```bash
git clone <repository-url>
cd PhishGuard-AI
```

### 2. Cài đặt Backend

```bash
cd backend

# Tạo môi trường ảo (khuyến nghị)
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install fastapi uvicorn scikit-learn pandas joblib python-dotenv requests
```

> **Lưu ý**: Nếu đã có `requirements.txt`, có thể dùng `pip install -r requirements.txt`

### 3. Chuẩn bị dữ liệu và huấn luyện mô hình

```bash
# Tại thư mục backend/

# Bước 1: Thu thập dữ liệu (tự động tải từ OpenPhish và Tranco)
python prepare_dataset.py

# Bước 2: Huấn luyện mô hình (so sánh 4 thuật toán, chọn mô hình tốt nhất)
python train_model.py
```

Sau khi chạy xong, sẽ tạo ra file `models/phishguard_model.pkl`

### 4. Chạy Backend API

```bash
# Tại thư mục backend/
python main.py
# Hoặc dùng uvicorn trực tiếp:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend sẽ chạy tại: **http://localhost:8000**

- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

### 5. Cài đặt và chạy Frontend

```bash
cd frontend

# Cài đặt dependencies
npm install

# Chạy development server
npm run dev
```

Frontend sẽ chạy tại: **http://localhost:5173**

### 6. Build production (tùy chọn)

```bash
# Frontend
cd frontend
npm run build

# Backend - chạy với uvicorn production
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📁 Cấu trúc thư mục

```
PhishGuard-AI/
├── backend/
│   ├── venv/                    # Môi trường ảo Python
│   ├── models/                  # Thư mục chứa mô hình đã train
│   │   ├── phishguard_model.pkl # Mô hình ML đã lưu
│   │   └── model_comparison.csv # Kết quả so sánh các mô hình
│   ├── dataset/                 # Dữ liệu huấn luyện (tự tạo)
│   │   └── url_dataset.csv      # Dataset phishing + benign
│   ├── logs/                    # File log (tự tạo khi chạy)
│   │   └── phishguard.log
│   ├── main.py                  # FastAPI application entry point
│   ├── feature_extractor.py     # Trích xuất 14 đặc trưng từ URL
│   ├── prepare_dataset.py       # Thu thập dữ liệu từ OpenPhish + Tranco
│   ├── train_model.py           # Huấn luyện và so sánh 4 mô hình ML
│   ├── test_api.py              # Test API endpoints
│   ├── test_features.py         # Test feature extractor
│   └── __init__.py
├── frontend/
│   ├── node_modules/            # Dependencies npm
│   ├── public/                  # Static assets
│   ├── src/
│   │   ├── App.jsx              # Component chính
│   │   ├── App.css              # Styles
│   │   ├── main.jsx             # Entry point
│   │   └── index.css            # Global styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── eslint.config.js
└── README.md                    # File này
```

---

## 🔌 API Endpoints

### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "OK",
  "project": "PhishGuard AI",
  "model_loaded": true
}
```

### Thông tin mô hình
```http
GET /api/model-info
```
**Response:**
```json
{
  "model_name": "Random Forest",
  "version": "1.0.0",
  "features": ["url_length", "hostname_length", "dot_count", ...],
  "number_of_features": 14
}
```

### Quét URL (Phân tích phishing)
```http
POST /api/scan
Content-Type: application/json

{
  "url": "https://example.com"
}
```

**Response thành công:**
```json
{
  "url": "https://example.com",
  "prediction": 0,
  "result": "Benign",
  "risk_level": "Low",
  "risk_score": 5.23,
  "phishing_probability": 0.0523,
  "model_name": "Random Forest",
  "features": {
    "url_length": 19,
    "hostname_length": 11,
    "dot_count": 1,
    "hyphen_count": 0,
    "at_count": 0,
    "question_count": 0,
    "equal_count": 0,
    "slash_count": 2,
    "https": 1,
    "has_ip": 0,
    "has_at_symbol": 0,
    "has_suspicious_keyword": 0,
    "has_double_slash": 0,
    "subdomain_count": 0
  },
  "warning": "Ket qua la danh gia tu mo hinh hoc may, khong dam bao website an toan tuyet doi."
}
```

**Response lỗi (400/422/500/503):**
```json
{
  "detail": "Mô tả lỗi"
}
```

---

## 🧠 Huấn luyện mô hình

### Quy trình tự động (`train_model.py`)

1. **Đọc dữ liệu** từ `dataset/url_dataset.csv`
2. **Trích xuất đặc trưng** cho mỗi URL (14 features)
3. **Chia dữ liệu** 80% train / 20% test (stratified)
4. **Huấn luyện 4 mô hình**:
   - Logistic Regression (với StandardScaler)
   - Decision Tree (max_depth=10)
   - **Random Forest** (n_estimators=200, max_depth=15) ⭐
   - SVM RBF (với StandardScaler)
5. **Đánh giá** bằng: Accuracy, Precision, Recall, F1-score, ROC-AUC
6. **Chọn mô hình tốt nhất** dựa trên Recall và F1-score
7. **Lưu mô hình** vào `models/phishguard_model.pkl`

### Đặc trưng được trích xuất (`feature_extractor.py`)

| Feature | Mô tả |
|---------|-------|
| `url_length` | Độ dài toàn bộ URL |
| `hostname_length` | Độ dài hostname |
| `dot_count` | Số dấu chấm trong URL |
| `hyphen_count` | Số dấu gạch ngang |
| `at_count` | Số ký tự @ |
| `question_count` | Số dấu hỏi |
| `equal_count` | Số dấu bằng |
| `slash_count` | Số dấu gạch chéo |
| `https` | 1 nếu HTTPS, 0 nếu HTTP |
| `has_ip` | 1 nếu hostname là địa chỉ IP |
| `has_at_symbol` | 1 nếu có @ trong URL |
| `has_suspicious_keyword` | 1 nếu có từ khóa: login, verify, update, secure, account, banking, password |
| `has_double_slash` | 1 nếu có // sau protocol |
| `subdomain_count` | Số subdomain (số phần hostname - 2) |

### Chạy lại huấn luyện

```bash
cd backend
python prepare_dataset.py  # Cập nhật dữ liệu mới
python train_model.py      # Train lại mô hình
```

---

## 🧪 Test

### Test Feature Extractor
```bash
cd backend
python test_features.py
```

### Test API
```bash
cd backend
python test_api.py
```

### Test thủ công với curl
```bash
# Health check
curl http://localhost:8000/api/health

# Quét URL
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'
```

---

## 🌍 Biến môi trường

Tạo file `.env` tại thư mục gốc (`PhishGuard-AI/.env`):

```env
APP_NAME=PhishGuard AI
APP_ENV=development
DEBUG=true
```

---

## ⚠️ Lưu ý quan trọng

1. **Kết quả chỉ mang tính tham khảo**: Mô hình ML không đảm bảo phát hiện 100% các trang phishing
2. **Không tự động truy cập website**: Hệ thống chỉ phân tích cấu trúc URL, không tải nội dung trang web
3. **Dữ liệu huấn luyện**: Mặc định lấy 300 URL phishing và 300 URL benign (có thể chỉnh trong `prepare_dataset.py`)
4. **CORS**: Backend chỉ cho phép origin `http://localhost:5173` và `http://127.0.0.1:5173`

---

## 🤝 Đóng góp

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/ten-tinh-nang`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng X'`)
4. Push lên branch (`git push origin feature/ten-tinh-nang`)
5. Tạo Pull Request

---

## 📄 Giấy phép

Dự án này được phát hành dưới giấy phép **MIT License** - xem file [LICENSE](LICENSE) để biết chi tiết.

---

## 👨‍💻 Tác giả

**PhishGuard AI Team** - Dự án nghiên cứu Machine Learning cho an ninh mạng

---

## 🙏 Lời cảm ơn

- [OpenPhish](https://openphish.com/) - Cung cấp feed URL phishing
- [Tranco List](https://tranco-list.eu/) - Cung cấp danh sách tên miền phổ biến
- Cộng đồng open source: FastAPI, React, scikit-learn, Chart.js và nhiều thư viện khác

---

> **⚡ Quick Start**: Chạy `backend/main.py` và `frontend/npm run dev` sau khi đã train xong mô hình!