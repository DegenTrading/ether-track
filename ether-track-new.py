import requests
import json
import time
import csv
import os
import tempfile
import urllib
from itertools import islice


#Setting variables 

#startadd is the root address
startadd = input("Enter root address: ").lower().strip() 


#Telegram specific variables
bot_token = input("Enter Telegram bot token: ").strip()
bot_chatID = input("Enter Telegram chat id: ").strip()

#EtherScan.io API key
ESAPIKey = input("Enter EtherScan API key: ").strip()

lista = []
listb = []
listoa = []
listob = []







def telegram_bot_sendtext(bot_message):

	safetext = urllib.parse.quote(bot_message)
	send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + safetext
	response = requests.get(send_text)
	return response.json()

def divide_chunks(l, n): 
      
    for i in range(0, len(l), n):  
        yield l[i:i + n] 


def checkadd(addlist20, createcsv, csvname):
	
	if len(addlist20) > 20:
		print("Address list too long")
		return 

	if len(addlist20) < 1:
		print("Address list cannot be less than 1")
		return

	urlprefix = "https://api.etherscan.io/api?module=account&action=balancemulti&address="  
	urlpostfix = "&tag=latest&apikey="+str(ESAPIKey)
	urlmiddle = ""
	for address in addlist20:
		urlmiddle = urlmiddle + address + ","

	#Remove trailing comma
	urlmiddle = urlmiddle[:-1]

	urltocheck = urlprefix + urlmiddle + urlpostfix

	rcheck = requests.get(urltocheck)

	jsoncheckD = json.loads(rcheck.text)['result']






	for x in jsoncheckD:

		if createcsv == False:
			newadd = x['account']
			newbal = str(int(x['balance'])/1000000000000000000)


			telegram_bot_sendtext("New address found: " + newadd + " Balance of: "+newbal+"ETH")
		else:
			for n, i in enumerate(lista):
				if i == x['account']:
					blocknum = listb[n]

			with open(str(temppath)+'/'+csvname, 'a') as fa:
				csvW2 = csv.writer(fa)
				csvW2.writerow([x['account'], str(int(x['balance'])/1000000000000000000), blocknum])





		
		



def gettoadd(startadd):
	global lista
	global listb
	global listoa
	global listob

	r = requests.get("http://api.etherscan.io/api?module=account&action=txlist&address="+startadd+"&startblock=0&endblock=99999999&sort=asc&apikey="+str(ESAPIKey))
	jsonD = json.loads(r.text)['result']

	
	if len(jsonD) == 1:
		return
	for t in jsonD:
	
		if t['to'] not in lista:
			lista.append(t['to'])
			listb.append(t['blockNumber'])
			gettoadd(t['to'])
		else:
			for n, i in enumerate(lista):
				if i == t['to']:
					if int(t['blockNumber']) > int(listb[n]):
						listb[n] = t['blockNumber']
						try:
							if int(t['blockNumber']) > int(listob[n]):
								telegram_bot_sendtext("New intra transfer to " + t['to'] + " of value " + str(int(t['value'])/1000000000000000000))
						except Exception as e:
							print(e)
							print("First time.. passing")
							pass


			


#######################################################################
################################ Start ################################
#######################################################################





telegram_bot_sendtext("NEW BOT - Starting checker for "+ str(startadd))


try:
	gettoadd(startadd)


	telegram_bot_sendtext("Found "+ str(len(lista)) + " associated addresses, refreshing...")

	
	while(True):
		listoa = lista
		listob = listb

		lista = []
		listb = []
		gettoadd(startadd)
		if lista != listoa:
			listalert = list(set(lista) - set(listoa))
			listoflistalert = list(divide_chunks(listalert, 20))
			for la in listoflistalert:
				checkadd(la, False, "")

		listoflistof20 = list(divide_chunks(lista, 20))
		

		csvname1 = "addwithbalance"+str(int(time.time()))+".csv"
		print(str(temppath) + '/' + csvname1)
		for listof20 in listoflistof20:
			checkadd(listof20, True, csvname1)



				
		


except Exception as e:
	print("Error Finding Addresses")
	print(str(e))





		






