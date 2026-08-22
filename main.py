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

# --- DANH SÁCH DRIVER ID CHO KHU VỰC 1 VÀ KHU VỰC 2 ---
KV1_DRIVER_IDS = {
    "116429", "116424", "114100", "136316", "142322", "140800", "143226", "141975", "144093", "124220", 
    "115449", "115456", "123654", "114749", "133970", "138575", "114472", "143023", "143662", "144894", 
    "146713", "147239", "143673", "145318", "114475", "135685", "144098", "138133", "113957", "141386", 
    "113707", "121878", "143507", "114467", "139234", "141388", "114468", "141383", "146936", "117631", 
    "142555", "116422", "141629", "146946", "138924", "117908", "142675", "143239", "141622", "122070", 
    "114334", "128461", "114916", "115444", "141379", "144895", "143235", "146151", "147404", "142678", 
    "146365", "122662", "139715", "132664", "145722", "146938", "142347", "145115", "121225", "116697", 
    "115111", "132836", "147099", "134459", "136314", "139708", "149787", "119086", "117912", "147405", 
    "123878", "136141", "143503", "140071", "145918", "147094", "126787", "127635", "146145", "124469", 
    "124302", "146368", "147411", "124305", "142670", "124303", "128922", "129548", "141097", "129916", 
    "133311", "141390", "142820", "138589", "143812", "145917", "146148", "146364", "146724", "147735", 
    "158000", "117911", "117910", "117633", "128151", "146726", "145756", "129105", "147980", "129361", 
    "130264", "143499", "141633", "145437", "132957", "146044"
}

KV2_DRIVER_IDS = {
    "113711", "143231", "113701", "140311", "136142", "123354", "146265", "113495", "141960", "141625", 
    "113497", "113490", "146263", "132487", "146549", "114471", "115250", "115452", "115110", "145439", 
    "113896", "146721", "115106", "120266", "142673", "115115", "145915", "116702", "141830", "113504", 
    "147234", "136430", "114337", "114752", "143506", "146725", "122440", "116428", "131746", "113691", 
    "142822", "146945", "117362", "118787", "113459", "144083", "143508", "113456", "113901", "114221", 
    "143817", "144097", "116013", "142548", "138590", "140069", "146366", "119532", "138593", "141973", 
    "142326", "138129", "146940", "113506", "146443", "140747", "146037", "146045", "113455", "142547", 
    "142546", "113452", "139713", "146711", "114335", "114473", "143669", "125873", "117640", "113517", 
    "128817", "139219", "146389", "147096", "157714", "146385", "124304", "147093", "146363", "138592", 
    "141832", "117638", "146968", "138925", "145720", "117914", "144643", "113697", "145575", "144326", 
    "116922", "144335", "122458", "147091", "117634", "144074", "117365", "127503", "157821", "127504", 
    "141628", "140312", "145723", "124470", "142676", "142550", "137637", "143520", "129913", "147722", 
    "143052", "143025", "129357", "157708", "143519", "157851", "157995", "157993", "143827", "144559", 
    "132230", "143255", "144557", "147244", "147970", "147987"
}

