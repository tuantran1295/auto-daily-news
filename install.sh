#!/bin/bash
# Script cài đặt ứng dụng Bản tin Thời tiết & Bão Việt Nam cho macOS

set -e

WORKSPACE_DIR="/Users/remakit12/Desktop/Daily news app"
PLIST_NAME="com.vietnam.weather.news.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "=== BẮT ĐẦU CÀI ĐẶT ỨNG DỤNG BẢN TIN THỜI TIẾT & BÃO ==="
cd "$WORKSPACE_DIR"

# 1. Tạo môi trường ảo Python venv
echo "--> Đang thiết lập Virtual Environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "    Đã tạo môi trường ảo Python."
else
    echo "    Môi trường ảo (.venv) đã tồn tại."
fi

# 2. Cài đặt các thư viện phụ thuộc
echo "--> Đang cài đặt các thư viện cần thiết..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install requests beautifulsoup4 lxml

# 3. Phân quyền thực thi cho main.py
echo "--> Phân quyền thực thi cho các file script..."
chmod +x main.py

# 4. Tạo thư mục LaunchAgents nếu chưa có
mkdir -p "$HOME/Library/LaunchAgents"

# 5. Copy file cấu hình LaunchAgent plist vào hệ thống
echo "--> Sao chép cấu hình khởi động..."
cp "$PLIST_NAME" "$TARGET_PLIST"
chmod 644 "$TARGET_PLIST"

# 6. Đăng ký LaunchAgent với launchctl
echo "--> Đang đăng ký dịch vụ chạy tự động với macOS..."
USER_ID=$(id -u)

# Hủy đăng ký cũ nếu có để tránh xung đột
launchctl bootout gui/$USER_ID "$TARGET_PLIST" 2>/dev/null || true
launchctl unload "$TARGET_PLIST" 2>/dev/null || true

# Đăng ký dịch vụ mới bằng bootstrap (khuyến nghị trên macOS mới)
if launchctl bootstrap gui/$USER_ID "$TARGET_PLIST" 2>/dev/null; then
    echo "    Đã kích hoạt dịch vụ thành công qua launchctl bootstrap."
else
    # Fallback cho hệ thống macOS cũ hoặc trường hợp bootstrap gặp hạn chế quyền
    echo "    Không thể dùng bootstrap. Thử dùng phương thức tương thích ngược..."
    launchctl load "$TARGET_PLIST"
    echo "    Đã kích hoạt dịch vụ thành công qua launchctl load."
fi

echo ""
echo "=== CÀI ĐẶT HOÀN TẤT ==="
echo "Dịch vụ đã được đăng ký chạy lúc khởi động và vào lúc 08:00 sáng hàng ngày."
echo "Bạn có thể kiểm tra trạng thái hoặc gỡ cài đặt bằng script uninstall.sh."
echo ""

# Hỏi người dùng có muốn chạy thử ngay không
read -p "Bạn có muốn CHẠY THỬ NGAY để tạo bản tin thời tiết đầu tiên không? (y/n): " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo "--> Đang kích hoạt chạy thử..."
    if ! launchctl kickstart -k gui/$USER_ID/com.vietnam.weather.news 2>/dev/null; then
        launchctl start com.vietnam.weather.news
    fi
    echo "Đang xử lý. Vui lòng đợi trong giây lát, hệ thống sẽ gửi Notification và tự động mở Bản tin HTML..."
fi
