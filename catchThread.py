import os
import requests, json, hashlib
from time import sleep
from threading import Thread
from datetime import datetime
import copy

import global_var
import dataConverter
import connectDB

from td.client import TDClient

def _validateProfit(postion, profits):
    for profit in profits:
        if profit['price'] != '' and postion['currentDayProfitLoss'] >= float(profit['price']):
            return {'msg':'profit', 'symbol':postion['instrument']['symbol'], 'profit':postion['currentDayProfitLoss'], 'value':profit['price'], 'type':'price'}
        if profit['contract'] != '' and postion['currentDayProfitLossPercentage'] >= float(profit['contract']):
            return {'msg':'profit', 'symbol':postion['instrument']['symbol'], 'profit':postion['currentDayProfitLossPercentage'], 'value':profit['contract'], 'type':'contract'}
    return None

def _validateStoploss(postion, stoploss):
    if stoploss['price'] != '' and postion['currentDayProfitLoss'] <= float(stoploss['price']):
        return {'msg':'stoploss', 'symbol':postion['instrument']['symbol'], 'stoploss':postion['currentDayProfitLoss'], 'value':stoploss['price'], 'type':'price'}
    if stoploss['contract'] != '' and postion['currentDayProfitLossPercentage'] <= float(stoploss['contract']):
        return {'msg':'stoploss', 'symbol':postion['instrument']['symbol'], 'stoploss':postion['currentDayProfitLossPercentage'], 'value':stoploss['contract'], 'type':'contract'}

def catch_thread(event):
    while event.is_set() == False:
        # td_consumer_key = 'UGPAX5IGKEO3JRPGAEQMS4CCNH4I6GPC'
        # base_url = 'https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/quotes?'
        # endpoint = base_url.format(stock_ticker = 'AAPL')
        # page = requests.get(url=endpoint,
        #                     params={'apikey' : td_consumer_key})
        # if page.status_code == 200:
        #     content = json.loads(page.content)
        #     val = content['AAPL']['mark']
        #     global_var.strike_val = val
        # else:
        #     pass
        accs = connectDB.getAvailableAccounts()
        for acc in accs:
            if acc['client_id'] == '' or acc['client_id'] is None:
                continue
            TDSession = TDClient(
                client_id=acc['client_id'],
                redirect_uri='http://127.0.0.1:3000',
                credentials_path='./token/'+acc['client_id']+'.json'
            )
            if(os.path.isfile(TDSession.credentials_path) and TDSession._silent_sso()):
                TDSession.login()
                acc_info = TDSession.get_accounts(account='all', fields=['orders','positions'])
                acc_id = acc_info[0]['securitiesAccount']['accountId']
                if 'positions' in acc_info[0]['securitiesAccount']:
                    postions = acc_info[0]['securitiesAccount']['positions']
                else :
                    postions = []
                if len(postions) > 0:
                    stoploss = global_var.stoploss
                    profitloss = global_var.getprofit
                    for pos in postions:
                        ret = _validateProfit(pos, profitloss)
                        if ret is not None:
                            ret['acc_id'] = acc_id
                            ret['acc_name'] = acc['acc_name']
                            dhash = hashlib.md5()
                            encoded = json.dumps(ret, sort_keys=True).encode()
                            dhash.update(encoded)
                            hashkey = dhash.hexdigest()
                            if hashkey not in global_var.messages:
                            # if hashkey not in global_var.messages or \
                            #         hashkey in global_var.messages and \
                            #         'opened' in global_var.messages[hashkey] and \
                            #         global_var.messages[hashkey]['opened'] == 0:
                                global_var.messages[hashkey] = ret
                            # print("*******      profit      ************")
                        else:
                            ret = _validateStoploss(pos, stoploss)
                            if ret is not None:
                                ret['acc_id'] = acc_id
                                ret['acc_name'] = acc['acc_name']
                                dhash = hashlib.md5()
                                encoded = json.dumps(ret, sort_keys=True).encode()
                                dhash.update(encoded)
                                hashkey = dhash.hexdigest()
                                if hashkey not in global_var.messages:
                                    global_var.messages[hashkey] = ret
                        # print(pos)
                
                if 'orderStrategies' in acc_info[0]['securitiesAccount']:
                    orders = acc_info[0]['securitiesAccount']['orderStrategies']
                else :
                    orders = []
                makeNotific = False
                if acc_id in global_var.acc_order_getted:
                    makeNotific = True
                else:
                    global_var.acc_order_getted.append(acc_id)
                for order in orders:
                    if (order['orderId'] in global_var.orders\
                        and global_var.orders[order['orderId']]['status'] != order['status']\
                        or order['orderId'] not in global_var.orders)\
                        and makeNotific:
                        instruction = order['orderLegCollection'][0]['instruction']
                        symbol = order['orderLegCollection'][0]['instrument']['symbol']
                        quantity = order['orderLegCollection'][0]['quantity']
                        if instruction == "Buy" or instruction == "buy" or instruction == "BUY":
                            instruction = "CALL"
                        else:
                            instruction = "PUT"

                        if order['status'] == "FILLED" or order['status'] == "WORKING":
                            color = global_var.color_info_back
                            if instruction == "CALL":
                                global_var.interact_msgs.append({'msg':"{acc} {instruction} {symbol} {quantity}".format(acc=acc['acc_name'], instruction=instruction, symbol=symbol, quantity=quantity)})
                        if order['status'] == "CANCELED" or order['status'] == "REJECTED":
                            color = global_var.color_err_back
                        else:
                            color = global_var.color_warning_back
                        
                        global_var.trade_msgs.append({'color':color, 'msg':"{acc}\n{instruction} {symbol} {quantity}\n{state}".format(acc=acc['acc_name'], instruction=instruction, symbol=symbol, quantity=quantity, state=order['status'])})
                    global_var.orders[order['orderId']] = order
        # print('*'*80)
        # for x in global_var.orders:
        #     order = global_var.orders[x]
        #     print("{orderid}   {acc}    c:{categ}    {symbol} q:{quantity}    s:{state}".format(orderid=order['orderId'], acc=order['accountId'], categ=order['orderLegCollection'][0]['instruction'], symbol=order['orderLegCollection'][0]['instrument']['symbol'], quantity=order['orderLegCollection'][0]['quantity'], state=order['status']))
        # # print(global_var.orders)
        # print('#'*80)
        print(' ...  Catching ... ')
        sleep(2)



