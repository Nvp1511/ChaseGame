# Hướng Dẫn Người Chơi ChaseGame (Windows)

Tài liệu này dành cho người dùng cuối: tải game ở đâu, mở game thế nào, và chơi ra sao.

## Tải game ở đâu?

Hiện tại dự án đang build tự động bằng GitHub Actions, đúng như bạn đang làm.

Bạn có 2 cách tải bản Windows:

1. **Cách 1 (khuyên dùng)**: Vào tab `Actions` trên GitHub, mở workflow `Build Windows Exe`, vào lần chạy mới nhất thành công, tải artifact `ChaseGame-windows-...`.
2. **Cách 2 (khi có gắn tag phát hành)**: Vào tab `Releases`, tải file zip bản mới nhất.

## Cách cài và mở game

1. Giải nén file zip vừa tải.
2. Mở thư mục đã giải nén.
3. Chạy file `ChaseGame.exe`.

Nếu Windows hiện cảnh báo SmartScreen:

1. Bấm `More info`.
2. Bấm `Run anyway`.

Đây là hành vi thường gặp với file `.exe` chưa được code-sign.

## Cách chơi nhanh

### Chế độ PvE (chơi vs AI)

1. Điều khiển nhân vật bằng phím `W A S D`.
2. Ăn chấm vàng để tăng tiến độ mục tiêu.
3. Ăn ô xanh để tăng tốc trong một khoảng thời gian.
4. Né đội AI truy đuổi đến hết giờ hoặc hoàn thành mục tiêu để thắng.

### Chế độ PvP (chơi vs người chơi khác)

1. **Player 1**: `W A S D`.
2. **Player 2**: Phím mũi tên.
3. **Vai trò**:
   - `[D]` là người đuổi.
   - `[C]` là người chạy.
4. Chạm đối thủ để đổi vai.
5. Ăn ô xanh để tăng tốc (có thể cộng dồn thời gian buff).

## Lời khuyên khi sử dụng

1. Nên chạy game ở chế độ pin tối đa (nếu dùng laptop) để khung hình ổn định hơn.
2. Nếu không nghe thấy âm thanh, vào `Cài Đặt` trong game để kiểm tra thanh volume.
3. Nếu game không mở được, thử tải lại bản build mới nhất từ `Actions`.

## Dành cho nhóm phát triển

Workflow build hiện tại:

1. Tự động chạy khi push lên `main` hoặc khi tạo tag `v*`.
2. Tạo các tệp:
   - `ChaseGame.exe`
   - `ChaseGame-<version>-windows.zip`
   - `SHA256SUMS.txt`
3. Nếu push tag `v*`, workflow sẽ tạo GitHub Release kèm các tệp trên.
