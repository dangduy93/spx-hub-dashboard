import asyncio
from datetime import datetime, time, timedelta, timezone
import json
import logging
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
from sse_starlette.sse import EventSourceResponse

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("SPX-Hub")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(BASE_DIR, "cookies.json")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
SPX_API_URL = "https://spx.shopee.vn/api/fleet_order/order/tracking_list/search"
DELIVERY_API_URL = (
    "https://spx.shopee.vn/api/driverservice/admin/performance/delivery/report/list"
)
PICKUP_API_URL = (
    "https://spx.shopee.vn/api/driverservice/admin/performance/pickup/report/list"
)
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

  logger.error(
      "Không tìm thấy file cookies.json! Hãy chắc chắn bạn đã upload file này"
      " lên."
  )
  return {}


SPX_COOKIES = load_cookies()
SPX_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Referer": "https://spx.shopee.vn/",
    "X-Csrftoken": SPX_COOKIES.get("csrftoken", ""),
}

# --- ZONES ---
ZONES_KV1_STR = (
    "Z1.02.BH.01,Z1.01.CQ.01,Z1.01.CQ.02,Z1.01.CLỚN.01,Z1.01.AĐ.04,Z1.01.CQ.03,Z1.01.AĐ.05,Z1.01.AĐ.02,Z1.01.AĐ.01,Z1.01.AĐ.03,Z1.01.CLỚN.05,Z1.01.CLỚN.06,Z1.01.CLỚN.02,Z1.01.CLỚN.03,Z1.02.BTIÊN.01,Z1.02.BTÂY.02,Z1.02.BTÂY.01,Z1.02.BTÂY.03,Z1.02.PL.03,Z1.02.PL.02,Z1.02.PL.01,Z1.01.BP.03,Z1.02.BTIÊN.04,Z1.01.BP.02,Z1.01.BP.01,Z1.02.BTIÊN.05,Z1.02.BTIÊN.02,Z1.02.BTIÊN.03,Z1.01.BP.04,Z1.02.PĐ.05,Z1.02.PĐ.04,Z1.02.BĐ.02,Z1.02.BĐ.01,Z1.02.PĐ.03,Z1.02.PĐ.02,Z1.02.PĐ.01,Z1.02.CH.08,Z1.02.CH.01,Z1.02.CH.02,Z1.02.CH.03,Z1.01.PT.05,Z1.02.CH.04,Z1.01.MP.03,Z1.01.CLỚN.04,Z1.01.MP.04,Z1.01.PT.04,Z1.01.PT.02,Z1.01.HB.01,Z1.01.HB.02,Z1.01.BTHỚI.03,Z1.01.BTHỚI.02,Z1.01.PT.03,Z1.01.MP.01,Z1.01.MP.06,Z1.01.MP.02,Z1.01.BTHỚI.01,Z1.01.MP.05,Z1.02.BH.02,Z1.02.CH.07,Z1.02.CH.06,Z1.01.BTHỚI.04,Z1.02.BĐ.03"
)
ZONES_KV2_STR = (
    "Z2.02.TB.01,Z2.02.TĐ.01,Z2.02.TĐ.02,Z2.02.LX.01,Z2.02.TB.02,Z2.02.TB.03,Z2.02.TĐ.05,Z2.02.HB.02,Z2.02.CK.02,Z2.02.CK.03,Z2.02.ĐN.01,Z2.02.ĐN.02,Z2.02.ĐN.03,Z2.02.PN.02,Z2.02.CK.04,Z2.02.CK.01,Z2.02.CK.05,Z2.02.PN.04,Z2.02.PN.03,Z2.02.PN.05,Z2.01.TH.03,Z2.01.BH.01,Z2.01.TH.02,Z2.01.TH.01,Z2.01.TSN.03,Z2.01.BH.02,Z2.01.TB.02,Z2.01.TSN.02,Z2.01.TSH.03,Z2.01.TSH.01,Z2.01.TSH.02,Z2.01.TSN.01,Z2.01.BH.03,Z2.01.TB.01,Z2.01.TB.03,Z2.02.PN.01,Z2.02.LX.03,Z2.02.LX.02,Z2.02.HB.01.A,Z2.02.HB.01.C,Z2.02.HB.01.B,Z2.02.HB.01.D,Z2.02.HB.01.E,Z2.02.HB.03.A,Z2.02.HB.03.B"
)

