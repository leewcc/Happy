import chinadata.ca_data as ts
import pymysql
import time
import traceback
from datetime import datetime

# 设置 Tushare Pro 的 token
ts.set_token('i593c24d0926bfb845f136082a335d64f71')
pro = ts.pro_api()

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        user='leewcc',
        password='leewcc',
        database='happy',
        charset='utf8mb4'
    )

def get_all_stock_codes():
    """获取所有股票代码"""
    try:
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        return data[['ts_code', 'symbol', 'name']].values.tolist()
    except Exception as e:
        print(f"获取股票列表时出错: {str(e)}")
        return []

def check_concept_exists(stock_code, concept_code):
    """检查股票的概念是否已存在"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        check_sql = """
        SELECT COUNT(*) FROM concept_stock 
        WHERE stock_code = %s AND sector_code = %s
        """
        cursor.execute(check_sql, (stock_code, concept_code))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"检查概念是否存在时出错: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def insert_stock_concept(stock_code, concept_code, concept_name, stock_name):
    """插入股票概念关系"""
    if check_concept_exists(stock_code, concept_code):
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        insert_sql = """
        INSERT INTO concept_stock 
        (sector_code, sector_name, stock_code, stokc_name, is_new) 
        VALUES (%s, %s, %s, %s, 'Y')
        """
        cursor.execute(insert_sql, (concept_code, concept_name, stock_code, stock_name))
        conn.commit()
        return True
    except Exception as e:
        print(f"插入概念数据时出错: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_stock_concepts(ts_code):
    """获取股票的概念信息"""
    try:
        # 使用 concept_detail 获取股票的概念信息
        df = pro.concept_detail(ts_code=ts_code)
        if df.empty:
            return []
        
        concepts = []
        for _, row in df.iterrows():
            # 修改这里以匹配实际的列名
            concept = {
                'concept_code': row['id'],  # 使用 'id' 而不是 'concept_code'
                'concept_name': row['concept_name']
            }
            concepts.append(concept)
        
        time.sleep(0.3)  # 避免触发频率限制
        return concepts
    except Exception as e:
        print(f"获取{ts_code}概念信息时出错: {str(e)}")
        # 打印更详细的错误信息
        print("返回的数据结构:")
        try:
            print(df.columns.tolist())  # 打印所有列名
            print(df.head())  # 打印前几行数据
        except:
            pass
        return []

def print_stock_concepts():
    """从数据库中读取并打印股票概念信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
        SELECT DISTINCT stokc_name, GROUP_CONCAT(sector_name) as concepts
        FROM concept_stock
        GROUP BY stokc_name
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        
        print("\n=== 股票概念信息 ===")
        print("股票名称\t所属概念")
        print("-" * 50)
        for stock_name, concepts in results:
            print(f"{stock_name}\t{concepts}")
            
    except Exception as e:
        print(f"读取概念数据时出错: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def format_stock_codes(codes):
    """
    格式化股票代码列表，不足6位的前面补0
    """
    formatted_codes = []
    for code in codes:
        # 将代码转换为字符串并去除空白
        code_str = str(code).strip()
        # 补零到6位
        formatted_code = code_str.zfill(6)
        # 根据长度判断是深市还是沪市
        if formatted_code.startswith(('000', '002', '003', '300', '301')):
            ts_code = f"{formatted_code}.SZ"
        else:
            ts_code = f"{formatted_code}.SH"
        formatted_codes.append(ts_code)
    return formatted_codes

def get_specified_stock_codes(ts_codes):
    """获取指定股票代码的详细信息"""
    try:
        # 获取所有股票的基本信息
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        # 只保留指定的股票代码
        filtered_data = data[data['ts_code'].isin(ts_codes)]
        return filtered_data[['ts_code', 'symbol', 'name']].values.tolist()
    except Exception as e:
        print(f"获取股票列表时出错: {str(e)}")
        return []

def print_stock_details(stock_codes):
    """
    从数据库获取并打印指定股票的概念，保持输入顺序
    :param stock_codes: 股票代码列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 将股票代码列表格式化为SQL中的IN子句格式
        formatted_codes = [str(code).zfill(6) for code in stock_codes]
        codes_str = "','".join(formatted_codes)
        
        sql = """
        SELECT cs.stock_code,
               GROUP_CONCAT(DISTINCT cs.sector_name ORDER BY cs.sector_name) as concepts
        FROM concept_stock cs
        WHERE cs.stock_code IN ('{}')
        GROUP BY cs.stock_code
        """.format(codes_str)
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        # 创建一个字典来存储结果，以股票代码为键
        stock_info = {row[0]: row[1] for row in results}
        
        # 按照输入的股票代码顺序打印信息
        for code in formatted_codes:
            if code in stock_info:
                concepts = stock_info[code]
                print(concepts or '')
            else:
                print("未找到概念信息")
            
    except Exception as e:
        print(f"获取股票详细信息时出错: {str(e)}")
        print(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()

def main():
    # 指定的股票代码列表
    stock_codes = [
        2366,2338,600550,603095,777,600360,600312,601611,600501,2441,881,2025,600579,601727,2145,3816,756,300875,300575,600343,519,600718,300722,2935,2648,603337,2130,600495,936,59,300446,600426,601985,2222,2745,600309,9,688569,600855,600135,1213,600435,2493,600125,601006,300979,600406,2191,601899,601816,601866,601766,600094,601606,600688,688543,600232,600362,600133,333,600010,600879,600737,600863,601857,703,901,600872,300455,600363,600765,547,2094,2511,2340,300030,600573,603993,300747,3037,600480,2006,756,2246,3022,600887,600028,2128,601333,600152,2361,300711,600178,301336,2027,2221,2389,600198,300197,603698,603798,600938,300295,600690,601919,300393,300087,301048,688459,651,2602,600151,878,630,601600,600843,603071,685,2012,603288,600416,600908,973,2371,99,3009,301592,547,600967,600821,600543,600271,600100,300355,300024,2668,988,729,600463,2819,600118,948,2415,2405,300158,600629,300096,688568,603000,600893,300277,2207,603037,600184,600536,2223,858,3004,2555,601698,2824,600026,2035,688047,600519,600336,10,600148,603927,2622,601216,2439,3036,600809,603444,600545,603131,568,601989,3002,603258,300557,300223,425,603855,600050,603019,2050,2418,536,2445,600150,2870,938,676,300326,300678,829,601615,300307,603016,601633,601858,2249,300120,600685,2163,566,301236,2977,681,300507,2472,600262,603328,685,158,300251,300063,2265,2953,300166,600428,600072,600302,2829,600482,2320,603068,425,2483,793,2512,301053,818,300256,890,901,
    ]
    
    # 格式化股票代码
    formatted_codes = format_stock_codes(stock_codes)
    
    # 获取指定股票的详细信息
    # specified_stocks = get_specified_stock_codes(formatted_codes)
    # total = len(specified_stocks)
    
    # print(f"开始获取{total}只指定股票的概念信息...")
    
    # for i, (ts_code, stock_code, stock_name) in enumerate(specified_stocks, 1):
    #     print(f"处理进度: {i}/{total} - {stock_name} ({ts_code})")
        
    #     concepts = get_stock_concepts(ts_code)
    #     for concept in concepts:
    #         success = insert_stock_concept(
    #             stock_code,
    #             concept['concept_code'],
    #             concept['concept_name'],
    #             stock_name
    #         )
    #         if success:
    #             print(f"已添加概念: {stock_name} - {concept['concept_name']}")
        
    #     # 增加一点延时，避免请求过快
    #     time.sleep(0.5)
    
    # print("\n所有指定股票概念数据获取完成！")
    
    # 打印详细信息
    print_stock_details(stock_codes)

if __name__ == "__main__":
    main() 