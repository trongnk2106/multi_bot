# Sử dụng một base image có Python 3.9
FROM python:3.9


COPY . /app
# Thiết lập thư mục làm việc trong image
WORKDIR /app

# Cài đặt các dependency
RUN pip install --no-cache-dir -r requirements.txt

# Mở cổng 8000 để lắng nghe các kết nối
EXPOSE 8000

# Khởi chạy ứng dụng FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]