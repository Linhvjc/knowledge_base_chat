# Bước 1: Chọn một base image nhẹ và chính thức từ Python
# python:3.11-slim là một lựa chọn tốt vì nó nhỏ gọn.
FROM python:3.11-slim

# Bước 2: Thiết lập thư mục làm việc bên trong container
# Tất cả các lệnh sau đó sẽ được thực thi trong thư mục /code
WORKDIR /code

# Bước 3: Cài đặt các thư viện cần thiết
# Copy file requirements.txt trước để tận dụng Docker layer caching.
# Nếu file này không thay đổi, Docker sẽ không cần chạy lại bước này, giúp build nhanh hơn.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Bước 4: Copy toàn bộ code của ứng dụng vào container
# Dấu "." đầu tiên là thư mục gốc của dự án (nơi có Dockerfile)
# Dấu "." thứ hai là thư mục làm việc hiện tại trong container (/code)
COPY ./app /code/app

# Bước 5: Chạy ứng dụng FastAPI bằng Uvicorn
# --host 0.0.0.0 là rất quan trọng để ứng dụng có thể được truy cập từ bên ngoài container.
# --port 8000 là cổng mà ứng dụng sẽ lắng nghe bên trong container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]