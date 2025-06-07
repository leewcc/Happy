import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging
from sqlalchemy import text

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加概念黑名单
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
    'MiniLED', 'MicroLED概念', '无线耳机', '分拆上市意愿', '中证500成份股','2024三季报预增',
    '上证380成份股','2024年报预增',
}

def get_db_connection():
    """获取数据库连接"""
    return create_engine('mysql+pymysql://root:root@localhost:3306/happy')

def get_stock_list():
    """获取股票列表"""
    # 这里使用示例数据，实际应该从数据库或API获取
    df = pd.DataFrame({
        'code': ['000001', '600001', '600519', '300750'],
        'name': ['平安银行', '邯郸钢铁', '贵州茅台', '宁德时代'],
        'price': [10.5, 15.2, 1800, 220],
        'industry': ['银行', '钢铁', '白酒', '新能源'],
        'concept': ['金融科技,数字货币', '碳中和', '消费升级,白酒', '新能源汽车,储能'],
        'turnover': [10000, 8000, 5000, 12000],  # 成交额（万元）
        'avg_turnover': [12000, 7500, 4800, 11500],  # 平均成交额
        'turnover_days': [5, 5, 5, 5]  # 成交额统计天数
    })
    return df.to_dict('records')

def get_industries():
    """获取行业列表"""
    engine = get_db_connection()
    query = "SELECT DISTINCT industry FROM stock WHERE industry IS NOT NULL"
    df = pd.read_sql(query, engine)
    return df['industry'].tolist()

def get_concepts():
    """获取概念列表"""
    engine = get_db_connection()
    query = """
    SELECT DISTINCT sector_name 
    FROM concept_stock 
    WHERE sector_name NOT IN %(blacklist)s
    """
    df = pd.read_sql(query, engine, params={'blacklist': tuple(CONCEPT_BLACKLIST)})
    return df['sector_name'].tolist()

