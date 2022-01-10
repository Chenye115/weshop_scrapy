# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

from lxml import etree
import math
from overseaSpider.util import item_check

website = 'artspace'


class ArtspaceSpider(scrapy.Spider):
    name = website

    # allowed_domains = ['artspace.com']
    # start_urls = ['http://artspace.com/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug',
                                                                                False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["HTTPCACHE_ENABLED"] = True
            custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(ArtspaceSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "涛儿")

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
            # 'overseaSpider.middlewares.PhantomjsUpdateCookieMiddleware': 543,
            # 'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },
        'HTTPCACHE_POLICY': 'overseaSpider.middlewares.DummyPolicy',
    }

    def filter_html_label(self, text):
        html_labels = re.findall(r'<[^>]+>', text)
        for h in html_labels:
            text = text.replace(h, '')
        text = text.replace('\n', '').replace('\r', '').replace('\t', '').replace('  ', '').strip()
        return text

    def start_requests(self):
        url_list = [
            'https://www.artspace.com/art?pr=0-500',
            'https://www.artspace.com/art?pr=500-5000',
            'https://www.artspace.com/art?pr=5000-15000',
            'https://www.artspace.com/art?pr=15000-50000',

        ]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
            )

        # url = "https://www.artspace.com/sandro_chia/surprising_novel_portfolio"
        # yield scrapy.Request(
        #     url=url,
        #     callback=self.parse_detail,
        # )

    def parse(self, response):

        total_page_num_list = re.findall('"num_pages": (.+), "previous_page_number"', response.text)

        if total_page_num_list:
            total_page_num = int(total_page_num_list[0])
        else:
            total_page_num = 1

        if total_page_num == 1:
            yield scrapy.Request(
                url=response.url,
                callback=self.parse_list,
            )
        else:
            url_list = []
            for page_n in range(1, total_page_num + 1):
                url_l = response.url.split('?')
                myurl = url_l[0] + '?it=120&page=' + str(page_n) + '&view=grid&' + url_l[1] + '&weighted=false'
                url_list.append(myurl)
            for url in url_list:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_list,
                )

    def parse_list(self, response):
        """列表页"""

        url_list = re.findall('"wl": "(.+?)", "', response.text)
        url_list = ['https://www.artspace.com' + url for url in url_list]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        items["source"] = website

        name = response.xpath('//div[@class="artist pull-left"]/a//text()').get()
        if name:
            items["name"] = name
        else:
            name = response.xpath('//div[@class="artist pull-left"]//text()').get()
            name_1 = self.filter_html_label(name)
            if name_1:
                items["name"] = name_1

        current_price = response.xpath(
            '//div[@class="single-product-price clearfix"]//span[@class="product-price"]//text()').get()
        if current_price:
            current_price_1 = current_price.replace('\n', '').replace(' ', '')
            if '-'in current_price_1:
                current_price_list = current_price_1.split('-')
                current_price_2 = current_price_list[0]
                items["current_price"] = current_price_2
                items["original_price"] = current_price_2
            else:
                items["current_price"] = current_price_1
                items["original_price"] = items["current_price"]
        else:
            # 区间价格
            current_price = response.xpath(
                '//div[@class="inquire-product-price"]//text()').get()
            if current_price:
                current_price_1 = self.filter_html_label(current_price)
                current_price_list = current_price_1.split('-')
                current_price_2 = current_price_list[0]
                items["current_price"] = current_price_2.replace(' ', '').replace('\n', '')
                items["original_price"] = current_price_2.replace(' ', '').replace('\n', '')
            else:
                items["current_price"] = ''
                items["original_price"] = ''



        attributes = list()
        attributes_list = response.xpath('//div[@class="work-info"]//div[@class="product-info"]//p//text()').getall()
        if attributes_list:
            for att in attributes_list:
                att_1 = self.filter_html_label(att)
                attributes.append(att_1)
        if attributes:
            items["attributes"] = attributes

        about_list = response.xpath(
            '//div[@class="col-sm-7 left-col"]//div[@class="info-left"]//div[@class="desc-section about"]//text()').getall()
        if about_list:
            about = ''
            for a in about_list:
                about += a
            about_1 = about.replace('\xa0', '').replace('\n', '')
            items["about"] = about_1

        description = response.xpath('//div[@class="work-info"]//p[@class="authentication"]//text()').get()
        if description:
            description_1 = self.filter_html_label(description)
            items["description"] = description_1

        images_list = response.xpath('//div[@class="slider-holder"]//li//img//@data-src').getall()
        images_ = response.xpath('//div[@class="img-holder"]/img//@data-src').get()
        img_list = []
        if images_:
            img_ = 'https:' + images_
            img_list.append(img_)
        if images_list:
            images_list_1 = ['https:' + img.replace('160x160-c', '800x800') for img in images_list]
            images_list_2 = [images_list_1[i] for i in range(1, len(images_list_1)) if '160x160' not in images_list_1[i]]
            for img in images_list_2:
                img_list.append(img)


        items["images"] = img_list

        Breadcrumb_list = response.xpath('//div[@class="tags"]//a//text()').getall()
        if Breadcrumb_list:
            items["cat"] = Breadcrumb_list[-1]
            detail_cat = Breadcrumb_list[0]
            for i in range(1, len(Breadcrumb_list)):
                detail_cat = detail_cat + '/' + Breadcrumb_list[i]
            items["detail_cat"] = detail_cat
        else:
            items["cat"] = items['name']
            items["detail_cat"] = 'Home/' + items["cat"]

        sku_list = list()
        json_list = re.findall('new WorksGenericCollection\(\[(.+?)], \{', response.text)
        if json_list:
            json_data = json.loads(json_list[0])
            json_data_1 = json_data['products']
            for product in json_data_1:
                normal_price = product['price']
                frame_price = product['framed_price'] if product['framed_price'] else items['current_price']
                if product['frames']:
                    for frame in product['frames']:
                        size = frame['size'] if frame['size'] else ''
                        color = frame['color'] if frame['color'] else ''
                        '''SkuAttributesItem'''
                        SAI = SkuAttributesItem()
                        if color:
                            SAI['colour'] = color
                        if size:
                            SAI['size'] = size
                        SI = SkuItem()
                        SI['attributes'] = SAI
                        SI['original_price'] = frame_price
                        SI['current_price'] = frame_price
                        if color == 'maple':
                            img = 'https://www.artspace.com/static/arts/img/frame_landscape_' + 'wood' + '_632.jpg'
                        else:
                            img = 'https://www.artspace.com/static/arts/img/frame_landscape_' + color +'_632.jpg'
                        img_list = [i for i in items['images']]
                        img_list.append(img)
                        SI['imgs'] = img_list if img_list else items['images']
                        SI['url'] = items['url']
                        sku_list.append(SI)

        items["sku_list"] = sku_list
        if items["current_price"]:
            try:
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
                yield items
                # item_check.check_item(items)
            except:
                pass
