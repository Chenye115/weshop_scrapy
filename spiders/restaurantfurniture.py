# -*- coding: utf-8 -*-
import html
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'restaurantfurniture'
# 全流程解析脚本

class RestaurantfurnitureSpider(scrapy.Spider):
    name = website
    allowed_domains = ['restaurantfurniture.net']
    start_urls = ['http://restaurantfurniture.net/']

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
        super(RestaurantfurnitureSpider, self).__init__(**kwargs)
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
            'http://restaurantfurniture.net/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://restaurantfurniture.net/"
        #yield scrapy.Request(
        #    url=url,
        #)


    def filter_html_label(self, text, type):
        text = str(text)
        # 注释，js，css
        filter_rerule_list = [r'(<!--[\s\S]*?-->)', r'<script[\s\S]*?</script>', r'<style[\s\S]*?</style>']
        for filter_rerule in filter_rerule_list:
            html_labels = re.findall(filter_rerule, text)
            for h in html_labels:
                text = text.replace(h, ' ')
        html_labels = re.findall(r'<[^>]+>', text)  # html标签单独拿出
        if type == 1:
            for h in html_labels:
                text = text.replace(h, ' ')
        filter_char_list = [
            u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000', u'\u200a', u'\u2028', u'\u2029', u'\u202f', u'\u205f',
            u'\u3000', u'\xA0', u'\u180E', u'\u200A', u'\u202F', u'\u205F', '\t', '\n', '\r', '\f', '\v',
        ]
        for f_char in filter_char_list:
            text = text.replace(f_char, '')
        text = html.unescape(text)
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
        url_list = response.xpath("//ul[@class='level0']/li[@class='level1']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@product-card-list]//li[@class='product-card-item first']//div[@class='product-card-info']/a/@href").getall()
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
        regular_price=response.xpath("//div[@class='product-options']//div[@class='row price-box']/span[@class='row price-box']/span/text()").get()
        regular_price=regular_price.split('$')[-1]
        original_price = regular_price
        current_price = regular_price
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        items["brand"] = 'Restaurant Furniture'
        items["name"] = response.xpath("//div[@class='product-shop']/h1/text()").get()
        items["product_code"]=response.xpath("//div[@class='product-shop']/span[@class='product-sku-main']/text()").get()

        attributes = list()
        items["attributes"] = attributes

        about=response.xpath("//div[@class='resp-tabs-container']/div[2]//text()").getall()
        items["about"] = self.filter_text(self.filter_html_label(about,True))
        description=response.xpath("//div[@class='resp-tabs-container']/div[1]//text()").getall()
        items["description"] = self.filter_text(self.filter_html_label(description,True))

        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()

        items["source"] = website
        images_list = response.xpath("//div[@class='product-view']//div[@class='product-img-box']/div[3]/a/@href").getall()
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//ul[@class='breadcrumbs']/li/a/text()").getall()
        #print(Breadcrumb_list)
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list

        #关键在于SKU的列表
        size_list = []
        attr_id = 0
        dic_list=[]
        label_list = response.xpath('//div[@class="wrapper-accordion"]/div')
        for index in range(len(label_list)):
            if index==1:
                pass
            elif index%2==0:
                temp_list=[];
                key = label_list[index].xpath('./div[2]/span/text()').get().strip().lower()
                temp_list.append(key)
                ifselected=label_list[index+1].xpath('.//select')
                if ifselected==0:
                    values = label_list[index+1].xpath('./div[1]/dl/dd/div[2]/div[1]/span[2]/text()').get()
                    temp_list.append(values)
                    dic_list.append(temp_list)
                else:
                    values=label_list[index+1].xpath('./div[1]/dl/dd/div[1]/select//option/text()').getall()
                    temp_list.append(values)
                    dic_list.append(temp_list)
        print(dic_list)

        search_dic_list=[]
        search_dic={}
#size_list = [{'id': v.xpath('./@data-product-attribute-value').get(), 'value': v.xpath('./span[1]/text()').get().strip()} for v in values]
        for i in len(dic_list):
            for j in len(dic_list[i][2]):
                search_dic.update(key=dic_list[i][1],value=dic_list[i][2][j])



        sku_origin_price=int(regular_price)
        sku_list = list()
        for sku in original_sku_list:
            sku_item = SkuItem()
            sku_item["original_price"] = items["original_price"]
            sku_item["current_price"] = items["current_price"]
            sku_item["inventory"] = sku["inventory"]
            sku_item["sku"] = sku["sku"]
            imgs = list()
            sku_item["imgs"] = imgs
            sku_item["url"] = response.url
            sku_item["sku"] = sku
            attributes = SkuAttributesItem()
            attributes["colour"] = sku["name"]
            attributes["size"] = sku["size"]
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
