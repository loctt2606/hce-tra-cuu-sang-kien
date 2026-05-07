import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- 1. Cấu hình giao diện ---
st.set_page_config(page_title="Hệ thống Tra cứu Sáng kiến - Hybrid AI", page_icon="🚀", layout="wide")

st.title("🚀 Tra cứu Sáng kiến thông minh (Hybrid AI)")
st.markdown("""
    Hệ thống sử dụng công nghệ **Hybrid Search**: Kết hợp giữa **Trí tuệ nhân tạo (AI)** để hiểu ngữ nghĩa 
    và **Đối soát từ khóa (TF-IDF)** để đảm bảo tìm chính xác các thuật ngữ chuyên môn như 'QR code', 'IoT', 'AI'...
""")

# --- 2. Hàm tải dữ liệu và tính toán Vector (Cache để tối ưu tốc độ) ---
@st.cache_resource
def load_ai_model():
    # Mô hình AI đa ngôn ngữ
    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

@st.cache_data
def prepare_database(file_path):
    # Đọc dữ liệu (header=1 vì file của bạn có tiêu đề ở dòng 2)
    df = pd.read_excel(file_path, header=1)
    df = df.dropna(subset=['TÊN SÁNG KIẾN'])
    df = df.reset_index(drop=True)
    
    sangkien_list = df['TÊN SÁNG KIẾN'].astype(str).tolist()
    
    # A. Tính toán Vector AI (Semantic)
    model = load_ai_model()
    semantic_embeddings = model.encode(sangkien_list, show_progress_bar=False)
    
    # B. Tính toán Ma trận Từ khóa (TF-IDF)
    vectorizer = TfidfVectorizer(lowercase=True, analyzer='word', token_pattern=r'(?u)\b\w\w+\b')
    tfidf_matrix = vectorizer.fit_transform(sangkien_list)
    
    return df, sangkien_list, semantic_embeddings, vectorizer, tfidf_matrix

# Thực thi tải dữ liệu
file_name = "list.xls"
try:
    df, texts, semantic_db, tfidf_vec, tfidf_db = prepare_database(file_name)
    st.sidebar.success(f"📚 Cơ sở dữ liệu: {len(df)} sáng kiến")
except Exception as e:
    st.error(f"❌ Không tìm thấy file '{file_name}'. Vui lòng kiểm tra lại tên file trên Github.")
    st.stop()

# --- 3. Giao diện người dùng ---
with st.container():
    query = st.text_input("🔍 Nhập tên sáng kiến hoặc từ khóa cần tra cứu:", 
                         placeholder="Ví dụ: Giải pháp chuyển đổi số...")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        top_k = st.slider("Số lượng kết quả hiển thị:", 5, 20, 10)
    with col2:
        # Cho phép người dùng điều chỉnh độ ưu tiên nếu muốn (mặc định 50/50)
        ai_weight = st.slider("Độ ưu tiên AI (Hiểu ý nghĩa) vs Từ khóa (Chính xác):", 0.0, 1.0, 0.5, 0.1)

# --- 4. Thuật toán Hybrid Search ---
if query:
    with st.spinner('Đang phân tích dữ liệu...'):
        # 1. Điểm Semantic (AI)
        model = load_ai_model()
        query_semantic = model.encode([query])
        semantic_scores = cosine_similarity(query_semantic, semantic_db)[0]
        
        # 2. Điểm Keyword (TF-IDF)
        query_tfidf = tfidf_vec.transform([query.lower()])
        tfidf_scores = cosine_similarity(query_tfidf, tfidf_db)[0]
        
        # 3. Kết hợp điểm theo trọng số (Hybrid)
        # Final Score = AI_Score * Weight + Keyword_Score * (1 - Weight)
        final_scores = (semantic_scores * ai_weight) + (tfidf_scores * (1 - ai_weight))
        
        # Lấy Top K
        top_indices = np.argsort(final_scores)[::-1][:top_k]
        
        # Hiển thị kết quả
        st.markdown(f"### 📋 Kết quả Top {top_k} sáng kiến tương đồng nhất:")
        
        results = []
        for idx in top_indices:
            score = final_scores[idx] * 100
            if score > 0: # Chỉ hiển thị nếu có sự tương đồng
                results.append({
                    "Độ tương đồng": f"{score:.2f}%",
                    "Tên sáng kiến": df.iloc[idx]['TÊN SÁNG KIẾN'],
                    "Tác giả": df.iloc[idx]['TÁC GIẢ'],
                    "Ghi chú": df.iloc[idx]['GHI CHÚ'] if 'GHI CHÚ' in df.columns else ""
                })
        
        if results:
            res_df = pd.DataFrame(results)
            st.table(res_df) # Dùng table để hiển thị đầy đủ text không bị cắt
            
            # Đưa ra lời khuyên
            max_score = final_scores[top_indices[0]] * 100
            if max_score > 75:
                st.error(f"❗ Cảnh báo: Tìm thấy sáng kiến trùng khớp rất cao ({max_score:.1f}%). Bạn nên kiểm tra kỹ tính mới.")
            elif max_score > 40:
                st.warning(f"⚠️ Lưu ý: Có sự tương đồng khá rõ ({max_score:.1f}%). Hãy điều chỉnh hướng tiếp cận để khác biệt hơn.")
            else:
                st.success(f"✅ Chúc mừng: Tên sáng kiến của bạn có tính mới khá cao so với dữ liệu lịch sử.")
        else:
            st.info("Không tìm thấy kết quả nào trùng khớp.")
