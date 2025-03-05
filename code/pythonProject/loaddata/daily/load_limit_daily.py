import chinadata.ca_data as ts
import pandas as pd
from datetime import datetime
import pymysql

# 设置 Tushare Pro 的 token
ts.set_token('i593c24d0926bfb845f136082a335d64f71')
pro = ts.pro_api()

# 连接到 MySQL 数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='happy',
    charset='utf8mb4',
    use_unicode=True
)
cursor = conn.cursor()

# 添加概念黑名单
CONCEPT_BLACKLIST = {
    '融资融券', '转融券标的', '深股通', '人民币', '富时罗素概念股', '富时罗素概念', '沪股通', 
    '高股息精选', '京津冀一体化', '专精特新', '台湾概念股', '统一大市场', '股权转让', 
    '虚拟数字人', '独角兽概念', '粤港澳大湾区', '共同富裕示范区', '联想概念', '三星', 
    '大湾区', '自贸区', '共享经济', '央视财经50', '数据交易中心', '汽车电商', '共享', 
    '进口博览会', '自由贸易港', '海底捞概念', '海水淡化', '食盐', '溴素', '白炭黑', 
    '同花顺', '贸易区', 'Web', '雄安新区', '快手概念', '人脸识别', '3D打印', '电子信息', 
    '高端装备', '网络直播', '比亚迪概念', '创投', '储能', '乡村振兴', '中俄贸易概念',
    '腾讯概念', '智慧政务', '信创', '智慧城市', '物联网', '区块链', '抖音概念', 
    'ChatGPT概念', '数据要素', '量子科技', '智能家居', '小米概念', 'AIGC概念', 
    '阿里巴巴概念', '老字号', '体育产业', '云办公', '动力电池回收', '碳中和', 
    '外贸受益概念', '长三角一体化', '军民融合', '智能穿戴', '新疆振兴',
    'MiniLED', 'MicroLED概念', '无线耳机', '分拆上市意愿'
}

def normalize_concept(concept):
    """合并同义概念"""
    # 添加同义词映射
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
    
    # 查找并返回规范化的概念名称
    for normalized, keywords in concept_mapping.items():
        # 如果任何关键词是概念的子字符串，就返回规范化的名称
        if any(keyword in concept for keyword in keywords):
            return normalized
    return concept

def format_amount(value):
    """格式化金额，处理None值"""
    if pd.isna(value) or value is None:
        return 0.00
    return value/100000000

def get_stock_info(ts_code):
    """获取股票的行业和概念信息"""
    # 获取行业
    query = "SELECT industry FROM stock WHERE stock_code = %s"
    cursor.execute(query, (ts_code,))
    industry = cursor.fetchone()
    industry = industry[0] if industry else '-'
    
    # 获取原始概念
    query = "SELECT sector_name FROM concept_stock WHERE stock_code = %s"
    cursor.execute(query, (ts_code,))
    original_concepts = [row[0] for row in cursor.fetchall()]
    
    # 过滤和合并概念
    filtered_concepts = set()  # 使用集合去重
    for concept in original_concepts:
        if concept not in CONCEPT_BLACKLIST:
            normalized = normalize_concept(concept)
            filtered_concepts.add(normalized)
    
    result = (industry, ', '.join(sorted(filtered_concepts)) if filtered_concepts else '-')
    return result

def get_limit_list_data(trade_date):
    """获取涨跌停板数据"""
    try:
        # 使用原接口获取基本的涨跌停数据
        print("\n=== 获取涨跌停数据 ===")
        df = pro.limit_list_d(trade_date=trade_date)
        
        # 使用同花顺接口获取涨停原因数据
        print("\n=== 获取涨停原因数据 ===")
        df_ths_up = pro.limit_list_ths(trade_date=trade_date, limit_type='涨停池')
        print(f"获取到 {len(df_ths_up) if not df_ths_up.empty else 0} 条涨停池数据")
        df_ths_break = pro.limit_list_ths(trade_date=trade_date, limit_type='炸板池')
        print(f"获取到 {len(df_ths_break) if not df_ths_break.empty else 0} 条炸板池数据")
        
        # 创建股票代码到涨停原因的映射
        reason_map = {}
        
        # 处理涨停池的原因
        if not df_ths_up.empty:
            for _, row in df_ths_up.iterrows():
                reason_map[row['ts_code']] = row['lu_desc']
                
        # 处理炸板池的原因
        if not df_ths_break.empty:
            for _, row in df_ths_break.iterrows():
                reason_map[row['ts_code']] = row['lu_desc']
        
        # 添加涨停原因列
        df['reason'] = df['ts_code'].map(lambda x: reason_map.get(x, ''))
        return df
        
    except Exception as e:
        print(f"获取涨跌停数据失败: {str(e)}")
        return pd.DataFrame()

def analyze_limit_stocks(limit_list_data, trade_date):
    """分析涨跌停数据"""
    # 原有的分析逻辑保持不变
    ...

def print_analysis_results(results, concept_stats, industry_stats):
    """打印分析结果"""
    # 原有的打印逻辑保持不变
    ...

