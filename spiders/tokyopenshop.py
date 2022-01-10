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

website = 'tokyopenshop'
# 全流程解析脚本

class TokyopenshopSpider(scrapy.Spider):
    name = website
    allowed_domains = ['tokyopenshop.com']
    start_urls = ['https://tokyopenshop.com/']

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
        super(TokyopenshopSpider, self).__init__(**kwargs)
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
            'https://tokyopenshop.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://tokyopenshop.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list=[]
        label_list = response.xpath("//li[@class='test']/ul/li")
        for n in range(len(label_list)):
            if(label_list[n].xpath("@class").get()!='submenu'):
                url_list.append(label_list[n].xpath("./a/@href").get())
        print('分类页面url：')
        print(url_list)
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='centerBoxContentsProducts centeredContent back']/a/@href").getall()
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
        price_base_lable=response.xpath("//h2[@id='productPrices']/span")
        if (len(price_base_lable)==1):
            original_price = response.xpath("//span[@class='productBasePrice']/text()").get().split("$")[-1]
            current_price = original_price
        else:
            original_price = response.xpath("//span[@class='normalprice']/text()").get().split("$")[-1]
            current_price = response.xpath("//span[@class='productSalePrice']/text()|//span[@class='productSpecialPrice']/text()").get().split("$")[-1]
            #


        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        items["brand"] = 'tokyopenshop'
        items["name"] = response.xpath("//h1[@id='productName']/text()").get()
        #attributes = list()
        #items["attributes"] = attributes
        #items["about"] = response.xpath("").get()

        des=response.xpath("//div[@id='productDescription']//text()").getall()
        description=''.join(des)
        description=self.filter_text(self.filter_html_label(description))
        items["description"] = description

        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = 'tokyopenshop.com'

        images_list =[]
        image_lable_list1=response.xpath("//div[@id='productMainImage']//a/@href").getall()
        for i in image_lable_list1:
            images_list.append(i)
        image_lable_list2=response.xpath("//div[@class='additionalImages centeredContent back']/noscript/a/@href").getall()
        for i in image_lable_list2:
            images_list.append(i)
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//div[@id='navBreadCrumb']/a/text()").getall()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list


        #sku属性列表
        attributes_list=[]
        color_list = []
        label_list = response.xpath("//div[@id='productAttributes']//select")
        attr_num=len(label_list)
        if(attr_num==1):
            for i in label_list:
                color_list=i.xpath("./option/text()").getall()
                for color in color_list:
                    attributes_list.append({'color':color})
        if(attr_num==2):
            # print('原始attr_num')
            size_list=label_list[0].xpath("./option/text()").getall()
            size_list.pop(0)
            # print('size_list')
            # print(size_list)
            color_list=label_list[1].xpath("./option/text()").getall()
            color_list.pop(0)
            # print('color_list')
            # print(color_list)
            for i in size_list:
                if color_list:
                    for j in color_list:
                        attributes_list.append({'size':i,'color':j})
                else:
                    attr_num=3
                    attributes_list.append({'size':i})

        # print('可选取的属性数量')
        # print(attr_num)
        # print(attributes_list)

        sku_list = list()
        for attr in attributes_list:
            sku_item = SkuItem()
            sku_item["original_price"] = items["original_price"]
            sku_item["current_price"] = items["current_price"]
            #sku_item["inventory"] = sku["inventory"]

            sku_item["url"] = response.url

            attributes = SkuAttributesItem()
            if(attr_num==1):
                attributes["colour"] = attr["color"]
                sku_item["attributes"] = attributes
            elif(attr_num==2):
                attributes["colour"] = attr["color"]
                attributes["size"] = attr["size"]
                sku_item["attributes"] = attributes
            elif(attr_num==3):
                attributes["size"] = attr["size"]
                sku_item["attributes"] = attributes
            else:
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

        #print(items)
        # check_item(items)
        yield items

        # detection_main(
        #     items=items,
        #     website=website,
        #     num=10,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)
