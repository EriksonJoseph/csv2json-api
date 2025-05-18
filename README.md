# csv2json
## How to run
### สร้าง Virtual environment
```zsh
python -m venv venv
```
### เปิดใช้งาน Virtual environment
Windows
```shell
python -m venv venv
```
Mac
```zsh
source venv/bin/activate
```

### ติดตั้ง Dependencies
```zsh
pip install fastapi ubicorn pandas
```

### สร้างไฟล์ Environment
```zsh
cp .env.example .env
```

### Run!
```zsh
uvicorn main:app --replad
```

