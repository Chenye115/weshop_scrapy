# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from overseaSpider.util.utils import isLinux, filter_text
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'desenio'

class DesenioSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['desenio.com.au']
    # start_urls = ['http://desenio.com.au/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["HTTPCACHE_ENABLED"] = True
            custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(DesenioSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "泽塔")

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
            "https://desenio.com.au/shop"
        ]
        offset = '0'
        query = "filter_params={}&funk=get_filter&Visn=Lista3&Sort=Egen&is_start=1&is_search=0&outlet=0&limits=36&category_id=22&offset=0"
        for url in url_list:
            yield scrapy.Request(
                url=url,
                method="POST",
                body=query,
                meta={"offset": offset}
            )

    def parse(self, response):
        offset = response.meta.get("offset")
        url_list = response.xpath('//div[@class="image text-center relative v-middle-outer"]/a/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        if url_list:
            for url in url_list:
                print(url)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )

            offset = str(int(offset) + 36)
            query = f"filter_params=&funk=get_filter&Visn=Lista3&Sort=Egen&is_start=1&is_search=0&outlet=0&limits=36&category_id=22&offset={offset}"
            next_page_url = "https://desenio.com.au/shop"
            yield scrapy.Request(
                url=next_page_url,
                method="POST",
                body=query,
                meta={"offset": offset},
                callback=self.parse,
            )


    def parse_detail(self, response):
        """详情页"""
        is_stock = response.xpath("//span[@id='inStock']/@class").get()
        if "reen-color" not in is_stock:
            pass
        else:
            items = ShopItem()
            items["url"] = response.url
            json_str = response.xpath('//script[@type="application/ld+json"]/text()').getall()[1]
            json_data = json.loads(json_str)
            # print(json_data)
            # re.findall("", response.text)[0]
            original_price = response.xpath("//span[@class='lato currentPrice']/text()").get()
            current_price = response.xpath("//span[@class='lato currentPrice']/text()").get()
            items["original_price"] = "$" + str(original_price) if original_price else "$" + str(current_price)
            items["current_price"] = "$" + str(current_price) if current_price else "$" + str(original_price)
            items["brand"] = json_data["brand"]["name"] if "brand" in json_data else ""
            items["name"] = response.xpath('//div[@id="tagAndTitle"]/h1/text()').get()
            items["description"] = json_data["description"]
            items["source"] = website
            image = json_data["image"].split("?")[0]
            images_list = [image]
            items["images"] = images_list

            Breadcrumb_list = response.xpath("//div[@id='breadcrumbs']/a/text()").getall()
            Breadcrumb_list = [filter_text(i) for i in Breadcrumb_list]
            items["cat"] = Breadcrumb_list[-1]
            items["detail_cat"] = "/".join(Breadcrumb_list)

            #attributes = list()
            #items["attributes"] = attributes
            #items["about"] = response.xpath("").get()
            #items["care"] = response.xpath("").get()
            #items["sales"] = response.xpath("").get()

            sku_list = list()

            offers_list = json_data["offers"]
            for sku in offers_list:
                sku_item = SkuItem()
                sku_item["original_price"] = "$" + sku["price"]
                sku_item["current_price"] = "$" + sku["price"]
                sku_item["url"] = sku["url"]
                attributes = SkuAttributesItem()
                attributes["size"] = sku["name"]
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
            yield items
