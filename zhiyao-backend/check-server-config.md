# 后端服务器配置检查清单

## 1. 服务器运行状态检查

### ✅ 确认Spring Boot应用已启动
```bash
# Windows检查Java进程
netstat -ano | findstr "8080"

# 或者检查进程
tasklist | findstr "java"
```

### ✅ 查看应用日志
检查 `zhijian-backend` 的启动日志，确认：
- 应用成功启动
- 端口8080已绑定
- 没有启动错误

## 2. 端口开放检查

### ✅ 确认端口8080已监听
```bash
# Windows PowerShell
netstat -an | findstr "8080"

# 应该看到类似输出：
# TCP    0.0.0.0:8080           0.0.0.0:0              LISTENING
```

### ✅ 测试本地访问
```bash
# 在开发电脑上测试
curl http://localhost:8080/api/health
# 或在浏览器访问
http://localhost:8080/api/health
```

## 3. 防火墙配置

### ✅ Windows防火墙设置
1. 打开 Windows Defender 防火墙
2. 点击"高级设置"
3. 检查"入站规则"
4. 确保端口8080允许入站连接

### ✅ 添加防火墙规则（如需要）
```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Allow Port 8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

## 4. 网络绑定地址检查

### ⚠️ 重要：确认应用监听所有网络接口

在 `application.yml` 或 `application.properties` 中配置：

```yaml
server:
  port: 8080
  address: 0.0.0.0  # 监听所有网络接口，允许局域网访问
```

**默认配置可能只监听 localhost (127.0.0.1)**，导致其他设备无法访问！

## 5. 获取本机局域网IP

### Windows命令
```bash
ipconfig

# 查找"无线局域网适配器 WLAN"或"以太网适配器"
# 记录IPv4地址，例如: 192.168.1.100
```

### 将此IP配置到小程序
更新 `zhijian-rider-mp/src/utils/request.ts`：
```typescript
development: 'http://192.168.1.100:8080/api'  // 使用实际IP
```

## 6. 跨域配置（CORS）

### ✅ 确保后端允许跨域请求

在Spring Boot中添加CORS配置：

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(false)
                .maxAge(3600);
    }
}
```

## 7. 测试局域网访问

### 从手机浏览器测试
在手机浏览器中访问：
```
http://192.168.1.100:8080/api/health
```

如果能访问，说明网络配置正确！

## 常见问题解决

### ❌ 问题1: 连接超时
**原因**：防火墙阻止或IP地址错误
**解决**：
1. 检查防火墙规则
2. 确认IP地址正确
3. 确认手机和电脑在同一WiFi

### ❌ 问题2: 连接被拒绝
**原因**：服务未启动或端口未监听
**解决**：
1. 重启Spring Boot应用
2. 检查application.yml配置
3. 确认没有端口冲突

### ❌ 问题3: 404错误
**原因**：API路径不正确
**解决**：
1. 检查后端Controller的路径映射
2. 确认请求URL拼接正确
