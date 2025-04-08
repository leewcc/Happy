import tushare as ts
import pandas as pd
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymysql
from datetime import datetime, timedelta
import schedule

# 设置tushare的token
ts.set_token('611ed160db014d775da9f5c6c511dd4cc269e5429b5815e885208216')
pro = ts.pro_api()

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'leewcc',
    'password': 'leewcc',
    'database': 'happy',
    'charset': 'utf8mb4'
}

# 全局变量存储涨跌停价格映射
LIMIT_PRICE_MAP = {}

# 全局变量存储股票列表
STOCK_GROUPS = []
NUM_THREADS = 12

# 添加概念黑名单和映射
CONCEPT_BLACKLIST = {
    '融资融券', '转融券标的', '深股通', '人民币', '富时罗素概念股', '富时罗素概念', '沪股通', 
    '高股息精选', '京津冀一体化', '专精特新', '台湾概念股', '统一大市场', '股权转让', 
    '虚拟数字人', '独角兽概念', '粤港澳大湾区', '共同富裕示范区', '联想概念', '三星', 
    '大湾区', '自贸区', '共享经济', '央视财经50', '数据交易中心', '汽车电商', '共享', 
    '进口博览会', '自由贸易港', '海底捞概念', '海水淡化', '食盐', '溴素', '白炭黑', 
    '同花顺', '贸易区', 'Web', '雄安新区', '快手概念', '人脸识别', '3D打印', '电子信息', 
    '高端装备', '网络直播', '比亚迪概念', '创投', '储能', '乡村振兴', '中俄贸易概念',
    '腾讯概念', '信创', '智慧城市', '物联网', '区块链', '抖音概念', 
    'ChatGPT概念', '数据要素', '量子科技', '智能家居', '小米概念', 'AIGC概念', 
    '阿里巴巴概念', '老字号', '体育产业', '云办公', '动力电池回收', '碳中和', 
    '外贸受益概念', '长三角一体化', '军民融合', '智能穿戴', '新疆振兴',
    'MiniLED', 'MicroLED概念', '无线耳机', '分拆上市意愿','同花顺中特估100','上证180成份股',
    '上证50样本股', '沪深300样本股','同花顺新质50', '同花顺出海50','中证500成份股',
}

