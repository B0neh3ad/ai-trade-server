import pandas as pd

masterfile = pd.read_csv("/home/js1044k/ai-trade-server/app/_experiment/masterfiles/fo_idx_code_mts.csv")
masterfile.columns = masterfile.columns.str.strip()

futures = masterfile[masterfile['한글종목명'].str.startswith('F ')]
futures = futures.sort_values(by='한글종목명')

recent_futures_code = futures['단축코드'][0]
recent_futures_maturity_contract = futures['한글종목명'].iloc[0].split(' ')[1]
next_recent_futures_code = futures['단축코드'][1]
next_recent_futures_maturity_contract = futures['한글종목명'].iloc[1].split(' ')[1]

print(recent_futures_code)
print(next_recent_futures_code)
print(recent_futures_maturity_contract)
print(next_recent_futures_maturity_contract)

monthly_options = masterfile[masterfile['한글종목명'].str.startswith('C ')].copy()
monthly_options['한글종목명_행사가제외'] = monthly_options['한글종목명'].str.split(' ').str[:-1].str.join(' ')

monthly_options_min = monthly_options.groupby('한글종목명_행사가제외').min()
monthly_options_max = monthly_options.groupby('한글종목명_행사가제외').max()
monthly_options_codes = monthly_options_min['단축코드'].iloc[0][1:-3]
monthly_options_maturity_contract = monthly_options_min['한글종목명'].iloc[0].split(' ')[1].replace('M', '0')

monthly_options_min = float(monthly_options_min['행사가'].iloc[0])
monthly_options_max = float(monthly_options_max['행사가'].iloc[0])

weekly_options = masterfile[masterfile['한글종목명'].str.startswith('위클리')].copy()
weekly_options['한글종목명_행사가제외'] = weekly_options['한글종목명'].str.split(' ').str[:-1].str.join(' ')

# 월요일 만기 옵션
weekly_options_monday = weekly_options[weekly_options['한글종목명'].str.startswith('위클리C')]
weekly_options_monday_code = weekly_options_monday['단축코드'].iloc[0][1:-3]

weekly_options_monday_min = float(weekly_options_monday['행사가'].min())
weekly_options_monday_max = float(weekly_options_monday['행사가'].max())
weekly_options_monday_maturity_contract = weekly_options_monday['한글종목명'].iloc[0].split(' ')[1].replace('W', '0')

# 목요일 만기 옵션
weekly_options_thursday = weekly_options[weekly_options['한글종목명'].str.startswith('위클리M')]
weekly_options_thursday_code = weekly_options_thursday['단축코드'].iloc[0][1:-3]

weekly_options_thursday_min = float(weekly_options_thursday['행사가'].min())
weekly_options_thursday_max = float(weekly_options_thursday['행사가'].max())
weekly_options_thursday_maturity_contract = weekly_options_thursday['한글종목명'].iloc[0].split(' ')[2].replace('W', '0')

print(monthly_options_codes, monthly_options_min, monthly_options_max, monthly_options_maturity_contract)

print(weekly_options_monday_code, weekly_options_monday_min, weekly_options_monday_max, weekly_options_monday_maturity_contract)
print(weekly_options_thursday_code, weekly_options_thursday_min, weekly_options_thursday_max, weekly_options_thursday_maturity_contract)
