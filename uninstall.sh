#!/bin/bash
# Script gỡ cài đặt ứng dụng Bản tin Thời tiết & Bão Việt Nam sạch sẽ khỏi macOS

WORKSPACE_DIR="/Users/remakit12/Desktop/Daily news app"
PLIST_NAME="com.vietnam.weather.news.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "=== BẮT ĐẦU GỠ CÀI ĐẶT ỨNG DỤNG BẢN TIN THỜI TIẾT & BÃO ==="

# 1. Hủy đăng ký LaunchAgent khỏi launchctl
echo "--> Đang gỡ bỏ dịch vụ chạy tự động khỏi macOS..."
USER_ID=$(id -u)

# Hủy đăng ký thông qua bootstrap (nếu có đăng ký qua bootstrap)
launchctl bootout gui/$USER_ID "$TARGET_PLIST" 2>/dev/null || true
# Hủy đăng ký thông qua unload truyền thống
launchctl unload "$TARGET_PLIST" 2>/dev/null || true

# 2. Xóa file plist
echo "--> Đang xóa file cấu hình LaunchAgent..."
if [ -f "$TARGET_PLIST" ]; then
    rm "$TARGET_PLIST"
    echo "    Đã xóa $TARGET_PLIST"
else
    echo "    Không tìm thấy file cấu hình trong LaunchAgents."
fi

# 3. Dọn dẹp thư mục làm việc (tùy chọn)
echo "--> Đang dọn dẹp các tệp tin rác trong thư mục dự án..."
cd "$WORKSPACE_DIR"

if [ -d ".venv" ]; then
    rm -rf .venv
    echo "    Đã xóa Virtual Environment (.venv)."
fi

if [ -f "today_news.html" ]; then
    rm "today_news.html"
    echo "    Đã xóa tệp giao diện today_news.html."
fi

if [ -f "out.log" ]; then
    rm "out.log"
    echo "    Đã xóa tệp nhật ký out.log."
fi

if [ -f "err.log" ]; then
    rm "err.log"
    echo "    Đã xóa tệp nhật ký err.log."
fi

echo ""
echo "=== GỠ CÀI ĐẶT HOÀN TẤT ==="
echo "Ứng dụng đã được gỡ bỏ hoàn toàn khỏi hệ thống của bạn."
echo ""
