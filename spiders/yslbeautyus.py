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

website = 'yslbeautyus'
# 全流程解析脚本

class YslbeautyusSpider(scrapy.Spider):
    name = website
    allowed_domains = ['yslbeautyus.com']
    start_urls = ['https://www.yslbeautyus.com/']

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
        super(YslbeautyusSpider, self).__init__(**kwargs)
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
            'https://www.yslbeautyus.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://yslbeautyus.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//a[@class='c-navigation__link m-without-subcategories m-level-3 ']/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='c-product-tile__wrapper c-product-grid__tile']/figure/div/div/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        print('url_list')
        print(url_list)

        # for url in url_list:
        #     print(url)
        #     yield scrapy.Request(
        #         url=url,
        #         callback=self.parse_detail,
        #     )

        # response_url = parse.unquote(response.url)
        # split_str = ''
        # base_url = response_url.split(split_str)[0]
        # page_num = int(response_url.split(split_str)[1])+1
        # next_page_url = base_url + split_str + str(page_num)
        next_page_url = response.xpath("//link[@rel='next']/@href").get()
        if next_page_url:
           next_page_url = response.urljoin(next_page_url)
           print("下一页:"+next_page_url)
           yield scrapy.Request(
               url=next_page_url,
               callback=self.parse_list,
           )
        else:
            print('开始解析商品详情')
            url_list_2=list(set(url_list))
            print('url_list_2')
            print(url_list_2)
            for url in url_list_2:
                print('商品url')
                print(url)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )



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
                       u'\u200A', u'\u202F', u'\u205F',u'\u2003']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//span[@class='c-product-price__value']/text()").getall()
        original_price=''.join(original_price).split("$")[1]
        current_price = original_price
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        items["brand"] = 'YSL Beauty'
        items["name"] = response.xpath("//h1[@class='c-product-main__name']/text()").get()

        #attributes = list()
        #items["attributes"] = attributes

        about=response.xpath("//div[@data-tab-hash='ingredients']/text()").get()
        if about:
            items["about"] = self.filter_text(self.filter_html_label(about))
        description = response.xpath("//div[@data-tab-hash='description']/div/div/div//text()").getall()
        # for n in range(len(description)):
        #     description[n]=self.filter_text(self.filter_html_label(description))
        description.pop(-1)
        description.pop(-1)
        description=' '.join(description)
        description=self.filter_text(self.filter_html_label(description))
        items["description"] = description
        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = 'yslbeautyus.com'
        images_list = response.xpath("//div[@class='c-product-detail-image__mosaic']/div/button/img/@src").getall()
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//ol[@class='c-breadcrumbs__list']/li/a/span/text()|//ol[@class='c-breadcrumbs__list']/li/span/text()").getall()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list

        size_list=[]
        label_list=response.xpath("//a[contains(@class,'c-variations-carousel__link')]")
        for label in label_list:
            size=label.xpath("./span/text()").get()
            #
            price=label.xpath("./div/span[@class='c-product-price__value']/text()").get()
            price=price.split("$")[-1]
            if price:
                new_price=price
                old_price=price
            else:
                new_price=label.xpath("./div/span[@class='c-product-price__value m-new ']/text()").get()
                new_price=new_price.split("$")[-1]
                old_price=label.xpath("./div/span[@class='c-product-price__value m-old ']/text()").get()
                old_price=old_price.split("$")[-1]
            size_list.append({'size':size,'old_price':old_price,'new_price':new_price})

        sku_list = list()
        for sku in size_list:
            sku_item = SkuItem()
            sku_item["original_price"] = sku['new_price']
            sku_item["current_price"] = sku['old_price']



            sku_item["url"] = response.url

            attributes = SkuAttributesItem()

            attributes["size"] = sku["size"]

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

        check_item(items)
        print(items)
        yield items

        detection_main(
            items=items,
            website=website,
            num=10,
            skulist=True,
            skulist_attributes=True,
        )

