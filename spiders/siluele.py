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

website = 'siluele'
# 全流程解析脚本

class SilueleSpider(scrapy.Spider):
    name = website
    allowed_domains = ['siluele.com']
    start_urls = ['https://www.siluele.com/']

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
        super(SilueleSpider, self).__init__(**kwargs)
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
            'https://www.siluele.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://siluele.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def filter_html_label(self, text):
        print('进入商品详情解析')
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

    def parse(self, response):
        url_list = response.xpath("//div[@id='pt_custommenu']/div/div/a/@href").getall()
        url_list.pop(0)
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='custom-products']/div/div//h2[@class='product-name']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
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
        next_page_url = response.xpath("//ul[@class='pagination']/li[@class='active']/following-sibling::li[1]/a/@href").get()
        if next_page_url:
           next_page_url = response.urljoin(next_page_url)
           print("下一页:"+next_page_url)
           yield scrapy.Request(
               url=next_page_url,
               callback=self.parse_list,
           )

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//ul[@class='list-unstyled price-product']/li/span[@class='old-price']/text()").get()
        current_price = response.xpath("//ul[@class='list-unstyled price-product']/li/span[@class='new-price']/text()").get()
        if original_price and current_price:
            print('sale')
            original_price=original_price.split("$")[-1]
            current_price=current_price.split("$")[-1]
            items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
            items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        else:
            price=response.xpath("//ul[@class='list-unstyled price-product']/li/span/text()").get()
            price=price.split("$")[-1]
            current_price=price
            original_price=price
            items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
            items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        items["brand"] = 'siluele'
        detail= response.xpath("//ul[@class='breadcrumb']/li/a/text()").getall()
        items["name"] =detail[-1]

        #attributes = list()
        #items["attributes"] = attributes
        about= response.xpath("//p[@class='short-des']/text()").get()
        items["about"] = self.filter_text(self.filter_html_label(about))

        des=response.xpath("//div[@id='tab-description']//text()").getall()
        description=''.join(des)
        description=self.filter_text(self.filter_html_label(description))
        items["description"] = description


        items["source"] = 'siluele.com'

        images_list = response.xpath("//div[@id='gallery_01']/a/img/@src").getall()
        if images_list:
            items["images"] = images_list
        else:
            images_list=response.xpath("//a[@class='thumbnails']/@href").getall()
            items["images"] = images_list

        strr='/'
        detail.pop(-1)
        breadcrumb_list=strr.join(detail)
        items["cat"] = detail[-1]
        items["detail_cat"] = breadcrumb_list


        label_list=response.xpath("//div[@id='product']/div/select/option")
        if label_list:
            label_list.pop(0)
        color_list=[]
        for label in label_list:
            print('hassku')
            color=label.xpath("./text()").get()
            color=self.filter_text(self.filter_html_label(color))
            color_list.append({'color':color})

        sku_list = list()
        for sku in color_list:
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
        # print(items)
        yield items

        # detection_main(
        #     items=items,
        #     website=website,
        #     num=10,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)