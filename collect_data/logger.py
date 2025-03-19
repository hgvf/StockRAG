import logging
import os

def setLogger(subset):
    """
    Set Logger
    """

    LOG_DIR = "logs"
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("rag_app_collection")
    logger.setLevel(logging.DEBUG)  # 設定最低日誌級別

    # 建立 Formatter (設定日誌格式)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 建立檔案處理器 (寫入 log 檔案)
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, f"{subset}_Collections.log"))
    file_handler.setLevel(logging.INFO)  # 只記錄 INFO 以上的日誌
    file_handler.setFormatter(formatter)

    # 建立控制台處理器 (輸出到 console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 允許 DEBUG 以上的日誌
    console_handler.setFormatter(formatter)

    # 加入處理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger