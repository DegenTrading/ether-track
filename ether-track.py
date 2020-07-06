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

#Create temporary directory to store data files
temppath = tempfile.mkdtemp()

newbool = True
neednewbalancelistbool = False
messagesentlist = []
blocknumber = 0
lista = []
newdatalista = []
newdatalistb = []



lista.append(startadd)



def telegram_bot_sendtext(bot_message):

	safetext = urllib.parse.quote(bot_message)
	send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + safetext
	response = requests.get(send_text)
	return response.json()

def divide_chunks(l, n): 
      
    for i in range(0, len(l), n):  
        yield l[i:i + n] 


def checkadd(addlist20):
	global messagesentlist
	global newbool
	global neednewbalancelistbool
	global lista
	global newdatalista
	global newdatalistb
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
		#If this function is passed for first time
		if newbool == True:
			
			with open(str(temppath)+'/addwithbalance1.csv', 'a') as fa:
				csvW2 = csv.writer(fa)
				csvW2.writerow([x['account'], str(int(x['balance'])/1000000000000000000)])
		
		#Else
		else:
			
			with open(str(temppath)+'/addwithbalance1.csv') as ff:
				csvR2 = csv.reader(ff)
				for row in islice(csvR2, startslice, endslice):

					if row[0] == x['account'] and row[1] != str(int(x['balance'])/1000000000000000000):
						print("CHANGE IN AMOUNT " + str(x['account']))
						neednewbalancelistbool = True
						if x['account'] not in newdatalista:
							newdatalista.append(x['account'])
							newdatalistb.append(str(int(x['balance'])/1000000000000000000))

						rnewtx = requests.get("http://api.etherscan.io/api?module=account&action=txlist&address="+x['account']+"&startblock="+str(blocknumber)+"&endblock=99999999&sort=asc&apikey="+str(ESAPIKey))
						
						jsonD = json.loads(rnewtx.text)['result']

						#Wait for 10 Seconds if no new transaction are showing on the API yet
						if len(jsonD) == 0:
							time.sleep(10)
							rnewtx = requests.get("http://api.etherscan.io/api?module=account&action=txlist&address="+x['account']+"&startblock="+str(blocknumber)+"&endblock=99999999&sort=asc&apikey="+str(ESAPIKey))
						
							jsonD = json.loads(rnewtx.text)['result']

							print(jsonD)

						#Check every new transaction
						for t in jsonD:
							if t['to'] not in lista:
								with open(str(temppath)+'/listofadd1.csv', 'a') as f:
									csvW = csv.writer(f)
									csvW.writerow([t['to']])

								lista.append(t['to'])
								if t['to'] not in messagesentlist:
									telegram_bot_sendtext("New Transaction to unmonitored address: " + t['to'] + " of value: " + str(int(t['value'])/1000000000000000000) + " ETH")
								
									messagesentlist.append(t['to'])

								if t['to'] not in newdatalista:
									newdatalista.append(t['to'])
									newdatalistb.append(str(int(t['value'])/1000000000000000000))
							else:
								if t['to'] not in messagesentlist:
									if t['from'] not in messagesentlist:
										telegram_bot_sendtext("Intra transfer from " + t['from'] + " to " + t['to'] + " of value: " + str(int(t['value'])/1000000000000000000) + " ETH")
										messagesentlist.append(t['to'])
							
					else:
						if x['account'] not in newdatalista:
							newdatalista.append(x['account'])
							newdatalistb.append(str(int(x['balance'])/1000000000000000000))



def gettoadd(startadd):

	r = requests.get("http://api.etherscan.io/api?module=account&action=txlist&address="+startadd+"&startblock=0&endblock=99999999&sort=asc&apikey="+str(ESAPIKey))
	jsonD = json.loads(r.text)['result']

	
	if len(jsonD) == 1:
		return
	for t in jsonD:
	
		if t['to'] not in lista:
			lista.append(t['to'])
		
			with open(str(temppath)+'/listofadd1.csv', 'a') as f:
				csvW = csv.writer(f)
				csvW.writerow([t['to']])
				print(t['to'])

			gettoadd(t['to'])


#######################################################################
################################ Start ################################
#######################################################################



if os.path.exists(str(temppath)+'/listofadd1.csv'):
	os.remove(str(temppath)+'/listofadd1.csv')
if os.path.exists(str(temppath)+'/addwithbalance1.csv'):
	os.remove(str(temppath)+'/addwithbalance1.csv')


telegram_bot_sendtext("Starting checker for "+ str(startadd))


try:

	#MAIN RECURSIVE FUNCTION 
	gettoadd(startadd)


	telegram_bot_sendtext("Found "+ str(len(lista)) + " associated addresses")

except Exception as e:
	telegram_bot_sendtext("Error Finding Addresses")
	telegram_bot_sendtext(str(e))




try:


	#MAIN LOOP
	while(True):
		#Get a resonably recent blocknumber to discover only new transactions (to check when address balance changes)
		rb = requests.get("https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp="+str(int(time.time()))+"&closest=before&apikey="+str(ESAPIKey))

		blocknumber = str(int(json.loads(rb.text)['result'])-300)
		
		#Break addresses into chunks of 20
		listoflistof20 = list(divide_chunks(lista, 20))
		startslice = 1
		endslice = 21
		for listof20 in listoflistof20:
			print("Checking Addresses " + str(startslice) + " to " + str(endslice))
			checkadd(listof20)
			startslice = startslice + 20
			endslice = endslice + 20
		newbool = False
		print("CHECKING Done.. Repeating")

		if neednewbalancelistbool == True:
			print("Creating New balance")


			if os.path.exists(str(temppath)+'/addwithbalance1.csv'):
				os.remove(str(temppath)+'/addwithbalance1.csv')

			if len(newdatalista) != len(newdatalistb):
				print("List mismatch")
				exit()

			cnt=0	

			for add in newdatalista:
				with open(str(temppath)+'/addwithbalance1.csv', 'a') as fg:
					csvW3 = csv.writer(fg)
					csvW3.writerow([add, newdatalistb[cnt]])
				cnt = cnt + 1



			neednewbalancelistbool = False
			lista = newdatalista

		newdatalista = []
		newdatalistb = []
except Exception as e:
	telegram_bot_sendtext("Error Arose, Bot needs restarting")
	telegram_bot_sendtext(str(e))





		






