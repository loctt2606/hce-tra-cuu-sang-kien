# --- Hàm tiện ích cho Admin Panel ---
import os
import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

def create_folders():
    """Tạo các folder cần thiết nếu chưa tồn tại"""
    for folder in ["uploads", "outputs"]:
        os.makedirs(folder, exist_ok=True)

def get_similarity_level(score):
    """
    Chuyển đổi điểm tương đồng thành mức độ
    score: điểm từ 0-1
    """
    if score >= 0.7:
        return "Cao"
    elif score >= 0.4:
        return "Trung bình"
    else:
        return "Thấp"

def get_first_existing_column(df, candidate_columns):
    """Lấy cột đầu tiên tồn tại trong danh sách ứng viên (so khớp linh hoạt)."""
    def normalize_col_name(value):
        value = str(value).replace("\n", " ").strip().lower()
        value = re.sub(r"\s+", " ", value)
        return value

    normalized_actual = {normalize_col_name(col): col for col in df.columns}
    for candidate in candidate_columns:
        normalized_candidate = normalize_col_name(candidate)
        if normalized_candidate in normalized_actual:
            return normalized_actual[normalized_candidate]
    return None

def calculate_similarity_matrix(old_df, new_df, model, name_column, new_entity_label, old_entity_label):
    """
    Tính độ tương đồng giữa dữ liệu mới và dữ liệu cũ
    
    Args:
        old_df: DataFrame chứa dữ liệu cũ
        new_df: DataFrame chứa dữ liệu mới
        model: SentenceTransformer model
        name_column: Tên cột chứa nội dung cần so sánh
        new_entity_label: Nhãn cho dữ liệu mới (vd: "sáng kiến mới")
        old_entity_label: Nhãn cho dữ liệu cũ (vd: "đề tài cũ")
    
    Returns:
        Danh sách kết quả
    """
    old_names = old_df[name_column].astype(str).tolist()
    new_names = new_df[name_column].astype(str).tolist()
    
    # Tính embeddings
    old_embeddings = model.encode(old_names, show_progress_bar=False)
    new_embeddings = model.encode(new_names, show_progress_bar=False)
    
    # Tính cosine similarity
    similarity_matrix = cosine_similarity(new_embeddings, old_embeddings)
    
    results = []
    
    for new_idx, new_name in enumerate(new_names):
        similarities = similarity_matrix[new_idx]
        
        # Lấy top 5 dữ liệu cũ có độ tương đồng cao nhất
        top_5_indices = np.argsort(similarities)[::-1][:5]
        
        top_5_similar = []
        for rank, old_idx in enumerate(top_5_indices, 1):
            score = similarities[old_idx]
            old_name = old_names[old_idx]
            level = get_similarity_level(score)
            
            top_5_similar.append({
                'Rank': rank,
                old_entity_label: old_name,
                'Độ tương đồng': f"{score*100:.2f}%",
                'Mức độ': level
            })
        
        # Tính mức độ chung dựa trên độ tương đồng cao nhất
        max_score = similarities[top_5_indices[0]]
        overall_level = get_similarity_level(max_score)
        
        results.append({
            new_entity_label: new_name,
            'Độ tương đồng cao nhất': f"{max_score*100:.2f}%",
            'Mức độ': overall_level,
            'Top 5 tương đồng': top_5_similar
        })
    
    return results

def create_summary_dataframe(results, new_entity_label, old_entity_label):
    """
    Tạo DataFrame tóm tắt kết quả - Top 5 dữ liệu cũ tách thành 5 cột riêng
    """
    summary_data = []
    
    for result in results:
        row = {
            new_entity_label: result[new_entity_label],
            'Độ tương đồng cao nhất': result['Độ tương đồng cao nhất'],
            'Ghi chú': result['Mức độ']
        }
        
        # Tách Top 5 thành 5 cột riêng
        for rank, item in enumerate(result['Top 5 tương đồng'], 1):
            row[f'Top {rank} - Tên'] = item[old_entity_label]
            row[f'Top {rank} - Độ tương đồng'] = item['Độ tương đồng']
        
        summary_data.append(row)
    
    return pd.DataFrame(summary_data)

def create_detailed_dataframe(results, new_entity_label, old_entity_label):
    """
    Tạo DataFrame chi tiết - Sắp xếp theo độ tương đồng từ cao xuống thấp, có phân nhóm
    """
    detailed_data = []
    
    for result in results:
        for item in result['Top 5 tương đồng']:
            detailed_data.append({
                new_entity_label: result[new_entity_label],
                old_entity_label: item[old_entity_label],
                'Độ tương đồng': item['Độ tương đồng'],
                'Ghi chú': item['Mức độ']
            })
    
    detailed_df = pd.DataFrame(detailed_data)
    
    # Sắp xếp theo tên dữ liệu mới (phân nhóm), sau đó theo Độ tương đồng từ cao xuống
    # Để sắp xếp đúng, cần convert độ tương đồng thành số
    detailed_df['_sort_similarity'] = detailed_df['Độ tương đồng'].str.rstrip('%').astype(float)
    detailed_df = detailed_df.sort_values([new_entity_label, '_sort_similarity'], 
                                          ascending=[True, False])
    detailed_df = detailed_df.drop('_sort_similarity', axis=1)
    
    return detailed_df

def export_results_to_excel(results, new_entity_label, old_entity_label, filename=None, output_prefix="thong_ke_"):
    """
    Xuất kết quả ra file Excel
    """
    if filename is None:
        filename = f"{output_prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    filepath = os.path.join("outputs", filename)
    
    # Tạo summary sheet
    summary_df = create_summary_dataframe(results, new_entity_label, old_entity_label)
    
    # Tạo detailed sheet
    detailed_df = create_detailed_dataframe(results, new_entity_label, old_entity_label)
    
    # Xuất ra Excel với multiple sheets
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Tóm tắt', index=False)
        detailed_df.to_excel(writer, sheet_name='Chi tiết', index=False)
    
    return filepath
