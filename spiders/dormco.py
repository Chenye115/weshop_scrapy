# -*- coding: utf-8 -*-
import html
import re
import json
import time
import scrapy
import requests
from hashlib import md5


from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util.item_check import check_item
from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'dormco'
# 全流程解析脚本

class DormcoSpider(scrapy.Spider):
    name = website
    allowed_domains = ['dormco.com']
    start_urls = ['https://www.dormco.com/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 10
            custom_debug_settings["HTTPCACHE_ENABLED"] = True
            # custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(DormcoSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "守约-shouyue")

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

    # def start_requests(self):
    #     url_list = [
    #
    #     ]
    #     for url in url_list:
    #         print(url)
    #         yield scrapy.Request(
    #             url=url,
    #         )

        #url = "http://dormco.com/"
        #yield scrapy.Request(
        #    url=url,
        #)
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

    def parse(self, response):
        """获取全部分类"""
        url_list = response.xpath("//ul[@class='vnav vnav__subnav vnav--level2']/li/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print('获取全部分类 '+url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        #//*[@id="MainForm"]/table[2]/tbody/tr/td/table/tbody/tr/td/table
        #//*[@id="MainForm"]/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[1]
        url_list = response.xpath("//table[@class='v65-productDisplay']//tr/td/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        print(url_list)
        for url in url_list:
            print('获取商品URL '+url)
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
        original_price = response.xpath("//div[@class='product_listprice']/b/text()").get()
        if original_price:
            original_price=original_price.split("$")[1]
        current_price = response.xpath("//div[@class='product_productprice']/b/span/text()").get()
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        items["brand"] =''
        items["name"] = response.xpath("//span[@itemprop='name']/text()").get()

        attributes = list()
        items["attributes"] = attributes

        description=response.xpath("//div[@id='ProductDetail_ProductDetails_div']//text()").getall()
        description=''.join(description)
        #print('商品描述'+description)
        items["description"] =self.filter_text(self.filter_html_label(description))


        about=response.xpath("//span[@itemprop='description']/ul/li/text()").getall()
        items["about"] = ''.join(about)


        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("//div[@class='product_yousave']/span[@class='save_price_val']/text()").get()
        items["source"] = website

        images_list=response.xpath("//span[@id='altviews']/a[@style='display: none;']/@href").getall()
        if images_list==[]:
            images_list = response.xpath("//img[@class='vCSS_img_product_photo']/@src").getall()

        #list('https://'+i for i in images_list)
        for n in range(0,len(images_list)):
            images_list[n]='https://bigchill.com/'+images_list[n]
        items["images"] = images_list

        # product_code=response.xpath("//span[@class='product_code']/text()").get()
        # items["product_code"]=product_code

        Breadcrumb_list = response.xpath("//td[@class='vCSS_breadcrumb_td']/b/a/text()").getall()
        print(Breadcrumb_list)
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

        #check_item(items)
        #print(items)
        yield items

        # detection_main(
        #     items=items,
        #     website=website,
        #     num=self.settings["CLOSESPIDER_ITEMCOUNT"],
        #     skulist=False,
        #     skulist_attributes=True
        # )
        # print(items)
