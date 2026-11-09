
import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState(() => {
  try {
    return JSON.parse(
      localStorage.getItem("phishguard_history") || "[]"
    );
  } catch {
    return [];
  }
});

useEffect(() => {
  localStorage.setItem(
    "phishguard_history",
    JSON.stringify(history)
  );
}, [history]);

  const handleScan = async (e) => {
    e.preventDefault();

    if (!url.trim()) {
      setError("Vui lòng nhập đường dẫn website cần kiểm tra.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        "https://phishguard-ai-4ubb.onrender.com/api/scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Không thể phân tích URL.");
      }

      setResult(data);

setHistory((previous) => [
  {
    ...data,
    id: Date.now(),
    url: url.trim(),
    scannedAt: new Date().toLocaleString("vi-VN"),
  },
  ...previous,
].slice(0, 20));
    } catch (err) {
      setError(
        err.message || "Không thể kết nối với máy chủ. Hãy kiểm tra Backend."
      );
    } finally {
      setLoading(false);
    }
  };

  const getResultColor = () => {
    
    if (!result) return "";
    const level = (result.risk_level || "").toLowerCase();

    if (level.includes("high")) return "danger";
    if (level.includes("medium")) return "warning";
    return "safe";
  };
  
  const totalScans = history.length;

  const highRisk = history.filter(
    (item) =>
      (item.risk_level || "").toLowerCase().includes("high")
  ).length;

  const mediumRisk = history.filter(
    (item) =>
      (item.risk_level || "").toLowerCase().includes("medium")
  ).length;

  const lowRisk = totalScans - highRisk - mediumRisk;

  const getPercent = (value) =>
    totalScans > 0 ? (value / totalScans) * 100 : 0;

  
