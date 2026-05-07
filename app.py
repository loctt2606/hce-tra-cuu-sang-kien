import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 1. Cấu hình trang web
st.set_page_config(page_title="Tra cứu Sáng kiến", page_icon="🔍", layout="wide")
st.title("🔍 Ứng dụng Tra cứu tỷ lệ tương đồng của Tên Sáng kiến")
st.markdown("Hệ thống sẽ dùng AI phân tích để tìm ra các sáng kiến tương đồng nhất trong cơ sở dữ liệu hiện có.")

# 2. Tải mô hình AI (Cache lại để không phải tải lại mỗi lần người dùng bấm nút)
@st.cache_resource
def load_model():
    # Sử dụng mô hình hỗ trợ đa ngôn ngữ (có tiếng Việt), tốc độ nhanh
    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

model = load_model()

# 3. Đọc và xử lý file CSV dữ liệu
@st.cache_data
def load_data():
    # File của bạn có tiêu đề ở dòng thứ 2 (index 1)
    df = pd.read_excel("list.xls", header=1)
    
    # Làm sạch dữ liệu: bỏ các dòng không có TÊN SÁNG KIẾN
    df = df.dropna(subset=['TÊN SÁNG KIẾN'])
    
    # Lấy danh sách tên sáng kiến
    sangkien_list = df['TÊN SÁNG KIẾN'].tolist()
    
    # Biến toàn bộ dữ liệu lịch sử thành vector (Chỉ tính 1 lần lúc khởi động web)
    embeddings = model.encode(sangkien_list)
    return df, sangkien_list, embeddings

try:
    df, sangkien_list, database_embeddings = load_data()
    st.success(f"✅ Đã tải cơ sở dữ liệu thành công với **{len(df)}** sáng kiến.")
except Exception as e:
    st.error(f"Lỗi đọc file dữ liệu: {e}. Hãy đảm bảo file dữ liệu nằm cùng thư mục với app.py.")
    st.stop()

# 4. Thiết kế Khu vực nhập liệu
st.markdown("---")
query = st.text_input("📝 **Nhập tên sáng kiến mới của bạn vào đây:**", placeholder="Ví dụ: Ứng dụng công nghệ thông tin trong việc quản lý điểm sinh viên...")
top_k = st.slider("Số lượng kết quả muốn xem:", min_value=5, max_value=20, value=10)

# 5. Xử lý thuật toán khi bấm nút
if st.button("Tra cứu ngay", type="primary"):
    if query.strip() == "":
        st.warning("⚠️ Vui lòng nhập tên sáng kiến!")
    else:
        with st.spinner('AI đang phân tích và đối chiếu...'):
            # Biến câu truy vấn thành vector
            query_embedding = model.encode([query])
            
            # Tính độ tương đồng Cosine
            similarities = cosine_similarity(query_embedding, database_embeddings)[0]
            
            # Lấy top K kết quả cao điểm nhất
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Lưu kết quả để hiển thị
            results = []
            for idx in top_indices:
                results.append({
                    "Độ trùng khớp": f"{similarities[idx] * 100:.2f}%",
                    "Tên sáng kiến (Cũ)": df.iloc[idx]['TÊN SÁNG KIẾN'],
                    "Tác giả": df.iloc[idx]['TÁC GIẢ']
                })
            
            result_df = pd.DataFrame(results)
            
            st.subheader(f"📊 Top {top_k} sáng kiến tương đồng nhất:")
            # Chỉnh màu sắc cho bảng đẹp hơn
            st.dataframe(result_df, use_container_width=True)
            
            # Đánh giá cảnh báo
            max_sim = similarities[top_indices[0]] * 100
            if max_sim > 80:
                st.error("🚨 Cảnh báo: Sáng kiến của bạn có độ trùng khớp rất cao với dữ liệu cũ!")
            elif max_sim > 60:
                st.warning("⚠️ Lưu ý: Có một số ý tưởng khá tương đồng, bạn nên xem xét kỹ.")
            else:
                st.success("🎉 Tốt: Tên sáng kiến của bạn khá mới mẻ, chưa có sự trùng lặp đáng kể!")