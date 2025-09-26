# ThorCryptoCurrency Strategy Library - Docker 部署指南

## 快速部署

### 一键部署脚本（推荐）

```bash
# 克隆项目
git clone https://github.com/your-username/ThorCryptocurrencyQuant.git
cd ThorCryptocurrencyQuant

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 手动部署

#### 1. 环境准备

```bash
# 安装 Docker 和 Docker Compose
sudo apt update
sudo apt install docker.io docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 创建数据目录
sudo mkdir -p /data/docker/ThorCQ/mongo
sudo chown -R $USER:$USER /data/docker/ThorCQ
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑环境变量
nano .env
```

#### 3. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

## 服务管理

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
docker-compose logs -f mongo

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建
docker-compose up -d --build

# 查看资源使用
docker stats
```

### 数据库管理

```bash
# 连接 MongoDB
docker-compose exec mongo mongosh

# 查看订单数据
use binance
db['ETH/USDT'].find().pretty()

# 备份数据
docker-compose exec mongo mongodump --out /data/backup
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| EXCHANGE | 交易所名称 | binance |
| API_KEY | API 密钥 | - |
| API_SECRET | API 密钥 | - |
| ORDER_SYMBOL | 交易对 | ETH/USDT |
| NUM_BUY | 买网格数量 | 3 |
| NUM_SELL | 卖网格数量 | 1 |
| ORDER_SPREAD | 网格步长 | 0.5 |
| ORDER_PROFIT | 利润目标 | 0.5 |
| ORDER_AMOUNT_BUY | 买单数量 | 30 |
| ORDER_AMOUNT_SELL | 卖单数量 | 30 |

### 端口配置

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|----------|----------|------|
| MongoDB | 27017 | 7399 | 数据库服务 |
| App | - | - | 应用服务（无外部端口） |

### 数据持久化

- MongoDB 数据目录：`/data/docker/ThorCQ/mongo`
- 应用日志目录：`./logs`

## 故障排除

### 常见问题

1. **容器无法启动**
   ```bash
   # 检查 Docker 服务
   sudo systemctl status docker

   # 查看详细日志
   docker-compose logs
   ```

2. **MongoDB 连接失败**
   ```bash
   # 检查 MongoDB 容器
   docker-compose ps mongo

   # 测试连接
   docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"
   ```

3. **API 连接失败**
   ```bash
   # 检查环境变量
   docker-compose exec app env | grep API

   # 查看应用日志
   docker-compose logs app
   ```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs app
docker-compose logs mongo

# 实时查看日志
docker-compose logs -f app

# 查看最近 100 行日志
docker-compose logs --tail=100 app
```

## 安全建议

1. **API 密钥安全**
   - 不要在代码中硬编码 API 密钥
   - 使用 `.env` 文件管理敏感信息
   - 定期轮换 API 密钥

2. **网络安全**
   - 配置防火墙限制端口访问
   - 使用 VPN 或内网访问
   - 定期更新系统和软件

3. **数据安全**
   - 定期备份数据库
   - 监控异常交易活动
   - 设置合理的资金限额

## 性能优化

### 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化网络参数
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
```

### Docker 优化

```bash
# 清理未使用的镜像和容器
docker system prune -a

# 限制容器资源使用
# 在 docker-compose.yml 中添加：
# deploy:
#   resources:
#     limits:
#       memory: 1G
#       cpus: '0.5'
```

## 监控和维护

### 健康检查

```bash
# 检查服务健康状态
docker-compose ps

# 检查容器资源使用
docker stats

# 检查磁盘使用
df -h /data/docker/ThorCQ/
```

### 定期维护

```bash
# 备份数据
docker-compose exec mongo mongodump --out /backup/$(date +%Y%m%d)

# 清理日志
docker-compose logs --tail=0 -f app > /dev/null

# 更新镜像
docker-compose pull
docker-compose up -d
```

## 技术支持

- 微信：3404034
- 邮箱：block@163.com
- GitHub Issues：提交问题和建议

## 免责声明

本项目仅供学习和研究使用，不构成投资建议。使用本项目进行实际交易的所有风险由用户自行承担。请在充分了解风险的前提下谨慎使用。
