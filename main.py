import asyncio
from datetime import datetime, time, timedelta, timezone
import json
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import httpx
from sse_starlette.sse import EventSourceResponse

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SPX-Hub")

COOKIE_FILE = "cookies.json"
SPX_API_URL = "https://spx.shopee.vn/api/fleet_order/order/tracking_list/search"
FORECAST_STATUS = "39,591,8,9,33,34,35,15,36"

# Định nghĩa múi giờ Việt Nam (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))

# --- TẢI COOKIE TỪ FILE JSON ---
def load_cookies() -> dict:
if os.path.exists(COOKIE_FILE):
try:
with open(COOKIE_FILE, "r", encoding="utf-8") as f:
logger.info("Đã tải cookie từ file cache cục bộ thành công.")
return json.load(f)
except Exception as e:
logger.warning(f"Lỗi đọc file cookie: {e}")

logger.error("Không tìm thấy file cookies.json! Hãy chắc chắn bạn đã upload file này lên GitHub.")
return {}

SPX_COOKIES = load_cookies()
SPX_HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
"Content-Type": "application/json",
"Referer": "https://spx.shopee.vn/",
"X-Csrftoken": SPX_COOKIES.get("csrftoken", ""),
}

# --- ZONES ---
ZONES_KV1_STR = "Z1.02.BH.01,Z1.01.CQ.01,Z1.01.CQ.02,Z1.01.CLỚN.01,Z1.01.AĐ.04,Z1.01.CQ.03,Z1.01.AĐ.05,Z1.01.AĐ.02,Z1.01.AĐ.01,Z1.01.AĐ.03,Z1.01.CLỚN.05,Z1.01.CLỚN.06,Z1.01.CLỚN.02,Z1.01.CLỚN.03,Z1.02.BTIÊN.01,Z1.02.BTÂY.02,Z1.02.BTÂY.01,Z1.02.BTÂY.03,Z1.02.PL.03,Z1.02.PL.02,Z1.02.PL.01,Z1.01.BP.03,Z1.02.BTIÊN.04,Z1.01.BP.02,Z1.01.BP.01,Z1.02.BTIÊN.05,Z1.02.BTIÊN.02,Z1.02.BTIÊN.03,Z1.01.BP.04,Z1.02.PĐ.05,Z1.02.PĐ.04,Z1.02.BĐ.02,Z1.02.BĐ.01,Z1.02.PĐ.03,Z1.02.PĐ.02,Z1.02.PĐ.01,Z1.02.CH.08,Z1.02.CH.01,Z1.02.CH.02,Z1.02.CH.03,Z1.01.PT.05,Z1.02.CH.04,Z1.01.MP.03,Z1.01.CLỚN.04,Z1.01.MP.04,Z1.01.PT.04,Z1.01.PT.02,Z1.01.HB.01,Z1.01.HB.02,Z1.01.BTHỚI.03,Z1.01.BTHỚI.02,Z1.01.PT.03,Z1.01.MP.01,Z1.01.MP.06,Z1.01.MP.02,Z1.01.BTHỚI.01,Z1.01.MP.05,Z1.02.BH.02,Z1.02.CH.07,Z1.02.CH.06,Z1.01.BTHỚI.04,Z1.02.BĐ.03"
ZONES_KV2_STR = "Z2.02.TB.01,Z2.02.TĐ.01,Z2.02.TĐ.02,Z2.02.LX.01,Z2.02.TB.02,Z2.02.TB.03,Z2.02.TĐ.05,Z2.02.HB.02,Z2.02.CK.02,Z2.02.CK.03,Z2.02.ĐN.01,Z2.02.ĐN.02,Z2.02.ĐN.03,Z2.02.PN.02,Z2.02.CK.04,Z2.02.CK.01,Z2.02.CK.05,Z2.02.PN.04,Z2.02.PN.03,Z2.02.PN.05,Z2.01.TH.03,Z2.01.BH.01,Z2.01.TH.02,Z2.01.TH.01,Z2.01.TSN.03,Z2.01.BH.02,Z2.01.TB.02,Z2.01.TSN.02,Z2.01.TSH.03,Z2.01.TSH.01,Z2.01.TSH.02,Z2.01.TSN.01,Z2.01.BH.03,Z2.01.TB.01,Z2.01.TB.03,Z2.02.PN.01,Z2.02.LX.03,Z2.02.LX.02,Z2.02.HB.01.A,Z2.02.HB.01.C,Z2.02.HB.01.B,Z2.02.HB.01.D,Z2.02.HB.01.E,Z2.02.HB.03.A,Z2.02.HB.03.B"