# --- DANH SÁCH ID TÀI XẾ CỐ ĐỊNH (KV1 & KV2) ---
KV1_DRIVER_IDS = set(
    x.strip()
    for x in """
    113707, 113957, 114100, 114334, 114467, 114468, 114472, 114475, 114749, 114916, 115111, 115444, 115449, 115456, 116422, 116424, 116429, 116697, 117631, 117633,
    117908, 117910, 117911, 117912, 119086, 121878, 122070, 122662, 123654, 123878, 124220, 124302, 124303, 124305, 124469, 126787, 128151, 128461, 128922, 129105,
    129361, 129548, 129916, 130264, 132664, 132836, 132957, 133311, 133970, 134459, 135685, 136141, 136314, 136316, 138133, 138575, 138589, 138924, 139234, 139708,
    139715, 140071, 140800, 141097, 141379, 141383, 141386, 141388, 141390, 141622, 141629, 141633, 141975, 142322, 142347, 142555, 142670, 142675, 142678, 142820,
    143023, 143226, 143235, 143239, 143499, 143503, 143507, 143662, 143673, 143812, 144093, 144098, 144894, 144895, 145115, 145318, 145437, 145722, 145756, 145917,
    145918, 146044, 146145, 146148, 146151, 146364, 146365, 146368, 146713, 146724, 146726, 146936, 146938, 146946, 147094, 147099, 147239, 147404, 147405, 147411,
    147735, 147980, 149787, 157993, 157994, 158000, 158184, 158190, 158191, 158197, 158414, 158419, 158546, 158548, 158549, 158552
""".strip().split(",")
)

KV2_DRIVER_IDS = set(
    x.strip()
    for x in """
    113452, 113455, 113456, 113459, 113490, 113495, 113497, 113504, 113506, 113517, 113691, 113697, 113701, 113711, 113896, 113901, 114221, 114335, 114337, 114471,
    114473, 114752, 115106, 115110, 115115, 115250, 115452, 116013, 116428, 116702, 116922, 117362, 117365, 117634, 117638, 117640, 117914, 118787, 119532, 120266,
    122440, 122458, 123354, 124304, 124470, 125873, 127503, 127504, 128817, 129357, 129913, 131746, 132230, 132487, 136142, 136430, 137637, 138129, 138590, 138592,
    138593, 138925, 139219, 139713, 140069, 140311, 140312, 140747, 141625, 141628, 141830, 141832, 141960, 141973, 142326, 142546, 142547, 142548, 142550, 142673,
    142676, 142822, 143025, 143052, 143231, 143255, 143506, 143508, 143519, 143520, 143669, 143817, 143827, 144074, 144083, 144097, 144326, 144335, 144557, 144559,
    144643, 145439, 145575, 145720, 145723, 145915, 146037, 146045, 146263, 146265, 146363, 146366, 146385, 146389, 146443, 146549, 146711, 146721, 146725, 146940,
    146945, 146968, 147091, 147093, 147096, 147234, 147244, 147722, 147970, 147987, 157708, 157714, 157821, 157851, 157995, 158002, 158199, 158410, 158412
""".strip().split(",")
)

app = FastAPI(title="SPX Hub Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cache_store = {
    "data": None,
    "expire_time": datetime.min.replace(tzinfo=VIETNAM_TZ),
}

performance_cache = {
    "data": None,
    "expire_time": datetime.min.replace(tzinfo=VIETNAM_TZ),
}
PERFORMANCE_CACHE_SECONDS = int(os.getenv("PERFORMANCE_CACHE_SECONDS", "300"))


async def fetch_api(client, payload):
  try:
    response = await client.post(
        SPX_API_URL,
        json=payload,
        cookies=SPX_COOKIES,
        headers=SPX_HEADERS,
        timeout=15.0,
    )
    if response.status_code == 200:
      res = response.json()
      data = res.get("data", {})
      return data.get("total_count", data.get("total", 0)), data.get(
          "list", []
      ) or data.get("orders", [])
    else:
      logger.warning(f"SPX API trả về mã lỗi: {response.status_code}")
  except Exception as e:
    logger.error(f"API Error: {e}")
  return 0, []


