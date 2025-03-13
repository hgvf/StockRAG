FROM python:3.12.3
WORKDIR /app

# 安裝 Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# 更新 Poetry 路徑
ENV PATH="${PATH}:/root/.local/bin"

# 複製 pyproject.toml 和 poetry.lock 到容器
COPY pyproject.toml poetry.lock* /app/

# 安裝相依套件
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev

RUN poetry install --no-root --verbose

# 複製剩餘的專案代碼
COPY . /app/

# 開放 API 端口，這裡假設使用 FastAPI 來提供服務
EXPOSE 8080

CMD ["/bin/bash"]