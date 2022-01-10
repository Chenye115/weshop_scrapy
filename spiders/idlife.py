# -*- coding: utf-8 -*-
import html
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from overseaSpider.util.item_check import check_item
from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'idlife'
# 全流程解析脚本

class IdlifeSpider(scrapy.Spider):
    headers = {
    "authority": "idlife.com",
    "pragma": "no-cache",
    "cache-control": "no-cache",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\", \"Google Chrome\";v=\"96\"",
    "sec-ch-ua-mobile": "?0",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "content-type": "application/json; charset=UTF-8",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "x-requested-with": "XMLHttpRequest",
    "__requestverificationtoken": "ZMvIy0_EHDmfEVL1Tl486ZYcAl0Ua7J-NIRvAZn8_igE25_RbJz9zLo4oD51oRITrjoXcc6G0Yqt25HY8ftw-3zFkR01",
    "sec-ch-ua-platform": "\"Windows\"",
    "origin": "https://idlife.com",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://idlife.com/shop/products/promos/fitmas",
    "accept-language": "zh-CN,zh;q=0.9"
    }
    cookies = {
    "IDLife_LastWebAlias": "corp",
    "IDLifeSelectedCountry": "US",
    "IDLifeSelectedLanguage": "en-US",
    "__RequestVerificationToken": "gm0O4J91oZRoXDUMbNLON9DowL-xanSeZgZSFM55tXgjnL1w8P5QHEoX3JC6neNU9dbNUKezs9NiXPxlPgXjkJUDTTQ1",
    "_ga": "GA1.2.327269955.1640072029",
    "_gid": "GA1.2.269934413.1640072029",
    "_fbp": "fb.1.1640072029197.1497504443",
    "IDLifeNoReferral": "true",
    "IDLife_CookiesAgreement": "true",
    "IDLifeReplicatedSiteShoppingPropertyBag": "5fcc3d94-279f-4f1a-9ac6-e42ecedcc469",
    "IDLifeReplicatedSiteShoppingCart": "34e0c47c-05da-49d3-8bb7-524343137a51",
    "_gat": "1"
    }
    name = website
    allowed_domains = ['idlife.com']
    start_urls = ['https://idlife.com/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["HTTPCACHE_ENABLED"] = True
            # custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(IdlifeSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "守约")

    is_debug = True
    custom_debug_settings = {
        'MONGODB_COLLECTION': website,
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'DEBUG',
        'COOKIES_ENABLED': False,
        'HTTPCACHE_ENABLED': True,
         # 'HTTPCACHE_EXPIRATION_SECS': 7 * 24 * 60 * 60, # 秒
        'DOWNLOADER_MIDDLEWARES': {
            #'overseaSpider.middlewares.PhantomjsUpdateCookieMiddleware': 543,
            #'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },
        'HTTPCACHE_POLICY': 'overseaSpider.middlewares.DummyPolicy',
    }

    def start_requests(self):
        url_list = [
            'https://idlife.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://idlife.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//li[@class='ml-1 hover-parent']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        print(len(url_list))
        for url in url_list:
            print('1111')
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.get_item_url,
            )

    def get_item_url(self,response):

        category_id=re.search(r'categoryID = (.*?),',response.text).group(1)
        if category_id:
            print(category_id)
            data = {
            "categoryID": category_id,
            "search": ""
                  }
            data = json.dumps(data)
            yield scrapy.FormRequest(
                url='https://idlife.com/shopping/getitemlist',
                #callback=self.parse_list,
                method='post',
                body=data,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_list
            )


    def parse_list(self, response):
        """列表页"""
        #print(response.text)
        url_dic=json.loads(response.text)
        #print('url_dic')
        #print(url_dic)
        items_list=url_dic['items']
        url_list=[]
        for item in items_list:
            url_list.append(item['ItemUrl'])

        print('url_list:')
        print(url_list)
        # url_list = response.xpath("//div[@id='itemList']/div/div/@href").getall()
        # url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            url='https://idlife.com/'+url
            print('2222')
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

        # response_url = parse.unquote(response.url)
        # split_str = ''
        # base_url = response_url.split(split_str)[0]
        # page_num = int(response_url.split(split_str)[1])+1
        # next_page_url = base_url + split_str + str(page_num)
        #next_page_url = response.xpath("").get()
        #if next_page_url:
        #   next_page_url = response.urljoin(next_page_url)
        #    print("下一页:"+next_page_url)
        #    yield scrapy.Request(
        #        url=next_page_url,
        #        callback=self.parse_list,
        #    )
    def filter_html_label(self, text):
        text = str(text)
        text = html.unescape(text)
        # 注释，js，css，html标签
        filter_rerule_list = [r'(<!--[\s\S]*?-->)', r'<script[\s\S]*?</script>', r'<style[\s\S]*?</style>', r'<[^>]+>']
        for filter_rerule in filter_rerule_list:
            html_labels = re.findall(filter_rerule, text)
            for h in html_labels:
                text = text.replace(h, ' ')
        filter_char_list = [
            u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000', u'\u200a', u'\u2028', u'\u2029', u'\u202f', u'\u205f',
            u'\u3000', u'\xA0', u'\u180E', u'\u200A', u'\u202F', u'\u205F', '\t', '\n', '\r', '\f', '\v',
        ]
        for f_char in filter_char_list:
            text = text.replace(f_char, '')
        text = re.sub(' +', ' ', text).strip()
        return text



    def filter_text(self, input_text):
        filter_list = [u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000-', u'\u200a',
                       u'\u2028', u'\u2029', u'\u202f', u'\u205f', u'\u3000', u'\xA0', u'\u180E',
                       u'\u200A', u'\u202F', u'\u205F']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//ul[@class='list-group list-group-flush']/li[2]/span[2]/text()").get()
        original_price=original_price.split("$")[-1]
        current_price = original_price
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        items["brand"] = 'ID Life'
        items["name"] = response.xpath("//ul[@class='list-group list-group-flush']/li[1]/p/text()").get()
        attributes = list()
        #items["attributes"] = attributes
        #items["about"] = response.xpath("").get()
        description= response.xpath("//ul[@class='list-group list-group-flush']/li[3]//text()").getall()
        description=''.join(description)
        description=self.filter_text(self.filter_html_label(description))
        items["description"] =description
        # items["care"] = response.xpath("").get()
        # items["sales"] = response.xpath("").get()

        items["source"] = 'idlife.com'

        images_list = response.xpath("//div[@class='preview-images d-inline-flex d-md-block']/div/div/img/@src|//div[@class='preview-images d-inline-flex d-md-block']/div/img/@src").getall()
        images=[]
        for n in range(len(images_list)):
            if 'data:' in images_list[n]:
                pass
            else:
                images_list[n]='https://idlife.com'+images_list[n]
                images.append(images_list[n])
        items["images"] = images

        Breadcrumb_list = response.xpath("//div[@class='breadcrumb-list']/a/text()").getall()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        breadcrumb_list=self.filter_text(self.filter_html_label(breadcrumb_list))
        items["cat"] =  self.filter_text(self.filter_html_label(Breadcrumb_list[-1]))
        items["detail_cat"] = breadcrumb_list

        label_list=response.xpath("//div[@class='col-md-12 d-inline-flex justify-content-center p-0']/div")
        taste_list=[]
        for label in label_list:
            color=label.xpath("./div/@style").get()
            color=color.split(":")[-1]
            taste_list.append({'color':color})





        sku_list = list()
        for sku in taste_list:
            sku_item = SkuItem()
            sku_item["original_price"] = items["original_price"]
            sku_item["current_price"] = items["current_price"]


            sku_item["url"] = response.url

            attributes = SkuAttributesItem()
            attributes["colour"] = sku["color"]


            sku_item["attributes"] = attributes
            sku_list.append(sku_item)

        items["sku_list"] = sku_list
        items["measurements"] = ["Weight: None", "Height: None", "Length: None", "Depth: None"]
        status_list = list()
        status_list.append(items["url"])
        status_list.append(items["original_price"])
        status_list.append(items["current_price"])
        status_list = [i for i in status_list if i]
        status = "-".join(status_list)
        items["id"] = md5(status.encode("utf8")).hexdigest()

        items["lastCrawlTime"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        items["created"] = int(time.time())
        items["updated"] = int(time.time())
        items['is_deleted'] = 0

        # check_item(items)
        # # print(items)
        yield items
        #
        # detection_main(
        #     items=items,
        #     website=website,
        #     num=10,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)

