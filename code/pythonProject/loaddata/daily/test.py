import chinadata.ca_data as ts

# 设置 Tushare Pro 的 token
# ts.set_token('4d35e3519c0542e998104d84cb4c00a7')
ts.set_token('i80872d274089319bd0e3fb9d7d6730d637')
pro = ts.pro_api()


if __name__ == "__main__":
    result = pro.disclosure_date(ann_date="20250903")
    print(result)