def makeOrder(pm_data, user_id, client_id, acc_name, max_balance, leverage, ret, index):
    ret_dic = {'state':'init', 'client':client_id, 'name':acc_name, 'user_pk':user_id}
    pm_data['orderLegCollection'][0]['quantity'] = float(pm_data['orderLegCollection'][0]['quantity']) * float(leverage)
    print(".....  making order {client_id} : {quantity}, {leverage} .....".format(client_id=client_id, quantity=pm_data['orderLegCollection'][0]['quantity'], leverage=leverage))

    symbol = pm_data['orderLegCollection'][0]['instrument']['symbol']
    quantity = float(pm_data['orderLegCollection'][0]['quantity'])
    quotes = quantity * float(pm_data['price'])
    order_categ = pm_data['orderLegCollection'][0]['instruction']
    if order_categ == "Buy":
        wkday = datetime.today().strftime('%A')
        if wkday == 'Friday':
            tmp = global_var.fridaymax
            tmp['max_percent'] = float(tmp['max_percent'])
            max_balance = float(max_balance)
            if tmp['on_off'] == 1:
                if tmp['all_some'] == 1:
                    if acc_name in tmp['accs']:
                        # max_balance = tmp['max_percent']
                        max_balance = max_balance * tmp['max_percent'] / 100
                else:
                    max_balance * tmp['max_percent'] / 100
        ret_dic['max_balance'] = float(max_balance)
        if quotes > ret_dic['max_balance']:
            ret_dic['state'] = 'overflow_balance'
            global_var.trade_msgs.append({'color':global_var.color_err_back, 'msg':"{acc} trying to trade\nmore cache than max balance".format(acc=acc_name)})
    if ret_dic['state'] == 'init':
        TDSession = TDClient(
            client_id=client_id,
            redirect_uri='http://127.0.0.1:3000',
            credentials_path='./token/'+client_id+'.json'
        )
        if(os.path.isfile(TDSession.credentials_path) and TDSession._silent_sso()):
            TDSession.login()
            acc_info = TDSession.get_accounts(account='all', fields=['orders','positions'])
            if order_categ == "Buy":            # -- check wether cach available
                cache = float(acc_info[0]['securitiesAccount']['initialBalances']['cashAvailableForTrading'])
                if cache >= quantity * float(pm_data['price']):
                    callback = TDSession.place_order(account=acc_info[0]['securitiesAccount']['accountId'], order=pm_data)
                    ret_dic['state'] = 'ok'
                    ret_dic['categ'] = 'buy'
                    ret_dic['order'] = callback
                else:
                    ret_dic['state'] = 'err'
                    ret_dic['categ'] = 'no_cache'
                    global_var.trade_msgs.append({'color':global_var.color_err_back, 'msg':"{acc} has less cache.\nPlease purchag now.\nCALL {symbol} {num} order cancelled".format(acc=acc_name, symbol=symbol, num=quantity)})
            else:                               # -- check wether stock availabe
                if 'positions' in acc_info[0]['securitiesAccount']:
                    postions = acc_info[0]['securitiesAccount']['positions']
                else :
                    postions = []
                found_flag = False
                for pos in postions:
                    if pos['instrument']['symbol'] == pm_data['orderLegCollection'][0]['instrument']['symbol']:
                        found_flag = True
                        if float(pos['longQuantity']) >= pm_data['orderLegCollection'][0]['quantity']:
                            callback = TDSession.place_order(account=acc_info[0]['securitiesAccount']['accountId'], order=pm_data)
                            ret_dic['state'] = 'ok'
                            ret_dic['categ'] = 'sell'
                            ret_dic['order'] = callback
                        else:
                            ret_dic['state'] = 'err'
                            ret_dic['categ'] = 'less_stock'
                            global_var.trade_msgs.append({'color':global_var.color_warning_back, 'msg':"{acc} has less stock than {num}.\nPUT {symbol} {num} order changed {num2}".format(acc=acc_name, symbol=symbol, num=quantity, num2=pos['longQuantity'])})
                            pm_data['orderLegCollection'][0]['quantity'] = pos['longQuantity']
                            callback = TDSession.place_order(account=acc_info[0]['securitiesAccount']['accountId'], order=pm_data)
                if not found_flag:
                    ret_dic['state'] = 'err'
                    ret_dic['categ'] = 'no_stock'
                    global_var.trade_msgs.append({'color':global_var.color_err_back, 'msg':"{acc} has no stock.\nPUT {symbol} {num} order cancelled".format(acc=acc_name, symbol=symbol, num=quantity)})
            # ret_dic['order_id'] = callback['order_id']
        else:
            # connectDB.updateSubLog(db_id, 'is_done', 3)
            ret_dic['state'] = 'no_token'
            if order_categ == "Buy":
                msg_categ = "CALL"
            else:
                msg_categ = "PUT"
            global_var.trade_msgs.append({'color':global_var.color_err_back, 'msg':"{acc} is not logged in.\nPlease register before use copier function.\n{call} {symbol} {num} order cancelled".format(acc=acc_name, call=msg_categ, symbol=symbol, num=quantity)})
    ret[index] = ret_dic

