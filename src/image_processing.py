import pandas as pd
from PIL import Image
import math
import os


def find_file(filename):
    """
    Tìm file theo tên trong tất cả các ổ đĩa trên hệ thống (C, D, E, ...)
    """
    drives = [
        f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")
    ]

    for drive in drives:
        for root, _, files in os.walk(drive):
            if filename in files:
                return os.path.join(root, filename)

    return None  # Trả về None nếu không tìm thấy


def crop_and_resize_image(image_path, plant_name, base_input_path, base_output_path):
    """
    Cắt ảnh để bao trọn ô vuông của nhà máy, sau đó mở rộng ảnh theo scale_factor.

    Parameters:
    - image_path (str): Đường dẫn ảnh gốc.
    - plant_name (str): Tên nhà máy cần xử lý.
    - base_input_path (str): Thư mục gốc chứa ảnh đầu vào.
    - base_output_path (str): Thư mục gốc chứa ảnh đầu ra.
    - scale_factor (int): Hệ số phóng to ảnh (mặc định là 10 lần).

    Returns:
    - str: Đường dẫn ảnh sau khi xử lý.
    """

    # 1. Đọc dữ liệu nhà máy
    csv_filename = "thongtintinh_farm.csv"
    csv_path = find_file(csv_filename)

    if csv_path is None:
        print(f"Không tìm thấy file {csv_filename} trong hệ thống!")
        return None

    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["VIDO", "KINHDO"])  # Loại bỏ dòng không có lat/lon

    # 2. Lọc dữ liệu theo nhà máy
    plant_data = df[df["TEN_NM"] == plant_name]

    if plant_data.empty:
        print(f"Không tìm thấy nhà máy '{plant_name}' trong dữ liệu.")
        return None

    # 3️⃣ Mở ảnh
    img = Image.open(image_path)
    width, height = img.size

    # 4️⃣ Xác định khung tọa độ
    min_lon, max_lon = 80, 115
    max_lat, min_lat = 30, 0

    # Hàm chuyển đổi tọa độ lat/lon sang pixel
    def latlon_to_pixel(
        lat,
        lon,
        min_lon=min_lon,
        max_lon=max_lon,
        min_lat=min_lat,
        max_lat=max_lat,
        img_width=width,
        img_height=height,
    ):
        # Kinh độ nội suy theo chiều ngang
        x = (lon - min_lon) / (max_lon - min_lon) * img_width
        # Vĩ độ nội suy theo chiều dọc (lưu ý: y tăng từ trên xuống)
        y = (max_lat - lat) / (max_lat - min_lat) * img_height
        return x, y

    # Hàm tính khoảng cách lat/lon từ km
    def compute_delta_lat(km):
        return km / 111

    def compute_delta_lon(lat, km):
        return km / (111 * math.cos(math.radians(lat)))

    # 5️⃣ Xác định vùng crop
    half_side_km = 50  # Bán kính 50km từ trung tâm

    for _, row in plant_data.iterrows():
        lat_center, lon_center = row["VIDO"], row["KINHDO"]
        x_center, y_center = latlon_to_pixel(lat_center, lon_center)

        d_lat = compute_delta_lat(half_side_km)
        d_lon = compute_delta_lon(lat_center, half_side_km)

        lat_north, lat_south = lat_center + d_lat, lat_center - d_lat
        lon_west, lon_east = lon_center - d_lon, lon_center + d_lon

        x_nw, y_nw = latlon_to_pixel(lat_north, lon_west)
        x_ne, y_ne = latlon_to_pixel(lat_north, lon_east)
        x_sw, y_sw = latlon_to_pixel(lat_south, lon_west)
        x_se, y_se = latlon_to_pixel(lat_south, lon_east)

        x_min = min(x_nw, x_ne, x_sw, x_se)
        y_min = min(y_nw, y_ne, y_sw, y_se)
        x_max = max(x_nw, x_ne, x_sw, x_se)
        y_max = max(y_nw, y_ne, y_sw, y_se)

        # # Vẽ ô vuông
        # draw.rectangle([x_min, y_min, x_max, y_max])

    # 6️⃣ Hàm crop ảnh
    def crop_square(img, x_min, y_min, x_max, y_max):
        W, H = img.size
        bbox_w = x_max - x_min
        bbox_h = y_max - y_min

        side = max(bbox_w, bbox_h)  # cạnh hình vuông
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2

        side = int(math.ceil(side))  # làm tròn lên để chắc chắn không cắt mất
        if side > W or side > H:
            print("Vùng crop yêu cầu lớn hơn kích thước ảnh! Giữ nguyên ảnh.")
            return img

        # Tính toạ độ ban đầu
        crop_xmin = int(cx - side / 2)
        crop_ymin = int(cy - side / 2)
        crop_xmax = crop_xmin + side
        crop_ymax = crop_ymin + side

        # Dời nếu tràn
        if crop_xmin < 0:
            shift = -crop_xmin
            crop_xmin = 0
            crop_xmax += shift
        if crop_xmax > W:
            shift = crop_xmax - W
            crop_xmax = W
            crop_xmin -= shift
        if crop_ymin < 0:
            shift = -crop_ymin
            crop_ymin = 0
            crop_ymax += shift
        if crop_ymax > H:
            shift = crop_ymax - H
            crop_ymax = H
            crop_ymin -= shift

        # Đảm bảo vẫn vuông (nếu có lệch 1 pixel do làm tròn, ta điều chỉnh)
        final_w = crop_xmax - crop_xmin
        final_h = crop_ymax - crop_ymin
        if final_w != final_h:
            side2 = min(final_w, final_h)
            crop_xmax = crop_xmin + side2
            crop_ymax = crop_ymin + side2

        return img.crop((crop_xmin, crop_ymin, crop_xmax, crop_ymax))

    # 7️⃣ Cắt ảnh & phóng to
    cropped_img = crop_square(img, x_min, y_min, x_max, y_max)
    resized_img = cropped_img.resize(
        (cropped_img.size[0] * 25, cropped_img.size[1] * 25),
        Image.LANCZOS,
    )

    # 8️⃣ Xây dựng đường dẫn lưu ảnh
    relative_path = os.path.relpath(
        image_path, base_input_path
    )  # VD: "20250314\0000\image1.jpg"
    output_dir = os.path.join(
        base_output_path,
        plant_name.upper().replace(" ", "_"),
        os.path.dirname(relative_path),
    )
    output_path = os.path.join(output_dir, os.path.basename(image_path))

    # 9️⃣ Tạo thư mục nếu chưa có & lưu ảnh
    os.makedirs(output_dir, exist_ok=True)
    resized_img.save(output_path)
    print(f"✅ Ảnh đã lưu tại: {output_path}")

    return output_path
