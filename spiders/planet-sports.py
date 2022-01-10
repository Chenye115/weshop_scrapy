# -*- coding: utf-8 -*-
import re
import time
import json
import scrapy
from hashlib import md5
from copy import deepcopy
from overseaSpider.util.utils import isLinux

from overseaSpider.items import ShopItem, SkuItem, SkuAttributesItem
from overseaSpider.util.item_check import check_item
from overseaSpider.util.scriptdetection import detection_main

website = 'planet-sports'

class OverseaSpider(scrapy.Spider):
    name = website
    # start_urls = ['http://acnestudios.com/']


    @classmethod
    def update_settings(cls, settings):
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["HTTPCACHE_ENABLED"] = True
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(OverseaSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "文澜")

    is_debug = True
    custom_debug_settings = {
        # 'CLOSESPIDER_ITEMCOUNT': 5,  # 检测个数
        'MONGODB_COLLECTION': website,
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'DEBUG',
        'COOKIES_ENABLED': False,
        # 'HTTPCACHE_EXPIRATION_SECS': 14 * 24 * 60 * 60, # 秒
        'DOWNLOADER_MIDDLEWARES': {
            #'overseaSpider.middlewares.PhantomjsUpdateCookieMiddleware': 543,
            #'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },

    }

    def filter_text(self, input_text):
        input_text = re.sub(r'[\t\n\r\f\v]', ' ', input_text)
        input_text = re.sub(r'<.*?>', ' ', input_text)
        filter_list = [u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000-', u'\u200a',
                       u'\u2028', u'\u2029', u'\u202f', u'\u205f', u'\u3000', u'\xA0', u'\u180E',
                       u'\u200A', u'\u202F', u'\u205F', '\r\n\r\n', '/', '**', '>>', '\\n\\t\\t', ', ', '\\n        ',
                       '\\n\\t  ','&#x27;','`','&lt;','p&gt;','amp;','b&gt;','&gt;', 'br ']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text

    def start_requests(self):
        url = 'https://www.planet-sports.de/marken/alle/'
        yield scrapy.Request(
            url=url,
        )

    def parse(self, response):
        """主页"""
        url_list = response.xpath('//ul[@class="all-brands-alphabet"]/li//div[@class="brands-marketshops"]//a/@href').getall()
        for url in url_list:
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )


    def parse_list(self, response):
        """商品列表页"""
        detail_url_list = response.xpath('//ul[@class="products-grid clearfix"]/li//div[@class="carousel"]/div/a/@href').getall()
        for detail_url in detail_url_list:
            # print("详情页url:"+detail_url)
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
            )


        next_page_url = response.xpath('//link[@rel="next"]/@href').get()
        if next_page_url and detail_url_list:
            # print("下一页:"+next_page_url)
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_list,
            )

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        brand = response.xpath('//div[@class="productview__brand-image"]/a/@title').get()
        items["brand"] = brand
        name = response.xpath('//strong[@class="productview__name"]/text()').get()
        name = self.filter_text(name)
        items["name"] = name

        original_price = response.xpath('//p[@class="old-price"]/span[@class="price"]/text()').get()
        current_price = response.xpath('//p[@class="special-price"]/span[@class="price"]/text()').get()
        current_price_2 = response.xpath('//span[@class="regular-price"]/span/text()').get()
        if original_price:
            current_price = self.filter_text(current_price).replace("€","").replace(",","")
            original_price = self.filter_text(original_price).replace("€","").replace(",","")
        else:
            current_price = self.filter_text(current_price_2).replace("€","").replace(",","")
            original_price = current_price

        detail_cat = response.xpath('//div[@id="breadcrumb-wrapper"]//ul[@class="clearfix"]/li//a/@title').getall()
        s1 = '/'
        detail_cat = s1.join(detail_cat)
        items["detail_cat"] = detail_cat
        items["cat"] = detail_cat.split('/')[-1]

        json_str = re.findall('"resources":(.*)}',response.text)
        images_list = []
        images_one = response.xpath('//div[@class="easyzoom zoom"]/div/@data-link').get()
        if json_str:
            images_id_list = []
            img_data = json.loads(json_str[0])
            img_len = len(img_data)

            for k in range(0,img_len):
                img_id = img_data[k]["public_id"]
                images_id_list.append(img_id)

            for img_id in images_id_list:
                img_head = images_one.split('/planetsports')[0]
                img_last = images_one.split('/')[-1]
                img_new = img_head + '/' + img_id + '/' + img_last
                images_list.append(img_new)


        else:
            images_list.append(images_one)


        items["images"] = images_list

        items["url"] = response.url
        items["original_price"] = str(original_price)
        items["current_price"] = str(current_price)
        items["source"] = website

        description = response.xpath('//div[@class="description_features"]/ul/li/text()').get()
        if description:
            items["description"] = self.filter_text(description)
        else:
            items["description"] = ""

        sku_list = list()
        color = response.xpath('//span[@class="scp-color selected"]/span/text()').get()

        size_str = re.findall('Config\((.*)\);',response.text)
        size_list = []
        if size_str:
            size_data = json.loads(size_str[0])
            size_len = len(size_data["attributes"]["248"]["options"])
            for k in range(0, size_len):
                size_instock = size_data["attributes"]["248"]["options"][k]["products"]
                if size_instock:
                    size_one = size_data["attributes"]["248"]["options"][k]["label"]
                    if not 'Size' in size_one:
                        size_list.append(size_one)


        if size_list:
            for size in size_list:
                sku_item = SkuItem()
                sku_item["original_price"] = original_price
                sku_item["current_price"] = current_price
                sku_item["url"] = response.url
                sku_item["imgs"] = []

                attributes = SkuAttributesItem()
                if color:
                    color = self.filter_text(color)
                    attributes["colour"] = color
                attributes["size"] = size
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
        # print(items)
        yield items
        # check_item(items)
        # detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True,
        #                skulist_attributes=True)


