# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'seventhavenue'
# 全流程解析脚本

class SeventhavenueSpider(scrapy.Spider):
    name = website
    allowed_domains = ['seventhavenue.com']
    start_urls = ['https://www.seventhavenue.com/']

    headers={
        # 'Accept':'application/json, text/javascript, */*; q=0.01',
        # 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        # 'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        # 'Origin':'https://www.choies.com',
        # 'Referer':'https://www.choies.com/coats-jackets-c-45',
        'Accept-Language':'zh-CN,zh;q=0.9',
        'Connection':'keep-alive',
        'Pragma':'no-cache',
        'Cache-Control':'no-cache',
        'sec-ch-ua':'" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'Accept':'application/json, text/javascript, */*; q=0.01',
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With':'XMLHttpRequest',
        'sec-ch-ua-mobile':'?0',
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
    }

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
        super(SeventhavenueSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "shouyue")

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

    # def start_requests(self):
    #     url_list = [
    #
    #
    #     ]
    #     for url in url_list:
    #         print(url)
    #         yield scrapy.Request(
    #             url=url,
    #         )

        #url = "http://seventhavenue.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//ul[@class='level-3']/li/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                headers=self.headers,
                dont_filter=True,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='product-tile  standard-product']/div[@class='product-name']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        print('商品url列表：'+url_list)
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                headers=self.headers,
                dont_filter=True,
            )
        next_page_url = response.xpath('//div[@class="pagination"]/li[2]/a/@href').get()
        if next_page_url:
            yield scrapy.Request(url=next_page_url, callback=self.parse_list, headers=self.headers,dont_filter=True,)



    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//div[@class='product-price']/div[@class='price-standard']/span//text()").get()
        if original_price:
            original_price=original_price.split("$")[1]
        current_price = response.xpath("/div[@class='product-price']/span[@class='selected-price-sales ']/span//text()").get()
        if current_price:
            current_price=current_price.split("$")[1]
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        items["brand"] = 'Seventh Avenue'
        items["name"] = response.xpath("//h1[@class='product-name']/text()").get()

        attributes = list()

        items["attributes"] = attributes

        about = response.xpath("//div[@class='product-info']//div[@class='tab-info']//li/text()").getall()
        items["about"] = ''.join(about)
        items["description"] = response.xpath("//div[@class='product-info']//div[@class='tab-info']/text()").get()
        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = website
        images_list = response.xpath("//div[@class='product-primary-image']//a/@href").getall()
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//ol[@class='breadcrumb']/li/text()").getall()
        strr = '/'
        breadcrumb_list = strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list

        color_list=[]
        label_list = response.xpath("//div[@class='attribute']/div[2]/ul[@class='swatches color']/li")
        for label in label_list:
            key = label.xpath("//div[@class='attribute']/div[@class='lable']/text()").get().strip().replace(':', '').lower()
            values = label.xpath("./a/img/@alt")
            if 'color' in key:
                color_list = [{'color_img': v.xpath('./@src').get(),'value': v} for v in values]
                #键值对定位

        sku_list = list()
        #sku_url=response.xpath("//ul[@class='swatches color']//li/a/@href").getall()
        for color in color_list:
            sku_item = SkuItem()
            sku_item["original_price"] = items["original_price"]
            sku_item["current_price"] = items["current_price"]
            #sku_item["inventory"] = sku["inventory"]
            #sku_item["sku"] = sku["sku"]
            imgs = list()
            sku_item["imgs"] = imgs
            sku_item["url"] = response.url
            #sku_item["sku"] = sku
            attributes = SkuAttributesItem()
            attributes["colour"] = color["value"]
            attributes["colour_img"]=color["color_img"]
            #attributes["size"] = sku["size"]
            other = dict()
            attributes["other"] = other
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

        print(items)
        # yield items
