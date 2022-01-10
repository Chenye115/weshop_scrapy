# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'roomstogo'

class RoomstogoSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['roomstogo.com']
    # start_urls = ['http://roomstogo.com/']

    @classmethod
    def update_settings(cls, settings):
        settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')

    def __init__(self, **kwargs):
        super(RoomstogoSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "凯棋")

    is_debug = True
    custom_debug_settings = {
        # 'MONGODB_SERVER': '127.0.0.1',
        # 'MONGODB_DB': 'fashionspider',
        # 'MONGODB_COLLECTION': 'fashions_pider',
        'MONGODB_COLLECTION': 'roomstogo',
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 0,
        'LOG_LEVEL': 'DEBUG',
        'COOKIES_ENABLED': False,
        'HTTPCACHE_ALWAYS_STORE': False,
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 7 * 24 * 60 * 60, # 秒
        # 'HTTPCACHE_DIR': "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache",
        'DOWNLOADER_MIDDLEWARES': {
            #'overseaSpider.middlewares.OverseaspiderDownloaderMiddleware': 543,
            #'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },
        # 'HTTPCACHE_POLICY': 'scrapy.extensions.httpcache.DummyPolicy',
        # 'HTTPCACHE_POLICY': 'scrapy.extensions.httpcache.RFC2616Policy',
        'HTTPCACHE_POLICY': 'overseaSpider.middlewares.DummyPolicy',
    }

    def start_requests(self):
        url = "https://www.roomstogo.com/"
        yield scrapy.Request(
            url=url,
        )

    def parse(self, response):
        url_list = response.xpath("//div[@class='link-list']//li/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            yield scrapy.Request(
                url=url,
                callback=self.parse_post,
            )

    def parse_post(self, response):
        ruleContexts = re.findall('<div data-cid="(.*?)"><div class="search-query"', response.text)[0]
        sub_category = response.xpath("//a[@aria-current='page']/@gtm-label").get()
        # print(ruleContexts)
        # print(sub_category)
        # ruleContexts = "SQ5bd3d2bd513fa18f7e3f9ae2f5872beb"
        # filters = '("sub_category":"Living Room Sets")'
        url = "https://fuin3o4lcf-dsn.algolia.net/1/indexes/*/queries?x-algolia-application-id=FUIN3O4LCF&x-algolia-api-key=20c90811a3555a6d37e4ee66e8934105"
        filters = f'("sub_category":"{sub_category}")'
        page = '1'
        payload = {
            "requests":[
                {
                    "indexName": "OOM-prod",
                    "params":f'query=&hitsPerPage=20&ruleContexts=["{ruleContexts}"]&filters={filters}&facets=["age","size","brand","decor","style","theme","gender","catalog","comfort","feature","inStock","is_room","category","closeout","material","movement","collection","technology","ad_position","is_featured","piece count","size_family","color_family","on_promotion","sub_category","delivery_type","finish_family","free_shipping","strikethrough","promotion_name","zone_0_on_sale","material_family","promotionOfferName","zone_0_sale_price_price_range"]&tagFilters=&page={page}'
                }
            ]
        }

        yield scrapy.Request(
            url=url,
            body=json.dumps(payload),
            method="POST",
            callback=self.parse_list,
            meta={"payload": payload}
        )

    def parse_list(self, response):
        """列表页"""
        payload = response.meta["payload"]
        # print(payload)
        json_data = json.loads(response.text)
        hits_list = json_data["results"][0]["hits"]
        if hits_list:
            for hits in hits_list:
                route = hits["route"]
                # print(route)
                url = "https://www.roomstogo.com/furniture/product" + route
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )

            params = payload["requests"][0]["params"]
            split_str = 'page='
            base_url = params.split(split_str)[0]
            page_num = int(params.split(split_str)[1]) + 1
            payload["requests"][0]["params"] = base_url + split_str + str(page_num)
            url = "https://fuin3o4lcf-dsn.algolia.net/1/indexes/*/queries?x-algolia-application-id=FUIN3O4LCF&x-algolia-api-key=20c90811a3555a6d37e4ee66e8934105"
            yield scrapy.Request(
                url=url,
                body=json.dumps(payload),
                method="POST",
                callback=self.parse_list,
                meta={"payload": payload}
            )

        else:
            print("当前页码无数据!")

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        json_data_str = response.xpath("//script[@type='application/ld+json']/text()").get()
        json_data = json.loads(json_data_str)
        # print(json_data)
        price = json_data["offers"]["price"]
        original_price = price
        current_price = price
        items["original_price"] = "$"+str(original_price) if original_price else "$"+str(current_price)
        items["current_price"] = "$"+str(current_price) if current_price else "$"+str(original_price)
        items["name"] = json_data["name"]
        # items["brand"] = response.xpath("").get()
        # # items["about"] = response.xpath("").get()
        items["description"] = json_data["description"]
        items["source"] = website
        image = json_data["image"]
        images_list = image.split(",")
        images_list = [i for i in images_list if i]
        # images_list = response.xpath("//ul[@aria-live='polite']/li/div/img/@src").getall()
        # images_list_new = list()
        # for i in images_list:
        #     if i not in images_list_new:
        #         images_list_new.append(i)
        items["images"] = images_list


        Breadcrumb_list = response.xpath("//div[@class='jss8']//section[@aria-label='Breadcrumb']/ul/li//text()").getall()
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = "/".join(Breadcrumb_list)

        sku_list = list()
        #for sku in original_sku_list:
        #     sku_item = SkuItem()
        #     sku_item["original_price"] = original_price
        #     sku_item["current_price"] = current_price
        #     sku_item["url"] = response.urljoin(sku["variantUrl"])
        #     sku_item["sku"] = sku["ids"][0]

        #     attributes = SkuAttributesItem()
        #     attributes["colour"] = sku["name"]
        #     sku_item["attributes"] = attributes
        #     sku_list.append(sku_item)

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

        # print(items)
        yield items
