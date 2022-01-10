# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem
from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util.utils import isLinux

website = 'generalpants'

class GeneralpantsSpider(scrapy.Spider):
    name = website
    allowed_domains = ['generalpants.com']
    start_urls = ['https://generalpants.com/us/']
    headers = {'accept': 'application/json, text/plain, */*'}

    @classmethod
    def update_settings(cls, settings):
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug',
                                                                                False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(GeneralpantsSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "方尘")

    is_debug = True
    custom_debug_settings = {
        'MONGODB_COLLECTION': website,
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'DEBUG',
        'COOKIES_ENABLED': True,
        # 'HTTPCACHE_EXPIRATION_SECS': 14 * 24 * 60 * 60, # 秒
        'DOWNLOADER_MIDDLEWARES': {
            # 'overseaSpider.middlewares.PhantomjsUpdateCookieMiddleware': 543,
            # 'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },
    }

    def filter_html_label(self, text):  # 洗description标签函数
        label_pattern = [r'(<!--[\s\S]*?-->)', r'<script>.*?</script>', r'<style>.*?</style>', r'<[^>]+>']
        for pattern in label_pattern:
            labels = re.findall(pattern, text, re.S)
            for label in labels:
                text = text.replace(label, '')
        text = text.replace('\n', '').replace('\r', '').replace('\t', '').replace('  ', '').strip()
        return text

    def filter_text(self, input_text):
        filter_list = [u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000-', u'\u200a',
                       u'\u2028', u'\u2029', u'\u202f', u'\u205f', u'\u3000', u'\xA0', u'\u180E',
                       u'\u200A', u'\u202F', u'\u205F']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text

    def parse(self, response):
        # 获取全部分类
        category_urls = response.xpath("//ul[@class='sub-links']/li/a[@class='cms link ']/@href").getall()
        for category_url in category_urls:
            url = 'https://generalpants.com' + category_url + '?page=0'
            url = url.replace('/us/', '/us/category/')
            yield scrapy.Request(
                url=url,
                headers=self.headers,
                callback=self.parse_list
            )

    def parse_list(self, response):
        """商品列表页"""
        json_data = json.loads(response.text)
        cat_list = ['HOME'] + [breadcrumb['name'] for breadcrumb in json_data['breadcrumbData']]
        products = json_data['results']
        for product in products:
            yield scrapy.Request(
                url='https://generalpants.com/us/product/{}'.format(product['defaultColorProductCode']),
                callback=self.parse_detail,
                headers=self.headers,
                meta={'cat_list': cat_list}
            )
        if products:
            page = int(re.search(r'page=(\d+)', response.url).group(1)) + 1
            url = re.sub(r'\?page=\d+', r'?page={}'.format(page), response.url)
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse_list)

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        json_data = json.loads(response.text)
        items["url"] = 'https://generalpants.com/us' + json_data['url']

        items["current_price"] = json_data['price']['formattedValue']
        items["original_price"] = items["current_price"]

        items["name"] = json_data['name']

        cat_list = response.meta.get('cat_list')
        items["detail_cat"] = '/'.join(cat_list)
        items["cat"] = cat_list[-1]

        items["description"] = self.filter_text(self.filter_html_label(json_data['description']))
        items["source"] = website

        items["brand"] = json_data['brand']

        items["images"] = [image['url'] for image in json_data['images'] if image['format'] == 'productZoom']
        items["images"] = [image if image.startswith('http') else 'https:' + image for image in items['images']]

        items["sku_list"] = self.parse_sku(json_data)

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
        # detection_main(items=items, website=website, num=20, skulist=True, skulist_attributes=True)
        print(items)
        yield items

    def parse_sku(self, json_data):
        variants = json_data['variantOptions']
        sku_list = list()
        for variant in variants:
            sku_info = SkuItem()
            sku_attr = SkuAttributesItem()
            for option in variant['variantOptionQualifiers']:
                if not option.get('name'):
                    continue
                label = option['name'].lower()
                label_value = option['value']
                if 'colour' in label and label_value:
                    sku_attr["colour"] = label_value
                elif 'size' in label and label_value:
                    sku_attr["size"] = label_value
                elif label and label_value:
                    sku_attr["other"] = {label: label_value}
            sku_info["current_price"] = variant['priceData']['formattedValue']
            sku_info["original_price"] = sku_info["current_price"]
            sku_info["attributes"] = sku_attr
            sku_list.append(sku_info)
        return sku_list
