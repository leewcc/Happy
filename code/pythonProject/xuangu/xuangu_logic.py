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

def filter_stocks(filters):
    """根据条件筛选股票"""
    engine = get_db_connection()
    result_stocks = None
    
    logger.info(f"开始筛选，筛选条件: {filters}")

    # 获取最新交易日期
    query = "SELECT MAX(trade_date) as latest_date FROM daily_data"
    logger.info(f"SQL - 获取最新日期: {query}")
    latest_date = pd.read_sql(query, engine).iloc[0]['latest_date']
    logger.info(f"最新交易日期: {latest_date}")

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

    # 3. 成交额筛选
    if filters.get('turnover_days') and filters.get('turnover_amount'):
        days = int(filters['turnover_days'])
        amount = float(filters['turnover_amount']) 
        
        # 构建 IN 子句的字符串
        stock_codes_str = ','.join([f"'{code}'" for code in result_stocks])
        
        query = f"""
        WITH recent_days AS (
            SELECT 
                stock_code,
                trade_date,
                turnover_amount/100000 as amount,  -- 转换为亿元
                ROW_NUMBER() OVER(PARTITION BY stock_code ORDER BY trade_date DESC) as rn
            FROM daily_data 
            WHERE stock_code IN ({stock_codes_str})
            AND trade_date <= '{latest_date}'
        )
        SELECT 
            stock_code,
            AVG(amount) as avg_amount
        FROM recent_days
        WHERE rn <= {days}
        GROUP BY stock_code
        HAVING avg_amount >= {amount}
        """
        
        # 直接打印完整的 SQL
        logger.info(f"SQL - 成交额筛选实际执行语句: {query}")
        
        # 使用参数化查询执行
        param_query = """
        WITH recent_days AS (
            SELECT 
                stock_code,
                trade_date,
                turnover_amount/100000 as amount,  -- 转换为亿元
                ROW_NUMBER() OVER(PARTITION BY stock_code ORDER BY trade_date DESC) as rn
            FROM daily_data 
            WHERE stock_code IN %(stock_codes)s
            AND trade_date <= %(latest_date)s
        )
        SELECT 
            stock_code,
            AVG(amount) as avg_amount
        FROM recent_days
        WHERE rn <= %(days)s
        GROUP BY stock_code
        HAVING avg_amount >= %(amount)s
        """
        
        params = {
            'stock_codes': tuple(result_stocks),
            'latest_date': latest_date,
            'days': days,
            'amount': amount
        }
        
        logger.info(f"SQL - 成交额筛选: {param_query}")
        logger.info(f"参数: {params}")
        
        df_turnover = pd.read_sql(param_query, engine, params=params)
        result_stocks = set(df_turnover['stock_code'])
        logger.info(f"成交额筛选后剩余股票数: {len(result_stocks)}")

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
            
            # 3. 获取概念信息（添加黑名单过滤）
            query = """
            SELECT 
                SUBSTRING(stock_code, 1, 6) as stock_code,
                GROUP_CONCAT(
                    DISTINCT CASE 
                        WHEN sector_name NOT IN %(blacklist)s THEN sector_name 
                    END
                ) as concept
            FROM concept_stock 
            WHERE SUBSTRING(stock_code, 1, 6) IN %(stock_codes)s
            GROUP BY SUBSTRING(stock_code, 1, 6)
            """
            params = {
                'stock_codes': tuple(df_base['stock_code'].tolist()),
                'blacklist': tuple(CONCEPT_BLACKLIST)
            }
            logger.info(f"SQL - 获取概念数据: {query}")
            logger.info(f"参数: {params}")
            df_concepts = pd.read_sql(query, engine, params=params)
            
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