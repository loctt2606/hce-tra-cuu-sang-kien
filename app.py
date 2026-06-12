import streamlit as st
import pandas as pd
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from admin_config import ADMIN_CREDENTIALS, LOOKUP_TYPE_CONFIG
from admin_utils import (
    create_folders, 
    calculate_similarity_matrix, 
    create_summary_dataframe, 
    create_detailed_dataframe,
    export_results_to_excel,
    get_first_existing_column
)

# --- 1. Cấu hình giao diện ---
st.set_page_config(page_title="Hệ thống Tra cứu tên Sáng kiến và Đề tài NCKH", page_icon="🚀", layout="wide")

# Tạo các folder cần thiết
create_folders()

# --- 2. Khởi tạo Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None

if 'analysis_results_by_type' not in st.session_state:
    st.session_state.analysis_results_by_type = {}

if 'analysis_meta_by_type' not in st.session_state:
    st.session_state.analysis_meta_by_type = {}

# --- 3. Hàm tải dữ liệu và tính toán Vector (Cache) ---
@st.cache_resource
def load_ai_model():
    """Tải mô hình AI đa ngôn ngữ"""
    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

@st.cache_data
def prepare_database(file_path, name_columns):
    """Chuẩn bị cơ sở dữ liệu từ file Excel"""
    try:
        detected = detect_dataframe_with_header(file_path, name_columns)
        if detected is None:
            return None

        df, name_col, _ = detected
        if name_col is None:
            return None

        df = df.dropna(subset=[name_col])
        df = df.reset_index(drop=True)
        
        text_list = df[name_col].astype(str).tolist()
        
        # A. Tính toán Vector AI (Semantic)
        model = load_ai_model()
        semantic_embeddings = model.encode(text_list, show_progress_bar=False)
        
        # B. Tính toán Ma trận Từ khóa (TF-IDF)
        vectorizer = TfidfVectorizer(lowercase=True, analyzer='word', token_pattern=r'(?u)\b\w\w+\b')
        tfidf_matrix = vectorizer.fit_transform(text_list)
        
        return df, text_list, semantic_embeddings, vectorizer, tfidf_matrix, name_col
    except Exception as e:
        return None

def detect_dataframe_with_header(file_path, name_columns, max_header_row=8):
    """Tự dò dòng header phù hợp trong vài dòng đầu file Excel."""
    for header_row in range(max_header_row + 1):
        try:
            df = pd.read_excel(file_path, header=header_row)
            if df is None or df.empty:
                continue

            name_col = get_first_existing_column(df, name_columns)
            if name_col is not None:
                return df, name_col, header_row
        except Exception:
            continue

    return None

def get_lookup_meta(lookup_type):
    """Trả về metadata cho loại tra cứu đã chọn."""
    cfg = LOOKUP_TYPE_CONFIG[lookup_type]
    entity_label = cfg['label']
    return {
        'cfg': cfg,
        'entity_label': entity_label,
        'entity_title': cfg['title'],
        'new_entity_col': f"Tên {entity_label} mới",
        'old_entity_col': f"Tên {entity_label} cũ"
    }

