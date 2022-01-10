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

website = 'icing'
# 全流程解析脚本

class IcingSpider(scrapy.Spider):
    name = website
    allowed_domains = ['icing.com']
    start_urls = ['https://www.icing.com/us/']

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
        super(IcingSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "")

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

    def filter_html_label(self, text):
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

    def start_requests(self):
        url_list = [
            'https://www.icing.com/us/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://icing.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list=[]
        start_xpath=response.xpath("//ul[@class='menu-category level-1']/li")
        print('level_1_list:')
        print(start_xpath)
        start_xpath.pop(0)
        for find_xpath in start_xpath:
            level_2_xpath=find_xpath.xpath(".//ul")
            if level_2_xpath:
                level_2_xpath.pop(0)
                print('level_2_list:')
                print(level_2_xpath)
                for find_next_xpath in level_2_xpath:
                    li_lable_list=find_next_xpath.xpath("./li")
                    print('li_lable')
                    print(li_lable_list)
                    for lable in li_lable_list:
                        if(lable.xpath("./@class").get()=='has-no-sub-menu'):
                            url_list.append(lable.xpath("./a/@href").get())
                        elif(lable.xpath("./@class").get()=='has-sub-menu'):
                            a_list=lable.xpath("./ul[@class='level-3']/li/a/@href").getall()
                            for i in a_list:
                                url_list.append(i)


        #url_list = response.xpath("//nav[id='navigation']/ul/").getall()
        url_list = [response.urljoin(url) for url in url_list]
        print('页面url：')
        print(url_list)
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='search-result-content']/ul/li/div/a/@href").getall()
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
        next_page_url=''
        page_url_list = response.xpath("//div[@class='pagination']/ul/li")
        for i in range(len(page_url_list)):
            if (page_url_list[i].xpath("./@class")=='current-page'):
                if(i!=len(page_url_list)-1):
                    next_page_url=page_url_list[i+1].xpath("./a/@href")
                else:
                    next_page_url=False

        if next_page_url:
           next_page_url = response.urljoin(next_page_url)
           #print("下一页:"+next_page_url)
           yield scrapy.Request(
               url=next_page_url,
               callback=self.parse_list,
           )

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//div[@id='pdpMain']/div[1]//div[@class='product-price']/del/text()").get()#需要清洗+截断
        original_price=self.filter_text(self.filter_html_label(''.join(original_price))).split("$")[-1]
        current_price = response.xpath("//div[@id='pdpMain']/div[1]//div[@class='product-price']/span/text()").get()
        current_price = self.filter_text(self.filter_html_label(''.join(current_price))).split("$")[-1]

        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        items["brand"] = 'icing'
        items["name"] = response.xpath("//div[@id='pdpMain']/div[1]/div[1]/h1[@class='product-name']/text()").get()


        #attributes=response.xpath("//div[@class='product-info']/div/div/div[@class='tab-content show']/ul/list/text()").getall()
        #items["attributes"] = attributes

        #items["about"] = response.xpath("").get()

        description=response.xpath("//div[@class='product-info']/div/div/div[@class='tab-content show']/p/text()").get()
        #description=''.join(description)
        #print('商品描述'+description)
        items["description"] =self.filter_text(self.filter_html_label(description))
        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = 'icing.com'

        #meta property="og:image"
        images_list = response.xpath("//ul[@class='product-image-slides']/li/@data-hires").getall()
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//ol[@class='breadcrumb']/li/a/text()").getall()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list

        sku_list = list()
        #for sku in original_sku_list:
        #     sku_item = SkuItem()
        #     sku_item["original_price"] = item["original_price"]
        #     sku_item["current_price"] = item["current_price"]
        #     sku_item["inventory"] = sku["inventory"]
        #     sku_item["sku"] = sku["sku"]
        #     imgs = list()
        #     sku_item["imgs"] = imgs
        #     sku_item["url"] = response.url
        #     sku_item["sku"] = sku
        #     attributes = SkuAttributesItem()
        #     attributes["colour"] = sku["name"]
        #     attributes["size"] = sku["size"]
        #     other = dict()
        #     attributes["other"] = other
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
        items['is_deleted'] = 0

        # print(items)
        # check_item(items)
        yield items

        # detection_main(
        #     items=items,
        #     website=website,
        #     num=self.settings["CLOSESPIDER_ITEMCOUNT"],
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)
