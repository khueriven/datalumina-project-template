import os
import datetime
import sys
sys.path.append('C:\Khue\H9_Solar_Power_Forecasting\src')
from image_processing import crop_and_resize_image


def batch_process_images(base_input_path, base_output_path, plant_name):
    """
    Lặp qua các thư mục ngày (20250101 - 20250314), thư mục giờ (0000 - 0550, cách 10 phút)
    và xử lý tất cả ảnh trong mỗi thư mục.
    
    Parameters:
    - base_input_path (str): Thư mục gốc chứa ảnh đầu vào.
    - base_output_path (str): Thư mục gốc chứa ảnh đầu ra.
    - plant_name (str): Tên nhà máy cần xử lý.
    """
    
    # 1️⃣ Tạo danh sách các ngày từ 20250101 đến 20250314
    start_date = datetime.date(2025, 1, 1)
    end_date = datetime.date(2025, 3, 14)
    date_list = [(start_date + datetime.timedelta(days=i)).strftime("%Y%m%d") 
                 for i in range((end_date - start_date).days + 1)]

    # 2️⃣ Lặp qua từng ngày
    for date_folder in date_list:
        date_path = os.path.join(base_input_path, date_folder)
        if not os.path.exists(date_path):
            continue  # Bỏ qua nếu thư mục không tồn tại

        print(f"📂 Đang xử lý ngày: {date_folder}")

        # 3️⃣ Lặp qua từng thư mục giờ (0000 - 0550, tăng 10 phút)
        # Lặp qua tất cả thư mục giờ trong ngày
        for time_folder in os.listdir(date_path):
                time_path = os.path.join(date_path, time_folder)

                if not os.path.exists(time_path):
                    continue  # Bỏ qua nếu thư mục không tồn tại

                print(f"  🕒 Đang xử lý thư mục giờ: {time_folder}")

                # 4️⃣ Lặp qua tất cả ảnh trong thư mục
                for image_file in os.listdir(time_path):
                    if image_file.lower().endswith(('.jpg', '.png', '.tif', '.jpeg')):  # Chỉ xử lý file ảnh
                        image_path = os.path.join(time_path, image_file)

                        try:
                            # Gọi hàm xử lý ảnh
                            output_path = crop_and_resize_image(image_path, plant_name, base_input_path, base_output_path)
                            
                            if output_path:
                                print(f"    ✅ Đã xử lý: {image_file} -> {output_path}")
                        except Exception as e:
                            print(f"    ⚠️ Không thể xử lý ảnh {image_file}: {str(e)}")
                        continue

    print("🎉 Hoàn thành xử lý tất cả ảnh!")

# ---- Gọi hàm chạy ----
base_input_path = r"X:\Sky-image\Data"
base_output_path = r"Z:\Sky-image\namnvn\Data_process"
plant_name = "MT Solarpark 1"

batch_process_images(base_input_path, base_output_path, plant_name)
