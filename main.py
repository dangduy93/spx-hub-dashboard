<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPX Hub Dashboard - Real-time</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans antialiased">

    <!-- Header -->
    <header class="bg-slate-800 border-b border-slate-700 px-6 py-4 flex flex-col md:flex-row justify-between items-center shadow-md">
        <div class="flex items-center space-x-3 mb-2 md:mb-0">
            <div class="bg-orange-500 p-2.5 rounded-lg text-white font-bold text-xl shadow-lg">
                <i class="fa-solid fa-boxes-stacked"></i>
            </div>
            <div>
                <h1 id="hub-name" class="text-xl font-bold tracking-wide">52-HCM SDD-01 Hub</h1>
                <p class="text-xs text-slate-400">Hệ thống giám sát vận hành Real-time</p>
            </div>
        </div>
        <div class="flex items-center space-x-4">
            <div id="api-status-text" class="text-xs px-3 py-1.5 rounded-full bg-slate-700 text-slate-300 flex items-center space-x-2 border border-slate-600">
                <i class="fa-solid fa-circle text-amber-400 text-[8px] animate-pulse"></i>
                <span>Đang khởi tạo...</span>
            </div>
            <div class="text-xs text-slate-400 bg-slate-700/50 px-3 py-1.5 rounded-lg border border-slate-600/50">
                Cập nhật lúc: <span id="update-time" class="font-semibold text-slate-200">--:--:--</span>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="p-6 max-w-7xl mx-auto space-y-6">

        <!-- Grid Thống kê tổng quan KV1 & KV2 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <!-- KHU VỰC 1 (KV1) -->
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-lg relative overflow-hidden">
                <div class="absolute top-0 left-0 h-1 w-full bg-blue-500"></div>
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-blue-400 flex items-center space-x-2">
                        <i class="fa-solid fa-location-dot"></i>
                        <span>Khu Vực 1 (KV1)</span>
                    </h2>
                    <span class="bg-blue-500/10 text-blue-400 text-xs px-2.5 py-1 rounded-full font-medium border border-blue-500/20">Hoạt động</span>
                </div>
                
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Đang giao</p>
                        <p id="val-giao-kv1" class="text-2xl font-bold text-white">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Tồn (Chưa Att)</p>
                        <p id="val-ton-chua-kv1" class="text-2xl font-bold text-amber-400">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Tồn (Đã Att)</p>
                        <p id="val-ton-da-kv1" class="text-2xl font-bold text-rose-400">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Dự báo WH</p>
                        <p id="val-wh-kv1" class="text-xl font-bold text-emerald-400">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50 col-span-2 sm:col-span-2">
                        <p class="text-xs text-slate-400 mb-1">Dự báo Pickup</p>
                        <p id="val-pickup-kv1" class="text-xl font-bold text-indigo-400">0</p>
                    </div>
                </div>
            </div>

            <!-- KHU VỰC 2 (KV2) -->
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-lg relative overflow-hidden">
                <div class="absolute top-0 left-0 h-1 w-full bg-purple-500"></div>
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-purple-400 flex items-center space-x-2">
                        <i class="fa-solid fa-location-dot"></i>
                        <span>Khu Vực 2 (KV2)</span>
                    </h2>
                    <span class="bg-purple-500/10 text-purple-400 text-xs px-2.5 py-1 rounded-full font-medium border border-purple-500/20">Hoạt động</span>
                </div>
                
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Đang giao</p>
                        <p id="val-giao-kv2" class="text-2xl font-bold text-white">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Tồn (Chưa Att)</p>
                        <p id="val-ton-chua-kv2" class="text-2xl font-bold text-amber-400">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Tồn (Đã Att)</p>
                        <p id="val-ton-da-kv2" class="text-2xl font-bold text-rose-400">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50">
                        <p class="text-xs text-slate-400 mb-1">Dự báo WH</p>
                        <p id="val-wh-kv2" class="text-xl font-bold text-emerald-400">0</p>
                    </div>
                    <div class="bg-slate-700/50 p-3 rounded-lg border border-slate-600/50 col-span-2 sm:col-span-2">
                        <p class="text-xs text-slate-400 mb-1">Dự báo Pickup</p>
                        <p id="val-pickup-kv2" class="text-xl font-bold text-indigo-400">0</p>
                    </div>
                </div>
            </div>

        </div>

        <!-- Bảng chi tiết Shipper / Driver -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <!-- Driver KV1 -->
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-lg">
                <h3 class="font-bold text-sm text-slate-300 mb-3 flex items-center space-x-2">
                    <i class="fa-solid fa-users text-blue-400"></i>
                    <span>Chi Tiết Shipper KV1</span>
                </h3>
                <div class="overflow-x-auto max-h-64 overflow-y-auto">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-700 text-slate-300 uppercase sticky top-0">
                            <tr>
                                <th class="p-2.5">Tên Shipper</th>
                                <th class="p-2.5 text-center">Đang giao</th>
                                <th class="p-2.5 text-center">Onhold</th>
                                <th class="p-2.5 text-center">Thành công</th>
                            </tr>
                        </thead>
                        <tbody id="table-drivers-kv1" class="divide-y divide-slate-700/50 text-slate-200">
                            <tr><td colspan="4" class="p-4 text-center text-slate-500">Đang tải dữ liệu...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Driver KV2 -->
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-lg">
                <h3 class="font-bold text-sm text-slate-300 mb-3 flex items-center space-x-2">
                    <i class="fa-solid fa-users text-purple-400"></i>
                    <span>Chi Tiết Shipper KV2</span>
                </h3>
                <div class="overflow-x-auto max-h-64 overflow-y-auto">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-700 text-slate-300 uppercase sticky top-0">
                            <tr>
                                <th class="p-2.5">Tên Shipper</th>
                                <th class="p-2.5 text-center">Đang giao</th>
                                <th class="p-2.5 text-center">Onhold</th>
                                <th class="p-2.5 text-center">Thành công</th>
                            </tr>
                        </thead>
                        <tbody id="table-drivers-kv2" class="divide-y divide-slate-700/50 text-slate-200">
                            <tr><td colspan="4" class="p-4 text-center text-slate-500">Đang tải dữ liệu...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

    </main>

    <!-- JavaScript Xử lý gọi API và Cập nhật giao diện -->
    <script>
        function updateDashboardUI(data, isCached = false) {
            if (!data) return;

            // Header info
            document.getElementById('hub-name').innerText = data.ten_hub || "SPX Hub";
            document.getElementById('update-time').innerText = data.thoi_gian_cap_nhat || "--:--:--";

            // KV1 metrics
            document.getElementById('val-giao-kv1').innerText = data.tong_don_giao_kv1 ?? 0;
            document.getElementById('val-ton-chua-kv1').innerText = data.tong_don_ton_kho_chua_attem_kv1 ?? 0;
            document.getElementById('val-ton-da-kv1').innerText = data.tong_don_ton_kho_da_attem_kv1 ?? 0;
            document.getElementById('val-wh-kv1').innerText = data.du_bao_warehouse_kv1 ?? 0;
            document.getElementById('val-pickup-kv1').innerText = data.du_bao_pickup_kv1 ?? 0;

            // KV2 metrics
            document.getElementById('val-giao-kv2').innerText = data.tong_don_giao_kv2 ?? 0;
            document.getElementById('val-ton-chua-kv2').innerText = data.tong_don_ton_kho_chua_attem_kv2 ?? 0;
            document.getElementById('val-ton-da-kv2').innerText = data.tong_don_ton_kho_da_attem_kv2 ?? 0;
            document.getElementById('val-wh-kv2').innerText = data.du_bao_warehouse_kv2 ?? 0;
            document.getElementById('val-pickup-kv2').innerText = data.du_bao_pickup_kv2 ?? 0;

            // Render bảng Drivers KV1
            const tbodyKv1 = document.getElementById('table-drivers-kv1');
            tbodyKv1.innerHTML = '';
            if (data.drivers_detail_kv1 && data.drivers_detail_kv1.length > 0) {
                data.drivers_detail_kv1.forEach(d => {
                    tbodyKv1.innerHTML += `
                        <tr class="hover:bg-slate-700/30">
                            <td class="p-2.5 font-medium">${d.ten}</td>
                            <td class="p-2.5 text-center text-blue-400 font-semibold">${d.dang_giao}</td>
                            <td class="p-2.5 text-center text-amber-400">${d.onhold}</td>
                            <td class="p-2.5 text-center text-emerald-400">${d.thanh_cong}</td>
                        </tr>`;
                });
            } else {
                tbodyKv1.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-slate-500">Không có dữ liệu shipper KV1</td></tr>`;
            }

            // Render bảng Drivers KV2
            const tbodyKv2 = document.getElementById('table-drivers-kv2');
            tbodyKv2.innerHTML = '';
            if (data.drivers_detail_kv2 && data.drivers_detail_kv2.length > 0) {
                data.drivers_detail_kv2.forEach(d => {
                    tbodyKv2.innerHTML += `
                        <tr class="hover:bg-slate-700/30">
                            <td class="p-2.5 font-medium">${d.ten}</td>
                            <td class="p-2.5 text-center text-purple-400 font-semibold">${d.dang_giao}</td>
                            <td class="p-2.5 text-center text-amber-400">${d.onhold}</td>
                            <td class="p-2.5 text-center text-emerald-400">${d.thanh_cong}</td>
                        </tr>`;
                });
            } else {
                tbodyKv2.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-slate-500">Không có dữ liệu shipper KV2</td></tr>`;
            }

            // Lưu cache local
            localStorage.setItem('spx_cached_dashboard_data', JSON.stringify(data));
        }

        async function fetchDashboardData() {
            try {
                document.getElementById('api-status-text').innerHTML = `
                    <i class="fa-solid fa-rotate animate-spin text-blue-400 text-[10px]"></i>
                    <span class="text-slate-300">Đang đồng bộ...</span>`;
                
                const response = await fetch('/api/dashboard');
                if (!response.ok) throw new Error('Phản hồi server lỗi');
                
                const data = await response.json();
                updateDashboardUI(data);
                
                document.getElementById('api-status-text').innerHTML = `
                    <i class="fa-solid fa-circle text-emerald-400 text-[8px]"></i>
                    <span class="text-slate-300">Đã đồng bộ</span>`;
            } catch (e) {
                console.error("Lỗi fetch:", e);
                document.getElementById('api-status-text').innerHTML = `
                    <i class="fa-solid fa-triangle-exclamation text-rose-400 text-[10px]"></i>
                    <span class="text-rose-400">Lỗi kết nối server</span>`;
            }
        }

        // Khi load trang
        document.addEventListener('DOMContentLoaded', () => {
            // Hiển thị dữ liệu cũ từ LocalStorage (nếu có) để giao diện không bị trống lúc đầu
            const cachedString = localStorage.getItem('spx_cached_dashboard_data');
            if (cachedString) {
                try {
                    updateDashboardUI(JSON.parse(cachedString), true);
                } catch (err) {
                    console.error("Lỗi parse cache:", err);
                }
            }

            // Gọi API lần đầu
            fetchDashboardData();

            // Tự động gọi lại sau mỗi 60 giây để làm mới dữ liệu
            setInterval(fetchDashboardData, 60000);
        });
    </script>
</body>
</html>