CONCEPT_MAPPING = {
    '国企改革': ['国企改革', '地方国企改革', '央企国企改革'],
    '机器人': ['机器人', '减速器', '传感器', '工业化', '工业机器人'],
    '锂电池': ['锂电池', '固态电池', '宁德时代', '钠离子电池', '锂'],
    '半导体': ['芯片', '光刻胶', '光刻机', '先进封装', '元器件', 'PCB'],
    '文化传媒': ['文化传媒', 'IP', '广告营销', '影视娱乐', '短剧', '出版', '知识产权'],
    '游戏': ['游戏'],
    '消费电子': ['消费电子', '虚拟现实', 'AI PC', '混合现实', 'AI眼镜', '柔性屏'],
    '算力': ['算力', 'CPO', '东数西算'],
    '无人驾驶': ['无人驾驶', '智能交通', '车路协同'],
    '大模型': ['模态AI', 'Sora', '智谱AI', 'AI语料'],
    '低空经济': ['低空', '无人机', '飞行汽车'],
    '光伏': ['光伏', '钙钛矿', 'TOPCON', 'HJT'],
    '房地产': ['物业', '房地产'],
    '医药': ['医疗', '诊断', '药', '肝炎', 'CRO', '流感', '螺杆菌', '猴痘'],
    '农业': ['农', '猪肉', '养鸡', '大豆', '人造肉'],
    '零售': ['消费', '零售', '乳业'],
    '化工': ['化工', '氢氟酸', '双氧水', '纯碱', '硝酸钠', '硫酸钾'],
    '上海': ['浦东'],
    '有色金属': ['金属'],
    '合成生物': ['合成生物', '维生素'],
    '食品': ['食品', '预制菜', '零食'],
    '互联网金融': ['金融', '期货', '互联网金融'],
    '数字经济': ['数字经济', '数字货币'],
    '5G': ['5G', '6G'],
    '三胎养老': ['三胎', '养老', '辅助生殖'],
    '安全': ['安防', '网络安全', '数据安全'],
    '电力': ['风电', '电网', '绿色电力'],
    '物流': ['物流'],
    '酒店旅游': ['旅游'],
    '教育': ['教育'],
    '环保': ['污水', '节能环保', '土壤修复'],
    '化债': ['化债', 'PPP'],
    '可控核聚变': ['核电']
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def init_limit_prices():
    """从数据库初始化涨跌停价格映射"""
    global LIMIT_PRICE_MAP
    try:
        today = datetime.now().strftime('%Y%m%d')
        print(f"正在从数据库获取 {today} 的涨跌停价格数据...")
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询当天的涨跌停价格数据
        sql = "SELECT ts_code, up_limit, down_limit FROM stock_limit_prices WHERE trade_date = %s"
        cursor.execute(sql, (today,))
        results = cursor.fetchall()
        
        if not results:
            print(f"数据库中没有找到 {today} 的涨跌停价格数据")
            return False
            
        # 将数据转换为字典格式
        for row in results:
            LIMIT_PRICE_MAP[row[0]] = {
                'up_limit': float(row[1]),
                'down_limit': float(row[2])
            }
                
        return True
        
    except Exception as e:
        print(f"\n获取涨跌停价格失败，详细错误:")
        print(f"错误类型: {type(e)}")
        print(f"错误信息: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def init_stock_list():
    """从数据库初始化股票列表分组"""
    global STOCK_GROUPS
    try:
        print("正在从数据库获取股票列表...")
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询股票列表
        sql = "SELECT stock_code FROM stock"
        cursor.execute(sql)
        results = cursor.fetchall()
        
        if not results:
            print("数据库中没有找到股票列表数据")
            return False
            
        # 将查询结果转换为列表
        stock_codes = [row[0] for row in results]
        
        # 将股票列表分成多份，每份不超过50个（新浪数据源限制）
        STOCK_GROUPS = []
        for i in range(0, len(stock_codes), 50):
            STOCK_GROUPS.append(stock_codes[i:i+50])
        
        print(f"成功初始化股票列表，共 {len(stock_codes)} 只股票，分成 {len(STOCK_GROUPS)} 组")
        return True
        
    except Exception as e:
        print(f"初始化股票列表失败，详细错误:")
        print(f"错误类型: {type(e)}")
        print(f"错误信息: {str(e)}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def calculate_limits(row):
    """计算是否涨跌停"""
    ts_code = row.get('TS_CODE') or row.get('ts_code')  # 兼容大小写
    if ts_code not in LIMIT_PRICE_MAP:
        return 0, 0, 0
    
    limit_info = LIMIT_PRICE_MAP[ts_code]
    
    # 使用缓存的涨跌停价格判断
    price = float(row.get('PRICE') or row.get('price') or 0)
    pre_close = float(row.get('PRE_CLOSE') or row.get('pre_close') or 0)
    
    is_up_limit = 1 if abs(price - limit_info['up_limit']) < 0.01 else 0
    is_down_limit = 1 if abs(price - limit_info['down_limit']) < 0.01 else 0
    
    # 计算竞价涨幅
    bid_ratio = ((price - pre_close) / pre_close * 100) if pre_close != 0 else 0
    
    return is_up_limit, is_down_limit, bid_ratio

def save_to_db(df):
    """保存数据到MySQL"""
    if df is None or df.empty:
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for index, row in df.iterrows():
            try:
                # 计算涨跌停和竞价涨幅
                is_up_limit, is_down_limit, bid_ratio = calculate_limits(row)
                
                # 当前日期和时间
                current_date = datetime.now().strftime('%Y-%m-%d')
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # 检查是否已有首次涨停时间记录
                check_sql = """
                    SELECT first_limit_up_time 
                    FROM realtime_quotes 
                    WHERE ts_code = %s AND trade_date = %s
                """
                cursor.execute(check_sql, (row.get('TS_CODE'), current_date))
                result = cursor.fetchone()
                
                # 如果是涨停且没有首次涨停时间记录，则更新首次涨停时间
                first_limit_up_time = None
                if is_up_limit == 1 and (result is None or result[0] is None):
                    first_limit_up_time = current_time
                
                sql = """
                    INSERT INTO realtime_quotes (
                        ts_code, name, trade_date, trade_time, open, pre_close, 
                        price, high, low, bid_price, ask_price, volume, amount,
                        bid_ratio, bid_amount, is_up_limit, is_down_limit,
                        first_limit_up_time
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        price = VALUES(price),
                        high = VALUES(high),
                        low = VALUES(low),
                        volume = VALUES(volume),
                        amount = VALUES(amount),
                        bid_ratio = VALUES(bid_ratio),
                        is_up_limit = VALUES(is_up_limit),
                        is_down_limit = VALUES(is_down_limit),
                        first_limit_up_time = COALESCE(first_limit_up_time, VALUES(first_limit_up_time))
                """
                
                # 准备SQL参数
                params = (
                    row.get('TS_CODE'), row.get('NAME'), current_date, current_time,
                    row.get('OPEN'), row.get('PRE_CLOSE'), row.get('PRICE'), 
                    row.get('HIGH'), row.get('LOW'), row.get('BID'), row.get('ASK'),
                    row.get('VOLUME'), row.get('AMOUNT'), bid_ratio, 
                    row.get('AMOUNT'), is_up_limit, is_down_limit,
                    first_limit_up_time
                )
                cursor.execute(sql, params)
                
            except Exception as row_error:
                print(f"处理行数据失败:")
                print(f"错误类型: {type(row_error)}")
                print(f"错误信息: {str(row_error)}")
                print("行数据:", row.to_dict())
                continue
        
        conn.commit()
        print(f"\n成功保存 {len(df)} 条记录到数据库")
        
    except Exception as e:
        print(f"\n保存数据到数据库失败:")
        print(f"错误类型: {type(e)}")
        print(f"错误信息: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_stock_quotes(stock_list):
    """获取单个线程中的股票实时行情"""
    results = []
    stock_codes = ','.join(stock_list)
    try:
        df = ts.realtime_quote(stock_codes, src='sina')
        if df is not None and not df.empty:
            # 保存到数据库
            save_to_db(df)
            results.append(df)
        time.sleep(0.5)
    except Exception as e:
        print(f"获取股票行情失败: {str(e)}")
    return results

def split_list(lst, n):
    """将列表平均分成n份"""
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

def fetch_all_quotes():
    """获取所有股票的实时行情"""
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"\n开始获取 {current_time} 的实时行情...")
    
    # 将股票组分配给线程
    split_stocks = split_list(STOCK_GROUPS, NUM_THREADS)
    
    # 创建线程池
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for stock_group_list in split_stocks:
            flat_stocks = [stock for group in stock_group_list for stock in group]
            future = executor.submit(get_stock_quotes, flat_stocks)
            futures.append(future)
        
        # 等待所有线程完成
        for future in as_completed(futures):
            try:
                results = future.result()
                if results:
                    print(f"线程处理完成，成功获取 {sum(len(df) for df in results)} 只股票的行情")
            except Exception as e:
                print(f"线程执行出错: {str(e)}")

def is_trade_time():
    """判断当前是否为交易时间"""
    return True
    now = datetime.now()
    current_time = now.time()
    
    # 判断是否为工作日
    if now.weekday() >= 5:  # 周六日不执行
        return False
    
    # 上午交易时间 9:30-11:30
    morning_start = datetime.strptime('09:30:00', '%H:%M:%S').time()
    morning_end = datetime.strptime('11:30:00', '%H:%M:%S').time()
    
    # 下午交易时间 13:00-15:00
    afternoon_start = datetime.strptime('13:00:00', '%H:%M:%S').time()
    afternoon_end = datetime.strptime('15:00:00', '%H:%M:%S').time()
    
    return (morning_start <= current_time <= morning_end) or \
           (afternoon_start <= current_time <= afternoon_end)

def run_schedule():
    """运行定时任务"""
    if is_trade_time():
        fetch_all_quotes()

def main():
    # 初始化涨跌停价格映射
    if not init_limit_prices():
        print("初始化涨跌停价格失败，程序退出")
        return
    
    # 初始化股票列表
    if not init_stock_list():
        print("初始化股票列表失败，程序退出")
        return
    
    # 设置定时任务，每分钟执行一次
    schedule.every().minute.do(run_schedule)
    
    print("开始运行实时行情获取程序...")
    print("程序将在交易时间内每分钟获取一次行情数据")
    
    # 运行定时任务
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n程序已停止运行")
            break
        except Exception as e:
            print(f"运行出错: {str(e)}")
            time.sleep(60)  # 出错后等待1分钟再继续

def log(msg):
    """打印带时间戳的日志"""
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"[{current_time}] {msg}")

class QuotesManager:
    def __init__(self):
        log("初始化 QuotesManager...")
        self.ready = False
        self.quotes_data = {}
        self.index_data = {}
        self.market_stats = {}
        self.amount_trend = []
        self.thread = None
        self.index_thread = None
        
        # 缓存股票的行业和概念数据
        self.stock_info_cache = {}
        
        # 指数代码列表
        self.index_codes = {
            'sh': {'code': '000001.SH', 'name': '上证指数'},
            'sz': {'code': '399001.SZ', 'name': '深证成指'},
            'cyb': {'code': '399006.SZ', 'name': '创业板指'},
            'kc': {'code': '000688.SH', 'name': '科创50'},
            'bj': {'code': '899050.BJ', 'name': '北证50'}
        }
        log("QuotesManager 初始化完成")

    def is_ready(self):
        """检查是否初始化完成"""
        return self.ready

    def start(self):
        """启动行情管理器"""
        if not init_limit_prices():
            print("初始化涨跌停价格失败")
            return
        
        if not init_stock_list():
            print("初始化股票列表失败")
            return
            
        # 初始化股票信息缓存
        self._init_stock_info_cache()
        
        self.ready = True
        
        # 启动个股行情线程
        self.thread = threading.Thread(target=self._run_stock_quotes)
        self.thread.daemon = True
        self.thread.start()
        
        # 启动指数行情线程
        self.index_thread = threading.Thread(target=self._run_index_quotes)
        self.index_thread.daemon = True
        self.index_thread.start()
    
    def _init_stock_info_cache(self):
        """初始化股票信息缓存"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 获取所有股票的行业信息
            sql_industry = "SELECT stock_code, industry FROM stock"
            cursor.execute(sql_industry)
            industry_results = cursor.fetchall()
            
            # 获取所有股票的概念信息
            sql_concepts = """
                SELECT stock_code, GROUP_CONCAT(DISTINCT sector_name) as concepts
                FROM concept_stock 
                WHERE (out_date IS NULL OR out_date = '')
                AND (is_new = 'Y' OR is_new IS NULL)
                GROUP BY stock_code
            """
            cursor.execute(sql_concepts)
            concept_results = cursor.fetchall()
            
            # 初始化缓存
            for stock_code, industry in industry_results:
                self.stock_info_cache[stock_code] = {
                    'industry': industry or '-',
                    'concepts': '-'
                }
            
            # 更新概念信息
            for stock_code, concepts in concept_results:
                if stock_code in self.stock_info_cache and concepts:
                    # 分割概念列表
                    concept_list = concepts.split(',')
                    # 规范化概念
                    normalized_concepts = []
                    for concept in concept_list:
                        norm_concept = normalize_concept(concept.strip())
                        if norm_concept:
                            normalized_concepts.append(norm_concept)
                    # 去重
                    normalized_concepts = list(set(normalized_concepts))
                    # 更新缓存
                    self.stock_info_cache[stock_code]['concepts'] = ','.join(normalized_concepts) if normalized_concepts else '-'
            
            log(f"成功缓存 {len(self.stock_info_cache)} 只股票的行业和概念信息")
            
        except Exception as e:
            log(f"初始化股票信息缓存失败: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def _run_stock_quotes(self):
        """运行个股行情更新循环"""
        log("个股行情线程启动")
        # 立即执行一次数据获取
        self._update_stock_quotes()
        
        # 设置定时任务
        schedule.every().minute.do(self._update_stock_quotes)
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                log(f"个股行情更新出错: {str(e)}")
                time.sleep(60)
    
    def _run_index_quotes(self):
        """运行指数行情更新循环"""
        log("指数行情线程启动")
        # 立即执行一次数据获取
        self._update_index_quotes()
        
        # 设置定时任务
        schedule.every(30).seconds.do(self._update_index_quotes)
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                log(f"指数行情更新出错: {str(e)}")
                time.sleep(10)

    def _update_index_quotes(self):
        """更新指数行情"""
        if not is_trade_time():
            return
            
        try:
            # log("开始更新指数行情...")
            success_count = 0
            
            for name, info in self.index_codes.items():
                quote = self._get_index_quote(info['code'])
                if quote:
                    self.index_data[info['code']] = quote
                    success_count += 1
                    # log(f"{info['name']}: {quote['price']} ({quote['change_pct']}%)")
            
            # log(f"指数行情更新完成，成功获取 {success_count}/{len(self.index_codes)} 个指数")
            
            # 更新成交额趋势
            current_time = datetime.now()
            main_indices = ['000001.SH', '399001.SZ', '399006.SZ']
            total_amount = sum(self.index_data[code]['amount'] 
                             for code in main_indices 
                             if code in self.index_data)
            
            # log(f"主要指数总成交额: {total_amount/100000000:.2f}亿")
            
            self.amount_trend.append({
                'time': current_time.strftime('%H:%M:%S'),
                'amount': total_amount,
                'sh_amount': self.index_data.get('000001.SH', {}).get('amount', 0),
                'sz_amount': self.index_data.get('399001.SZ', {}).get('amount', 0),
                'cyb_amount': self.index_data.get('399006.SZ', {}).get('amount', 0)
            })
            
            if len(self.amount_trend) > 30:
                self.amount_trend = self.amount_trend[-30:]
                
        except Exception as e:
            log(f"更新指数行情失败: {str(e)}")

    def _update_stock_quotes(self):
        """更新个股行情"""
        if not is_trade_time():
            return
            
        try:
            # log("开始更新个股行情...")
            split_stocks = split_list(STOCK_GROUPS, NUM_THREADS)
            all_quotes = []
            
            with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                futures = []
                for i, stock_group_list in enumerate(split_stocks):
                    flat_stocks = [stock for group in stock_group_list for stock in group]
                    # log(f"线程 {i+1} 开始处理 {len(flat_stocks)} 只股票")
                    future = executor.submit(self._get_stock_quotes, flat_stocks)
                    futures.append(future)
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        all_quotes.extend(result)
            
            # log(f"个股行情更新完成，成功获取 {len(all_quotes)} 只股票")
            self.quotes_data = all_quotes
            
            # 更新市场统计
            self._update_market_stats()
            
        except Exception as e:
            log(f"更新个股行情失败: {str(e)}")

    def _get_index_quote(self, code):
        """获取单个指数行情"""
        try:
            # 不需要转换代码格式，直接使用正确的代码
            # log(f"获取指数 {code} 行情...")
            
            df = ts.realtime_quote(code)
            if df is not None and not df.empty:
                try:
                    price = float(df['PRICE'].iloc[0])
                    pre_close = float(df['PRE_CLOSE'].iloc[0])
                    change = price - pre_close
                    change_pct = (change / pre_close * 100) if pre_close != 0 else 0
                    
                    quote = {
                        'ts_code': code,
                        'name': df['NAME'].iloc[0],
                        'price': price,
                        'pre_close': pre_close,
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2),
                        'volume': float(df['VOLUME'].iloc[0]),
                        'amount': float(df['AMOUNT'].iloc[0]),
                        'open': float(df['OPEN'].iloc[0]),
                        'high': float(df['HIGH'].iloc[0]),
                        'low': float(df['LOW'].iloc[0])
                    }
                    # log(f"指数 {code} 获取成功: {price} ({change_pct:+.2f}%)")
                    return quote
                except Exception as e:
                    log(f"处理指数 {code} 数据失败: {str(e)}")
                    log(f"原始数据: {df.iloc[0].to_dict()}")
            else:
                log(f"获取指数 {code} 返回空数据")
        except Exception as e:
            log(f"获取指数 {code} 行情失败: {str(e)}")
        return None

    def _update_market_stats(self):
        """更新市场统计数据"""
        try:
            # 基本统计
            up_count = sum(1 for quote in self.quotes_data if quote['change_pct'] > 0)
            down_count = sum(1 for quote in self.quotes_data if quote['change_pct'] < 0)
            limit_up_count = sum(1 for quote in self.quotes_data if quote['is_up_limit'])
            limit_down_count = sum(1 for quote in self.quotes_data if quote['is_down_limit'])
            
            # 添加涨跌分布数据
            stocks_data = [{
                'ts_code': quote['ts_code'],
                'change_pct': quote['change_pct']
            } for quote in self.quotes_data]
            
            self.market_stats = {
                'up_count': up_count,
                'down_count': down_count,
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'stocks': stocks_data,  # 添加个股涨跌幅数据
                'total_amount': sum(self.index_data[code]['amount'] 
                                  for code in ['000001.SH', '399001.SZ', '399006.SZ'] 
                                  if code in self.index_data),
                'sh_amount': self.index_data.get('000001.SH', {}).get('amount', 0),
                'sz_amount': self.index_data.get('399001.SZ', {}).get('amount', 0),
                'cyb_amount': self.index_data.get('399006.SZ', {}).get('amount', 0)
            }
            
            log(f"市场统计 - 上涨: {up_count} 下跌: {down_count} 涨停: {limit_up_count} 跌停: {limit_down_count}")
            
        except Exception as e:
            log(f"更新市场统计失败: {str(e)}")

    def _get_stock_quotes(self, stock_list):
        """获取单个线程中的股票实时行情"""
        try:
            stock_codes = ','.join(stock_list)
            # log(f"正在获取 {len(stock_list)} 只股票的行情...")
            
            df = ts.realtime_quote(stock_codes)
            if df is not None and not df.empty:
                quotes = []
                success_count = 0
                error_count = 0
                
                for _, row in df.iterrows():
                    try:
                        ts_code = row['TS_CODE']
                        stock_info = self.stock_info_cache.get(ts_code, {'industry': '-', 'concepts': '-'})
                        
                        # 计算涨跌停和涨跌幅
                        is_up_limit, is_down_limit, change_pct = calculate_limits(row)
                        
                        # 转换金额为数值类型
                        amount = float(row.get('AMOUNT', 0))
                        bid_amount = float(row.get('BID_AMOUNT', 0))
                        
                        quote = {
                            'ts_code': ts_code,
                            'name': row['NAME'],
                            'price': float(row['PRICE']),
                            'change_pct': change_pct,
                            'amount': amount,
                            'bid_amount': bid_amount,
                            'is_up_limit': is_up_limit,
                            'is_down_limit': is_down_limit,
                            'industry': stock_info['industry'],
                            'concepts': stock_info['concepts']
                        }
                        quotes.append(quote)
                        success_count += 1
                        
                        if is_up_limit or is_down_limit:
                            status = "涨停" if is_up_limit else "跌停"
                            
                    except Exception as e:
                        error_count += 1
                        log(f"处理股票 {row.get('TS_CODE', 'unknown')} 数据失败: {str(e)}")
                        log(f"错误详情: {str(e)}")
                        log(f"原始数据: {row.to_dict()}")
                
                # log(f"股票行情获取完成 - 成功: {success_count}, 失败: {error_count}")
                return quotes
            else:
                log("获取股票行情返回空数据")
                
        except Exception as e:
            log(f"批量获取股票行情失败: {str(e)}")
        return []
    
    def get_stock_list(self):
        """获取个股列表"""
        try:
            # 返回个股行情数据
            return self.quotes_data
        except Exception as e:
            log(f"获取个股列表失败: {str(e)}")
            return []

    def get_index_quotes(self):
        """获取指数行情"""
        return list(self.index_data.values())

    def get_index_quote(self, code):
        """获取单个指数行情"""
        return self.index_data.get(code)

    def get_main_indices_amount(self):
        """获取主要指数成交额"""
        main_indices = ['000001.SH', '399001.SZ', '399006.SZ']
        return {
            'total': sum(self.index_data[code]['amount'] 
                        for code in main_indices 
                        if code in self.index_data),
            'sh': self.index_data.get('000001.SH', {}).get('amount', 0),
            'sz': self.index_data.get('399001.SZ', {}).get('amount', 0),
            'cyb': self.index_data.get('399006.SZ', {}).get('amount', 0)
        }

    def get_amount_trend(self):
        """获取成交额趋势数据"""
        try:
            return self.amount_trend
        except Exception as e:
            log(f"获取成交额趋势失败: {str(e)}")
            return []

    def get_market_stats(self):
        """获取市场统计数据"""
        try:
            return self.market_stats
        except Exception as e:
            log(f"获取市场统计失败: {str(e)}")
            return {}

def get_stock_industry(ts_code):
    """获取股票所属行业"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT industry FROM stock WHERE stock_code = %s"
        cursor.execute(sql, (ts_code,))
        result = cursor.fetchone()
        return result[0] if result else '-'
    except Exception as e:
        log(f"获取股票 {ts_code} 行业失败: {str(e)}")
        return '-'
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_stock_concepts(ts_code):
    """获取股票概念"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT GROUP_CONCAT(DISTINCT sector_name) 
            FROM concept_stock 
            WHERE stock_code = %s 
            AND (out_date IS NULL OR out_date = '')
            AND (is_new = 'Y' OR is_new IS NULL)
        """
        cursor.execute(sql, (ts_code,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else '-'
    except Exception as e:
        log(f"获取股票 {ts_code} 概念失败: {str(e)}")
        return '-'
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def normalize_concept(concept):
    """合并同义概念"""
    # 移除概念和主题后缀
    concept = concept.replace('概念', '').replace('主题', '')
    
    # 如果在黑名单中则跳过
    if concept in CONCEPT_BLACKLIST:
        return None
        
    # 查找并返回规范化的概念名称
    for normalized, keywords in CONCEPT_MAPPING.items():
        if any(keyword in concept for keyword in keywords):
            return normalized
    return concept

# 如果直接运行此文件，则启动独立进程
if __name__ == '__main__':
    manager = QuotesManager()
    manager.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序已停止运行") 