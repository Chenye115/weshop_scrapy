# -*- coding: utf-8 -*-
import re
import html
import time
import json
import scrapy
from hashlib import md5
from copy import deepcopy
from overseaSpider.util.utils import isLinux

from overseaSpider.items import ShopItem, SkuItem, SkuAttributesItem
from overseaSpider.util.item_check import check_item
from overseaSpider.util.scriptdetection import detection_main

website = 'mashsf'

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
        # 'CLOSESPIDER_ITEMCOUNT': 3,  # 检测个数
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

    def filter_html_label(self,text):
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

    def start_requests(self):
        url_list = ["https://shop.mashsf.com/clothing/",
                    "https://shop.mashsf.com/components/",
                    "https://shop.mashsf.com/accessories/"]
        for url in url_list:
            cat = url.split('/')[-2]
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                meta={'cat': cat}
            )



    def parse_list(self, response):
        """商品列表页"""
        cat = response.meta['cat']
        detail_url_list = response.xpath('//li[@class="three column product product-tile check-variants "]/a/@href').getall()
        for detail_url in detail_url_list:
            # print("详情页url:"+detail_url)
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={'cat': cat}
            )

        next_page_url = response.xpath('//link[@rel="next"]/@href').get()
        if next_page_url and detail_url_list:
            # print("下一页:"+next_page_url)
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_list,
                meta={'cat': cat}
            )

    def parse_detail(self, response):
        """详情页"""
        instock = response.xpath('//a[@class=" soldout"]/text()').get()
        if not instock:
            items = ShopItem()
            items["brand"] = ''
            name = response.xpath('//div[@class="six columns"]/h2/text()').get()
            name = self.filter_html_label(name)
            items["name"] = name

            price = response.xpath('//span[@id="price-field"]/strong/text()').get()
            price = self.filter_html_label(price)
            price = price.split('$')[-1]
            price = price.replace(',', '')
            original_price = price
            current_price = price

            cat = response.meta['cat']
            items["detail_cat"] = cat
            items["cat"] = cat

            images_list = response.xpath('//div[@id="thumbs"]/div/a/@href').getall()
            if not images_list:
                images_list = response.xpath('//div[@id="product-image"]/img/@src').getall()
            items["images"] = images_list

            items["url"] = response.url
            items["original_price"] = str(original_price)
            items["current_price"] = str(current_price)
            items["source"] = 'mashsf.com'

            description = response.xpath('//div[@id="desc"]//p//text()').getall()
            description = "".join(description)
            if description:
                items["description"] = self.filter_html_label(description)
            else:
                items["description"] = ""

            sku_list = list()
            size_list_all = response.xpath('//div[@class="col-md-12 variants"]/a[contains(@class,"variant-selector")]/text()').getall()
            size_list = []
            for key in size_list_all:
                key = self.filter_html_label(key)
                size_list.append(key)

            if size_list:
                for size in size_list:
                    sku_item = SkuItem()
                    sku_item["original_price"] = original_price
                    sku_item["current_price"] = current_price
                    sku_item["url"] = response.url
                    sku_item["imgs"] = []

                    attributes = SkuAttributesItem()
                    other = {'color or size': size}
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
            #yield items
            # check_item(items)
            # detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True,
            #                skulist_attributes=True)

