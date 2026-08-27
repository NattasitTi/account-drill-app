# Account Drill App
Risk Portfolio Analytics — Tidlor

## วิธี Deploy บน Databricks Apps

### Step 1: Environment Variables
ตั้งค่า environment variables ใน Databricks Apps:

| Variable | ค่า |
|---|---|
| `DATABRICKS_HOST` | `adb-3773489680991224.4.azuredatabricks.net` |
| `DATABRICKS_HTTP_PATH` | `/sql/1.0/warehouses/70d21945eb781e08` |
| `DATABRICKS_TOKEN` | Personal Access Token ของ user |

### Step 2: สร้าง App บน Databricks
1. Databricks UI → **Compute → Apps → Create App**
2. Source: GitHub → `https://github.com/NattasitTi/account-drill-app`
3. Branch: `main`
4. Entrypoint: `app.py`
5. ใส่ environment variables จาก Step 1
6. **Deploy**

### Step 3: แชร์ URL
หลัง deploy เสร็จจะได้ URL เช่น  
`https://account-drill-app-xxx.azuredatabricks.net`  
แชร์ URL นี้ให้ทีมได้เลย ไม่ต้องติดตั้งอะไร

## Source Table
`risk_dev.dev_stg_dbcube.tb_all_cube_test_v1`

## Features
- Dynamic filter ตาม dimension ทั้งหมดของ metric view
- Summary metrics ตาม measure ที่เลือก
- Ratio measures คำนวณอัตโนมัติ (%30+, %90+ ฯลฯ)
- Download Excel / CSV
- SQL preview สำหรับ debug
