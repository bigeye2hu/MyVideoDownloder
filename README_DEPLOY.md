# MyVideoDownloader 閮ㄧ讲璇存槑

## 馃摝 鏈嶅姟淇℃伅

- **瀹瑰櫒鍚嶇О**: my_video_downloader_api
- **鏈湴绔彛**: 8081
- **瀹瑰櫒绔彛**: 80
- **API鏂囨。**: http://localhost:8081/docs
- **Web鐣岄潰**: http://localhost:8081/

## 馃殌 蹇€熷惎鍔?
### 浣跨敤绠＄悊鑴氭湰锛堟帹鑽愶級

\\ash
# 鍚姩鏈嶅姟
./manage.sh start

# 鍋滄鏈嶅姟
./manage.sh stop

# 閲嶅惎鏈嶅姟
./manage.sh restart

# 鏌ョ湅鏃ュ織
./manage.sh logs

# 鏌ョ湅鐘舵€?./manage.sh status
\
### 浣跨敤Docker Compose

\\ash
# 鍚姩
docker-compose -f docker-compose.prod.yml up -d

# 鍋滄
docker-compose -f docker-compose.prod.yml down

# 鏌ョ湅鏃ュ織
docker logs -f my_video_downloader_api
\
## 馃寪 Cloudflare Tunnel 閰嶇疆

### 1. 瀹夎 cloudflared

\\ash
# Ubuntu/Debian
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# 鎴栦娇鐢ㄥ寘绠＄悊鍣?sudo apt install cloudflared
\
### 2. 鐧诲綍 Cloudflare

\\ash
cloudflared tunnel login
\
### 3. 鍒涘缓 Tunnel

\\ash
# 鍒涘缓tunnel锛堣涓嬭繑鍥炵殑ID锛?cloudflared tunnel create video-downloader

# 鏌ョ湅tunnel鍒楄〃
cloudflared tunnel list
\
### 4. 閰嶇疆 Tunnel

缂栬緫 \cloudflare-tunnel-config.yml\ 鏂囦欢锛屾浛鎹互涓嬪唴瀹癸細
- \YOUR_TUNNEL_ID\: 浣犵殑tunnel ID
- \ideo-api.yourdomain.com\: 浣犵殑鍩熷悕
- \/path/to/.cloudflared/YOUR_TUNNEL_ID.json\: credentials鏂囦欢璺緞锛堥€氬父鍦▇/.cloudflared/锛?
### 5. 閰嶇疆DNS

鍦–loudflare Dashboard娣诲姞DNS璁板綍锛?\绫诲瀷: CNAME
鍚嶇О: video-api (鎴栦綘鎯宠鐨勫瓙鍩熷悕)
鐩爣: YOUR_TUNNEL_ID.cfargotunnel.com
浠ｇ悊鐘舵€? 宸蹭唬鐞嗭紙姗欒壊浜戞湹锛?\
### 6. 鍚姩 Tunnel

\\ash
# 娴嬭瘯閰嶇疆
cloudflared tunnel --config cloudflare-tunnel-config.yml run

# 鍚庡彴杩愯
nohup cloudflared tunnel --config cloudflare-tunnel-config.yml run &

# 鎴栧畨瑁呬负绯荤粺鏈嶅姟
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
\
## 馃敡 閰嶇疆璇存槑

### Cookie 閰嶇疆

涓洪伩鍏嶉鎺э紝闇€瑕侀厤缃瓹ookie锛?
1. **鎶栭煶Cookie**: \crawlers/douyin/web/config.yaml2. **TikTok Cookie**: \crawlers/tiktok/web/config.yaml
鑾峰彇Cookie鏂规硶锛?1. 鎵撳紑娴忚鍣ㄨ闂姈闊?TikTok
2. 鐧诲綍璐﹀彿
3. F12鎵撳紑寮€鍙戣€呭伐鍏?4. Network鏍囩椤碉紝鍒锋柊椤甸潰
5. 澶嶅埗璇锋眰澶翠腑鐨凜ookie鍊?6. 绮樿创鍒板搴旈厤缃枃浠?
### 绔彛淇敼

濡傞渶淇敼绔彛锛岀紪杈?\docker-compose.prod.yml\:
\\yaml
ports:
  - '浣犵殑绔彛:80'  # 淇敼宸﹁竟鐨勭鍙ｅ彿
\
## 馃搳 甯哥敤API鎺ュ彛

### 娣峰悎瑙ｆ瀽锛堟姈闊?TikTok锛?\GET http://localhost:8081/api/hybrid/video_data?url=[瑙嗛閾炬帴]
\
### 涓嬭浇瑙嗛
\GET http://localhost:8081/api/download?url=[瑙嗛閾炬帴]&with_watermark=false
\
## 馃攳 鏁呴殰鎺掓煡

### 鏌ョ湅瀹瑰櫒鐘舵€?\\ash
docker ps -a | grep my_video_downloader_api
\
### 鏌ョ湅璇︾粏鏃ュ織
\\ash
docker logs my_video_downloader_api --tail 100
\
### 閲嶆柊鏋勫缓
\\ash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
\
### 妫€鏌ョ鍙ｅ崰鐢?\\ash
netstat -tulpn | grep 8081
\
## 馃摑 渚涢珮灏斿かApp浣跨敤鐨勯厤缃?
鍦ㄤ綘鐨勯珮灏斿かApp涓厤缃瓵PI鍦板潃锛?
### 鏈湴娴嬭瘯
\API_URL=http://localhost:8081
\
### 閫氳繃Cloudflare Tunnel锛堢敓浜х幆澧冿級
\API_URL=https://video-api.yourdomain.com
\
### 绀轰緥璇锋眰
\\javascript
// 瑙ｆ瀽瑙嗛
const response = await fetch('http://localhost:8081/api/hybrid/video_data?url=' + encodeURIComponent(videoUrl));
const data = await response.json();

// 涓嬭浇瑙嗛
const downloadUrl = 'http://localhost:8081/api/download?url=' + encodeURIComponent(videoUrl) + '&with_watermark=false';
\
## 馃攼 瀹夊叏寤鸿

1. 涓嶈灏嗛厤缃枃浠朵腑鐨凜ookie鎻愪氦鍒癎it
2. 瀹氭湡鏇存柊Cookie閬垮厤澶辨晥
3. 鐢熶骇鐜浣跨敤Cloudflare Tunnel鐨凥TTPS
4. 鑰冭檻娣诲姞API璁よ瘉锛坈onfig.yaml涓殑API_Key锛?
## 馃摓 鏀寔

椤圭洰鍦板潃: https://github.com/bigeye2hu/MyVideoDownloder
