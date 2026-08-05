# Bản tin Đa chuyên mục Tự động (macOS Auto Daily News)

Ứng dụng macOS tự khởi động cùng hệ thống, tự động cập nhật thông tin thời tiết 3 miền, quét tin tức bão/thiên tai khẩn cấp, tin tức công nghệ, trí tuệ nhân tạo (AI), FIFA World Cup 2026 và tin tức giới trẻ tại Việt Nam. Ứng dụng sẽ gửi thông báo hệ thống và mở Dashboard HTML Premium trên trình duyệt mặc định vào lúc **8:00 sáng hàng ngày**.

---

## 🌟 Các tính năng chính

* **Khởi động cùng macOS**: Tự động đăng ký với LaunchAgent để tự động khởi chạy lúc 8:00 sáng hàng ngày và tự động chạy bù ngay sau khi máy Mac được bật/đánh thức nếu thời điểm đó đã qua 8h.
* **Thời tiết 3 miền**: Cập nhật thời tiết Hà Nội, Đà Nẵng, TP.HCM qua Open-Meteo API với cơ chế tự động thử lại (Retry) tránh lỗi 503 và tạo khoảng trễ an toàn giữa các request.
* **🚨 Cảnh báo bão & thiên tai khẩn cấp**: Cào tin cảnh báo bão, lũ lụt, mưa lớn từ NCHMF và RSS VnExpress/Tuổi Trẻ để hiển thị cảnh báo đỏ nổi bật.
* **🏆 FIFA World Cup 2026**: Tự động cào và lọc tin tức liên quan đến World Cup 2026 từ các nguồn thể thao uy tín để đưa lên đầu Cột 3 với thiết kế Vàng Gold nổi bật.
* **🧠 Chuyên mục AI nổi bật (Lọc Toàn cục)**: Quét ưu tiên các tin tức liên quan đến Trí tuệ nhân tạo (AI, ChatGPT, Gemini, Claude, Sora, DeepSeek, OpenAI, Nvidia...) từ **tất cả các nguồn tin tức** để hiển thị lên tới 8 bài viết mới nhất với tone màu tím neon đặc trưng.
* **💻 Thế giới Công nghệ (GenK.vn)**: Cập nhật liên tục 60+ tin công nghệ tiêu dùng, khoa học, đời sống số mới nhất từ GenK (Trang chủ, Chuyên mục AI) và VnExpress Số hóa.
* **🎮 Thế giới Game & Esports (GameK.vn)**: Chuyên mục mới cập nhật các tin tức game online, giải đấu Esports, gaming gear và đời sống game thủ từ GameK.
* **✨ Nhịp sống Giới trẻ**: Tin tức xu hướng, đời sống giới trẻ Việt Nam từ báo Thanh Niên.
* **Hiệu năng tối ưu**: Quá trình cào tin và hiển thị chỉ diễn ra trong 3-5 giây và tự động thoát hoàn toàn, không chạy nền gây tốn RAM/pin của máy Mac.

---

## 🚀 Hướng dẫn cài đặt

Bạn chỉ cần chạy script cài đặt tự động được tích hợp sẵn:

1. Mở Terminal và di chuyển đến thư mục dự án:
   ```bash
   cd "/Users/remakit12/Desktop/Daily news app"
   ```
2. Chạy file cài đặt:
   ```bash
   ./install.sh
   ```
   *Script sẽ tự động tạo môi trường ảo Python `.venv`, cài đặt các thư viện cần thiết (`requests`, `beautifulsoup4`, `lxml`), sao chép cấu hình khởi động plist vào hệ thống và kích hoạt LaunchAgent.*

3. Khi cài đặt xong, script sẽ hỏi bạn có muốn chạy thử nghiệm ngay lập tức hay không. Hãy nhập `y` để kiểm tra kết quả ngay.

---

## 🛠️ Quản lý & Sử dụng

### 1. Chạy thủ công bất kỳ lúc nào
Nếu bạn muốn làm mới dữ liệu và xem Dashboard ngay lập tức mà không cần đợi đến 8:00 sáng:
```bash
cd "/Users/remakit12/Desktop/Daily news app"
.venv/bin/python3 main.py
```

### 2. Xem Logs hoạt động
Dịch vụ tự động ghi log để bạn dễ dàng theo dõi hoặc gỡ lỗi:
- Nhật ký thành công: `out.log`
- Nhật ký lỗi (nếu có): `err.log`

### 3. Gỡ cài đặt hoàn toàn (Uninstall)
Để xóa bỏ dịch vụ khởi động cùng macOS, môi trường ảo `.venv` và các tệp tin log rác:
```bash
cd "/Users/remakit12/Desktop/Daily news app"
./uninstall.sh
```

---

## 📂 Cấu trúc thư mục

* `main.py`: File script Python thực thi chính.
* `com.vietnam.weather.news.plist`: Cấu hình LaunchAgent của macOS.
* `install.sh`: Script cài đặt và load LaunchAgent.
* `uninstall.sh`: Script gỡ cài đặt sạch sẽ.
* `today_news.html`: Giao diện Dashboard tin tức Premium (tự động cập nhật hàng ngày).
* `.gitignore`: Các tệp tin cấu hình môi trường ảo, logs và HTML tạm thời được bỏ qua khi đẩy lên Git.
