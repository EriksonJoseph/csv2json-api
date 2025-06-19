# Email Debug Guide for Docker Container

## ปัญหาที่พบบ่อย: SMTP Send Failed ใน Container

เมื่อ local สามารถส่ง email ได้แต่ container ส่งไม่ได้ มักเกิดจากสาเหตุดังนี้:

### 1. Network Connectivity Issues
- Container ไม่มี internet access
- Firewall บล็อก SMTP port (587, 465, 25)
- Docker network configuration ผิดพลาด

### 2. DNS Resolution Problems
- Container ไม่สามารถ resolve SMTP hostname ได้
- DNS server ใน container ไม่ทำงาน

### 3. Authentication Issues
- Credentials ผิดพลาด
- Gmail App Password ไม่ได้ใช้
- 2FA settings

## วิธี Debug

### Method 1: ใช้ Debug Endpoints (แนะนำ)

#### 1. Test Email Connectivity
```bash
curl -X GET "http://your-api/api/email/debug/connectivity" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### 2. Send Test Email
```bash
curl -X POST "http://your-api/api/email/debug/test-send?test_email=your@email.com" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Method 2: ใช้ Debug Script ใน Container

#### 1. Copy script เข้า container
```bash
docker cp debug_email.py <container_name>:/app/debug_email.py
```

#### 2. Run script ใน container
```bash
docker exec -it <container_name> python debug_email.py
```

### Method 3: Manual Testing ใน Container

#### 1. เข้าไป container
```bash
docker exec -it <container_name> /bin/bash
```

#### 2. Test network connectivity
```bash
# Test internet connectivity
ping 8.8.8.8

# Test SMTP server connectivity
telnet smtp.gmail.com 587

# Test DNS resolution
nslookup smtp.gmail.com
```

#### 3. Test Python SMTP
```python
import smtplib
import socket

# Test DNS
print(socket.gethostbyname('smtp.gmail.com'))

# Test SMTP connection
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_username', 'your_password')
server.quit()
```

## การแก้ปัญหาตามสาเหตุ

### 1. Container ไม่มี Internet Access

#### Docker Run
```bash
docker run --network host your-app
```

#### Docker Compose
```yaml
services:
  app:
    network_mode: host
    # หรือ
    networks:
      - default
networks:
  default:
    driver: bridge
```

### 2. DNS Resolution Problems

#### เพิ่ม DNS servers
```yaml
services:
  app:
    dns:
      - 8.8.8.8
      - 1.1.1.1
```

#### ใช้ IP แทน hostname
```env
SMTP_HOST=172.253.115.108  # Gmail SMTP IP
```

### 3. Firewall Issues

#### ตรวจสอบ ports ที่เปิด
```bash
# ใน container
nc -zv smtp.gmail.com 587
nc -zv smtp.gmail.com 465
nc -zv smtp.gmail.com 25
```

#### Docker port mapping
```yaml
services:
  app:
    ports:
      - "8000:8000"
    # Ensure outbound ports are not blocked
```

### 4. Gmail Specific Issues

#### ใช้ App Password
1. Enable 2FA ใน Google Account
2. สร้าง App Password ใน Security Settings
3. ใช้ App Password แทน regular password

```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Not regular password
```

### 5. Alternative SMTP Configurations

#### Gmail SMTP (SSL)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_TLS=False
SMTP_USE_SSL=True
```

#### Gmail SMTP (TLS)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=True
```

### 6. Container Environment Variables

#### ตรวจสอบ env vars ใน container
```bash
docker exec <container_name> env | grep SMTP
```

#### Set environment variables properly
```yaml
services:
  app:
    environment:
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_USE_TLS=True
```

## Logging และ Monitoring

### 1. เพิ่ม Detailed Logging
Code ใหม่จะมี detailed SMTP logging แล้ว โดยจะ log:
- Network connectivity tests
- SMTP connection steps
- Authentication results
- Detailed error messages

### 2. ตรวจสอบ Container Logs
```bash
docker logs <container_name> | grep "📧"
```

### 3. Monitor Failed Email Tasks
```bash
curl -X GET "http://your-api/api/email/tasks?status=failed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Quick Fixes

### 1. เปลี่ยนเป็น External SMTP Service
```env
# ใช้ SendGrid
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# ใช้ Mailgun
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your-mailgun-username
SMTP_PASSWORD=your-mailgun-password
```

### 2. ใช้ SMTP Relay Service
```env
# ใช้ local SMTP relay
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_USE_TLS=False
```

### 3. Bypass Docker Network Issues
```bash
# Run container with host network
docker run --network host your-app

# หรือใช้ external SMTP service
```

## การทดสอบ

### 1. Test Script Results
- ✅ ทุก test ผ่าน = SMTP configuration ถูกต้อง
- ❌ DNS Resolution Failed = DNS/Network issue  
- ❌ Network Connectivity Failed = Firewall/Internet issue
- ❌ Authentication Failed = Credentials issue

### 2. Debug Endpoint Results
```json
{
  "overall_status": "failed",
  "failed_tests": ["network_connectivity", "authentication"],
  "tests": {
    "network_connectivity": {
      "status": "failed", 
      "error": "[Errno 111] Connection refused"
    }
  }
}
```

### 3. Log Analysis
ใน logs หา pattern ตาม priority:
1. `Network connectivity failed` = Internet/Firewall issue
2. `SMTP Authentication failed` = Credentials issue  
3. `SMTP Connection failed` = SMTP server issue
4. `DNS error` = DNS resolution issue

## Best Practices

1. **ใช้ App Password สำหรับ Gmail**
2. **Test connectivity ก่อน deploy**
3. **Monitor email queue และ failed tasks**
4. **ใช้ external SMTP service สำหรับ production**
5. **Set proper timeout values**
6. **Enable detailed logging ใน production**