# --- CÁC HÀM XỬ LÝ REPORT HIỆU SUẤT TÀI XẾ ---
def get_field(metrics_dict, keys, default=0):
  for key in keys:
    if key in metrics_dict and metrics_dict[key] is not None:
      return metrics_dict[key]
  return default


def parse_rate(success_rate):
  if isinstance(success_rate, (int, float)):
    raw_rate = (
        success_rate * 100 if success_rate <= 1 else float(success_rate)
    )
  else:
    try:
      raw_rate = float(str(success_rate).replace("%", "").strip())
    except ValueError:
      raw_rate = 0.0
  return raw_rate, f"{raw_rate:.1f}%"


async def fetch_report_data(client, api_url, function_type):
  all_data_list = []
  pageno = 1
  page_count = 200  # Tăng số lượng item mỗi trang lên để lấy nhanh và đủ hơn
  now = datetime.now(VIETNAM_TZ)
  start_date_str = now.strftime("%Y-%m")

  while True:
    payload = {
        "pageno": pageno,
        "count": page_count,
        "frequency": 4,
        "function_type": function_type,
        "start_date": start_date_str,
    }
    try:
      response = await client.post(
          api_url,
          json=payload,
          cookies=SPX_COOKIES,
          headers=SPX_HEADERS,
          timeout=20.0,
      )
      if response.status_code != 200:
        logger.warning(
            "SPX Report %s trả về HTTP %s: %s",
            api_url,
            response.status_code,
            response.text[:500],
        )
        break  # Dừng nếu lỗi HTTP thay vì crash toàn bộ
        
      result = response.json()
      data_list = result.get("data", {}).get("list", [])
      
      # Nếu danh sách trả về rỗng thì kết thúc quá trình phân trang
      if not data_list:
        break
        
      all_data_list.extend(data_list)
      
      # Nếu số lượng trả về ít hơn page_count thì chắc chắn đã đến trang cuối cùng
      if len(data_list) < page_count:
        break
        
      pageno += 1
    except Exception as e:
      logger.error(f"Lỗi khi gọi API Report {api_url} trang {pageno}: {e}")
      break
      
  logger.info(f"Đã load toàn bộ từ API {api_url}: tổng số bản ghi = {len(all_data_list)}")
  return all_data_list

