import pymysql
from datetime import datetime

# 添加概念黑名单
CONCEPT_BLACKLIST = {
    '融资融券', '转融券标的', '深股通', '人民币', '富时罗素概念股', '富时罗素概念', '沪股通', 
    '高股息精选', '京津冀一体化', '专精特新', '台湾概念股', '统一大市场', '股权转让', 
    '虚拟数字人', '独角兽概念', '粤港澳大湾区', '共同富裕示范区', '联想概念', '三星', 
    '大湾区', '自贸区', '共享经济', '央视财经50', '数据交易中心', '汽车电商', '共享', 
    '进口博览会', '自由贸易港', '海底捞概念', '海水淡化', '食盐', '溴素', '白炭黑', 
    '同花顺', '贸易区', 'Web', '雄安新区', '人脸识别', '3D打印', '电子信息', 
    '高端装备', '网络直播', '创投', '储能', '乡村振兴', '中俄贸易概念',
    '腾讯概念', '信创', '智慧城市', '物联网', '区块链', '抖音概念', 
    'ChatGPT概念', '数据要素', '量子科技', '智能家居', 'AIGC概念'
    , '老字号', '体育产业', '云办公', '动力电池回收', '碳中和', 
    '外贸受益概念', '长三角一体化', '军民融合', '智能穿戴', '新疆振兴',
    'MiniLED', 'MicroLED概念', '无线耳机', '分拆上市意愿'
}

# 概念到行业的映射
CONCEPT_TO_INDUSTRY = {
    '金融': ['银行', '证券', '保险', '多元金融'],
    '房地产': ['房地产', '物业管理'],
    '医药': ['医药生物', '医疗器械', '生物制品', '化学制药', '中药', '化学制药', '生物制品', '医疗器械'],
    '科技': ['计算机', '通信', '电子', '互联网', '软件服务'],
    '文化传媒': ['传媒', '出版', '影视'],
    '电力': ['电气设备', '电力', '电网'],
    '机械': ['机械设备', '通用机械'],
    '汽车': ['汽车'],
    '汽车零部件': ['汽车零部件'],
    '白酒': ['白酒', '啤酒'],
    '食品': ['食品饮料', '预制菜', '零食'],
    '家电': ['家用电器'],
    '零售': ['商业贸易', '电子商务', '纺织服装', '休闲服务', '日用品'],
    '农业': ['农林牧渔'],
    '基建': ['建筑', '建材', '水泥'],
    '煤炭': ['煤炭'],
    '石油': ['石油'],
    '化工': ['化工', '化学制品'],
    '公用事业': ['公用事业', '水务'],
    '物流': ['交通运输', '物流', '港口'],
    '酒店旅游': ['旅游酒店', '景区'],
    '教育': ['教育培训']
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
        '光伏': ['光伏', '钙钛矿', 'TOPCON', 'HJT', 'BC电池'],
        '房地产': ['物业', '房地产'],
        '医药': ['医疗', '诊断', '药', '肝炎', 'CRO', '流感', '螺杆菌', '猴痘', '细胞免疫治疗'],
        '农业': ['农', '猪肉', '养鸡', '大豆', '人造肉'],
        '零售': ['消费', '零售', '乳业', '电子商务'],
        '化工': ['化工', '氢氟酸', '双氧水', '纯碱', '硝酸钠', '硫酸钾'],
        '上海': ['浦东'],
        '有色金属': ['金属', '铜', '铝'],
        '合成生物': ['合成生物', '维生素'],
        '食品': ['食品', '预制菜', '零食'],
        '互联网金融': ['金融', '期货', '互联网金融', '信托概念'],
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
        '核电': ['核电', '可控核聚变'],
        '白酒': ['白酒概念', '啤酒概念'],
        '煤炭': ['煤炭']
    }
    
    # 查找并返回规范化的概念名称
    for normalized, keywords in concept_mapping.items():
        # 如果任何关键词是概念的子字符串，就返回规范化的名称
        if any(keyword in concept for keyword in keywords):
            return normalized
    return concept

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='happy',
        charset='utf8mb4'
    )

def get_limit_stocks(trade_date):
    """获取指定日期的涨跌停股票"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT 
            ts_code,
            name,
            limit_type,
            industry,
            reason
        FROM limit_stocks
        WHERE trade_date = %s
        ORDER BY limit_type, ts_code
        """
        
        cursor.execute(query, (trade_date,))
        stocks = cursor.fetchall()
        return stocks
        
    finally:
        cursor.close()
        conn.close()

