# Aff Video Tool — Video sản phẩm affiliate cho TikTok và Facebook

Tool này dùng để làm video giới thiệu sản phẩm từ ảnh sản phẩm do bạn gửi,
dạng dọc 9:16, đăng TikTok và Facebook Reels kèm link affiliate.

Không dùng login bằng cookie, không gọi API nội bộ của bất kỳ nền tảng nào.
Video được tạo trong chat với Muse, sau đó ghép bằng ffmpeg trong repo này.

## Thể loại chính

- Quần áo bộ trẻ em đời thường.
- Mẫu mặc sản phẩm, di chuyển tự nhiên trong đời sống hàng ngày.
- Studio cao cấp, boutique, flat-lay, góc nhà, móc treo trong cửa hàng.

## Quy tắc bắt buộc cho mọi video

- Giữ nguyên tuyệt đối hình ảnh sản phẩm trong ảnh tham chiếu:
  không đổi màu sắc, kiểu dáng, cổ áo, vị trí và hình dạng logo,
  họa tiết hay chi tiết khác.
- Không thêm phụ đề, không thêm chữ trong video, không thêm lời thoại
  hay thuyết minh, trừ khi bạn dặn cụ thể.
- Dạng dọc 9:16.
- Trong một video, chỉ dùng một nhân vật duy nhất xuyên suốt các cảnh.

## Giao diện web quản lý (Web Studio)

Repo có sẵn giao diện web quản lý, kiểu như Web Studio của repo bạn gửi trước đó,
nhưng chỉ chạy trên máy của bạn, không có đăng nhập, không gửi cookie hay key.

Chạy:

```bash
python3 web/server.py
python3 web/server.py --port 8080
```

Mở: http://127.0.0.1:8080

Các tab trong giao diện:

- **Tổng quan** — số prompt, số job, số job đã xong, số video kết quả,
  số ảnh nhân vật, và quy tắc bắt buộc.
- **Tạo video** — tải ảnh sản phẩm lên ngay trên giao diện (khung tải ảnh,
  kéo thả được, lưu vào `input/`), bấm vào ảnh để chọn cho job, rồi điền tên
  sản phẩm, chi tiết sản phẩm, chọn prompt, tạo job. Sau đó copy prompt của
  job đó vào chat với Muse, kèm ảnh sản phẩm và ảnh nhân vật, để tạo video.
  Video xong thì bỏ file vào `output/`, rồi bấm “Đã xong” cho job đó.
- **Nhân vật** — tải ảnh nhân vật chuẩn lên ngay trên giao diện (lưu vào
  `character-reference/`), xem trước và xoá ảnh ngay tại đó.
- **Kết quả** — xem trước và tải video trong `output/`.

Lưu ý: giao diện này quản lý job, prompt và kết quả. Nó không tự tạo video
bằng API ngoài, và không dùng cookie đăng nhập của bất kỳ nền tảng nào.
Video vẫn được tạo trong chat với Muse, rồi bạn lưu vào `output/`.

## Cách dùng

1. Tải ảnh sản phẩm lên ngay trên tab Tạo video (hoặc bỏ file vào `input/`,
   ví dụ `input/product.png`).
2. Tải ảnh nhân vật chuẩn của kênh lên ngay trên tab Nhân vật (hoặc bỏ file
   vào `character-reference/`, ví dụ `character-reference/character.png`).
   Nếu chưa có ảnh nhân vật, tạo cảnh đầu tiên rồi trích một khung hình
   rõ mặt làm ảnh nhân vật chuẩn, sau đó dùng ảnh đó cho mọi cảnh sau.
3. Chọn một prompt trong `prompts/`, thay đúng tên sản phẩm, cổ áo,
   logo và chi tiết trong ảnh của bạn.
4. Tạo từng đoạn video trong chat với Muse, dùng ảnh nhân vật trước,
   ảnh sản phẩm sau, rồi đến văn bản prompt.
5. Ghép các đoạn bằng script trong `scripts/`.

## Các dạng video có sẵn

- `prompts/01-store.md` — mẫu toàn thân trong cửa hàng quần áo trẻ em.
- `prompts/02-flatlay.md` — flat-lay sản phẩm, không có mẫu.
- `prompts/03-home-corner.md` — mẫu ở góc nhà đời thường.
- `prompts/04-hanger.md` — tay cầm móc treo bộ đồ trong cửa hàng.
- `prompts/05-natural-30s.md` — video 30 giây, 3 cảnh tự nhiên.
- `prompts/06-cool-montage-20s.md` — montage ngầu khoảng 20 giây,
  cắt nhanh 5 cảnh, mỗi cảnh 4 giây.
- `prompts/07-real-and-cool-30s.md` — vừa thật vừa ngầu, 30 giây.

## Ghép video bằng ffmpeg

Ghép 3 đoạn 10 giây thành video 30 giây:

```bash
./scripts/concat.sh output/video-30s.mp4 input/clip1.mp4 input/clip2.mp4 input/clip3.mp4
```

Ghép montage ngầu: cắt mỗi đoạn còn 4 giây, từ giây thứ 1, rồi ghép
thành khoảng 20 giây:

```bash
./scripts/montage.sh output/video-20s.mp4 input/clip1.mp4 input/clip2.mp4 input/clip3.mp4 input/clip4.mp4 input/clip5.mp4
```

Yêu cầu: đã cài `ffmpeg` trong PATH.

## Random bối cảnh và tình huống

Khi bạn muốn random, mỗi lần tạo phải bốc tổ hợp bối cảnh và tình huống
khác nhau, không lặp lại bộ vừa làm trước đó.

Bối cảnh có thể xoay vòng: công viên, sân chơi, gian hàng cửa hàng,
nhà sách, quán cà phê ngoài trời, phố đi bộ, ven biển, ven sông,
sân vườn, chợ, siêu thị, trung tâm thương mại, sân trường, thư viện,
khu dân cư.

Tình huống có thể xoay vòng: đi dạo tự nhiên, chạy nhẹ vui vẻ,
đứng nhìn quanh, nhìn hàng hóa trên kệ, nắm tay người lớn đi dạo,
chơi cầu trượt hoặc xích đu, ngồi nghỉ trên ghế đá, cầm đồ chơi nhìn quanh,
bước qua cầu nhỏ, đi dọc hàng cây.

## Bộ 3 video từ 1 sản phẩm

Khi bạn yêu cầu 3 video từ 1 sản phẩm, 3 video phải khác nhau ở cả 3 điểm:
bối cảnh, nhân vật và cách trình bày. Xem chi tiết trong `SKILL.md`.

## Thư mục

- `SKILL.md`, `skill.yaml` — quy tắc đầy đủ của tool.
- `prompts/` — mẫu prompt cho từng dạng video.
- `scripts/` — script ghép video bằng ffmpeg.
- `input/` — ảnh sản phẩm bạn đưa vào, không commit ảnh thật lên repo công khai
  nếu không muốn lộ sản phẩm.
- `character-reference/` — ảnh nhân vật chuẩn của kênh.
- `output/` — video đã ghép xong.

## Lưu ý

- Ảnh và video trong `input/`, `output/` và `character-reference/`
  đã được đưa vào `.gitignore`, trừ file `.gitkeep`.
- Đừng đưa cookie, mật khẩu, API key hay thông tin đăng nhập vào repo này.
