// MongoDB 初始化脚本
// 创建应用数据库和用户

// 切换到 binance 数据库
db = db.getSiblingDB('binance');

// 创建应用用户
db.createUser({
  user: 'trader',
  pwd: 'trader123',
  roles: [
    {
      role: 'readWrite',
      db: 'binance'
    }
  ]
});

// 创建订单集合
db.createCollection('ETH/USDT');

// 创建索引
db['ETH/USDT'].createIndex({ "order_id": 1 }, { unique: true });
db['ETH/USDT'].createIndex({ "order_status": 1 });
db['ETH/USDT'].createIndex({ "order_side": 1 });

print('MongoDB 初始化完成');
print('数据库: binance');
print('用户: trader');
print('集合: ETH/USDT');