def get_stock_concepts(stock_code):
    """获取股票的所有概念"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT 
            sector_code,
            sector_name,
            stock_code
        FROM concept_stock
        WHERE stock_code = %s
        ORDER BY sector_code
        """
        
        cursor.execute(query, (stock_code,))
        concepts = cursor.fetchall()
        # 过滤掉黑名单中的概念
        return [c for c in concepts if c[1] not in CONCEPT_BLACKLIST]
        
    finally:
        cursor.close()
        conn.close()

def format_limit_type(limit_type):
    """格式化涨跌停类型"""
    type_marks = {
        'U': '🔴涨停',
        'D': '🟢跌停',
        'Z': '🟡炸板'
    }
    return type_marks.get(limit_type, '未知')

def industry_to_concept(industry):
    """将行业转换为概念"""
    if not industry or industry == '-':
        return None
    
    # 查找行业所属的概念
    for concept, industries in CONCEPT_TO_INDUSTRY.items():
        if any(ind == industry or ind in industry for ind in industries):
            return concept
    
    # 如果没有匹配，返回原行业名称
    return industry

def print_concept_stats(stocks):
    """统计并打印概念信息"""
    print(f"\n=== 概念板块统计 ===\n")
    
    # 统计每个概念的涨跌停情况
    concept_stats = {}
    for stock in stocks:
        ts_code, name, limit_type, industry, reason = stock
        concepts = get_stock_concepts(ts_code)
        
        # 添加行业作为概念
        industry_concept = industry_to_concept(industry)
        if industry_concept:
            # 创建一个虚拟的概念元组 (code, name, stock_code)
            industry_tuple = ('IND', industry_concept, ts_code)
            concepts.append(industry_tuple)
        
        for concept_code, concept_name, _ in concepts:
            # 跳过黑名单中的概念
            if concept_name in CONCEPT_BLACKLIST:
                continue
            
            # 规范化概念名称
            normalized_concept = normalize_concept(concept_name)
            
            if normalized_concept not in concept_stats:
                concept_stats[normalized_concept] = {'U': 0, 'Z': 0, 'D': 0}
            concept_stats[normalized_concept][limit_type] += 1
    
    # 打印表头
    print("="*80)
    print(f"{'概念名称':<30}{'涨停数':>10}{'炸板数':>10}{'跌停数':>10}")
    print("="*80)
    
    # 按涨停数、炸板数、跌停数排序并显示
    sorted_stats = sorted(
        concept_stats.items(),
        key=lambda x: (-x[1]['U'], -x[1]['Z'], x[1]['D'])
    )
    
    for concept_name, stats in sorted_stats:
        # 只显示至少有一个涨跌停的概念
        if stats['U'] + stats['Z'] + stats['D'] > 0:
            print(f"{concept_name:<30}{stats['U']:>10}{stats['Z']:>10}{stats['D']:>10}")
    
    print("="*80)

def main(trade_date=None):
    """主函数"""
    if trade_date is None:
        trade_date = datetime.now().strftime('%Y%m%d')
    
    print(f"\n分析 {trade_date} 的涨跌停股票概念...\n")
    
    # 获取涨跌停股票
    stocks = get_limit_stocks(trade_date)
    if not stocks:
        print("未找到任何涨跌停股票")
        return
    
    # 打印表头
    print("="*150)
    print(f"{'股票代码':<12}{'股票名称':<12}{'涨停原因':<50}{'行业':<15}{'所属概念'}")
    print("="*150)
    
    # 遍历每只股票
    for stock in stocks:
        ts_code, name, limit_type, industry, reason = stock
        concepts = get_stock_concepts(ts_code)
        # 过滤和规范化概念
        normalized_concepts = []

        # 添加行业作为概念
        industry_concept = industry_to_concept(industry)
        if industry_concept and industry_concept not in normalized_concepts:
            normalized_concepts.append(industry_concept)
          
        for _, concept_name, _ in concepts:
            if concept_name not in CONCEPT_BLACKLIST:
                normalized = normalize_concept(concept_name)
                if normalized not in normalized_concepts:
                    normalized_concepts.append(normalized)
        
        # 转换为字符串
        concept_str = ','.join(normalized_concepts) if normalized_concepts else '无概念'
        
        print(f"{ts_code:<12}{name:<12}{reason or '无':<50}{industry:<15}{concept_str}")
    
    print("="*150)
    
    # 打印概念统计信息
    print_concept_stats(stocks)
    
    print("\n分析完成")

if __name__ == "__main__":
    # 可以传入指定日期，格式为'YYYYMMDD'
    main('20250314') 