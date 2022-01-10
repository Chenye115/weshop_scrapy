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

website = 'heramoto'
# 全流程解析脚本

class HeramotoSpider(scrapy.Spider):
    name = website
    allowed_domains = ['heramoto.com']
    start_urls = ['http://www.heramoto.com/']

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
        super(HeramotoSpider, self).__init__(**kwargs)
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
            'http://www.heramoto.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://heramoto.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//ul[@class='category-list']//a/@href").getall()
        # print('url_list_old')
        # print(url_list)
        url_list.pop(-1)
        # print('url_list_new')
        # print(url_list)
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:

            if 'http://www.heramoto.com' in url:
                print(url)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_list,
                )
            else:
                url='http://www.heramoto.com'+url
                print(url)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_list,
                )

    def parse_list(self, response):

        """列表页"""
        url_list = response.xpath("//ul[@class='ProductList']/li/div[1]/a/@href").getall()
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
        next_page_url = response.xpath("//ul[@class='PagingList']/li[@class='ActivePage']/following-sibling::li[1]/a/@href").get()
        if next_page_url:
           next_page_url = response.urljoin(next_page_url)
           print("下一页:"+next_page_url)
           yield scrapy.Request(
               url=next_page_url,
               callback=self.parse_list,
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

    def product_dict(self,**kwargs):
        # 字典值列表笛卡尔积
        keys = kwargs.keys()
        vals = kwargs.values()
        for instance in itertools.product(*vals):
            yield dict(zip(keys, instance))

    def parse_detail(self, response):

        """详情页"""

        items = ShopItem()
        Breadcrumb_list = response.xpath("//div[@id='ProductBreadcrumb']/ul/li/a/text()|//div[@id='ProductBreadcrumb']/ul/li/text()").getall()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list
        if Breadcrumb_list[1]=='Shop All':
            return
        else:
            pass
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//em[@class='ProductPrice VariationProductPrice']/text()").get()
        original_price=original_price.split("$")[-1]
        current_price = original_price
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        brand=response.xpath("//h5[@class='brandName']/a/text()").get()
        if brand:
            items["brand"] = brand
        items["name"] = response.xpath("//div[@class='ContentArea']/h1/text()").get()

        #attributes = list()
        #items["attributes"] = attributes
        #items["about"] = response.xpath("").get()
        des = response.xpath("//div[@class='ProductDescriptionContainer prodAccordionContent']//text()").getall()
        des=''.join(des)
        des = self.filter_text(self.filter_html_label(des))
        items["description"]=des
        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = 'heramoto.com'
        image_list=[]
        image_search=re.findall(r'ZoomImageURLs(.*?)";',response.text)
        # print(image_search)
        for n in range(len(image_search)):
            image=image_search[n].replace('\\','').split("\"")[-1]
            image_list.append(image)
        items["images"] = image_list



        sku_list = list()
        have_sku = response.xpath("//div[@class='productAttributeList']//div[@class='productAttributeLabel']/label/span[2]/text()").getall()

        if len(have_sku)>0:
            print('hassku')
            sku_option_list = response.xpath("//div[@class='productAttributeList']//div[@class='productAttributeValue']//select")

            #print(response.text)
            sku_dict = {}
            for i,sku_option in enumerate(sku_option_list):
                sku_title = self.filter_text(self.filter_html_label(have_sku[i])) #have_sku[i].strip()
                sku_opts = sku_option.xpath("./option/text()").getall()
                if sku_opts:
                    sku_opts.pop(0)
                    sku_dict[sku_title] = sku_opts
                    org_sku_list = list(self.product_dict(**sku_dict))
                    for sku in org_sku_list:
                        sku_item = SkuItem()
                        attributes = SkuAttributesItem()
                        other = dict()
                        sku_item["url"] = response.url
                        sku_item["original_price"] = items["original_price"]
                        sku_item["current_price"] = items["current_price"]
                        for k, v in sku.items():
                            if k == 'Color:':
                                attributes["colour"] = v
                            elif k == 'Size:':
                                attributes["size"] = v
                            else:
                                other[k] = v
                        if len(other) > 0:
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

        # check_item(items)
        # # print(items)
        yield items
        # #
        # detection_main(
        #     items=items,
        #     website=website,
        #     num=8,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)
