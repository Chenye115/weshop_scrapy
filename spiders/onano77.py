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

website = 'onano77'
# 全流程解析脚本

class Onano77Spider(scrapy.Spider):
    name = website
    #allowed_domains = ['onano77.com']
    #start_urls = ['https://www.onano77.com/products']

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
        super(Onano77Spider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "")

    is_debug = True
    custom_debug_settings = {
        'CLOSESPIDER_ITEMCOUNT' : 10,#检测个数
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
            'https://www.onano77.com/products',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

        #url = "http://onano77.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    # def parse(self, response):
    #     url_list = response.xpath("").getall()
    #     url_list = [response.urljoin(url) for url in url_list]
    #     for url in url_list:
    #         print(url)
    #         yield scrapy.Request(
    #             url=url,
    #             callback=self.parse_list,
    #         )



    #这个网站不需要找分类页 所有商品都在一页

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@id='product_list']/article/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for n in range(0,len(url_list)):
            url_list[n]=url_list[n]
        for url in url_list:
            print('商品详情url：')
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
        print('进入解析')
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//section[@class='product_price']/h3//text()").getall()
        original_price=''.join(original_price)
        current_price=''
        original_price=self.filter_text(self.filter_html_label(original_price)).split("$")[-1].replace(',', '').strip()
        if(original_price[1].isdigit()):
            print('商品原价')
            print(original_price)
            current_price = original_price
            items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
            items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
            items['is_deleted'] = 0
        else:
            items["original_price"] = '0'
            items["current_price"] = '0'
            items['is_deleted'] = 1

        # items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        # items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        items["brand"] = 'onano77'
        items["name"] = response.xpath("//header[@id='content_header']/h1/text()").get()

        attributes = list()
        items["attributes"] = attributes

        #items["about"] = response.xpath("").get()
        #items["description"] = response.xpath("").get()
        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = website
        images_list = response.xpath("//section[@class='product_images galy']/ul/li/img/@src").getall()
        items["images"] = images_list

        # Breadcrumb_list = response.xpath("").getall()
        items["cat"] = ''
        items["detail_cat"] = ''


        region_list=[]
        label_list = response.xpath("//select[@class='product_option_select']/option")
        if label_list:
            label_list.pop(0)
        #print('lable_list')
        #print(label_list)
        #print('label表')
        #print(label_list)
        for label in label_list:
            reigion_name = label.xpath('./text()').get().strip().replace(':', '').lower()
            reigion_price=label.xpath('./@data-price').get().strip().replace(':', '').lower()
            region_list.append({'reigion': reigion_name,'price':reigion_price})

        sku_list = list()
        for region in region_list:
            sku_item = SkuItem()
            sku_item["original_price"] = region["price"]
            sku_item["current_price"] = region["price"]
            #sku_item["inventory"] = sku["inventory"]
            #sku_item["sku"] = sku["sku"]
            #imgs = list()
            #sku_item["imgs"] = imgs
            sku_item["url"] = response.url
            #sku_item["sku"] = sku
            attributes = SkuAttributesItem()
            #attributes["colour"] = sku["name"]
            #attributes["size"] = sku["size"]
            other = dict()
            other.update({'reigion':region['reigion']})
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

        #print(items)
        # check_item(items)
        yield items

        # detection_main(
        #     items=items,
        #     website=website,
        #     num=self.settings["CLOSESPIDER_ITEMCOUNT"],
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        #print(items)
