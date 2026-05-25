# --- Cấu hình Admin ---
# File này chứa thông tin đăng nhập admin

ADMIN_CREDENTIALS = {
    "admin": "admin123",  # username: password
    "admin2": "password123"
}

# Các folder được sử dụng
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

# Cấu hình loại dữ liệu tra cứu
LOOKUP_TYPE_CONFIG = {
    "sangkien": {
        "label": "sáng kiến",
        "title": "Sáng kiến",
        "old_file": "sk.xlsx",
        "output_prefix": "sk_",
        "name_columns": [
            "TÊN SÁNG KIẾN",
            "TÊN",
            "TEN SANG KIEN"
        ],
        "author_columns": [
            "TÁC GIẢ",
            "CHỦ NHIỆM",
            "TAC GIA"
        ],
        "note_columns": [
            "GHI CHÚ",
            "MÔ TẢ",
            "GHI CHU"
        ]
    },
    "nckh": {
        "label": "đề tài nghiên cứu khoa học",
        "title": "Đề tài nghiên cứu khoa học",
        "old_file": "nckh.xlsx",
        "output_prefix": "nckh_",
        "name_columns": [
            "TÊN ĐỀ TÀI",
            "TÊN ĐỀ TÀI ĐÃ NGHIỆM THU",
            "TÊN ĐỀ TÀI NCKH",
            "TÊN ĐỀ TÀI NGHIÊN CỨU KHOA HỌC",
            "TÊN",
            "TEN DE TAI"
        ],
        "author_columns": [
            "CHỦ NHIỆM ĐỀ TÀI",
            "TÁC GIẢ",
            "NHÓM THỰC HIỆN",
            "CHU NHIEM DE TAI"
        ],
        "note_columns": [
            "GHI CHÚ",
            "MÔ TẢ",
            "LĨNH VỰC",
            "GHI CHU"
        ]
    }
}
