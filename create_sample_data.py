# File demo cho testing - Tạo dữ liệu mẫu

import pandas as pd
import os

# Tạo file Excel mẫu để test upload
def create_sample_new_initiatives():
    """Tạo file Excel mẫu chứa các sáng kiến MỚI để test"""
    
    data = {
        'TÊN SÁNG KIẾN': [
            'Giải pháp chuyển đổi số cho doanh nghiệp nhỏ',
            'Hệ thống quản lý IoT thông minh',
            'Nền tảng AI để phân tích dữ liệu tiếp thị',
            'Ứng dụng blockchain cho chuỗi cung ứng',
            'Công nghệ AR/VR trong giáo dục trực tuyến'
        ],
        'TÁC GIẢ': [
            'Công ty A',
            'Công ty B',
            'Công ty C',
            'Công ty D',
            'Công ty E'
        ],
        'GHI CHÚ': [
            'Khởi tạo 2024',
            'Phát triển 2024',
            'Test thử nghiệm',
            'Triển khai pilot',
            'Ý tưởng mới'
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Thêm header trống ở hàng 1 (để match format file cũ)
    df_with_header = pd.concat([
        pd.DataFrame([[None] * len(df.columns)], columns=df.columns),
        df
    ], ignore_index=True)
    
    # Lưu file
    output_file = "sample_new_initiatives.xls"
    df_with_header.to_excel(output_file, index=False, sheet_name='Sheet1')
    
    print(f"✅ Đã tạo file mẫu: {output_file}")
    return output_file

if __name__ == "__main__":
    create_sample_new_initiatives()
