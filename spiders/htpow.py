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

website = 'htpow'
# 全流程解析脚本

class HtpowSpider(scrapy.Spider):
    name = website
    allowed_domains = ['htpow.com']
    start_urls = ['https://www.htpow.com/']

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
        super(HtpowSpider, self).__init__(**kwargs)
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
            'https://www.htpow.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

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


        #url = "http://htpow.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//ul[@class='nav navbar-nav']/li[1]/ul/li/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        print("页面url列表")
        print(url_list)
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='wrapper-box full-wide']/section[@class='full-wide m-b-30']/div[2]/div/div/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        #print('商品url列表')
        print(url_list)
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
        next_page_li = response.xpath("//ul[@class='pagination']/li")
        next=next_page_li[-1]
        next_url=next.xpath("./a/@href").get()
        if next_url:
            next_url = response.urljoin(next_url)
            yield scrapy.Request(
               url=next_url,
               callback=self.parse_list,
           )


    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        #价格
        current_price = response.xpath("//span[@id='product_price']/text()").get()
        current_price=self.filter_text(self.filter_html_label(''.join(current_price))).split("$")[-1]
        current_price=current_price.replace(',', '').strip()
        #//section[contains(@class,'product-detail-top')]//p[contains(@class,'price')]//del//text()
        original_price =  response.xpath("//section[contains(@class,'product-detail-top')]//p[contains(@class,'price')]//del//text()").get()
        if original_price:
            original_price=original_price.split("$")[-1]
            original_price=original_price.replace(',', '').strip()
        else:
            original_price=current_price
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        items["brand"] = 'htpow'
        name=response.xpath("//section[@class='product-detail-top m-b-30']/div/div[2]/div[1]/h1[@class='title']/text()").get()
        name=self.filter_text(self.filter_html_label(name))
        items["name"] =name

        # attributes = list()
        # items["attributes"] = attributes
        # items["about"] = response.xpath("").get()
        attributes = []
        attr_list = response.xpath("//div[@class='am-panel-bd']//table//tr")
        for attr in attr_list:
            attr_key = attr.xpath("./td[1]//text()").get()
            attr_value = attr.xpath("./td[2]//text()").get()
            attributes.append(self.filter_html_label(attr_key)+self.filter_html_label(attr_value))
        items["attributes"] = attributes

        description= response.xpath("//div[@id='tabs01']//text()").getall()
        description=''.join(description)
        #print('商品描述'+description)
        items["description"] =self.filter_text(self.filter_html_label(description))

        care= response.xpath("//div[@class='tabs03']//text()").getall()
        care=''.join(care)
        items["care"]=self.filter_text(self.filter_html_label(care))

        #items["sales"] = response.xpath("").get()
        items["source"] = website

        images_list = response.xpath("//section[@class='product-detail-top m-b-30']/div//img/@src").getall()
        for n in range(0,len(images_list)):
            images_list[n]='https://htpow.com/'+images_list[n]
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//div[@class='search-box']/p/a/text()").getall()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list


        #sku_list
        wave_list=[]
        label_list = response.xpath("//select[@name='code_n']/option")
        #print('label表')
        #print(label_list)
        if label_list:
            label_list.pop(0)
        for label in label_list:
            wave_specifiction = label.xpath("./text()").get().strip().replace(':', '').lower()
            model = label.xpath("./@value").get().strip()
            price= label.xpath("./@price_data").get().split("$")[-1].replace(',', '').strip()
            wave_list.append({'specifiction': wave_specifiction, 'model': model,'price':price})



        sku_list = list()
        for sku in wave_list:
            sku_item = SkuItem()
            sku_item["original_price"] = sku["price"]
            sku_item["current_price"] = sku["price"]
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
            other.update({'specifiction': sku['specifiction'], 'model': sku['model']})
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
        # # # yield items
        # #
        # check_item(items)
        yield items

        # detection_main(
        #     items=items,
        #     website=website,
        #     num=10,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