# --- ZONES CHO TỒN KHO VÀ DỰ BÁO ---
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
    now = datetime.now(VIETNAM_TZ)
    if cache_store["data"] and now < cache_store["expire_time"]:
        return cache_store["data"]

    start = int(datetime.combine(now.date(), time.min).replace(tzinfo=VIETNAM_TZ).timestamp())
    end = int(datetime.combine(now.date(), time.max).replace(tzinfo=VIETNAM_TZ).timestamp())
    time_str = f"{start},{end}"

    async with httpx.AsyncClient() as client:
        async def get_forecast_count(status, zone, pickup_ids):
            p = {"count": 1, "station_ids": "4232", "order_status": status, "page_no": 1, "zone_id": zone, "pickup_station_ids": pickup_ids}
            total, _ = await fetch_api(client, p)
            return total

        async def get_inv(zone):
            un, att, page = 0, 0, 1
            max_pages = 50
            while page <= max_pages:
                p = {"count": 100, "current_station_ids": "4232", "current_station_received_time": time_str, "order_status": "1", "page_no": page, "zone_id": zone}
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

        async def get_drivers_data():
            drivers_kv1 = {}
            drivers_kv2 = {}
            page = 1
            max_pages = 50
            
            while page <= max_pages:
                p = {"count": 100, "current_station_ids": "4232", "current_station_received_time": time_str, "order_status": "2,4,5", "page_no": page}
                _, orders = await fetch_api(client, p)
                if not orders: 
                    break
                
                for o in orders:
                    d_id = str(o.get("driver_id", ""))
                    if not d_id or d_id == "None": 
                        continue
                    
                    st = str(o.get("order_status", ""))
                    
                    # Phân loại theo danh sách driver_id đã cung cấp
                    if d_id in KV1_DRIVER_IDS:
                        if d_id not in drivers_kv1:
                            drivers_kv1[d_id] = {"id": d_id, "ten": o.get("driver_name") or f"DRV {d_id}", "dang_giao": 0, "onhold": 0, "thanh_cong": 0}
                        if st == "2": drivers_kv1[d_id]["dang_giao"] += 1
                        elif st == "5": drivers_kv1[d_id]["onhold"] += 1
                        elif st == "4": drivers_kv1[d_id]["thanh_cong"] += 1
                        
                    elif d_id in KV2_DRIVER_IDS:
                        if d_id not in drivers_kv2:
                            drivers_kv2[d_id] = {"id": d_id, "ten": o.get("driver_name") or f"DRV {d_id}", "dang_giao": 0, "onhold": 0, "thanh_cong": 0}
                        if st == "2": drivers_kv2[d_id]["dang_giao"] += 1
                        elif st == "5": drivers_kv2[d_id]["onhold"] += 1
                        elif st == "4": drivers_kv2[d_id]["thanh_cong"] += 1

                if len(orders) < 100: 
                    break
                page += 1

            list_kv1 = list(drivers_kv1.values())
            list_kv2 = list(drivers_kv2.values())
            
            total_giao_kv1 = sum(d["dang_giao"] + d["onhold"] + d["thanh_cong"] for d in list_kv1)
            total_giao_kv2 = sum(d["dang_giao"] + d["onhold"] + d["thanh_cong"] for d in list_kv2)
            
            return total_giao_kv1, total_giao_kv2, list_kv1, list_kv2

        res = await asyncio.gather(
            get_inv(ZONES_KV1_STR), get_inv(ZONES_KV2_STR),
            get_forecast_count(FORECAST_STATUS, ZONES_KV1_STR, "1997,4289"), get_forecast_count(FORECAST_STATUS, ZONES_KV2_STR, "1997,4289"),
            get_forecast_count(FORECAST_STATUS, ZONES_KV1_STR, "4232"), get_forecast_count(FORECAST_STATUS, ZONES_KV2_STR, "4232"),
            get_drivers_data()
        )
        
        drv_data = res[6] # (total_giao_kv1, total_giao_kv2, list_kv1, list_kv2)
        
        data = {
            "ten_hub": "52-HCM SDD-01 Hub",
            "tong_don_giao_kv1": drv_data[0], "tong_don_giao_kv2": drv_data[1],
            "tong_don_ton_kho_chua_attem_kv1": res[0][0], "tong_don_ton_kho_da_attem_kv1": res[0][1],
            "tong_don_ton_kho_chua_attem_kv2": res[1][0], "tong_don_ton_kho_da_attem_kv2": res[1][1],
            "du_bao_warehouse_kv1": res[2], "du_bao_warehouse_kv2": res[3],
            "du_bao_pickup_kv1": res[4], "du_bao_pickup_kv2": res[5],
            "drivers_detail_kv1": drv_data[2], "drivers_detail_kv2": drv_data[3],
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
            await asyncio.sleep(360)
    return EventSourceResponse(gen())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
