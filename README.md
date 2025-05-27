# StockRAG
## Usage
```shell=
docker-compose up
```

* Collect data
```shell=
cd collect_data/
python collect.py --start_date <start of date, YYYY-MM-DD> --subset <TW/US>
```

* Activate the telegram bot
```shell=
python main.py
```

---
## Demo1: 依照個股股價趨勢 query
<img src="https://github.com/user-attachments/assets/a3d314e1-f8b7-465a-a92a-ff9250ebb4c0" width="500" height=500/>

## Demo2: 依照個股成交量趨勢 query
<img src="https://github.com/user-attachments/assets/46ec57fe-4c7d-43a4-84a0-ebda91a1772b" width="500" height=500/>