// XUẤT LỊCH SỬ QUÉT RA FILE CSV
const exportHistory = () => {
  if (history.length === 0) {
    alert("Chưa có dữ liệu để xuất!");
    return;
  }

  const headers = [
    "STT",
    "URL",
    "Muc do rui ro",
    "Thoi gian quet",
  ];

  const escapeCSV = (value) => {
    let text = String(value ?? "");

    // Ngăn dữ liệu CSV bị hiểu nhầm là công thức
    if (/^[=+\-@\t\r]/.test(text)) {
      text = "'" + text;
    }

    return `"${text.replace(/"/g, '""')}"`;
  };

  const rows = history.map((item, index) => [
    index + 1,
    item.url,
    item.risk_level || "Chua xac dinh",
    item.scannedAt,
  ]);

  const csvContent = [
    headers,
    ...rows,
  ]
    .map((row) => row.map(escapeCSV).join(","))
    .join("\n");

  const blob = new Blob(
    ["\uFEFF" + csvContent],
    { type: "text/csv;charset=utf-8;" }
  );

  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.href = url;
  link.download = "phishguard_scan_history.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
};

  return (
    <div className="app">
      <header className="navbar">
        <a className="brand" href="/">
          <span className="brand-icon">🛡️</span>
          <span>PhishGuard <strong>AI</strong></span>
        </a>

        <nav>
          <a href="#home">Trang chủ</a>
          <a href="#features">Tính năng</a>
          <a href="#about">Giới thiệu</a>
        </nav>

        <span className="status">
          <span className="status-dot"></span>
          AI Security
        </span>
      </header>

      <main>
        <section className="hero" id="home">
          <div className="hero-badge">
            ✨ HỆ THỐNG PHÁT HIỆN WEBSITE GIẢ MẠO
          </div>

          <h1>
            Bảo vệ bạn khỏi
            <br />
            <span>Website lừa đảo</span>
          </h1>

          <p className="hero-description">
            Sử dụng trí tuệ nhân tạo và Machine Learning để phân tích
            đường dẫn, nhận diện website có dấu hiệu phishing.
          </p>

          <div className="scan-card">
            <form onSubmit={handleScan}>
              <label htmlFor="url-input">
                Nhập đường dẫn website bạn muốn kiểm tra
              </label>

              <div className="input-group">
                <span>🔗</span>
                <input
                  id="url-input"
                  type="text"
                  placeholder="Ví dụ: https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />

                <button type="submit" disabled={loading}>
                  {loading ? "Đang phân tích..." : "🔍 Phân tích"}
                </button>
              </div>
            </form>

            <div className="scan-note">
              🔒 Hệ thống phân tích đặc trưng URL, không tự động truy cập website.
            </div>

            {error && <div className="error-box">⚠️ {error}</div>}

            {result && (
              <div className={`result-box ${getResultColor()}`}>
                <h3>Kết quả phân tích</h3>
                <p className="result-url">{result.url}</p>

                <div className="result-grid">
                  <div>
                    <small>Kết quả</small>
                    <strong>{result.result || result.prediction || "Chưa xác định"}</strong>
                  </div>

                  <div>
                    <small>Mức độ rủi ro</small>
                    <strong>{result.risk_level || "Chưa xác định"}</strong>
                  </div>

                  <div>
                    <small>Điểm rủi ro</small>
                    <strong>
                      {result.risk_score != null
                        ? `${Number(result.risk_score).toFixed(2)}%`
                        : "N/A"}
                    </strong>
                  </div>

                  <div>
                    <small>Mô hình AI</small>
                    <strong>{result.model_name || "PhishGuard AI"}</strong>
                  </div>
                </div>

                {result.warning && (
                  <p className="result-warning">⚠️ {result.warning}</p>
                )}
              </div>
            )}
          </div>
        </section>

        {/* DASHBOARD */}
<section className="dashboard" id="dashboard">
  <div className="section-heading">
    <span className="section-tag">ANALYTICS</span>
    <h2>Dashboard thống kê</h2>
    <p>Theo dõi kết quả phân tích các URL đã quét gần đây.</p>
  </div>

  {/* Các thẻ thống kê */}
  <div className="stats-grid">
    <div className="stat-card">
      <span>🔎</span>
      <h3>{totalScans}</h3>
      <p>Tổng số lượt quét</p>
    </div>

    <div className="stat-card danger-stat">
      <span>🚨</span>
      <h3>{highRisk}</h3>
      <p>Nguy cơ cao</p>
    </div>

    <div className="stat-card warning-stat">
      <span>⚠️</span>
      <h3>{mediumRisk}</h3>
      <p>Nguy cơ trung bình</p>
    </div>

    <div className="stat-card safe-stat">
      <span>🛡️</span>
      <h3>{lowRisk}</h3>
      <p>Nguy cơ thấp</p>
    </div>
  </div>

  {/* Biểu đồ thống kê */}
  <div className="analytics-card">
    <h3>Phân bố mức độ rủi ro</h3>

    <div className="bar-row">
      <span>Nguy cơ cao</span>
      <div className="bar-track">
        <div
          className="bar-fill high-fill"
          style={{ width: `${getPercent(highRisk)}%` }}
        />
      </div>
      <span>{Math.round(getPercent(highRisk))}%</span>
    </div>

    <div className="bar-row">
      <span>Trung bình</span>
      <div className="bar-track">
        <div
          className="bar-fill medium-fill"
          style={{ width: `${getPercent(mediumRisk)}%` }}
        />
      </div>
      <span>{Math.round(getPercent(mediumRisk))}%</span>
    </div>

    <div className="bar-row">
      <span>Nguy cơ thấp</span>
      <div className="bar-track">
        <div
          className="bar-fill low-fill"
          style={{ width: `${getPercent(lowRisk)}%` }}
        />
      </div>
      <span>{Math.round(getPercent(lowRisk))}%</span>
    </div>
  </div>

  {/* Lịch sử quét */}
  <div className="history-card">
    <div className="history-heading">
      <h3>Lịch sử quét URL</h3>

      <button
  className="export-button"
  onClick={exportHistory}
>
  📥 Xuất CSV
</button>
      <button
        className="clear-button"
        onClick={() => {
          if (window.confirm("Bạn có chắc muốn xóa toàn bộ lịch sử?")) {
            setHistory([]);
          }
        }}
      >
        Xóa lịch sử
      </button>
    </div>

    {history.length === 0 ? (
      <p className="empty-history">
        Chưa có dữ liệu. Hãy nhập URL và thực hiện quét để xem lịch sử.
      </p>
    ) : (
      <div className="table-wrapper">
        <table className="history-table">
          <thead>
            <tr>
              <th>STT</th>
              <th>Địa chỉ URL</th>
              <th>Kết quả</th>
              <th>Thời gian quét</th>
            </tr>
          </thead>

          <tbody>
            {history.map((item, index) => (
              <tr key={item.id}>
                <td>{index + 1}</td>
                <td className="url-cell">{item.url}</td>
                <td>{item.risk_level || "Chưa xác định"}</td>
                <td>{item.scannedAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </div>
</section>
        <section className="features" id="features">
          <div className="section-heading">
            <span>GIẢI PHÁP BẢO MẬT</span>
            <h2>Công nghệ bảo vệ thông minh</h2>
            <p>Phân tích URL nhanh chóng với các thuật toán học máy.</p>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-icon purple">🧠</div>
              <h3>Machine Learning</h3>
              <p>
                Sử dụng các mô hình học máy để nhận diện dấu hiệu
                của đường dẫn độc hại.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-icon blue">⚡</div>
              <h3>Phân tích nhanh</h3>
              <p>
                Trích xuất các đặc trưng URL và trả về kết quả
                phân tích trong thời gian ngắn.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-icon green">🛡️</div>
              <h3>Đánh giá rủi ro</h3>
              <p>
                Hiển thị mức độ rủi ro giúp người dùng thận trọng
                trước các liên kết đáng ngờ.
              </p>
            </article>
          </div>
        </section>

        <section className="about" id="about">
          <h2>PhishGuard AI là gì?</h2>
          <p>
            PhishGuard AI là hệ thống nghiên cứu phát hiện website giả mạo
            bằng các thuật toán Machine Learning. Kết quả chỉ mang tính
            hỗ trợ đánh giá, không đảm bảo website an toàn tuyệt đối.
          </p>
        </section>
      </main>

      <footer>
        <div className="brand">
          🛡️ PhishGuard <strong>AI</strong>
        </div>
        <p>© 2026 PhishGuard AI. Dự án nghiên cứu Machine Learning.</p>
      </footer>
    </div>
  );
}

export default App;