async def get_drivers_performance_data(force_refresh: bool = False):
  """Lấy report hiệu suất giao/lấy và cache để Render không gọi SPX liên tục."""
  now = datetime.now(VIETNAM_TZ)
  if (
      not force_refresh
      and performance_cache["data"] is not None
      and now < performance_cache["expire_time"]
  ):
    return performance_cache["data"]

  async with httpx.AsyncClient() as client:
    delivery_raw_list, pickup_raw_list = await asyncio.gather(
        fetch_report_data(client, DELIVERY_API_URL, 0),
        fetch_report_data(client, PICKUP_API_URL, 2),
    )

  logger.info(
      "Performance raw data: delivery=%s, pickup=%s",
      len(delivery_raw_list),
      len(pickup_raw_list),
  )

  riders_map = {}

  for item in delivery_raw_list:
    rider_id = str(item.get("driver_id", "")).strip()
    khu_vuc = (
        "Khu vực 1"
        if rider_id in KV1_DRIVER_IDS
        else ("Khu vực 2" if rider_id in KV2_DRIVER_IDS else None)
    )
    if not khu_vuc:
      continue

    metrics = item.get("period_metric") or {}
    assigned = get_field(metrics, [
        "MONTHLY_NUMBER_OF_PARCEL_ASSIGNED_V2",
        "MONTHLY_VN_NUMBER_OF_PARCEL_ASSIGNED",
    ], 0)
    delivered = get_field(metrics, [
        "MONTHLY_NUMBER_OF_PARCEL_DELIVERED",
        "MONTHLY_VN_NUMBER_OF_PARCEL_DELIVERED",
    ], 0)
    onhold = get_field(metrics, [
        "MONTHLY_NUMBER_OF_PARCEL_ON_HOLD",
        "MONTHLY_VN_NUMBER_OF_PARCEL_ON_HOLD",
    ], 0)
    success_rate = get_field(metrics, [
        "MONTHLY_VN_DELIVERY_SUCCESS_RATE",
        "MONTHLY_DELIVERY_SUCCESS_RATE_V2",
    ], 0)
    raw_rate, rate_str = parse_rate(success_rate)
    working_days = get_field(metrics, ["MONTHLY_TOTAL_NUMBER_OF_DAY_WORKING"], 0)

    riders_map[rider_id] = {
        "avatar": item.get("avatar_url", ""),
        "name": item.get("driver_name", "N/A"),
        "id": rider_id,
        "khu_vuc": khu_vuc,
        "days": working_days,
        "assigned": assigned,
        "success": delivered,
        "onhold": onhold,
        "rate": rate_str,
        "raw_rate": raw_rate,
        "pickup_assigned": 0,
        "pickup_success": 0,
        "pickup_onhold": 0,
        "pickup_rate": "0.0%",
        "raw_pickup_rate": 0.0,
    }

  for item in pickup_raw_list:
    rider_id = str(item.get("driver_id", "")).strip()
    if rider_id not in riders_map:
      continue
    metrics = item.get("period_metric") or {}
    p_assigned = get_field(metrics, ["MONTHLY_VN_NUMBER_OF_PICKUP_PARCEL_ASSIGNED"], 0)
    p_success = get_field(metrics, ["MONTHLY_NUMBER_OF_PICKUP_PARCEL_PICKED_UP"], 0)
    p_onhold = get_field(metrics, ["MONTHLY_VN_NUMBER_OF_PICKUP_PARCEL_ON_HOLD"], 0)
    p_rate_val = get_field(metrics, ["MONTHLY_VN_PICKUP_SUCCESS_RATE"], 0)
    raw_p_rate, p_rate_str = parse_rate(p_rate_val)

    riders_map[rider_id]["pickup_assigned"] = p_assigned
    riders_map[rider_id]["pickup_success"] = p_success
    riders_map[rider_id]["pickup_onhold"] = p_onhold
    riders_map[rider_id]["pickup_rate"] = p_rate_str
    riders_map[rider_id]["raw_pickup_rate"] = raw_p_rate

  riders = sorted(riders_map.values(), key=lambda x: x["raw_rate"], reverse=True)
  performance_cache["data"] = riders
  performance_cache["expire_time"] = now + timedelta(seconds=PERFORMANCE_CACHE_SECONDS)
  logger.info("Performance processed: %s riders", len(riders))
  return riders


