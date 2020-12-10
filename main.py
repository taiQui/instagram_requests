"""

author: taiQui

Class to interacte with Instagram with only requests

Explication:

After logging in
we need to request to /SomeAccount/?__a=1 for json result
on this json result, we pick Id of the account chosen, cursor of scrolling and number of picture in account (max)
once this done, we can request graphql to get all links
https://www.instagram.com/graphql/query/?query_hash=003056d32c2554def87228bc3fd9668a&variables=%7B%22id%22%3A%22{  -- ID   --}%22%2C%22first%22%3A{   -- STEP --  }%2C%22after%22%3A%22{ -- cursor -- }\"%7D
ID => id of account previously got
STEP => get picture by range of 50 by 50 (50 is max but we can get only 12 picture and stop here)
CURSOR => cursor previously got
cursor is like cursor in file
cursor --> +------------------+
           |                  |
           |                  |
           |                  |
           +------------------+
next iteration
           +------------------+
cursor --> |                  |
           |                  |
           |                  |
           +------------------+

on each requests on this, we need to get another time the cursor modified to use it next iteration

if the requests doesnt work, maybe need to go on instagram and accept the "suspicious request" or in Setting => confidentiality/security => logging => it's me for the last connection

"""

import requests,json,time
from os import mkdir
from os.path import isdir
from datetime import datetime

class InstaBot:
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.session = None
        self.login()

    def login(self):
        self.session = requests.Session()
        r = self.session.get("https://www.instagram.com/data/shared_data/").json()
        csrf = r['config']['csrf_token']
        ajax = r['rollout_hash']
        pubkey = r['encryption']['public_key']
        key_id = r['encryption']['key_id']
        header = {
                    "X-CSRFToken":csrf,
                    "X-Instagram-AJAX":ajax,
                    "X-IG-WWW-Claim": "0",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Requested-With": "XMLHttpRequest",
                    "TE": "Trailers"

        }
        self.session.headers.update({"User-Agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0"})
        time = int(datetime.now().timestamp())
        data = {
                    "username":self.username,
                    "enc_password":f'#PWD_INSTAGRAM_BROWSER:0:{time}:{self.password}',
                    "query_Params":{},
                    "optIntoOneTap":"false"
        }
        r = self.session.post("https://instagram.com/accounts/login/ajax/",headers=header,data=data).json()
        try:
            if r["authenticated"]:
                print("[+] Connected Successfully")
        except:
            print("[-] Something went wrong with login !")
            exit()

    def _get_cursor(self,account):
        print(f"[+] Getting {account}")
        try:
            time.sleep(5)
            r = self.session.get(f"https://www.instagram.com/{account}/?__a=1").json()
            id = r['graphql']['user']['id']
            cursor = r['graphql']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
            max = r['graphql']['user']['edge_owner_to_timeline_media']['count']
            return id,cursor,max
        except:
            return None


    def _get_link(self,id,cursor,max,acc):
        current = 0
        pictures_link = []
        step = 50
        print(f"[+] Getting all link for {acc}")
        while current < max :
            try:
                time.sleep(5)
                r = self.session.get(f"https://www.instagram.com/graphql/query/?query_hash=003056d32c2554def87228bc3fd9668a&variables=%7B%22id%22%3A%22{id}%22%2C%22first%22%3A{step}%2C%22after%22%3A%22{cursor}\"%7D").json()
                cursor = r['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
                for edge in r['data']['user']['edge_owner_to_timeline_media']['edges']:
                    pictures_link.append(edge['node']['display_url'])
            except Exception as e:
                print(e)

            current += step
        size = len(pictures_link)
        print(f"[*] Got {size} link")
        return pictures_link

    def get(self,account,path=None):
        id,cursor,max = self._get_cursor(account)
        links = self._get_link(id,cursor,max,account)
        if path is None:
            return links
        else:
            if not isdir(f"{path}/{account}"):
                mkdir(f"{path}/{account}")
            count = 0
            for link in links:
                with open(f"{path}/{account}/{count}.jpg", 'wb') as handle:
                    response = requests.get(link, stream=True,timeout=120)
                    if not response.ok:
                        return None
                    for block in response.iter_content(1024):
                        if not block:
                            break
                        handle.write(block)
                count += 1
                print(f"[*] Picture downloaded {count}/{len(links)}",end="\r")
            return True



if __name__ == "__main__":
    bot = InstaBot("username","password")
    print(bot.get("account"))
