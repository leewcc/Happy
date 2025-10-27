import requests
import pandas as pd
import time
import requests.adapters
from urllib3.util.retry import Retry

# 创建优化的session
session = requests.Session()

# 配置连接池
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,  # 连接池大小
    pool_maxsize=20,      # 最大连接数
    max_retries=Retry(
        total=3,          # 总重试次数
        backoff_factor=0.1,  # 重试间隔
        status_forcelist=[500, 502, 503, 504]  # 需要重试的状态码
    )
)
session.mount('http://', adapter)
session.mount('https://', adapter)

# 设置超时
session.timeout = (5, 30)  # (连接超时, 读取超时)

class pro_api:
    # def __init__(self, token):
    #     self.token = token  # 实例变量 name
    #     set_token(token)

    def __init__(self, token=None):
        if token is not None:
            self.token = token  # 实例变量，用于内部使用或调试
            set_token(token)

        else:
            self.token = get_token()
            if self.token is None:
                raise ValueError("请设置token")
            else:
                pass



    def query(self,api_name, fields='', **kwargs):
        """
        Query data from the API.

        Args:
        ts_code (str): The stock code to fetch data for.
        start_date (str): The start date for fetching data (in 'YYYY-MM-DD HH:MM:SS' format).
        end_date (str): The end date for fetching data (in 'YYYY-MM-DD HH:MM:SS' format).
        freq (str): The frequency of the data (e.g., '1min', '5min'，'15min', '30min'， '60min').
        token (str): The access token for the data source. Default is provided.
        offset (str, 可选): 数据偏移量，用于分页获取数据，默认为'0'。当需要获取更多数据时，可以增大此值。
        freq (str, 可选): 数据频率，指定返回数据的时间间隔，例如'1min'（1分钟）、'5min'（5分钟）、'15min'（15分钟）、
                          '30min'（30分钟）、'60min'（60分钟，即1小时）等。默认为'60min'。

        Returns:
        pd.DataFrame: A DataFrame containing the fetched stock data.
        """
        url = "http://114.132.244.63/api-tushare/tushare"

        params = {
            'token': get_token(),
            'api_name': api_name,
            'params': kwargs,
            'fields': fields,
        }

        print(params)
        
        # 记录请求开始时间
        start_time = time.time()
        response = session.post(url, json=params)
        # 计算耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"请求耗时: {elapsed_time:.2f} 秒")
        

        if response.status_code == 200:
            try:
                # 尝试解析JSON
                data = response.json()
                if data == 'token无效或已超期,请重新购买':
                    return data
                else:
                    # 改进的DataFrame创建逻辑
                    try:
                        # 如果数据是列表且非空
                        if isinstance(data, list) and data:
                            df = pd.DataFrame(data)
                        # 如果数据是字典
                        elif isinstance(data, dict):
                            # 如果字典的值都是列表，可以直接创建DataFrame
                            if all(isinstance(v, list) for v in data.values()):
                                df = pd.DataFrame(data)
                            else:
                                # 如果是单行数据，包装成列表
                                df = pd.DataFrame([data])
                        # 如果数据是标量值
                        elif isinstance(data, (str, int, float, bool)):
                            # 创建单列单行的DataFrame
                            df = pd.DataFrame({'result': [data]})
                        # 如果数据是空列表
                        elif isinstance(data, list) and not data:
                            # 创建空DataFrame
                            df = pd.DataFrame()
                        else:
                            # 其他情况，尝试直接创建
                            df = pd.DataFrame(data)
                        
                        return df
                        
                    except Exception as df_error:
                        # 如果DataFrame创建失败，记录详细信息并返回原始数据
                        print(f"DataFrame创建失败: {df_error}")
                        print(f"数据类型: {type(data)}")
                        print(f"数据内容: {str(data)[:200]}...")
                        
                        # 返回原始数据，让调用者决定如何处理
                        return data
                        
            except ValueError as e:
                raise ValueError("数据获取错误",e)

        else:
            raise ValueError("数据获取错误",response.status_code,response.text)



    def fund_basic(self, api_name='fund_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stock_basic(self, api_name='stock_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def trade_cal(self, api_name='trade_cal', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def daily(self, api_name='daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def adj_factor(self, api_name='adj_factor', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def daily_basic(self, api_name='daily_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def income(self, api_name='income', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)
    def income_vip(self, api_name='income_vip', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def balancesheet(self, api_name='balancesheet', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def balancesheet_vip(self, api_name='balancesheet_vip', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cashflow(self, api_name='cashflow', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cashflow_vip(self, api_name='cashflow_vip', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def forecast(self, api_name='forecast', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def forecast_vip(self, api_name='forecast_vip', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def express(self, api_name='express', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def express_vip(self, api_name='express_vip', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def moneyflow_hsgt(self, api_name='moneyflow_hsgt', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hsgt_top10(self, api_name='hsgt_top10', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ggt_top10(self, api_name='ggt_top10', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def coinpair(self, api_name='coinpair', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def coinlist(self, api_name='coinlist', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def coincap(self, api_name='coincap', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def margin(self, api_name='margin', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def margin_detail(self, api_name='margin_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def top10_holders(self, api_name='top10_holders', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def top10_floatholders(self, api_name='top10_floatholders', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def coinfees(self, api_name='coinfees', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def coinexchanges(self, api_name='coinexchanges', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def jinse(self, api_name='jinse', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def btc8(self, api_name='btc8', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bishijie(self, api_name='bishijie', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def exchange_ann(self, api_name='exchange_ann', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def btc_marketcap(self, api_name='btc_marketcap', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def btc_pricevol(self, api_name='btc_pricevol', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fina_indicator(self, api_name='fina_indicator', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fina_indicator_vip(self, api_name='fina_indicator_vip', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fina_audit(self, api_name='fina_audit', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fina_mainbz(self, api_name='fina_mainbz', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fina_mainbz_vip(self, api_name='fina_mainbz_vip', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def tmt_twincomedetail(self, api_name='tmt_twincomedetail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def tmt_twincome(self, api_name='tmt_twincome', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def exchange_twitter(self, api_name='exchange_twitter', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_basic(self, api_name='index_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_daily(self, api_name='index_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_weight(self, api_name='index_weight', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def namechange(self, api_name='namechange', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def dividend(self, api_name='dividend', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hs_const(self, api_name='hs_const', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def twitter_kol(self, api_name='twitter_kol', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def top_list(self, api_name='top_list', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def top_inst(self, api_name='top_inst', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def pledge_stat(self, api_name='pledge_stat', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def pledge_detail(self, api_name='pledge_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stock_company(self, api_name='stock_company', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bo_monthly(self, api_name='bo_monthly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bo_weekly(self, api_name='bo_weekly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bo_daily(self, api_name='bo_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bo_cinema(self, api_name='bo_cinema', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_company(self, api_name='fund_company', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_nav(self, api_name='fund_nav', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_div(self, api_name='fund_div', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_portfolio(self, api_name='fund_portfolio', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def new_share(self, api_name='new_share', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def repurchase(self, api_name='repurchase', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def concept(self, api_name='concept', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def concept_detail(self, api_name='concept_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_daily(self, api_name='fund_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_dailybasic(self, api_name='index_dailybasic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_basic(self, api_name='fut_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def trade_cal(self, api_name='trade_cal', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_daily(self, api_name='fut_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_holding(self, api_name='fut_holding', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_wsr(self, api_name='fut_wsr', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_settle(self, api_name='fut_settle', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def news(self, api_name='news', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'


    def weekly(self, api_name='weekly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def monthly(self, api_name='monthly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def shibor(self, api_name='shibor', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def shibor_quote(self, api_name='shibor_quote', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def shibor_lpr(self, api_name='shibor_lpr', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def libor(self, api_name='libor', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hibor(self, api_name='hibor', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cctv_news(self, api_name='cctv_news', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def index_daily(self, api_name='index_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def film_record(self, api_name='film_record', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def opt_basic(self, api_name='opt_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def opt_daily(self, api_name='opt_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def share_float(self, api_name='share_float', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def block_trade(self, api_name='block_trade', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def disclosure_date(self, api_name='disclosure_date', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_account(self, api_name='stk_account', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_account_old(self, api_name='stk_account_old', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_holdernumber(self, api_name='stk_holdernumber', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def moneyflow(self, api_name='moneyflow', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_weekly(self, api_name='index_weekly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_monthly(self, api_name='index_monthly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def wz_index(self, api_name='wz_index', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def gz_index(self, api_name='gz_index', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_holdertrade(self, api_name='stk_holdertrade', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def anns_d(self, api_name='anns_d', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fx_obasic(self, api_name='fx_obasic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fx_daily(self, api_name='fx_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def teleplay_record(self, api_name='teleplay_record', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_classify(self, api_name='index_classify', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_limit(self, api_name='stk_limit', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cb_basic(self, api_name='cb_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cb_issue(self, api_name='cb_issue', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cb_daily(self, api_name='cb_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hk_hold(self, api_name='hk_hold', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_mapping(self, api_name='fut_mapping', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hk_basic(self, api_name='hk_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hk_daily(self, api_name='hk_daily', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def stk_managers(self, api_name='stk_managers', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_rewards(self, api_name='stk_rewards', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def major_news(self, api_name='major_news', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def ggt_daily(self, api_name='ggt_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ggt_monthly(self, api_name='ggt_monthly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_adj(self, api_name='fund_adj', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def yc_cb(self, api_name='yc_cb', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ncov_num(self, api_name='ncov_num', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_share(self, api_name='fund_share', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_manager(self, api_name='fund_manager', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_global(self, api_name='index_global', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def idx_factor_pro(self, api_name='idx_factor_pro', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)
    def fund_factor_pro(self, api_name='fund_factor_pro', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ncov_global(self, api_name='ncov_global', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def suspend_d(self, api_name='suspend_d', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def daily_info(self, api_name='daily_info', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_weekly_detail(self, api_name='fut_weekly_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_tycr(self, api_name='us_tycr', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_trycr(self, api_name='us_trycr', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_tbr(self, api_name='us_tbr', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_tltr(self, api_name='us_tltr', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_trltr(self, api_name='us_trltr', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cn_gdp(self, api_name='cn_gdp', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cn_cpi(self, api_name='cn_cpi', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def eco_cal(self, api_name='eco_cal', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def coin_bar(self, api_name='coin_bar', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cn_m(self, api_name='cn_m', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cn_ppi(self, api_name='cn_ppi', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cb_price_chg(self, api_name='cb_price_chg', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cb_share(self, api_name='cb_share', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hk_tradecal(self, api_name='hk_tradecal', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_basic(self, api_name='us_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_tradecal(self, api_name='us_tradecal', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_daily(self, api_name='us_daily', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def bak_daily(self, api_name='bak_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def repo_daily(self, api_name='repo_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def coin_pair(self, api_name='coin_pair', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ths_index(self, api_name='ths_index', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ths_daily(self, api_name='ths_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)
    def dc_index(self, api_name='dc_index', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def dc_member(self, api_name='dc_member', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ths_member(self, api_name='ths_member', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bak_basic(self, api_name='bak_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_sales_ratio(self, api_name='fund_sales_ratio', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fund_sales_vol(self, api_name='fund_sales_vol', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def broker_recommend(self, api_name='broker_recommend', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def sz_daily_info(self, api_name='sz_daily_info', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cb_call(self, api_name='cb_call', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bond_blk(self, api_name='bond_blk', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bond_blk_detail(self, api_name='bond_blk_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ccass_hold_detail(self, api_name='ccass_hold_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_surv(self, api_name='stk_surv', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def sge_basic(self, api_name='sge_basic', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def sge_daily(self, api_name='sge_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def report_rc(self, api_name='report_rc', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cyq_perf(self, api_name='cyq_perf', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cyq_chips(self, api_name='cyq_chips', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ccass_hold(self, api_name='ccass_hold', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_factor(self, api_name='stk_factor', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def limit_list_d(self, api_name='limit_list_d', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stock_mx(self, api_name='stock_mx', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stock_vx(self, api_name='stock_vx', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hk_mins(self, api_name='hk_mins', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def cb_rate(self, api_name='cb_rate', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ci_daily(self, api_name='ci_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def sf_month(self, api_name='sf_month', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hm_list(self, api_name='hm_list', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def hm_detail(self, api_name='hm_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ft_mins(self, api_name='ft_mins', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'


    def realtime_quote(self, api_name='realtime_quote', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def realtime_tick(self, api_name='realtime_tick', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def realtime_list(self, api_name='realtime_list', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def ths_hot(self, api_name='ths_hot', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def dc_hot(self, api_name='dc_hot', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bc_otcqt(self, api_name='bc_otcqt', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def bc_bestotcqt(self, api_name='bc_bestotcqt', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def cn_pmi(self, api_name='cn_pmi', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def margin_secs(self, api_name='margin_secs', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def sw_daily(self, api_name='sw_daily', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_factor_pro(self, api_name='stk_factor_pro', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_premarket(self, api_name='stk_premarket', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def slb_len(self, api_name='slb_len', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def slb_sec(self, api_name='slb_sec', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def slb_sec_detail(self, api_name='slb_sec_detail', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def slb_len_mm(self, api_name='slb_len_mm', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def index_member_all(self, api_name='index_member_all', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_weekly_monthly(self, api_name='stk_weekly_monthly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def fut_weekly_monthly(self, api_name='fut_weekly_monthly', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def us_daily_adj(self, api_name='us_daily_adj', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def hk_daily_adj(self, api_name='hk_daily_adj', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def rt_fut_min(self, api_name='rt_fut_min', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def opt_mins(self, api_name='opt_mins', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def moneyflow_ind_ths(self, api_name='moneyflow_ind_ths', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def moneyflow_ind_dc(self, api_name='moneyflow_ind_dc', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def moneyflow_mkt_dc(self, api_name='moneyflow_mkt_dc', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def kpl_list(self, api_name='kpl_list', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def moneyflow_ths(self, api_name='moneyflow_ths', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def moneyflow_dc(self, api_name='moneyflow_dc', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def kpl_concept(self, api_name='kpl_concept', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def kpl_concept_cons(self, api_name='kpl_concept_cons', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_auction_o(self, api_name='stk_auction_o', **kwargs):

        return '此接口为单独权限，和积分没有关系,需要单独购买'

    def stk_auction_c(self, api_name='stk_auction_c', **kwargs):
        return '此接口为单独权限，和积分没有关系,需要单独购买'
    def stk_auction(self, api_name='stk_auction', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)
    def ft_limit(self, api_name='ft_limit', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)
    def irm_qa_sh(self, api_name='irm_qa_sh', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def irm_qa_sz(self, api_name='irm_qa_sz', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def stk_week_month_adj(self, api_name='stk_week_month_adj', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def limit_list_ths(self, api_name='limit_list_ths', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def limit_step(self, api_name='limit_step', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)

    def limit_cpt_list(self, api_name='limit_cpt_list', **kwargs):
        return self.query(token=self.token, api_name=api_name, **kwargs)


import pandas as pd
import os

BK = 'bk'

def set_token(token):
    df = pd.DataFrame([token], columns=['token'])
    user_home = os.path.expanduser('~')
    fp = os.path.join(user_home, 'c_t.csv')
    df.to_csv(fp, index=False)


def get_token():
    user_home = os.path.expanduser('~')
    fp = os.path.join(user_home, 'c_t.csv')
    if os.path.exists(fp):

        df = pd.read_csv(fp)


        return str(df.loc[0]['token'])
    else:
        print("请设置token")
        return None

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)#消除告警

import requests



#
#
def pro_bar(ts_code='', api=None, start_date='', end_date='', freq='D', asset='E',
           exchange='',
           adj = None,
           ma = [],
           factors = None,
           adjfactor = False,
           offset = None,
           limit = None,
           fields = '',
           contract_type = ''):
    """

    """
    url = "http://114.132.244.63/api-tushare/tushare/pro_bar"

    params = {
        'token':get_token(),
        'ts_code':ts_code,
        'api':api,
        'start_date':start_date,
        'end_date':end_date,
        'freq':freq,
        'asset':asset,
        'exchange':exchange,
        'adj' :adj,
        'ma' :ma,
        "factors" : factors,
        "adjfactor" : adjfactor,
        "offset" : offset,
        "limit" :limit,
        "fields" : fields,
        "contract_type" : contract_type
    }
    if 'min' in freq :
        return '此接口为单独权限，和积分没有关系,需要单独购买'
    else:
        # 记录请求开始时间
        start_time = time.time()
        response = requests.post(url, json=params,)
        # 计算耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"pro_bar 请求耗时: {elapsed_time:.2f} 秒")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data == 'token无效或已超期,请重新购买':
                    return data
                else:
                    # 改进的DataFrame创建逻辑（与query方法保持一致）
                    try:
                        # 如果数据是列表且非空
                        if isinstance(data, list) and data:
                            df = pd.DataFrame(data)
                        # 如果数据是字典
                        elif isinstance(data, dict):
                            # 如果字典的值都是列表，可以直接创建DataFrame
                            if all(isinstance(v, list) for v in data.values()):
                                df = pd.DataFrame(data)
                            else:
                                # 如果是单行数据，包装成列表
                                df = pd.DataFrame([data])
                        # 如果数据是标量值
                        elif isinstance(data, (str, int, float, bool)):
                            # 创建单列单行的DataFrame
                            df = pd.DataFrame({'result': [data]})
                        # 如果数据是空列表
                        elif isinstance(data, list) and not data:
                            # 创建空DataFrame
                            df = pd.DataFrame()
                        else:
                            # 其他情况，尝试直接创建
                            df = pd.DataFrame(data)
                        
                        return df
                        
                    except Exception as df_error:
                        # 如果DataFrame创建失败，记录详细信息并返回原始数据
                        print(f"pro_bar DataFrame创建失败: {df_error}")
                        print(f"数据类型: {type(data)}")
                        print(f"数据内容: {str(data)[:200]}...")
                        
                        # 返回原始数据，让调用者决定如何处理
                        return data
                        
            except ValueError as e:
                raise ValueError(e)
        else:

            raise ValueError("数据获取错误",response.status_code,response.text)
