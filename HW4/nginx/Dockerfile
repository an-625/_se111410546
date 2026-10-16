# nginx — Web Server + Reverse Proxy
FROM nginx:1.27-alpine

# 移除預設站台，改用自訂 reverse proxy 設定
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 簡易 Web 介面（靜態站）
COPY html/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
