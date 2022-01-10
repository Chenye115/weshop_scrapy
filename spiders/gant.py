# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy
import requests
from hashlib import md5
from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util import item_check
from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'gant'

class GantSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['gant.co']
    # start_urls = ['http://gant.co/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 10
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            # custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(GantSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "汀幡")

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
    def filter_text(self, input_text):
        input_text = re.sub(r'[\t\n\r\f\v]', ' ', input_text)
        input_text = re.sub(r'<.*?>', ' ', input_text)
        filter_list = [u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000-', u'\u200a',
                       u'\u2028', u'\u2029', u'\u202f', u'\u205f', u'\u3000', u'\xA0', u'\u180E',
                       u'\u200A', u'\u202F', u'\u205F']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text
    def start_requests(self):
        url_list = [
            'https://www.gant.co.uk/menswear?page[number]=1&page[size]=60',
            'https://www.gant.co.uk/womenswear?page[number]=1&page[size]=60'
        ]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://gant.co/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath('//a[@class="c-product-tile in--view"]/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )
        if url_list:
            prefix = response.url.split('page[number]=')[0]
            surfix = response.url.split('page[number]=')[1].split('&page[size]=')[0]
            surfix = int(surfix) + 1
            next_page_url = prefix + 'page[number]=' + str(surfix)+'&page[size]=60'
            if next_page_url:
                # print("下一页:" + next_page_url)
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse,
                )


    # def parse_list(self, response):
    #     """列表页"""
    #     url_list = response.xpath("").getall()
    #     url_list = [response.urljoin(url) for url in url_list]
    #     for url in url_list:
    #         print(url)
    #         yield scrapy.Request(
    #             url=url,
    #             callback=self.parse_detail,
    #         )

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

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        current_price = response.xpath('//h3[@data-cy="price-pdp"]/text()').get()
        current_price = self.filter_text(current_price)
        original_price =current_price
        items["original_price"] = original_price
        items["current_price"] =current_price
        items["brand"] = website
        name1 =response.xpath('//h4[@data-cy="heading-pdp"]//text()').getall()
        name =''
        for i in name1:
            a =self.filter_text(i)
            if a!='':
                name+=a
        items["name"] = name
        # attributes = list()
        # items["attributes"] = attributes
        # items["about"] = response.xpath("").get()
        des = response.xpath('//div[@data-cy="plp-content-accord-description"]/div//text()').getall()
        description = ''
        for i in des:
            a = self.filter_text(i)
            if a != '':
                description += a
        items["description"] = description
        # items["care"] = response.xpath("").get()
        # items["sales"] = response.xpath("").get()
        items["source"] = website
        images_list1 = response.xpath('//li[@class="slide___3-Nqo slideHorizontal___1NzNV carousel__slide carousel__slide--visible"]//img/@data-lowsrc').getall()
        images_list = []
        for i in images_list1:
            a = i.replace('q_10','q_80').replace('w_20','w_3500')
            images_list.append(a)
        items["images"] = images_list

        Breadcrumb_list = response.xpath('//nav[@aria-label="Breadcrumb"]/ol/li/a/text()').getall()
        items["cat"] = Breadcrumb_list[len(Breadcrumb_list)-1]
        det_cat = ''
        for i in Breadcrumb_list:
            det_cat = det_cat + i + '/'
        det_cat = det_cat + name
        items["detail_cat"] = det_cat

        sku_list = list()
        scriptall =response.xpath('//script').getall()
        id_sc =''
        id =''
        for i in scriptall:
            if "window['REDUX_STATE_SHOP-gant-react-product-app']" in i:
                id_sc = i
                id = id_sc.split('productReference":"')[1].split('","')[0]
        url1 = 'https://www.gant.co.uk/api/v3/product/'+id+'/sizes/gb/en_GB'
        headers = {
            'authority': 'www.gant.co.uk',
            'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
            'accept': 'application/json, text/plain, */*',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.gant.co.uk/mens-jackets/green-cotton-parka/59075',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': 'OptanonAlertBoxClosed=2021-09-27T05:27:00.796Z; _ga=GA1.3.837621471.1632720419; IR_gbd=gant.co.uk; pnctest=1; _gcl_au=1.1.1447460719.1632720430; _cs_c=1; _hjid=e05591d3-33b1-45fa-b29e-3520c79e8f80; _fbp=fb.2.1632720433650.397513242; _scid=29bf0cd9-730d-44b8-973d-16379d74fe18; _sctr=1|1633708800000; _gid=GA1.3.2126891353.1634034551; _hjAbsoluteSessionInProgress=0; _gaexp=GAX1.3.8K9qyZZSRyiRz5xwnRR2cQ.19004.1; _hjIncludedInPageviewSample=1; _cs_mk=0.7651793251319214_1634091838336; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Oct+13+2021+10%3A30%3A29+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=6.21.0&isIABGlobal=false&hosts=&consentId=db87ce8d-af38-402f-9af9-9dbd78b8d2c9&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1%2CC0003%3A1&geolocation=%3B&AwaitingReconsent=false; IR_7992=1634092229822%7C0%7C1634091840663%7C%7C; _uetsid=3e03e3a02b4711eca9799f83d2853d46; _uetvid=8c12da201f5311ec8af5b14e6aee7f46; _cs_id=4c4d9c62-14dd-a692-d0e5-3ea5ca7afc44.1632720430.5.1634092230.1634091420.1.1666884430654; _cs_s=3.1.0.1634094030315; preferredSizes={%22size%22:%22S%22%2C%22value%22:%227325706280192%22}'
        }
        sku_res =requests.get(url1,headers=headers)
        sku_res =sku_res.json()
        sku_size1 = sku_res.get('data').get('attributes').get('sizes')
        sku_size = []
        for i in sku_size1:
            if i.get('stock')>1:
                sku_size.append(i.get('sizeName'))
        if sku_size:
            for sku in sku_size:
                sku_item = SkuItem()
                sku_item["original_price"] = original_price
                sku_item["current_price"] = current_price
                sku_item["inventory"] = None
                sku_item["imgs"] = []
                sku_item["url"] = response.url
                sku_item["sku"] = sku
                attributes = SkuAttributesItem()
                attributes["size"] = sku
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


        detection_main(
            items=items,
            website=website,
            num=self.settings["CLOSESPIDER_ITEMCOUNT"],
            skulist=True,
            skulist_attributes=True)
        print(items)
        item_check.check_item(items)
        yield items