def format_time(time_str):
    """格式化时间字符串"""
    if time_str:
        try:
            if len(time_str) == 5:
                hours = int(time_str[0])
                minutes = int(time_str[1:3])
                seconds = int(time_str[3:])
            elif len(time_str) == 6:
                hours = int(time_str[:2])
                minutes = int(time_str[2:4])
                seconds = int(time_str[4:])
            else:
                return None

            if 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except ValueError:
            pass
    return None

def inspect_concept_data(trade_date):
    """直接检查数据库中的核心概念数据"""
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='happy',
        charset='utf8mb4',
        use_unicode=True
    )
    cursor = conn.cursor()
    
    try:
        print("\n==== 直接检查数据库中的核心概念数据 ====")
        print(f"查询日期: {trade_date}")
        
        # 查询有核心概念的记录
        query = """
            SELECT ts_code, name, concept, HEX(concept) as hex_concept
            FROM limit_stocks 
            WHERE trade_date = %s AND concept IS NOT NULL AND concept != ''
            LIMIT 10
        """
        cursor.execute(query, (trade_date,))
        results = cursor.fetchall()
        
        print(f"找到 {len(results)} 条有核心概念的记录")
        
        for row in results:
            ts_code, name, concept, hex_concept = row
            print(f"\n股票: {name} ({ts_code})")
            print(f"  概念(原始): {concept}")
            print(f"  概念(十六进制): {hex_concept}")
            print(f"  概念(长度): {len(concept) if concept else 0}")
            print(f"  概念(类型): {type(concept)}")
            
            # 尝试解析概念
            if concept:
                concepts = [c.strip() for c in concept.split(',') if c.strip()]
                print(f"  解析后的概念: {concepts}")
                print(f"  概念数量: {len(concepts)}")
                
                for i, c in enumerate(concepts):
                    print(f"    概念{i+1}: '{c}' (长度: {len(c)})")
        
    except Exception as e:
        print(f"检查数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

def get_limit_stocks_page(trade_date=None):
    """获取涨跌停股票页面的数据"""
    if trade_date is None:
        trade_date = datetime.now().strftime('%Y%m%d')
    
    df = get_limit_list_data(trade_date)
    
    # 获取股票的已保存核心概念 - 移除 concept 的限制条件
    concept_map = {}
    try:
        concept_query = """
            SELECT ts_code, concept 
            FROM limit_stocks 
            WHERE trade_date = %s
        """
        cursor.execute(concept_query, (trade_date,))
        for ts_code, concept in cursor.fetchall():
            # 如果 concept 是 None，转换为空字符串
            concept_map[ts_code] = concept if concept else ''
    except Exception as e:
        print(f"获取核心概念失败: {str(e)}")
    
    # 获取每个股票的行业和概念信息
    stocks_info = []
    for _, row in df.iterrows():
        ts_code = row['ts_code']
        industry, concepts = get_stock_info(ts_code)
        
        # 初始化核心概念字段
        core_concept1 = ''
        core_concept2 = ''
        core_concept3 = ''
        
        # 如果有保存的核心概念，进行解析
        saved_concept = concept_map.get(ts_code, '')
        if saved_concept:
            concept_list = [c.strip() for c in saved_concept.split(',') if c.strip()]
            if len(concept_list) > 0:
                core_concept1 = concept_list[0]
            if len(concept_list) > 1:
                core_concept2 = concept_list[1]
            if len(concept_list) > 2:
                core_concept3 = concept_list[2]
        
        stock_info = {
            'ts_code': ts_code,
            'name': row['name'],
            'first_time': format_time(row.get('first_time', '')),
            'industry': industry,
            'reason': row.get('reason', ''),
            'concepts': concepts,
            'lbd_num': row.get('limit_times', 0),
            'core_concept1': core_concept1,
            'core_concept2': core_concept2,
            'core_concept3': core_concept3
        }
        stocks_info.append(stock_info)
    
    return stocks_info

def save_core_concepts(data, trade_date):
    """保存核心概念到数据库"""
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='happy',
        charset='utf8mb4',
        use_unicode=True
    )
    cursor = conn.cursor()
    
    try:
        for item in data:
            update_query = """
                UPDATE limit_stocks 
                SET concept = %s
                WHERE ts_code = %s AND trade_date = %s
            """
            cursor.execute(update_query, (
                item['core_concepts'],
                item['ts_code'],
                trade_date
            ))
        
        conn.commit()
        print(f"成功更新 {len(data)} 条核心概念数据")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_limit_stocks_with_concepts(trade_date):
    """获取涨跌停股票及其核心概念"""
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='happy',
        charset='utf8mb4',
        use_unicode=True
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    query = """
    SELECT 
        ls.ts_code, 
        ls.name as stock_name, 
        ls.concept as core_concept,
        ls.limit_type,
        ls.industry 
    FROM limit_stocks ls
    WHERE ls.trade_date = %s
    ORDER BY ls.limit_times DESC
    """
    
    cursor.execute(query, (trade_date,))
    stocks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return stocks

if __name__ == "__main__":
    today = '20250303'
    print(f"\n获取{today}的数据:")
    data = get_limit_list_data(today)
    
    cursor.close()
    conn.close()