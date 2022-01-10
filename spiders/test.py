import requests


headers = {
    "authority": "www.rugsusa.com",
    "pragma": "no-cache",
    "cache-control": "no-cache",
    "sec-ch-ua": "^\\^",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "^\\^Windows^^",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-language": "zh-CN,zh;q=0.9"
}
cookies = {
    "cf-currency": "USD",
    "cf-device": "desktop",
    "cf-postalcode": "10001",
    "__cf_bm": "u_E.relSZxm1.axk0vs6.ilJHc1YGQV3kL_Msxz372w-1641441831-0-AWIWpchssvV9B9RxFRFaMj0z+TQsJdcTyg+GzAa0jgPn6vmVkpPVx8Nh80ani/EBVQ5Z3XRgmklabe/63hShyKQ=",
    "visited": "yes",
    "JSESSIONID": "0495845A932FCB3C59FCCD9293086A4B.jvm3",
    "cartList": "",
    "_gcl_au": "1.1.1721753435.1641441836",
    "user_cn": "us",
    "_uetsid": "ab1738a06ea511eca4b1e73e968cd776",
    "_uetvid": "ab1764a06ea511ec995a23db59402ea3",
    "_ga": "GA1.2.1198637501.1641441836",
    "_gid": "GA1.2.355363318.1641441836",
    "_dc_gtm_UA-1889015-1": "1",
    "IR_gbd": "rugsusa.com",
    "IR_9280": "1641441836529^%^7C0^%^7C1641441836529^%^7C^%^7C",
    "_svsid": "6772888ec4058f4825fd1b59bd5fc2f5",
    "_fbp": "fb.1.1641441836726.394150874",
    "_gaexp": "GAX1.2.MppUbhWQREuc_ir4PqqAGg.19068.0^!4Ewb9cHXTOmNQRWYeEhFHQ.19090.1",
    "_tq_id.TV-18907281-1.59e4": "2fcbd1b7af09f4d0.1641441837.0.1641441837..",
    "_pin_unauth": "dWlkPU0yUmtOMkV3WVRJdE56WTJNeTAwTXpObExUZzFaREV0WW1KbE9ERXpOMk0yWmpRMQ",
    "_hjSessionUser_1666591": "eyJpZCI6ImZmNTgwODEwLTk4OTEtNWI2MS05Zjk1LWViYzA5N2I0NzdlNiIsImNyZWF0ZWQiOjE2NDE0NDE4MzgxOTQsImV4aXN0aW5nIjpmYWxzZX0=",
    "_hjFirstSeen": "1",
    "_hjSession_1666591": "eyJpZCI6IjRkYmY4MGU4LWY2Y2UtNDQxYi05MDgzLWMyZTZlZDRhZDMyNiIsImNyZWF0ZWQiOjE2NDE0NDE4MzgyMDJ9",
    "_hjIncludedInSessionSample": "0",
    "_hjAbsoluteSessionInProgress": "1",
    "_dy_ses_load_seq": "72461^%^3A1641441838395",
    "_dy_csc_ses": "t",
    "_dy_c_exps": "",
    "_dy_soct": "572999.1105933.1641441838*603626.1164482.1641441838*557513.1075548.1641441838",
    "__idcontext": "eyJjb29raWVJRCI6IjVXQVlDSjRQU0hQTE9XTlpZUVlENFk2Slk1QUNHNlhSS082RFJQVDQ0S0dRPT09PSIsImRldmljZUlEIjoiNVdBWUNKNFBTNzZaR0s0UTdVV0RXNFVMWUo2U0FWTzRMTDJHTE1UUjRUUUE9PT09IiwiaXYiOiJWUlVKWDNCN0g3NTI2R1lLQUhHR1lHTEVaQT09PT09PSIsInYiOjF9",
    "_dycnst": "dg",
    "_dyid": "4634204417635222283",
    "_dyfs": "1641441839201",
    "_dyjsession": "3a54082fdada6fc661a474dd6dd890b5",
    "dy_fs_page": "www.rugsusa.com",
    "_dy_lu_ses": "3a54082fdada6fc661a474dd6dd890b5^%^3A1641441839202",
    "_dycst": "dk.w.c.ws.",
    "_dy_geo": "US.NA.US_CA.US_CA_",
    "_dy_df_geo": "United^%^20States.California.",
    "_dy_toffset": "-1",
    "crl8.fpcuid": "a6001bb2-d757-4983-95fb-6915fd9d98e5",
    "bounceClientVisit3354v": "N4IgNgDiBcIBYBcEQM4FIDMBBNAmAYnvgO6kB0ATgK4DmKVKAhmQMYD2AtkSADQgUwQvECgCmNGAG0AugF8gA",
    "_li_dcdm_c": ".rugsusa.com",
    "_lc2_fpi": "59e23fac8034--01frprxjrnj068psngpyn0b9g0",
    "ConstructorioID_client_id": "c24bd9b1-978f-4442-93bf-6aef1e008a1d",
    "__attentive_id": "32438d52df734df6a0e6bcec3456cf8a",
    "__attentive_cco": "1641441841117",
    "__attentive_pv": "1",
    "__attentive_ss_referrer": "^\\^ORGANIC^^",
    "__attentive_dv": "1"
}
url = "https://www.rugsusa.com/"
response = requests.get(url, headers=headers, cookies=cookies)

print(response.text)
print(response)