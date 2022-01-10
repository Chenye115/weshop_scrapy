# -*- coding: utf-8 -*-
import html
import itertools
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

website = 'quantumlabs'
# 全流程解析脚本

class quantumlabs(scrapy.Spider):
    name = website
    # allowed_domains = ['$domain']
    # start_urls = ['http://$domain/']

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
        super(quantumlabs, self).__init__(**kwargs)
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

    def product_dict(self,**kwargs):
        # 字典值列表笛卡尔积
        keys = kwargs.keys()
        vals = kwargs.values()
        for instance in itertools.product(*vals):
            yield dict(zip(keys, instance))

    def start_requests(self):
        url_list = [
            'https://quantumlabs.com/',

        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://$domain/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//ul[@class='mega-menu']/li[1]/div//a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_sublist,
            )

    def parse_sublist(self,response):
        url_list = response.xpath("//div[@class='category-grid sub-category-grid']//h2[@class='title']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='item-grid']//div[@class='picture']//a/@href").getall()
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
        original_price = response.xpath('//div[@class="old-product-price"]/span/text()').get()
        if original_price:
            original_price=original_price.replace("$","")
        current_price = response.xpath("//span[@itemprop='price']/@content").get()
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        items["brand"] = ''
        name = response.xpath('//h1[@itemprop="name"]/text()').get()
        items["name"]=self.filter_text(self.filter_html_label(name))
        # attributes = list()
        # items["attributes"] = attributes
        # items["about"] = response.xpath("//div[@class='fulldescription']/p/text()").get()
        des=response.xpath("//div[@id='full-description']//text()").getall()
        des=' '.join(des)
        items["description"] =self.filter_text(self.filter_html_label(des))
        # items["care"] = response.xpath("").get()
        # items["sales"] = response.xpath("").get()
        items["source"] = 'quantumlabs.com'
        images_list = response.xpath("//div[@class='picture-thumbs in-carousel']//a/@data-full-image-url").getall()
        if images_list:
            items["images"] = images_list
        else:
            images_list=response.xpath("//img[@id='cloudZoomImage']/@src").getall()
            items["images"] = images_list

        Breadcrumb_list = response.xpath("//div[@class='breadcrumb']//text()").getall()
        br_list=self.filter_text(self.filter_html_label(''.join(Breadcrumb_list)))
        items["cat"] = br_list.split("/")[-1]
        items["detail_cat"] = br_list

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

        sku_list = list()
        # have_sku = response.xpath("//div[@class='attributes']//dt/label//text()").getall()
        # if len(have_sku)>0:
        #     sku_option_list = response.xpath("//div[@class='attributes']//dd/select")
        #     sku_dict = {}
        #     for i,sku_option in enumerate(sku_option_list):
        #         sku_title = have_sku[i].strip()
        #         sku_opts = sku_option.xpath(
        #             ".//option//text()").getall()
        #         sku_dict[sku_title] = sku_opts
        #     org_sku_list = list(self.product_dict(**sku_dict))
        #     for sku in org_sku_list:
        #         sku_item = SkuItem()
        #         attributes = SkuAttributesItem()
        #         other = dict()
        #         sku_item["url"] = response.url
        #         add_price = 0.00
        #         sku_item["original_price"] = items["original_price"]
        #         sku_item["current_price"] = items["current_price"]
        #         for k, v in sku.items():
        #             if k == 'Color':
        #                 attributes["colour"] = v
        #             elif k == 'Size':
        #                 attributes["size"] = v
        #             else:
        #                 other[k] = v
        #             if '$' in v:
        #                 a_p = v.split("$")[1].replace("]", '').strip()
        #                 add_price = add_price + float(a_p.replace(',',''))
        #         sku_item["original_price"] = str(float(items["original_price"]) + add_price)
        #         sku_item["current_price"] = str(float(items["current_price"]) + add_price)
        #         if len(other) > 0:
        #             attributes["other"] = other
        #         sku_item["attributes"] = attributes
        #         sku_list.append(sku_item)


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
        yield items
        #
        # detection_main(
        #     items=items,
        #     website=website,
        #     num=5,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)
        #
