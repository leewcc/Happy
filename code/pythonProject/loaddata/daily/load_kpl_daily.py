import  chinadata.ca_data as ts
import pandas as pd
from datetime import datetime

# 设置 Tushare Pro 的 token
ts.set_token('i593c24d0926bfb845f136082a335d64f71')
pro = ts.pro_api()

def format_amount(value):
    """格式化金额，处理None值"""
    if pd.isna(value) or value is None:
        return 0.00
    return value/100000000

def get_kpl_data(trade_date=None):
    """
    获取开盘啦涨停、跌停、炸板等榜单数据
    
    参数:
        trade_date: str, 可选, 格式YYYYMMDD, 默认为当天
    """
    if trade_date is None:
        trade_date = datetime.now().strftime('%Y%m%d')
    
    try:
        # 获取涨停数据
        df_up = pro.kpl_list(trade_date=trade_date, tag='涨停')
        # 获取跌停数据
        df_down = pro.kpl_list(trade_date=trade_date, tag='跌停')
        # 获取炸板数据
        df_break = pro.kpl_list(trade_date=trade_date, tag='炸板')
        
        # 打印涨停数据
        print("\n=== 涨停数据 ===")
        if not df_up.empty:
            print(f"共有{len(df_up)}只涨停股")
            for _, row in df_up.iterrows():
                print(f"\n股票: {row['name']}({row['ts_code']})")
                print(f"交易日期: {row['trade_date']}")
                print(f"涨停时间: {row['lu_time'] or '-'}")
                print(f"开板时间: {row['open_time'] or '-'}")
                print(f"最后涨停时间: {row['last_time'] or '-'}")
                print(f"涨停原因: {row['lu_desc'] or '-'}")
                print(f"标签: {row['tag'] or '-'}")
                print(f"相关题材: {row['theme'] or '-'}")
                print(f"主力净额: {format_amount(row['net_change']):.2f}亿")
                print(f"竞价成交额: {format_amount(row['bid_amount']):.2f}亿")
                print(f"连板状态: {row['status'] or '-'}")
                print(f"竞价净额: {format_amount(row['bid_change']):.2f}亿")
                print(f"竞价换手: {row['bid_turnover'] or 0:.2f}%")
                print(f"涨停委买额: {format_amount(row['lu_bid_vol']):.2f}亿")
                print(f"涨跌幅: {row['pct_chg'] or 0:.2f}%")
                print(f"竞价涨幅: {row['bid_pct_chg'] or 0:.2f}%")
                print(f"实时涨幅: {row['rt_pct_chg'] or 0:.2f}%")
                print(f"封单: {format_amount(row['limit_order']):.2f}亿")
                print(f"成交额: {format_amount(row['amount']):.2f}亿")
                print(f"换手率: {row['turnover_rate'] or 0:.2f}%")
                print(f"实际流通: {format_amount(row['free_float']):.2f}亿")
                print(f"最大封单: {format_amount(row['lu_limit_order']):.2f}亿")
                print("-" * 50)
        else:
            print("无涨停数据")
            
        # 打印跌停数据
        print("\n=== 跌停数据 ===")
        if not df_down.empty:
            print(f"共有{len(df_down)}只跌停股")
            for _, row in df_down.iterrows():
                print(f"\n股票: {row['name']}({row['ts_code']})")
                print(f"交易日期: {row['trade_date']}")
                print(f"跌停时间: {row['ld_time'] or '-'}")
                print(f"开板时间: {row['open_time'] or '-'}")
                print(f"标签: {row['tag'] or '-'}")
                print(f"相关题材: {row['theme'] or '-'}")
                print(f"主力净额: {format_amount(row['net_change']):.2f}亿")
                print(f"竞价成交额: {format_amount(row['bid_amount']):.2f}亿")
                print(f"竞价净额: {format_amount(row['bid_change']):.2f}亿")
                print(f"竞价换手: {row['bid_turnover'] or 0:.2f}%")
                print(f"涨跌幅: {row['pct_chg'] or 0:.2f}%")
                print(f"竞价涨幅: {row['bid_pct_chg'] or 0:.2f}%")
                print(f"实时涨幅: {row['rt_pct_chg'] or 0:.2f}%")
                print(f"成交额: {format_amount(row['amount']):.2f}亿")
                print(f"换手率: {row['turnover_rate'] or 0:.2f}%")
                print(f"实际流通: {format_amount(row['free_float']):.2f}亿")
                print("-" * 50)
        else:
            print("无跌停数据")
            
        # 打印炸板数据
        print("\n=== 炸板数据 ===")
        if not df_break.empty:
            print(f"共有{len(df_break)}只炸板股")
            for _, row in df_break.iterrows():
                print(f"\n股票: {row['name']}({row['ts_code']})")
                print(f"交易日期: {row['trade_date']}")
                print(f"涨停时间: {row['lu_time'] or '-'}")
                print(f"开板时间: {row['open_time'] or '-'}")
                print(f"最后涨停时间: {row['last_time'] or '-'}")
                print(f"涨停原因: {row['lu_desc'] or '-'}")
                print(f"标签: {row['tag'] or '-'}")
                print(f"相关题材: {row['theme'] or '-'}")
                print(f"主力净额: {format_amount(row['net_change']):.2f}亿")
                print(f"竞价成交额: {format_amount(row['bid_amount']):.2f}亿")
                print(f"连板状态: {row['status'] or '-'}")
                print(f"竞价净额: {format_amount(row['bid_change']):.2f}亿")
                print(f"竞价换手: {row['bid_turnover'] or 0:.2f}%")
                print(f"涨停委买额: {format_amount(row['lu_bid_vol']):.2f}亿")
                print(f"涨跌幅: {row['pct_chg'] or 0:.2f}%")
                print(f"竞价涨幅: {row['bid_pct_chg'] or 0:.2f}%")
                print(f"实时涨幅: {row['rt_pct_chg'] or 0:.2f}%")
                print(f"封单: {format_amount(row['limit_order']):.2f}亿")
                print(f"成交额: {format_amount(row['amount']):.2f}亿")
                print(f"换手率: {row['turnover_rate'] or 0:.2f}%")
                print(f"实际流通: {format_amount(row['free_float']):.2f}亿")
                print(f"最大封单: {format_amount(row['lu_limit_order']):.2f}亿")
                print("-" * 50)
        else:
            print("无炸板数据")
            
        return {
            'up': df_up,
            'down': df_down,
            'break': df_break
        }
        
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return None

if __name__ == "__main__":
    # 获取今日数据
    today = '20250228'
    print(f"\n获取{today}的数据:")
    data = get_kpl_data(today)
    
    # 如果要获取指定日期的数据，可以这样调用：
    # data = get_kpl_data('20240305') 