# --- 4. Trang Đăng nhập ---
def show_login_page():
    """Hiển thị trang đăng nhập"""
    st.title("🔐 Tra cứu tên Sáng kiến - tên Đề tài NCKH tại HCE")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Admin Login")
        
        username = st.text_input("👤 Tên đăng nhập:", key="login_username")
        password = st.text_input("🔑 Mật khẩu:", type="password", key="login_password")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🔓 Đăng nhập", use_container_width=True):
                if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.session_state.username = username
                    st.success("✅ Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("❌ Tên đăng nhập hoặc mật khẩu không đúng")
        
        with col_b:
            if st.button("👥 Tra cứu công khai", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.user_role = "user"
                st.session_state.username = "guest"
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        **Hướng dẫn:**
        - Chọn "Tra cứu công khai" để sử dụng tính năng tra cứu
        - Chọn "Đăng nhập" để truy cập chức năng Admin                 
        """)

# --- 5. Trang Admin Dashboard ---
def show_admin_dashboard():
    """Hiển thị trang Admin Dashboard"""
    
    # Sidebar cho Admin
    with st.sidebar:
        st.markdown("### ⚙️ Admin Menu")
        page = st.radio("Chọn chức năng:", 
                       ["📊 Thống kê tương đồng", "📁 Quản lý dữ liệu", "🚪 Đăng xuất"],
                       index=0)
        
        st.markdown("---")
        st.markdown(f"**Người dùng:** {st.session_state.username}")
        st.markdown(f"**Vai trò:** Admin")
    
    # --- Page 1: Thống kê tương đồng ---
    if page == "📊 Thống kê tương đồng":
        st.title("📊 Thống kê độ tương đồng")

        lookup_type = st.radio(
            "Chọn loại tra cứu:",
            options=["sangkien", "nckh"],
            format_func=lambda x: f"Tra cứu {LOOKUP_TYPE_CONFIG[x]['title']}",
            horizontal=True,
            key="admin_lookup_type"
        )
        meta = get_lookup_meta(lookup_type)
        cfg = meta['cfg']
        entity_label = meta['entity_label']
        entity_title = meta['entity_title']
        new_entity_col = meta['new_entity_col']
        old_entity_col = meta['old_entity_col']

        st.markdown(f"### Loại dữ liệu: **{entity_title}**")
        st.markdown(f"File dữ liệu cũ: **{cfg['old_file']}**")

        st.markdown(f"""
        Chức năng này cho phép bạn:
        1. Upload file Excel chứa các {entity_label} **MỚI**
        2. So sánh với {entity_label} **CŨ** trong cơ sở dữ liệu
        3. Xem bảng thống kê chi tiết mức độ tương đồng
        4. Xuất kết quả ra file Excel
        """)

        # Tải dữ liệu cũ
        old_data = prepare_database(cfg['old_file'], tuple(cfg['name_columns']))

        if old_data is None:
            st.error(
                f"❌ Không đọc được dữ liệu cũ từ '{cfg['old_file']}'. "
                f"Vui lòng kiểm tra file và cột tên phù hợp ({', '.join(cfg['name_columns'])})."
            )
            return

        old_df, _, _, _, _, old_name_col = old_data
        st.success(f"✅ Đã tải {len(old_df)} {entity_label} cũ từ cơ sở dữ liệu")

        # Upload file Excel mới
        st.markdown(f"### 📤 Bước 1: Upload file {entity_label} mới")
        uploaded_file = st.file_uploader(
            f"Chọn file Excel chứa {entity_label} mới:",
            type=['xls', 'xlsx'],
            key=f"admin_upload_{lookup_type}"
        )

        if uploaded_file is not None:
            try:
                # Lưu file tạm
                temp_path = os.path.join("uploads", uploaded_file.name)
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())

                # Đọc file mới với cơ chế tự dò dòng header
                detected_new = detect_dataframe_with_header(temp_path, cfg['name_columns'])
                if detected_new is None:
                    st.error(
                        "❌ File mới không có cột tên hợp lệ hoặc header không đúng vị trí. "
                        f"Cần một trong các cột: {', '.join(cfg['name_columns'])}"
                    )
                    return

                new_df, new_name_col, detected_header_row = detected_new

                st.caption(f"Đã tự nhận dòng tiêu đề: {detected_header_row + 1}")

                if new_name_col is None:
                    st.error(
                        "❌ File mới không có cột tên hợp lệ. "
                        f"Cần một trong các cột: {', '.join(cfg['name_columns'])}"
                    )
                    return

                new_df = new_df.dropna(subset=[new_name_col]).reset_index(drop=True)
                st.success(f"✅ Đã tải {len(new_df)} {entity_label} mới")

                # Hiển thị preview
                with st.expander("👀 Xem trước dữ liệu"):
                    st.dataframe(new_df[[new_name_col]].head(10))

                # Tính toán độ tương đồng
                st.markdown("### 🔄 Bước 2: Tính toán độ tương đồng")

                if st.button("🚀 Bắt đầu phân tích", key=f"analyze_btn_{lookup_type}"):
                    if old_name_col != new_name_col:
                        old_for_calc = old_df.rename(columns={old_name_col: 'lookup_name'})
                        new_for_calc = new_df.rename(columns={new_name_col: 'lookup_name'})
                        name_column = 'lookup_name'
                    else:
                        old_for_calc = old_df
                        new_for_calc = new_df
                        name_column = old_name_col

                    with st.spinner("Đang phân tích dữ liệu... (Đây có thể mất vài phút)"):
                        model = load_ai_model()
                        results = calculate_similarity_matrix(
                            old_for_calc,
                            new_for_calc,
                            model,
                            name_column,
                            new_entity_col,
                            old_entity_col
                        )

                    st.session_state.analysis_results_by_type[lookup_type] = results
                    st.session_state.analysis_meta_by_type[lookup_type] = {
                        'new_entity_col': new_entity_col,
                        'old_entity_col': old_entity_col,
                        'output_prefix': cfg['output_prefix']
                    }
                    st.success("✅ Phân tích hoàn tất!")

                # Hiển thị kết quả
                if lookup_type in st.session_state.analysis_results_by_type:
                    results = st.session_state.analysis_results_by_type[lookup_type]
                    analysis_meta = st.session_state.analysis_meta_by_type[lookup_type]

                    st.markdown("### 📋 Bước 3: Xem kết quả")

                    view_type = st.radio(
                        "Chế độ xem:",
                        ["📊 Bảng tóm tắt", "📈 Bảng chi tiết"],
                        horizontal=True,
                        key=f"view_type_{lookup_type}"
                    )

                    if view_type == "📊 Bảng tóm tắt":
                        summary_df = create_summary_dataframe(
                            results,
                            analysis_meta['new_entity_col'],
                            analysis_meta['old_entity_col']
                        )

                        level_order = {'Cao': 0, 'Trung bình': 1, 'Thấp': 2}
                        summary_df['sort_key'] = summary_df['Ghi chú'].map(level_order)
                        summary_df = summary_df.sort_values('sort_key').drop('sort_key', axis=1)

                        col_order = [analysis_meta['new_entity_col'], 'Độ tương đồng cao nhất']
                        for i in range(1, 6):
                            col_order.append(f'Top {i} - Tên')
                            col_order.append(f'Top {i} - Độ tương đồng')
                        col_order.append('Ghi chú')

                        summary_df = summary_df[col_order]
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)

                        st.markdown("### 📈 Thống kê nhanh:")
                        col1, col2, col3 = st.columns(3)

                        high_count = (summary_df['Ghi chú'] == 'Cao').sum()
                        mid_count = (summary_df['Ghi chú'] == 'Trung bình').sum()
                        low_count = (summary_df['Ghi chú'] == 'Thấp').sum()

                        with col1:
                            st.metric("🔴 Độ tương đồng Cao", high_count)
                        with col2:
                            st.metric("🟡 Độ tương đồng Trung bình", mid_count)
                        with col3:
                            st.metric("🟢 Độ tương đồng Thấp", low_count)

                    else:
                        detailed_df = create_detailed_dataframe(
                            results,
                            analysis_meta['new_entity_col'],
                            analysis_meta['old_entity_col']
                        )

                        st.markdown(
                            f"**📌 Lưu ý:** Dữ liệu được sắp xếp theo từng {entity_label} mới, "
                            f"trong mỗi nhóm các {entity_label} cũ được xếp từ độ tương đồng cao nhất xuống thấp nhất."
                        )

                        for new_item in detailed_df[analysis_meta['new_entity_col']].unique():
                            st.markdown(f"#### 🎯 **{new_item}**")

                            group_df = detailed_df[detailed_df[analysis_meta['new_entity_col']] == new_item][
                                [analysis_meta['old_entity_col'], 'Độ tương đồng', 'Ghi chú']
                            ].reset_index(drop=True)

                            group_df.insert(0, 'STT', range(1, len(group_df) + 1))
                            st.dataframe(group_df, use_container_width=True, hide_index=True)
                            st.markdown("")

                    st.markdown("### 💾 Bước 4: Xuất kết quả")

                    if st.button("💾 Xuất ra file Excel", key=f"export_btn_{lookup_type}"):
                        output_file = export_results_to_excel(
                            results,
                            analysis_meta['new_entity_col'],
                            analysis_meta['old_entity_col'],
                            output_prefix=analysis_meta['output_prefix']
                        )

                        with open(output_file, 'rb') as f:
                            st.download_button(
                                label="📥 Tải file Excel",
                                data=f.read(),
                                file_name=os.path.basename(output_file),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                        st.success(f"✅ Đã xuất kết quả: {output_file}")

            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")
    
    # --- Page 2: Quản lý dữ liệu ---
    elif page == "📁 Quản lý dữ liệu":
        st.title("📁 Quản lý dữ liệu")
        
        lookup_type = st.radio(
            "Chọn loại dữ liệu:",
            options=["sangkien", "nckh"],
            format_func=lambda x: LOOKUP_TYPE_CONFIG[x]['title'],
            horizontal=True,
            key="admin_manage_lookup_type"
        )
        meta = get_lookup_meta(lookup_type)
        cfg = meta['cfg']
        entity_label = meta['entity_label']
        data_file = cfg['old_file']

        st.markdown("### 🗂️ Tệp dữ liệu hiện tại")
        if os.path.exists(data_file):
            file_stat = os.stat(data_file)
            col_file_1, col_file_2, col_file_3 = st.columns(3)
            with col_file_1:
                st.metric("📄 Tên file", data_file)
            with col_file_2:
                st.metric("📦 Dung lượng", f"{file_stat.st_size / 1024:.1f} KB")
            with col_file_3:
                st.metric(
                    "🕒 Cập nhật lần cuối",
                    pd.to_datetime(file_stat.st_mtime, unit='s').strftime('%d/%m/%Y %H:%M')
                )

            with open(data_file, 'rb') as f:
                st.download_button(
                    label=f"📥 Download file dữ liệu hiện tại ({cfg['title']})",
                    data=f.read(),
                    file_name=os.path.basename(data_file),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"admin_download_data_{lookup_type}"
                )
        else:
            st.warning(
                f"⚠️ Chưa có file dữ liệu '{data_file}' cho {cfg['title']}. "
                "Vui lòng upload file mới bên dưới."
            )

        st.markdown("### 📤 Upload file mới")
        replacement_file = st.file_uploader(
            f"Chọn file Excel mới cho {cfg['title']} (sẽ ghi đè dữ liệu cũ):",
            type=['xls', 'xlsx'],
            key=f"admin_replace_data_{lookup_type}"
        )

        if st.button("📥 Lưu file mới", key=f"admin_save_replacement_{lookup_type}"):
            if replacement_file is None:
                st.warning("⚠️ Vui lòng chọn file trước khi lưu.")
            else:
                try:
                    with open(data_file, 'wb') as f:
                        f.write(replacement_file.getbuffer())

                    # Xóa cache để dữ liệu vừa thay thế được tải lại ngay.
                    prepare_database.clear()
                    st.session_state.analysis_results_by_type.pop(lookup_type, None)
                    st.session_state.analysis_meta_by_type.pop(lookup_type, None)

                    st.success(f"✅ Đã cập nhật dữ liệu thành công vào file '{data_file}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Không thể lưu file mới: {str(e)}")

        st.markdown("### 🗑️ Xóa dữ liệu cũ")
        confirm_delete = st.checkbox(
            f"Tôi xác nhận muốn xóa file '{data_file}'",
            key=f"admin_confirm_delete_{lookup_type}"
        )

        if st.button("🧹 Xóa file dữ liệu", key=f"admin_delete_data_{lookup_type}"):
            if not confirm_delete:
                st.warning("⚠️ Vui lòng tick xác nhận trước khi xóa dữ liệu.")
            elif not os.path.exists(data_file):
                st.info("ℹ️ File dữ liệu hiện tại không tồn tại.")
            else:
                try:
                    os.remove(data_file)
                    prepare_database.clear()
                    st.session_state.analysis_results_by_type.pop(lookup_type, None)
                    st.session_state.analysis_meta_by_type.pop(lookup_type, None)

                    st.success(f"✅ Đã xóa file dữ liệu '{data_file}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Không thể xóa file dữ liệu: {str(e)}")

        data = prepare_database(cfg['old_file'], tuple(cfg['name_columns']))

        if data is not None:
            df, _, _, _, _, _ = data

            author_col = get_first_existing_column(df, cfg['author_columns'])

            st.markdown("### 📊 Thông tin cơ sở dữ liệu")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"📚 Tổng {entity_label}", len(df))
            with col2:
                st.metric("👥 Số tác giả/chủ nhiệm", df[author_col].nunique() if author_col else 0)
            with col3:
                st.metric("📄 Cột dữ liệu", len(df.columns))

            st.markdown("### 📋 Dữ liệu chi tiết (mẫu 20 dòng đầu):")
            st.dataframe(df.head(20), use_container_width=True)

            st.markdown("### 📊 Thống kê cơ bản:")
            if author_col:
                author_stats_df = (
                    df[author_col]
                    .astype(str)
                    .str.strip()
                    .replace({'': np.nan, 'nan': np.nan, 'None': np.nan})
                    .dropna()
                    .value_counts()
                    .reset_index()
                )
                author_stats_df.columns = ['Tên tác giả', 'Số lượng']
                author_stats_df.insert(0, 'STT', range(1, len(author_stats_df) + 1))

                st.dataframe(author_stats_df, use_container_width=True, hide_index=True)
            else:
                st.info("Không tìm thấy cột tác giả/chủ nhiệm để thống kê.")
        else:
            st.info(
                f"ℹ️ Chưa thể đọc dữ liệu từ '{cfg['old_file']}'. "
                "Bạn có thể upload file mới ở mục phía trên."
            )
    
    # --- Page 3: Đăng xuất ---
    elif page == "🚪 Đăng xuất":
        if st.button("Xác nhận đăng xuất", key="logout_confirm"):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.username = None
            st.success("✅ Đã đăng xuất")
            st.rerun()

# --- 6. Trang Tra cứu công khai ---
def show_user_page():
    """Hiển thị trang tra cứu công khai"""
    
    st.title("🚀 Tra cứu Sáng kiến và Đề tài NCKH (Hybrid AI)")
    st.markdown("""
        Hệ thống sử dụng công nghệ **Hybrid Search**: Kết hợp giữa **Trí tuệ nhân tạo (AI)** để hiểu ngữ nghĩa 
        và **Đối soát từ khóa (TF-IDF)** để đảm bảo tìm chính xác các thuật ngữ chuyên môn như 'QR code', 'IoT', 'AI'...
    """)

    lookup_type = st.radio(
        "Chọn loại tra cứu:",
        options=["sangkien", "nckh"],
        format_func=lambda x: f"Tra cứu {LOOKUP_TYPE_CONFIG[x]['title']}",
        horizontal=True,
        key="user_lookup_type"
    )
    meta = get_lookup_meta(lookup_type)
    cfg = meta['cfg']
    entity_label = meta['entity_label']
    entity_title = meta['entity_title']
    
    # Sidebar
    with st.sidebar:
        if st.button("🚪 Đăng xuất", key="user_logout"):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.username = None
            st.rerun()
    
    # Tải dữ liệu
    data = prepare_database(cfg['old_file'], tuple(cfg['name_columns']))
    
    if data is None:
        st.error(
            f"❌ Không đọc được file '{cfg['old_file']}' cho {entity_title}. "
            f"Vui lòng kiểm tra tên file và cột dữ liệu."
        )
        return
    
    df, _, semantic_db, tfidf_vec, tfidf_db, name_col = data
    st.sidebar.success(f"📚 Cơ sở dữ liệu: {len(df)} {entity_label}")

    author_col = get_first_existing_column(df, cfg['author_columns'])
    note_col = get_first_existing_column(df, cfg['note_columns'])
    
    # Giao diện tra cứu
    with st.container():
        query = st.text_input(
            f"🔍 Nhập tên {entity_label} hoặc từ khóa cần tra cứu:",
            placeholder="Ví dụ: Giải pháp chuyển đổi số..."
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            top_k = st.slider("Số lượng kết quả hiển thị:", 5, 20, 10)
        with col2:
            ai_weight = st.slider("Độ ưu tiên AI vs Từ khóa:", 0.0, 1.0, 0.5, 0.1)
    
    # Hybrid Search
    if query:
        with st.spinner('Đang phân tích dữ liệu...'):
            model = load_ai_model()
            query_semantic = model.encode([query])
            semantic_scores = cosine_similarity(query_semantic, semantic_db)[0]
            
            query_tfidf = tfidf_vec.transform([query.lower()])
            tfidf_scores = cosine_similarity(query_tfidf, tfidf_db)[0]
            
            final_scores = (semantic_scores * ai_weight) + (tfidf_scores * (1 - ai_weight))
            
            top_indices = np.argsort(final_scores)[::-1][:top_k]
            
            st.markdown(f"### 📋 Kết quả Top {top_k} {entity_label} tương đồng nhất:")
            
            results = []
            for idx in top_indices:
                score = final_scores[idx] * 100
                if score > 0:
                    result_row = {
                        "Độ tương đồng": f"{score:.2f}%",
                        f"Tên {entity_label}": df.iloc[idx][name_col]
                    }

                    if author_col:
                        result_row["Tác giả/Chủ nhiệm"] = df.iloc[idx][author_col]

                    if note_col:
                        result_row["Ghi chú"] = df.iloc[idx][note_col]

                    results.append({
                        **result_row
                    })
            
            if results:
                res_df = pd.DataFrame(results)
                st.table(res_df)
                
                max_score = final_scores[top_indices[0]] * 100
                if max_score > 75:
                    st.error(
                        f"❗ Cảnh báo: Tìm thấy {entity_label} trùng khớp rất cao ({max_score:.1f}%). "
                        "Bạn nên kiểm tra kỹ tính mới."
                    )
                elif max_score > 40:
                    st.warning(f"⚠️ Lưu ý: Có sự tương đồng khá rõ ({max_score:.1f}%). Hãy điều chỉnh hướng tiếp cận để khác biệt hơn.")
                else:
                    st.success(f"✅ Chúc mừng: Nội dung của bạn có tính mới khá cao so với dữ liệu {entity_title.lower()} lịch sử.")
            else:
                st.info("Không tìm thấy kết quả nào trùng khớp.")

# --- 7. Main App Logic ---
if not st.session_state.logged_in:
    show_login_page()
elif st.session_state.user_role == "admin":
    show_admin_dashboard()
else:
    show_user_page()