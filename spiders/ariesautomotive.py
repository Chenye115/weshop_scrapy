# -*- coding: utf-8 -*-
# 网站翻页自己有问题
import re
import json
import time
import scrapy
import requests
from hashlib import md5
from collections import defaultdict
from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem
from overseaSpider.util.scriptdetection import detection_main
import hashlib
from lxml import etree
import math
from overseaSpider.util.item_check import check_item
from scrapy.selector import Selector
import httpx
import html

website = 'ariesautomotive'

class AriesautomotiveSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['www.ariesautomotive.com']
    # start_urls = ['http://www.ariesautomotive.com/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 10 #检测个数
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            # custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(AriesautomotiveSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "猛男")

    is_debug = True
    custom_debug_settings = {
        # 'CLOSESPIDER_ITEMCOUNT' : 10,#检测个数
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
        'DOWNLOAD_HANDLERS': {
            "https": "overseaSpider.downloadhandlers.HttpxDownloadHandler",
        },
    }


    # 不改变顺序去重(list)
    def delete_duplicate(self, oldlist):
        newlist = list(set(oldlist))
        newlist.sort(key=oldlist.index)
        return newlist

    def remove_repeat(self,LLL):
        L = []
        for i in LLL:
            if i not in L:
                L.append(i)
        return L


    def filter_html_label(self,text):
        if text:
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
        yield scrapy.Request(
            url='https://www.ariesautomotive.com/part/2164003',
            # meta={'h2':True},
            callback=self.parse_detail,
        )

        url_list = [

        ]
        for url in url_list:
            yield scrapy.Request(
                meta={'h2':True},
                url=url,
            )

        url = "https://www.ariesautomotive.com/"
        yield scrapy.Request(
            url=url,
        )

        # callback = self.parse_list,


    def parse(self, response):
        url_list = response.xpath('//ul[@class="level0 submenu"]//li/a/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
# var catId =     ;
        catId = re.findall('var catId = (.+?);',response.text)
        if catId:
            catid = catId[0]
            url = 'https://www.ariesautomotive.com/catalog/category/ajaxview/?id='+str(catid)+'&hash='
            new_response = requests.get(url)
            if new_response.status_code == 200:
                js_data = new_response.json()
                html_text = js_data.get('html')
                if html_text:
                    html = Selector(text=html_text)


                    url_list = html.xpath('//div[@class="product-item-info"]/a/@href').getall()
                    if url_list:
                        url_list = [response.urljoin(url) for url in url_list]
                        url_list = list(set(url_list))
                        for url in url_list:
                            yield scrapy.Request(
                                url=url,
                                callback=self.parse_detail,
                            )
                        next_page = html.xpath('//a[@class="action  next"]/@href').get()
                        if next_page:
                            yield scrapy.Request(
                                url=response.urljoin(next_page),
                                callback=self.parse_list,
                            )

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        items["source"] = 'ariesautomotive.com'

        # check_availability = response.xpath('').get()
        # if check_availability == 'In stock':
        name = response.xpath('//h1[@class="page-title"]/span/text()').get()
        if name:
            items["name"] = self.filter_html_label(name)

        items["brand"] = ''


        items["cat"] = ''
        items["detail_cat"] =''
        #response.xpath('//li[@class="level0 nav-1 category-item first level-top parent"]//a/span/text()').getall()
        Breadcrumb_list = response.xpath('//meta[@property="product:category"]/@content').get()
        cat_1 = response.xpath('//li[@class="level0 nav-1 category-item first level-top parent"]/a/span/text()').get()
        if Breadcrumb_list:
            items["cat"] = self.filter_html_label(items["name"])
            if cat_1:
                detail_cat = 'Home/'+ cat_1 +'/' +Breadcrumb_list +'/' + items["cat"]
            else:
                detail_cat = 'Home/' + Breadcrumb_list + '/' + items["cat"]
            items["detail_cat"] = self.filter_html_label(detail_cat)


        current_price = response.xpath('//meta[@property="product:price:amount"]/@content').get()
        if current_price and self.filter_html_label(str(current_price)) != '':
            items["current_price"] =  '' + self.filter_html_label(str(current_price)).replace(',','')
        else:
            items["current_price"] = ''


        items["original_price"] = items["current_price"]


        description_list = response.xpath('//meta[@property="og:description"]/@content').get()
        if description_list:
            description = ''.join(description_list)
            des = self.filter_html_label(description)
            if des:
                items["description"] = des

        attributes = list()
        attributes_list = response.xpath('//div[@class="data table additional-attributes"]//li')
        if attributes_list:
            for i in attributes_list:
                k_l=i.xpath('./strong//text()').getall()
                v_l=i.xpath('./span//text()').getall()
                if k_l and v_l:
                    k = ''.join(k_l)
                    v = ''.join(v_l)
                    att = k + ':' +  v
                    att_1 = self.filter_html_label(att)
                    if att_1 != '' and att_1 != ' ':
                        attributes.append(att_1)

        if attributes:
            items["attributes"] = attributes
        images_list = []
        get_data = response.xpath('//script[@type="text/x-magento-init" and contains(text(),"magnifierOpts")]/text()').get()
        if get_data:
            js_data = json.loads(get_data)
            get_imgs = js_data.get('[data-gallery-role=gallery-placeholder]').get('mage/gallery/gallery').get('data')
            if get_imgs:
                for i in get_imgs:
                    img = i.get('full')
                    if img and img not in images_list:
                        images_list.append(img)

        if images_list:
            items["images"] =  [ i for i in images_list]


        sku_list = list()

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
        # print('=============')
        # print(items)
        # detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True, skulist_attributes=True)
        # check_item(items)
        yield items