app = FastAPI(title="SPX Hub Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

cache_store = {"data": None, "expire_time": datetime.min.replace(tzinfo=VIETNAM_TZ)}

async def fetch_api(client, payload):
try:
response = await client.post(SPX_API_URL, json=payload, cookies=SPX_COOKIES, headers=SPX_HEADERS, timeout=15.0)
if response.status_code == 200:
res = response.json()
data = res.get("data", {})
return data.get("total_count", data.get("total", 0)), data.get("list", []) or data.get("orders", [])
else:
logger.warning(f"SPX API trả về mã lỗi: {response.status_code}")
except Exception as e:
logger.error(f"API Error: {e}")
return 0, []

async def get_latest_data():
# Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)
now = datetime.now(VIETNAM_TZ)
if cache_store["data"] and now < cache_store["expire_time"]:
return cache_store["data"]

start = int(datetime.combine(now.date(), time.min).replace(tzinfo=VIETNAM_TZ).timestamp())
end = int(datetime.combine(now.date(), time.max).replace(tzinfo=VIETNAM_TZ).timestamp())
time_str = f"{start},{end}"

async with httpx.AsyncClient() as client:
async def get_count(status, zone):
p = {"count": 1, "current_station_ids": "4232", "order_status": status, "page_no": 1, "zone_id": zone, "current_station_received_time": time_str}
total, _ = await fetch_api(client, p)
return total

async def get_forecast_count(status, zone, pickup_ids):
p = {"count": 1, "station_ids": "4232", "order_status": status, "page_no": 1, "zone_id": zone, "pickup_station_ids": pickup_ids}
total, _ = await fetch_api(client, p)
return total

async def get_inv(zone):
un, att, page = 0, 0, 1
while True:
p = {"count": 100, "current_station_ids": "4232", "current_station_received_time": time_str, "order_status": "1", "page_no": page, "zone_id": zone}
_, orders = await fetch_api(client, p)
if not orders: break
for o in orders:
if o.get("on_hold_times", 0) == 0: un += 1
else: att += 1
if len(orders) < 100: break
page += 1
return un, att

async def get_drivers_detail(zone):
drivers = {}
page = 1
while True:
p = {"count": 100, "current_station_ids": "4232", "current_station_received_time": time_str, "order_status": "2,4,5", "page_no": page, "zone_id": zone}
_, orders = await fetch_api(client, p)
if not orders: break
for o in orders:
d_id = str(o.get("driver_id", ""))
if not d_id or d_id == "None": continue
if d_id not in drivers:
drivers[d_id] = {"id": d_id, "ten": o.get("driver_name") or f"DRV {d_id}", "dang_giao": 0, "onhold": 0, "thanh_cong": 0}
st = str(o.get("order_status", ""))
if st == "2": drivers[d_id]["dang_giao"] += 1
elif st == "5": drivers[d_id]["onhold"] += 1
elif st == "4": drivers[d_id]["thanh_cong"] += 1
if len(orders) < 100: break
page += 1
return list(drivers.values())

res = await asyncio.gather(
get_count("2,4,5", ZONES_KV1_STR), get_count("2,4,5", ZONES_KV2_STR),
get_inv(ZONES_KV1_STR), get_inv(ZONES_KV2_STR),
get_forecast_count(FORECAST_STATUS, ZONES_KV1_STR, "1997,4289"), get_forecast_count(FORECAST_STATUS, ZONES_KV2_STR, "1997,4289"),
get_forecast_count(FORECAST_STATUS, ZONES_KV1_STR, "4232"), get_forecast_count(FORECAST_STATUS, ZONES_KV2_STR, "4232"),
get_drivers_detail(ZONES_KV1_STR), get_drivers_detail(ZONES_KV2_STR)
)

data = {
"ten_hub": "52-HCM SDD-01 Hub",
"tong_don_giao_kv1": res[0], "tong_don_giao_kv2": res[1],
"tong_don_ton_kho_chua_attem_kv1": res[2][0], "tong_don_ton_kho_da_attem_kv1": res[2][1],
"tong_don_ton_kho_chua_attem_kv2": res[3][0], "tong_don_ton_kho_da_attem_kv2": res[3][1],
"du_bao_warehouse_kv1": res[4], "du_bao_warehouse_kv2": res[5],
"du_bao_pickup_kv1": res[6], "du_bao_pickup_kv2": res[7],
"drivers_detail_kv1": res[8], "drivers_detail_kv2": res[9],
"thoi_gian_cap_nhat": now.strftime("%H:%M:%S")
}
cache_store.update({"data": data, "expire_time": now + timedelta(seconds=300)})
return data

@app.get("/", response_class=FileResponse)
async def serve_index():
if os.path.exists("index.html"):
return FileResponse("index.html")
return HTMLResponse("<h1>Không tìm thấy file index.html trên hệ thống!</h1>", status_code=404)

@app.get("/drivers-view", response_class=FileResponse)
async def serve_drivers_view():
if os.path.exists("index.html"):
return FileResponse("index.html")
return HTMLResponse("<h1>Không tìm thấy file index.html trên hệ thống!</h1>", status_code=404)

@app.get("/api/dashboard")
async def dashboard(): 
return await get_latest_data()

@app.get("/api/stream")
async def stream(request: Request):
async def gen():
while not await request.is_disconnected():
latest_data = await get_latest_data()
yield {"event": "update", "data": json.dumps(latest_data, ensure_ascii=False)}
            await asyncio.sleep(5)
            await asyncio.sleep(360)
return EventSourceResponse(gen())

if __name__ == "__main__":
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)
