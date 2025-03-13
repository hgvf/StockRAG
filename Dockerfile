FROM python:3.8
WORKDIR /app

# 更新 Poetry 路徑
ENV PATH="${PATH}:/root/.local/bin"

# 複製剩餘的專案代碼
COPY . /app/

RUN apt-get update -y
RUN apt-get install python3-pip -y
RUN pip install --upgrade pip setuptools wheel
# RUN pip3 install torch torchvision torchaudio 
RUN pip install -r requirements.txt 


# 開放 API 端口，這裡假設使用 FastAPI 來提供服務
EXPOSE 8080

CMD ["/bin/bash"]