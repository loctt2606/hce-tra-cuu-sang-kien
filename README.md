# He thong Tra cuu Sang kien va De tai NCKH - Huong dan su dung

## Gioi thieu

He thong su dung cong nghe Hybrid AI Search de:
- Tra cuu cong khai theo 2 che do: Sang kien hoac De tai nghien cuu khoa hoc (NCKH).
- Admin thong ke do tuong dong giua du lieu moi va du lieu cu theo tung loai.
- Xuat ket qua chi tiet ra file Excel.

## Thong tin dang nhap

### Admin
- Username: admin
- Password: admin123
- Username: admin2
- Password: password123

### Nguoi dung thuong
- Chon "Tra cuu cong khai" de su dung tinh nang tim kiem.

## Huong dan cho Nguoi dung

1. Mo ung dung Streamlit.
2. Chon "Tra cuu cong khai".
3. Chon loai tra cuu:
- Sang kien
- De tai nghien cuu khoa hoc
4. Nhap ten hoac tu khoa can tra cuu.
5. Dieu chinh:
- So luong ket qua hien thi (5-20)
- Do uu tien AI vs Tu khoa (0-1)

Ket qua hien thi gom:
- Do tuong dong (%)
- Ten doi tuong (sang kien hoac de tai)
- Tac gia/Chu nhiem (neu co)
- Ghi chu (neu co)

Canh bao muc do:
- Cao (>75%): trung khop rat cao
- Trung binh (40-75%): co tuong dong dang ke
- Thap (<40%): tinh moi cao

## Huong dan cho Admin

### 1. Dang nhap
- Nhap username/password admin
- Chon "Dang nhap"

### 2. Chuc nang Thong ke tuong dong

Buoc 0: Chon loai du lieu
- Sang kien (du lieu cu mac dinh: list.xls)
- De tai NCKH (du lieu cu mac dinh: new.xls)

Buoc 1: Upload file moi
- File Excel can co cot ten phu hop voi loai da chon (vi du: TEN SANG KIEN, TEN DE TAI, ...)
- Header du lieu doc o dong tieu de thu 2

Buoc 2: Bam "Bat dau phan tich"
- He thong tinh toan do tuong dong voi du lieu cu

Buoc 3: Xem ket qua
- Bang tom tat
- Bang chi tiet
- Thong ke nhanh theo muc Cao/Trung binh/Thap

Buoc 4: Xuat Excel
- Ket qua luu trong thu muc outputs/
- Quy tac dat ten file:
- Sang kien: bat dau bang sk_
- De tai NCKH: bat dau bang nckh_

### 3. Chuc nang Quan ly du lieu
- Chon loai du lieu (Sang kien/NCKH)
- Xem tong so ban ghi, so tac gia/chu nhiem, va thong tin tong quan

## Co che tinh do tuong dong

He thong ket hop:
- Semantic AI (SentenceTransformer)
- TF-IDF (doi soat tu khoa)

Nguong muc do:
- Cao: >= 70%
- Trung binh: 40% den < 70%
- Thap: < 40%

## Cau truc file

- app.py: file Streamlit chinh
- admin_config.py: cau hinh admin va cau hinh loai tra cuu
- admin_utils.py: ham tien ich tinh do tuong dong va xuat bao cao
- list.xls: du lieu cu cho Sang kien
- new.xls: du lieu cu cho De tai NCKH
- uploads/: luu file upload tam
- outputs/: luu file ket qua xuat

## Cach chay

Cai thu vien:

pip install -r requirements.txt

Chay ung dung:

python -m streamlit run app.py

Truy cap:
- http://localhost:8501

## FAQ

Q: Co the doi nguong Cao/Trung binh/Thap khong?
A: Co. Sua ham get_similarity_level trong admin_utils.py.

Q: Neu file moi khong co cot ten dung thi sao?
A: He thong se bao loi. Can doi ten cot theo mot trong cac cot duoc cau hinh trong admin_config.py.

Q: Bao cao xuat ra gom gi?
A: 2 sheet:
- Tom tat
- Chi tiet

Version: 2.0
Last Updated: May 2026
