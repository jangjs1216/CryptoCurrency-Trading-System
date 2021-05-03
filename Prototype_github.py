import pyupbit as pu
import pandas as pd
from pandas import DataFrame, Series
import time
import datetime
import csv

"""
##########################################################

         CryptoCurrency Trading System *PROTOTYPE*

        Trade Cryptocurrency using Simple Algorithm
        
    Desc:
        캘리비중(CalPer) 만큼 자산의 비중을 나눠서, 매수 시그널(VolumeCut 기준) 이 발생한 종목에 대해 자동으로 오전 9시에 시장가로 매수를 진행합니다.
        그 이후, 익절비율(profitCut)만큼 가격이 상승했을때 시장가로 매도를 진행합니다. 일정 기간(MaxDay)만큼 매도가 진행되지 않으면 전량 시장가로 처분합니다.

#########################################################

"""

# Upbit Key
access_key = "Your access Key" 
secret_key = "Your secret Key"
upbit = pu.Upbit(access_key, secret_key)

# CalPer - 캘리비중 / profitCut - 익절비율 / VolumeCut - 거래랑비중 / MaxDay - 들고있는 기간
def Trading(CalPer, BuyVolume, profitCut, VolumeCut, MaxDay):
    
    data = pd.read_csv("./financialData.csv", index_col = 0)
    
    print("Running Trading.. ")
    
    while True:
        time.sleep(0.05)
        File = open("TradingLog.txt", "a")
        
        # 종목 리스트 받아오기
        contentsList = pu.get_tickers()
        
        # 현재 KRW 잔고
        curBalance = upbit.get_balances()[0]['balance']

        now = datetime.datetime.now()
        print(now.hour, now.minute, now.second)
        if now.hour == 9 and now.minute == 0 and now.second >= 0 and now.second < 5:
            # == 2 - 3. MaxDay 기간을 넘은 경우 ==
            print(data)
            for i in range(len(data)):
                date = data.loc[i,'Date']
                curdate = time.time();

                # 시간초 계산
                diff = curdate - int(date)
                
                ticker = data.loc[i,'ticker']
                
                Balance = upbit.get_balances()
                for compare in Balance:
                    if diff > 86400 * MaxDay:
                        print("    판매 대상 발견   ( MaxDay ) ...")
                        print(ticker)
                        balance = float(compare['balance'])
                        upbit.sell_market_order(ticker=ticker, volume=balance)
                        idx = data[data['ticker'] == ticker].index
                        data = data.drop(idx)
                      

            # ===================================
            
            
            print(" 9시 감시 시작... ")
            
            buyCount = 0
            buyTicker = []
            
            # == 1. 감시하면서 구매하기 ==
            for ticker in contentsList:
                time.sleep(0.05)
                
                if ticker[0] != "K":
                    continue
                
                print(ticker)
                
                curlcv = pu.get_ohlcv(ticker=ticker, interval = "day")
                
                if len(curlcv) < 3:
                    continue
                
                yesterday = curlcv.iloc[-2]
                prevday = curlcv.iloc[-3]
                
                # 구매 대상 조건
                if yesterday.loc['volume'] > prevday.loc['volume'] * BuyVolume:
                    print("구매 대상 발견" + time.ctime() + " , " + ticker, file = File)
                    print("    구매 대상 발견    ...")
                    print(ticker)
                    buyCount += 1
                    buyTicker.append(ticker)
            

            buyBalance = float(curBalance) * CalPer / int(buyCount)
            print(buyCount)
            
            # CSV 파일에 기록하기
            for ticker in buyTicker:
                print("구매 체결" + time.ctime() + " , " + ticker, file = File)
                print("      구매 체결      ")
                print(ticker)
                upbit.buy_market_order(ticker = ticker, price = buyBalance)
                data = data.append({'Date' : time.time(), 'ticker' : ticker, 'BuyPrice' : pu.get_ohlcv(ticker).iloc[-1]['close'], 'BuyVolume' : pu.get_ohlcv(ticker).iloc[-2]['volume']}, ignore_index=True)
                
            buyTicker.clear()
                
            # ============================
            
                
        # == 2. 구매시 판매 감시 ==

        for i, row in data.iterrows():
            time.sleep(0.05)
            
            try:
                print(data)
                ticker = data.loc[i, 'ticker']
                
                # 2 - 1. profitCut을 넘은 경우
                
                Balance = upbit.get_balances()
                
                print("Current Close")
                print(pu.get_ohlcv(ticker).iloc[-1]['close'])
                print("Prev Close")
                print(data.loc[i, 'BuyPrice'])
                time.sleep(0.05)
                
                if float(float(pu.get_ohlcv(ticker).iloc[-1]['close'])/data.loc[i, 'BuyPrice']) > profitCut:
                    print("    판매 대상 발견   ( profitCut ) ...")
                    print(ticker)
                    
                    for compare in Balance:
                        if compare['currency'] == ticker[4:]:
                            print("매도 체결, by profitCut" + time.ctime() + " , " + ticker, file = File)
                            print("      매도 체결      ")
                            print(ticker)
                            balance = float(compare['balance'])
                            upbit.sell_market_order(ticker=ticker, volume=balance)
                            idx = data[data['ticker'] == ticker].index
                            data = data.drop(idx)
                            
                time.sleep(0.05)

    
                # 2 - 2. VolumeCut을 넘은 경우
                
                print("Current Close")
                print(pu.get_ohlcv(ticker).iloc[-1]['volume'])
                print("Prev Close")
                print(data.loc[i, 'BuyVolume'])
                time.sleep(0.05)
                
                if float(float(pu.get_ohlcv(ticker).iloc[-1]['volume'])/data.loc[i, 'BuyVolume']) > VolumeCut:
                    print("    판매 대상 발견   ( VolumeCut ) ...")
                    print(ticker)
                    
                    for compare in Balance:
                        if compare['currency'] == ticker[4:]:
                            print("매도 체결, by VolumeCut" + time.ctime() + " , " + ticker, file = File)
                            print("      매도 체결      ")
                            print(ticker)
                            balance = float(compare['balance'])
                            upbit.sell_market_order(ticker=ticker, volume=balance)
                            idx = data[data['ticker'] == ticker].index
                            data = data.drop(idx)
                            

            except KeyError:
                print("Key Error")
                
            data.to_csv('financialData.csv')
            
        File.close()
        
        # ==========================

    # 저장

Trading(0.8, 5.0, 1.075, 0.5, 3)
# Trade!