# Xem suất chiếu và đặt nhiều ghế

Chạy `Main.py`. Chương trình mô phỏng khách mua vé bằng console, dùng chung
luồng chọn suất và ghế khi thao tác tại rạp hoặc ở nhà. Chưa có website,
thanh toán hay đồng bộ dữ liệu giữa nhiều máy.

## Ví dụ: đặt hai ghế phim A lúc 18:30

Khi chạy, chương trình tự đọc `cinema_data.txt` nằm cạnh `Main.py` và báo số
phim, suất chiếu, vé đã tải. Không cần chọn mục **10**. Mục này dùng để đọc
lại dữ liệu đã lưu trong lúc chương trình đang chạy.
Nếu file thiếu hoặc lỗi, chương trình thông báo và vẫn mở menu với dữ liệu trống.
Nếu chưa có, chuẩn bị dữ liệu như sau:

1. Chọn **1 – Add Movie with First Showtime**: mã `M01`, tên `Movie A`,
   thể loại `Comedy`, thời lượng `100`, năm `2026`, giá vé `75000`, trạng thái
   `Showing`. Ngay sau đó nhập suất đầu tiên: giờ `18:30 - 30/10/2026`, phòng
   `Room 1`, số hàng `2`, số ghế mỗi hàng `3`. Giá suất đầu tiên dùng giá vừa nhập.
2. Phim và suất được thêm cùng nhau, xuất hiện ngay ở mục **13**. Nếu suất đầu
   tiên không hợp lệ thì cả phim và suất đều chưa được lưu; có thể chọn mục 1 để nhập lại.
3. Muốn có thêm giờ chiếu, chọn **12**, nhập cùng mã phim `M01`, rồi nhập giờ
   `20:30 - 30/10/2026`, phòng, số hàng, số ghế mỗi hàng và giá của suất mới.

Các mục trên menu dùng chung **mã phim**. Mã suất trong dữ liệu được chương
trình quản lý tự động; người dùng chọn từng suất bằng số thứ tự của giờ chiếu.

Khách hàng thực hiện:

1. Chọn **13** để xem danh sách; nhập `M01`, chọn **1** (giờ 18:30) để xem ghế.
2. Chọn **4 – Book Tickets**; nhập `M01`, chọn **1** (giờ 18:30).
3. Nhập `A01,A02` để đặt hai ghế. Mỗi ghế có một mã vé riêng.
4. Kết quả hiển thị phim, ngày giờ, phòng, mã vé, ghế và tổng `150,000 VND`.
5. Chọn **13**, nhập `M01`, chọn **1**: hai ghế đã đặt hiển thị `[X]`.
   Nếu chọn **2** (giờ 20:30), hai ghế đó vẫn còn trống nếu chưa được đặt.
6. Chọn **9** để lưu trước khi thoát. Lần chạy tiếp theo dữ liệu tự được tải lại.

Sơ đồ trước khi đặt:

```text
SCREEN - [A01] = available, [X] = booked
[A01] [A02] [A03]
[B01] [B02] [B03]
```

Sơ đồ sau khi đặt:

```text
[X] [X] [A03]
[B01] [B02] [B03]
```

## Cách giải thích với giáo viên

### Phân biệt xóa phim và xóa suất chiếu

- **Mục 3** nhận mã phim, ví dụ `M00007` (Inception), và xóa phim cùng tất cả
  suất chiếu của phim đó nếu chưa có lịch sử vé.
- **Mục 14** cũng nhận mã phim, ví dụ `M00007`, rồi cho chọn số thứ tự của
  khung giờ cần xóa. Chỉ suất được chọn bị xóa; phim và các suất khác vẫn còn.
- Chọn **0** khi chọn giờ hoặc bỏ trống khi nhập mã phim để quay lại menu.
- Nếu xóa hết các suất, phim vẫn được liệt kê với thông báo chưa có suất chiếu;
  thêm giờ mới bằng mục **12** hoặc xóa cả phim bằng mục **3**.
- Phim hoặc suất có lịch sử vé, kể cả vé đã hủy, không được xóa để giữ dữ liệu.
- Dữ liệu tự tải khi mở chương trình. Chọn **9** để lưu kết quả sau khi xóa.

### Các đối tượng và quy tắc

- **Movie** lưu thông tin chung của phim.
- **Showtime** lưu mã phim, ngày giờ, phòng, số hàng, số ghế mỗi hàng và giá vé.
  Một phim có nhiều suất chiếu. Mã suất riêng được giữ bên trong để vé luôn
  gắn đúng giờ và phòng; giao diện chỉ yêu cầu người dùng nhập mã phim.
- **Ticket** lưu mã suất và ghế đã chọn, cùng giá tại thời điểm mua.
  Một suất có nhiều vé; một vé ứng với một ghế.
- Ghế trống = toàn bộ ghế của suất trừ các ghế có vé chưa hủy.
- Khi khách chọn nhiều ghế, kiểm tra tất cả trước khi lưu bất kỳ vé nào.
  Nếu một ghế sai hoặc đã được đặt, toàn bộ yêu cầu bị từ chối.
- Hủy vé giải phóng ghế trong đúng suất; vé đã Checked-In vẫn chiếm ghế.
- Doanh thu và số vé bán vẫn cộng theo phim, bao gồm các suất của phim đó.

Các phần chính: [Models.py](./Models.py), [Cinema_manager.py](./Cinema_manager.py),
[Console_io.py](./Console_io.py), [Main.py](./Main.py).

## Dữ liệu cũ và phạm vi mô phỏng

File cũ không có danh sách suất chiếu vẫn đọc được; vé cũ được giữ để thống kê.
Các trường `Movie.showtime`, `Movie.total_seats`, `Movie.ticket_price` còn giữ
để tương thích dữ liệu và chức năng cũ. Luồng đặt vé mới dùng sơ đồ ghế và giá
của `Showtime`. Mục 13 hiển thị các đối tượng `Showtime` thực tế, tránh hiện
giờ cũ sau khi xóa suất. Phim từ file cũ chưa có `Showtime` cần thêm suất bằng
mục 12 để đặt qua luồng mới. Vé cũ không tự động chuyển sang suất mới.

Đây là mô phỏng nghiệp vụ: chưa chặn suất đã qua giờ, chưa kiểm tra lịch phòng
bị chồng nhau và chưa xử lý nhiều khách đặt đồng thời trên các máy khác nhau.
