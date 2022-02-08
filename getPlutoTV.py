#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests

def ordered_set(in_list):
    out_list = []
    added = set()
    for val in in_list:
        if not val in added:
            out_list.append(val)
            added.add(val)
    return out_list
    
content = ""
url = f"http://api.pluto.tv/v2/channels"
r = requests.get(url)

data = r.json()

ch_list = []


i = 0
for ch in data:
    ch_dict = {
      "id": 0,
      "group": "",
      "name": "",
      "url": ""
    }
    name = ch['name'].replace('Pluto TV ', '')
    deviceId = ch['_id']
    group = ch['category']
    url = f'https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/{deviceId}/master.m3u8?deviceId=channel&deviceModel=web&deviceVersion=1.0&appVersion=1.0&deviceType=rokuChannel&deviceMake=rokuChannel&deviceDNT=1&advertisingId=channel&embedPartner=rokuChannel&appName=rokuchannel&is_lat=1&bmodel=bm1&content=channel&platform=web&tags=ROKU_CONTENT_TAGS&coppa=false&content_type=livefeed&rdid=channel&genre=ROKU_ADS_CONTENT_GENRE&content_rating=ROKU_ADS_CONTENT_RATING&studio_id=viacom&channel_id=channel'
    
    ch_dict["id"] = i
    ch_dict['group']=(group) 
    ch_dict['name']=(name)
    ch_dict['url']=(url)
    
    ch_list.append(ch_dict)
    i += 1

    
with open("pluto.txt", 'w') as f:
    for ch in ch_list:
        f.write(f'{ch["name"]},{ch["url"]}\n')
