import requests, json
import sched, time
import sys
import logging
import pyotp
from colorama import Fore, Back, Style
import os
import smtplib, ssl

skinbaron_key = 'YOURE SKINBARON KEY HERE'
bitskins_key = 'YOURE BITSKINS KEY HERE'
bitskins_secret = 'YOURE BITSKINS SECRET HERE'
s = sched.scheduler(time.time, time.sleep)
pricelist = []
PERCENTAGE = 50

'''
Read data from input-file and scan skinbaron for them

    Parameters
    ----------
    sc : the scheduler for the method
    
'''
def initRun(sc):
    print(Fore.YELLOW+'- Init Run and start Scanning for static Items')
    try:
        filepath = './example.txt'
        with open(filepath) as fp:
            line = fp.readline()
            while line:
                line = fp.readline().rstrip()
                params = tuple(line.split(','))
                if params[0] == '':
                    break
                #print(params)
                scanForItems(params[0], params[1], True)
            s.enter(60, 1, initRun, (s,))
            print(Fore.YELLOW+'--- Check for Items under percentage')
            checkSkinBaronForItemsUnderPercent(PERCENTAGE)
    except KeyboardInterrupt:
        pass
     



'''
Scan skinbaron for specfic items by name

    Parameters
    ----------
    name : String
         The name of the item to look for.
    max : Number
         The max value to pay for the specific item
    buy : boolean
         if true the item will be instantly buyed else you will get only notified
'''
def scanForItems(name, max, buy=False):
    data_search = {'apikey': skinbaron_key, 'appid': '730', 'search_item': name, 'max': max}
    headers = {'content-type': 'application/json',  'x-requested-with': 'XMLHttpRequest', 'accept': 'application/json'}
    try:
        r = requests.post('https://api.skinbaron.de/Search', data=json.dumps(data_search), headers=headers)
        json_dict = r.json()
        print(max, json_dict)
        ids = []
        price = 0
        count = 0
        for item in json_dict['sales']:
            if count == 49:
                break
            ids.append(str(item['id']))
            price += item['price']
            count += 1
        price = round(price, 2)
        data_buy = {'apikey': skinbaron_key, 'total': price, 'saleids': ids}
        r = requests.post('https://api.skinbaron.de/BuyItems', data=json.dumps(data_buy), headers=headers)
        j_response = r.json()
        if(len(ids) == 0):
            print(Fore.RED+'-- '+name+' not found for buy')
        else:
            print(Fore.GREEN+'-!!- '+name+' found and buyed: ')
            print(r.content)

        if 'generalErrors' not in j_response:
                logging.info('%s buyed %s times for %s', j_response['items'][0]['name'], len(j_response['items']), j_response['total'])
                
    except:
        print("Exception triggered")
        logging.warning('Exception triggered in request request')


'''Get the actual Price-List of all items from Bitskins.com'''
def getBitskinsPriceList(api_key, secret):
    try:
        token = pyotp.TOTP(bitskins_secret)
        data_bit = {'api_key': '5f899935-6c30-466c-8aed-ce857a8735cf', 'app_id': '730', 'code': token.now()}
        headers_bit = {'content-type': 'application/json', 'accept': 'application/json'}
        r = requests.post('https://bitskins.com/api/v1/get_all_item_prices', data=json.dumps(data_bit), headers=headers_bit)
        return r.json()
    except Exception as e:
        print("Exception triggered "+ str(e))
    return []