def normalize_concepts(concepts_str):
    """合并同义概念"""
    logger.info(f"\n开始合并同义概念: {concepts_str}")
    if not concepts_str or concepts_str == '-':
        logger.info("空概念字符串，返回 '-'")
        return '-'
    
    concept_mapping = {
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
    
    # 分割并过滤概念
    filtered_concepts = set()  # 使用集合去重
    for concept in concepts_str.split(','):
        concept = concept.strip()
        if concept not in CONCEPT_BLACKLIST:
            # 查找并返回规范化的概念名称
            found_match = False
            for normalized, keywords in concept_mapping.items():
                if any(keyword in concept for keyword in keywords):
                    filtered_concepts.add(normalized)
                    found_match = True
                    break
            if not found_match:
                filtered_concepts.add(concept)
    
    return ','.join(sorted(filtered_concepts)) if filtered_concepts else '-'

def filter_stocks(filters):
    """根据条件筛选股票"""
    engine = get_db_connection()
    result_stocks = None
    
    logger.info(f"开始筛选，筛选条件: {filters}")

    # 获取指定日期或最新交易日期
    if filters.get('trade_date'):
        latest_date = filters['trade_date']
    else:
        query = "SELECT MAX(trade_date) as latest_date FROM daily_data"
        latest_date = pd.read_sql(query, engine).iloc[0]['latest_date']
    
    logger.info(f"使用交易日期: {latest_date}")

    # 低吸战法筛选
    if filters.get('dip_buy'):
        try:
            # 1. 获取最近两个交易日
            date_query = """
            SELECT DISTINCT trade_date
            FROM daily_data
            WHERE trade_date <= %(latest_date)s
            ORDER BY trade_date DESC
            LIMIT 2
            """
            dates_df = pd.read_sql(date_query, engine, params={'latest_date': latest_date})
            if len(dates_df) < 2:
                logger.warning("没有足够的交易日数据进行低吸战法筛选")
                return []
            
            # 确保日期格式统一
            latest_date = dates_df.iloc[0]['trade_date'].strftime('%Y-%m-%d')
            prev_date = dates_df.iloc[1]['trade_date'].strftime('%Y-%m-%d')
            
            logger.info(f"处理日期: latest_date={latest_date}, prev_date={prev_date}")
            
            # 2. 查询第一天（最新交易日）满足条件的股票
            latest_day_query = """
            SELECT DISTINCT stock_code
            FROM daily_data
            WHERE trade_date = %(latest_date)s
            AND close_price < open_price
            AND close_price/open_price <= 0.95
            """
            logger.info("执行最新交易日查询:")
            logger.info(f"SQL: {latest_day_query}")
            logger.info(f"参数: latest_date={latest_date}")
            
            latest_stocks = pd.read_sql(latest_day_query, engine, params={'latest_date': latest_date})
            logger.info(f"最新交易日满足条件的股票数: {len(latest_stocks)}")
            logger.info(f"最新交易日满足条件的股票列表: {sorted(latest_stocks['stock_code'].tolist())}")
            
            # 3. 查询前一天满足条件的股票
            prev_day_query = """
            SELECT DISTINCT stock_code
            FROM daily_data
            WHERE trade_date = %(prev_date)s
            AND close_price < open_price
            AND close_price/open_price <= 0.95
            AND open_price > ma_5
            """
            
            try:
                logger.info("执行前一交易日查询:")
                logger.info(f"SQL: {prev_day_query}")
                logger.info(f"参数: prev_date={prev_date}")
                
                prev_stocks = pd.read_sql(prev_day_query, engine, params={'prev_date': prev_date})
                logger.info(f"前一交易日满足条件的股票数: {len(prev_stocks)}")
                logger.info(f"前一交易日满足条件的股票列表: {sorted(prev_stocks['stock_code'].tolist())}")
                
                # 打印被过滤掉的股票
                latest_only = set(latest_stocks['stock_code']) - set(prev_stocks['stock_code'])
                prev_only = set(prev_stocks['stock_code']) - set(latest_stocks['stock_code'])
                logger.info(f"仅在最新交易日满足条件的股票: {sorted(list(latest_only))}")
                logger.info(f"仅在前一交易日满足条件的股票: {sorted(list(prev_only))}")
                
                # 与之前的结果取交集（如果有的话）
                dip_buy_stocks = set(latest_stocks['stock_code']) & set(prev_stocks['stock_code'])
                logger.info(f"低吸战法筛选后的股票数: {len(dip_buy_stocks)}")
                
                # 与之前的结果取交集（如果有的话）
                result_stocks = dip_buy_stocks if result_stocks is None else result_stocks & dip_buy_stocks
                logger.info(f"与其他条件取交集后剩余股票数: {len(result_stocks) if result_stocks else 0}")
                
            except Exception as sql_error:
                logger.error("SQL执行错误:")
                logger.error(f"SQL语句: {prev_day_query}")
                logger.error(f"参数: prev_date={prev_date}")
                logger.error(f"错误信息: {str(sql_error)}")
                raise
            
        except Exception as e:
            logger.error("低吸战法筛选出错:")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误信息: {str(e)}")
            logger.error("详细堆栈:", exc_info=True)
            return []

    # 1. 行业筛选
    if filters.get('industry'):
        query = """
        SELECT DISTINCT LEFT(stock_code, 6) as stock_code 
        FROM stock 
        WHERE industry = %(industry)s
        """
        params = {'industry': filters['industry']}
        logger.info(f"SQL - 行业筛选: {query}")
        logger.info(f"参数: {params}")
        df_industry = pd.read_sql(query, engine, params=params)
        result_stocks = set(df_industry['stock_code'])
        logger.info(f"行业筛选后剩余股票数: {len(result_stocks)}")

    # 2. 概念筛选
    if filters.get('concepts'):
        concepts = [c.strip() for c in filters['concepts'].split(',') if c.strip()]
        logger.info(f"执行概念筛选: {concepts}")
        if concepts:
            stocks_by_concept = []
            for concept in concepts:
                query = """
                SELECT DISTINCT SUBSTRING(stock_code, 1, 6) as stock_code 
                FROM concept_stock 
                WHERE sector_name = %(concept)s
                """
                params = {'concept': concept}
                logger.info(f"SQL - 概念筛选: {query}")
                logger.info(f"参数: {params}")
                df_concept = pd.read_sql(query, engine, params=params)
                concept_stocks = set(df_concept['stock_code'])
                logger.info(f"概念 {concept} 包含股票数: {len(concept_stocks)}")
                stocks_by_concept.append(concept_stocks)
            
            concept_stocks = set.intersection(*stocks_by_concept) if stocks_by_concept else set()
            logger.info(f"多个概念取交集后剩余股票数: {len(concept_stocks)}")
            result_stocks = concept_stocks if result_stocks is None else result_stocks.intersection(concept_stocks)
            logger.info(f"与行业筛选结果取交集后剩余股票数: {len(result_stocks) if result_stocks else 0}")

    # 如果没有行业和概念筛选，获取所有股票
    if result_stocks is None:
        query = "SELECT DISTINCT stock_code FROM daily_data"
        logger.info(f"SQL - 获取所有股票: {query}")
        df_all = pd.read_sql(query, engine)
        result_stocks = set(df_all['stock_code'])
        logger.info(f"未指定行业和概念，获取所有股票数: {len(result_stocks)}")

    # 3. 成交额筛选 - 使用stock_turnover_avg表
    if filters.get('turnover_days') and filters.get('turnover_amount'):
        days = int(filters['turnover_days'])
        amount = float(filters['turnover_amount']) * 100000  # 转换为元（输入为亿元）
        
        # 当天数大于0时才进行成交额筛选
        if days > 0:
            # 构建查询
            avg_column = f'avg_{days}d'  # 根据天数选择对应的平均值列
            if days > 5:  # 如果天数超过5天，使用5日均值
                logger.warning(f"请求的天数 {days} 超过5天，将使用5日均值")
                avg_column = 'avg_5d'
                
            query = f"""
            SELECT DISTINCT SUBSTRING_INDEX(stock_code, '.', 1) as stock_code
            FROM stock_turnover_avg
            WHERE trade_date = %(latest_date)s
            AND {avg_column} >= %(amount)s
            """
            
            params = {
                'latest_date': latest_date,
                'amount': amount
            }
            
            logger.info(f"SQL - 成交额筛选: {query}")
            logger.info(f"参数: {params}")
            
            df_turnover = pd.read_sql(query, engine, params=params)
            turnover_stocks = set(df_turnover['stock_code'])
            # 与之前的结果取交集
            result_stocks = turnover_stocks if result_stocks is None else result_stocks & turnover_stocks
            logger.info(f"成交额筛选后剩余股票数: {len(result_stocks)}")
        else:
            logger.info("天数为0，跳过成交额筛选")

    # 4. 均线多头筛选（增加均线发散条件）
    if filters.get('ma_trend') and result_stocks:
        query = """
        WITH today_data AS (
            SELECT 
                stock_code,
                ma_5,
                ma_10,
                ma_20,
                ma_60,
                close_price,
                -- 计算今天的均线间距
                (ma_5 - ma_10) as gap_5_10_today,
                (ma_10 - ma_20) as gap_10_20_today,
                (ma_20 - ma_60) as gap_20_60_today
            FROM daily_data
            WHERE stock_code IN %(stock_codes)s
            AND trade_date = %(latest_date)s
        ),
        yesterday_data AS (
            SELECT 
                stock_code,
                -- 计算昨天的均线间距
                (ma_5 - ma_10) as gap_5_10_yesterday,
                (ma_10 - ma_20) as gap_10_20_yesterday,
                (ma_20 - ma_60) as gap_20_60_yesterday
            FROM daily_data
            WHERE stock_code IN %(stock_codes)s
            AND trade_date = (
                SELECT MAX(trade_date) 
                FROM daily_data 
                WHERE trade_date < %(latest_date)s
            )
        )
        SELECT t.stock_code
        FROM today_data t
        LEFT JOIN yesterday_data y ON t.stock_code = y.stock_code
        WHERE 
            -- 均线多头排列
            t.close_price >= t.ma_5
            AND t.ma_5 >= t.ma_10 
            AND t.ma_10 >= t.ma_20 
            AND t.ma_20 >= t.ma_60
            -- 均线发散（至少两组均线间距在扩大）
            AND (
                (t.gap_5_10_today > y.gap_5_10_yesterday AND t.gap_10_20_today > y.gap_10_20_yesterday)
                OR (t.gap_10_20_today > y.gap_10_20_yesterday AND t.gap_20_60_today > y.gap_20_60_yesterday)
                OR (t.gap_5_10_today > y.gap_5_10_yesterday AND t.gap_20_60_today > y.gap_20_60_yesterday)
            )
        """
        params = {
            'stock_codes': tuple(result_stocks),
            'latest_date': latest_date
        }
        logger.info(f"SQL - 均线多头发散筛选: {query}")
        logger.info(f"参数: {params}")
        df_ma = pd.read_sql(query, engine, params=params)
        result_stocks = set(df_ma['stock_code'])
        logger.info(f"均线多头发散筛选后剩余股票数: {len(result_stocks)}")

    # 上影线筛选
    if filters.get('upper_shadow'):
        query = """
        SELECT DISTINCT t.stock_code
        FROM daily_data t
        WHERE t.stock_code IN %(stock_codes)s
        AND t.trade_date = %(latest_date)s
        AND t.high_price/t.close_price > 1.05  -- 上影线条件
        AND t.close_price > t.open_price      -- 收盘价大于开盘价
        AND t.close_price > t.previous_close_price
        """
        params = {
            'stock_codes': tuple(result_stocks),
            'latest_date': latest_date
        }
        logger.info(f"SQL - 上影线筛选: {query}")
        logger.info(f"参数: {params}")
        df_shadow = pd.read_sql(query, engine, params=params)
        result_stocks = set(df_shadow['stock_code'])
        logger.info(f"上影线筛选后剩余股票数: {len(result_stocks)}")

    # 获取最终结果的详细信息
    if result_stocks:
        # 1. 从 daily_data 获取基础数据
        query = """
        SELECT 
            stock_code,
            stock_name,
            price_change_rate as change_rate,
            turnover_amount/10000 as turnover,  # 转换为万元显示
            total_mv/10000 as total_mv,  # 总市值（亿）
            trade_date  # 添加交易日期
        FROM daily_data
        WHERE stock_code IN %(stock_codes)s
        AND trade_date = %(latest_date)s
        ORDER BY price_change_rate DESC
        """
        params = {
            'stock_codes': tuple(result_stocks),
            'latest_date': latest_date
        }
        logger.info(f"SQL - 获取基础数据: {query}")
        logger.info(f"参数: {params}")
        df_base = pd.read_sql(query, engine, params=params)
        
        if not df_base.empty:
            # 2. 从 stock 表获取行业信息
            stock_codes_with_suffix = [
                f"{code}.SZ" if code.startswith(('000', '002', '300', '301')) else f"{code}.SH" 
                for code in df_base['stock_code']
            ]
            query = """
            SELECT 
                LEFT(stock_code, 6) as stock_code,
                industry
            FROM stock 
            WHERE stock_code IN %(stock_codes)s
            """
            params = {
                'stock_codes': tuple(stock_codes_with_suffix)
            }
            logger.info(f"SQL - 获取行业数据: {query}")
            logger.info(f"参数: {params}")
            df_industry = pd.read_sql(query, engine, params=params)
            
            # 3. 获取概念信息（在Python中进行过滤和合并）
            query = """
            SELECT 
                SUBSTRING(stock_code, 1, 6) as stock_code,
                GROUP_CONCAT(DISTINCT sector_name) as concept
            FROM concept_stock 
            WHERE SUBSTRING(stock_code, 1, 6) IN %(stock_codes)s
            GROUP BY SUBSTRING(stock_code, 1, 6)
            """
            params = {
                'stock_codes': tuple(df_base['stock_code'].tolist())
            }
            logger.info(f"SQL - 获取概念数据: {query}")
            logger.info(f"参数: {params}")
            df_concepts = pd.read_sql(query, engine, params=params)
            
            # 过滤黑名单概念并合并同义概念
            def process_concepts(concepts_str):
                logger.info(f"开始处理概念字符串: {concepts_str}")
                if not concepts_str or concepts_str == '-':
                    logger.info("空概念字符串，返回 '-'")
                    return '-'
                # 分割概念
                concepts = concepts_str.split(',')
                logger.info(f"分割后的概念列表: {concepts}")
                
                # 过滤黑名单
                filtered_concepts = [c for c in concepts if c not in CONCEPT_BLACKLIST]
                logger.info(f"过滤黑名单后的概念: {filtered_concepts}")
                
                if not filtered_concepts:
                    logger.info("过滤后没有剩余概念，返回 '-'")
                    return '-'
                
                # 合并为字符串后再进行同义词合并
                # normalized = normalize_concepts(','.join(filtered_concepts))
                # logger.info(f"同义词合并后的结果: {normalized}")
                # return normalized
                return ','.join(filtered_concepts)
            
            logger.info("开始处理所有股票的概念...")
            # 应用概念处理
            df_concepts['concept'] = df_concepts['concept'].apply(process_concepts)
            logger.info("概念处理完成")
            logger.info("\n处理后的概念数据示例：")
            logger.info(df_concepts.head().to_string())
            
            # 4. 合并所有数据
            final_results = pd.merge(
                df_base,
                df_industry,
                on='stock_code',
                how='left'
            )
            
            final_results = pd.merge(
                final_results,
                df_concepts,
                on='stock_code',
                how='left'
            )
            
            # 处理空值
            final_results['industry'] = final_results['industry'].fillna('-')
            final_results['concept'] = final_results['concept'].fillna('-')
            
            logger.info(f"最终筛选结果数量: {len(final_results)}")
            return final_results.to_dict('records')
    
    logger.info("没有符合条件的股票")
    return [] 