async def get_latest_data():
  now = datetime.now(VIETNAM_TZ)
  if cache_store["data"] and now < cache_store["expire_time"]:
    return cache_store["data"]

  start = int(
      datetime.combine(now.date(), time.min)
      .replace(tzinfo=VIETNAM_TZ)
      .timestamp()
  )
  end = int(
      datetime.combine(now.date(), time.max)
      .replace(tzinfo=VIETNAM_TZ)
      .timestamp()
  )
  time_str = f"{start},{end}"

  async with httpx.AsyncClient() as client:

    async def get_count(status, zone):
      p = {
          "count": 1,
          "current_station_ids": "4232",
          "order_status": status,
          "page_no": 1,
          "zone_id": zone,
          "current_station_received_time": time_str,
      }
      total, _ = await fetch_api(client, p)
      return total

    async def get_forecast_count(status, zone, pickup_ids):
      p = {
          "count": 1,
          "station_ids": "4232",
          "order_status": status,
          "page_no": 1,
          "zone_id": zone,
          "pickup_station_ids": pickup_ids,
      }
      total, _ = await fetch_api(client, p)
      return total

    async def get_inv(zone):
      un, att, page = 0, 0, 1
      while True:
        p = {
            "count": 100,
            "current_station_ids": "4232",
            "current_station_received_time": time_str,
            "order_status": "1",
            "page_no": page,
            "zone_id": zone,
        }
        _, orders = await fetch_api(client, p)
        if not orders:
          break
        for o in orders:
          if o.get("on_hold_times", 0) == 0:
            un += 1
          else:
            att += 1
        if len(orders) < 100:
          break
        page += 1
      return un, att

    async def get_drivers_detail(zone, allowed_ids: set):
      drivers = {}
      page = 1
      while True:
        p = {
            "count": 100,
            "current_station_ids": "4232",
            "current_station_received_time": time_str,
            "order_status": "2,4,5",
            "page_no": page,
            "zone_id": zone,
        }
        _, orders = await fetch_api(client, p)
        if not orders:
          break
        for o in orders:
          d_id = str(o.get("driver_id", ""))
          if not d_id or d_id == "None" or d_id not in allowed_ids:
            continue
          if d_id not in drivers:
            drivers[d_id] = {
                "id": d_id,
                "ten": o.get("driver_name") or f"DRV {d_id}",
                "dang_giao": 0,
                "onhold": 0,
                "thanh_cong": 0,
            }
          st = str(o.get("order_status", ""))
          if st == "2":
            drivers[d_id]["dang_giao"] += 1
          elif st == "5":
            drivers[d_id]["onhold"] += 1
          elif st == "4":
            drivers[d_id]["thanh_cong"] += 1
        if len(orders) < 100:
          break
        page += 1
      return list(drivers.values())

    res = await asyncio.gather(
        get_count("2,4,5", ZONES_KV1_STR),
        get_count("2,4,5", ZONES_KV2_STR),
        get_inv(ZONES_KV1_STR),
        get_inv(ZONES_KV2_STR),
        get_forecast_count(FORECAST_STATUS, ZONES_KV1_STR, "1997,4289"),
        get_forecast_count(FORECAST_STATUS, ZONES_KV2_STR, "1997,4289"),
        get_forecast_count(FORECAST_STATUS, ZONES_KV1_STR, "4232"),
        get_forecast_count(FORECAST_STATUS, ZONES_KV2_STR, "4232"),
        get_drivers_detail(ZONES_KV1_STR, KV1_DRIVER_IDS),
        get_drivers_detail(ZONES_KV2_STR, KV2_DRIVER_IDS),
    )

  data = {
      "ten_hub": "52-HCM SDD-01 Hub",
      "tong_don_giao_kv1": res[0],
      "tong_don_giao_kv2": res[1],
      "tong_don_ton_kho_chua_attem_kv1": res[2][0],
      "tong_don_ton_kho_da_attem_kv1": res[2][1],
      "tong_don_ton_kho_chua_attem_kv2": res[3][0],
      "tong_don_ton_kho_da_attem_kv2": res[3][1],
      "du_bao_warehouse_kv1": res[4],
      "du_bao_warehouse_kv2": res[5],
      "du_bao_pickup_kv1": res[6],
      "du_bao_pickup_kv2": res[7],
      "drivers_detail_kv1": res[8],
      "drivers_detail_kv2": res[9],
      "thoi_gian_cap_nhat": now.strftime("%H:%M:%S"),
  }
  cache_store.update({"data": data, "expire_time": now + timedelta(seconds=300)})
  return data


@app.get("/", response_class=FileResponse)
async def root():
  return FileResponse(INDEX_FILE)


@app.get("/drivers-view", response_class=FileResponse)
async def drivers_view():
  return FileResponse(INDEX_FILE)


@app.get("/health")
async def health():
  return {"status": "ok", "service": "spx-hub"}


@app.get("/api/dashboard")
async def api_dashboard():
  return await get_latest_data()


@app.get("/api/performance")
async def api_performance(force: str = "0"):
  try:
    force_refresh = force.lower() in {"1", "true", "yes", "force"}
    riders = await get_drivers_performance_data(force_refresh=force_refresh)
    return {
        "riders": riders,
        "count": len(riders),
        "cached": (
            performance_cache["data"] is riders
            and datetime.now(VIETNAM_TZ) < performance_cache["expire_time"]
            and not force_refresh
        ),
    }
  except Exception as e:
    logger.exception("Lỗi API /api/performance")
    raise HTTPException(status_code=502, detail=f"Không lấy được dữ liệu hiệu suất: {e}")


@app.get("/api/stream")
async def stream(request: Request):
  async def event_generator():
    while True:
      if await request.is_disconnected():
        break
      try:
        data = await get_latest_data()
        yield {"event": "update", "data": json.dumps(data, ensure_ascii=False)}
      except Exception as e:
        logger.exception("Lỗi SSE")
        yield {"event": "error", "data": json.dumps({"error": str(e)}, ensure_ascii=False)}
      await asyncio.sleep(30)

  return EventSourceResponse(event_generator(), ping=15)


if __name__ == "__main__":
  import uvicorn

  port = int(os.environ.get("PORT", "8000"))
  uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