'''
Check skinbaron Items against the Bitskins price list and buy items which are half the price on skinbaron

    Parameters
    ----------
    percent : int
         The percentage which a price on skinbaron is under the steam price.
         As Example: M9 on skinbaron 50$, on steam 100$ => if percentage = 50 the bot would buy the m9
'''
last_result_length = 0
def checkSkinBaronForItemsUnderPercent(percent):
    global last_result_length
    data_search = {'apikey': skinbaron_key, 'appid': '730', 'min':0.40, 'max':1000.0, 'items_per_page':500}
    headers = {'content-type': 'application/json',  'x-requested-with': 'XMLHttpRequest', 'accept': 'application/json'}
    try:
        r = requests.post('https://api.skinbaron.de/Search', data=json.dumps(data_search), headers=headers)
        json_dict = r.json()
        count = 0
        result = []
        for item in json_dict['sales']:
            if count == 100:
                break
            for st_item in pricelist['prices']:
                if(item['market_name'] == st_item['market_hash_name']):
                    if(float(item['price'])*1.1 <= (float(st_item['price'])/100)*percent):
                        result.append(tuple((item['market_name'], item['price'], st_item['price'], 'skinbaron.de/offers/show?offerUuid='+str(item['id']))))
                        if(float(item['price']) >= 1 and item['market_name'].find('X-Ray') == -1 and item['market_name'].find('Souvenir') == -1 and item['market_name'].find('Graffiti') == -1 and (item['market_name'].find('AWP') != -1 or item['market_name'].find('AK-47') != -1 or item['market_name'].find('M9') != -1 or item['market_name'].find('Butterfly') != -1 or item['market_name'].find('Karambit') != -1 or item['market_name'].find('Knife') != -1)):
                            id = []
                            id.append(item['id'])
                            data_buy = {'apikey': skinbaron_key, 'total': item['price'], 'saleids': id}
                            r = requests.post('https://api.skinbaron.de/BuyItems', data=json.dumps(data_buy), headers=headers)
                        count += 1
        if len(result) == 0:
            print(Fore.RED+'---- NO Items found under Percentage')
        else:
            print(Fore.GREEN+'--!!!-- Items found:')
            print(result)
            if(last_result_length < len(result)):
                notify('New Item', 'New Item found look fast!!!')
                last_result_length = len(result)
                #message = "New Item. "+" \n "+str(result)
                #sendEmail(message)

    except Exception as e:
        print("Exception triggered "+ str(e))
    return
    
'''
Calculate your inventory value on static prices which you have to adapt.
Could be optimized if you check your inventory against the bitskins price-list
'''
"""
def calculateInventoryValue():
    data_search = {'apikey': skinbaron_key, 'appid': '730'}
    headers = {'content-type': 'application/json',  'x-requested-with': 'XMLHttpRequest', 'accept': 'application/json'}
    try:
        r = requests.post('https://api.skinbaron.de/GetInventory', data=json.dumps(data_search), headers=headers)
        json_dict = r.json()
        result = 0
        print(json_dict['items'][0])
        for item in json_dict['items']:
            if item['marketHashName'] == 'Clutch Case':
                result += 0.03
            elif item['marketHashName'] == 'Glove Case':
                result += 0.03
            elif item['marketHashName'] == 'Danger Zone Case':
                result += 0.03
            elif item['marketHashName'] == 'Shadow Case':
                result += 0.03
            elif item['marketHashName'] == 'Prisma Case':
                result += 0.05
            elif item['marketHashName'] == 'Spectrum 2 Case':
                result += 0.03
        print(Fore.BLUE+'Inventarwert mit '+str(len(json_dict['items']))+ ' -> '+str(result))    
    except Exception as e:
        print("Exception triggered "+ str(e))
    return
"""

def notify(title, text):
    os.system("""
        osascript -e 'display notification "{}" with title "{}"'
    """.format(text, title))
    
    
"""
Send a email if a item under percentage of the steam price is found
"""
"""
def sendEmail(message):
    port = 465  # For SSL
    password = ''
    sender_email = ''
    receiver_email = ''
    context = ssl.create_default_context()

    server = smtplib.SMTP_SSL("smtp.gmail.com", port)
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
    server.quit()
"""

#calculateInventoryValue()

#Setup logging data
logging.basicConfig(filename='./buyHistory.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

pricelist = getBitskinsPriceList(bitskins_key, bitskins_secret)
s.enter(0, 1, initRun, (s,))
s.run()