def cancelOrder(json_data):
    print('cancel_order')
    tmp_json = json.loads(json_data['order_json'])
    instruction = tmp_json['orderLegCollection'][0]['instruction']
    quantity = tmp_json['orderLegCollection'][0]['quantity']
    symbol = tmp_json['orderLegCollection'][0]['instrument']['symbol']
    client_id = json_data['client_id']
    TDSession = TDClient(
        client_id=client_id,
        redirect_uri='http://127.0.0.1:3000',
        credentials_path='./token/'+client_id+'.json'
    )
    if(os.path.isfile(TDSession.credentials_path) and TDSession._silent_sso()):
        TDSession.login()
        accmeta = TDSession.get_accounts()
        callback = TDSession.get_orders(account=accmeta[0]['securitiesAccount']['accountId'], order_id=json_data['sub_orderid'])
        if callback['status'] == 'QUEUED' or callback['status'] == 'WORKING':
            TDSession.cancel_order(account=accmeta[0]['securitiesAccount']['accountId'], order_id=json_data['sub_orderid'])
            # connectDB.updateSubLog(json_data['id'], 'state', 'CANCELED')
        else:
            global_var.trade_msgs.append({'color':global_var.color_err_back, 'msg':"{acc} can not cancel order.\n{categ} {symbol} {num} order is already {state}".format(acc=json_data['acc_name'], categ=instruction, symbol=symbol, num=quantity, state=callback['status'])})
    else:
        global_var.trade_msgs.append({'color':global_var.color_err_back, 'msg':"{acc} is not logged in.\nPlease register before use copier function.\n{categ} {symbol} {num} order cancel operation rejected".format(acc=json_data['acc_name'], categ=instruction, symbol=symbol, num=quantity)})
    
def copy_trade(event):
    while event.is_set() == False:
        if len(global_var.tradeCode) > 0:
            print(global_var.tradeCode)
            data = dataConverter.xmlParser(global_var.tradeCode.pop(), global_var.tradeXml.pop())
            if data != None:
                print(data['code'])
                if data['code'] == 'place_order':
                    global_var.tadeJson = data['json']
                    main_log_id = connectDB.createMainLog(data['id'], global_var.TDStreamingDbUserID, json.dumps(data['json']))

                    rows = connectDB.getToTradeAccounts(global_var.TDStreamingClientID)
                    copier_arr = []
                    arr_thrd_ret = []
                    ind = 0
                    for row in rows:
                        arr_thrd_ret.append({'state':'init'})
                        # tmp = dict(data['json'])
                        tmp = copy.deepcopy(data['json'])
                        tmp_thread = Thread(target=makeOrder, args=(tmp, row['id'], row['client_id'], row['acc_name'], row['max_balance'], row['leverage'], arr_thrd_ret, ind, ))
                        copier_arr.append(tmp_thread)
                        tmp_thread.start()
                        ind = ind + 1
                    ind = 0
                    for thrd in copier_arr:
                        thrd.join()
                    # print(' ** '*20)
                    for ret in arr_thrd_ret:
                        if ret['state'] == 'ok':
                            sub_log_id = connectDB.createSubLog(main_log_id, ret['order']['order_id'], ret['user_pk'], ret['order']['request_body'].decode("utf-8"))
                        # print(ret)
                    # print(' #$ '*20)
                elif data['code'] == 'cancel_order':
                    main_order = connectDB.getMainOrder(data['id'])
                    suborders = connectDB.getSubOrdersByMainID(main_order['id'])
                    copier_arr = []
                    for suborder in suborders:
                        tmp_thread = Thread(target=cancelOrder, args=(suborder, ))
                        copier_arr.append(tmp_thread)
                        tmp_thread.start()
                    for thrd in copier_arr:
                        thrd.join()

                    #print(data)
                    #print(main_order)
        print(' ... Copying ...')
        sleep(1)