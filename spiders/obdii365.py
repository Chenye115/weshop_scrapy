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

website = 'obdii365'
# 全流程解析脚本

class Obdii365Spider(scrapy.Spider):
    name = website
    allowed_domains = ['obdii365.com']
    start_urls = ['https://www.obdii365.com/']

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
        super(Obdii365Spider, self).__init__(**kwargs)
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
            'https://www.obdii365.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://obdii365.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        '''按品牌找'''
        url_list = response.xpath("//ul[@aria-labelledby='xri_Hd_Nav_ProBrandMenu']/li/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            brand=url.split("/")[-1]
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                meta={'brand':brand}
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='row no-gutters py-3 xr-box-list xr-hover-lightgray']/div/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        brand=response.meta.get('brand')
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={'brand':brand}
            )

        # response_url = parse.unquote(response.url)
        # split_str = ''
        # base_url = response_url.split(split_str)[0]
        # page_num = int(response_url.split(split_str)[1])+1
        # next_page_url = base_url + split_str + str(page_num)
        next_page_url = response.xpath("//nav[@aria-label='Page navigation']/ul//a[@aria-label='Next']/@href").get()
        if next_page_url:
           next_page_url = response.urljoin(next_page_url)
           # brand=response.meta.get('brand')
           print("下一页:"+next_page_url)
           yield scrapy.Request(
               url=next_page_url,
               callback=self.parse_list,
               meta={'brand':brand}
           )

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]

        #re_find=re.findall('">\$</span>(.*?)</strong></span><span',response.text)
        # if(len(re_find)==1):
        #     original_price = re_find
        #     current_price=original_price
        #     print('价格1')
        #     print(original_price)
        # elif(len(re_find)>1):
        #     original_price=re.findall('">\$</span>(.*?)</span><span',response.text)[0]
        #     print('价格2')
        #     print(original_price)
        # else:
        #     original_price=re.findall('">\$</span>(.*?)</sup></span><span',response.text)
        #     print('zmhs')
        #     print(original_price)

        or_price= response.xpath("//span[contains(@name,'xrn-Curr-USD') and contains(@style,'display:')][1]//text()").getall()
        or_price=''.join(or_price).split("$")[1].replace(',','').strip()
        original_price=self.filter_text(self.filter_html_label(or_price))
        cu_price=response.xpath("//span[contains(@name,'xrn-Curr-USD') and contains(@style,'display:')][2]//text()").getall()
        cu_price=''.join(cu_price).split("$")[1].replace(',','').strip()
        current_price = self.filter_text(self.filter_html_label(cu_price))
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)

        location= response.xpath("//div[@class='d-none d-md-block']")
        items["name"]=location.xpath("../h1/text()").get()

        attributes = []
        attr_list = response.xpath("//div[@class='form-row mt-1']")
        for attr in attr_list:
            attr_key = attr.xpath("./div[1]/text()").get()
            attr_key=self.filter_html_label(attr_key)
            attr_value = attr.xpath("./div[2]//text()").getall()
            attr_value=''.join(attr_value)
            attr_value=self.filter_html_label(attr_value)
            if attr_key:
                attributes.append(attr_key+attr_value)
        items["attributes"] = attributes


        #items["about"] = response.xpath("").get()
        description= response.xpath("//div[@id='xri_ProDt_Description']/div[1]//text()").getall()
        description=''.join(description)
        description=self.filter_text(self.filter_html_label(description))
        items["description"]=description
        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = 'obdii365.com'
        images_list = response.xpath("//div[@class='swiper-slide easyzoom']/a/@href").getall()
        for n in range(0,len(images_list)):
            images_list[n]='https://www.obdii365.com'+images_list[n]
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//ol[@class='breadcrumb']/li/a/text()").getall()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list
        items["brand"] = Breadcrumb_list[-2]



        select_list=[]
        label_list = response.xpath("//select/option")
        #print('label表')
        #print(label_list)
        if label_list:
            label_list.pop(0)
        for label in label_list:
            langauage = label.xpath("./text()").get()
            select_list.append({'lan': langauage})


        sku_list = list()
        for select in select_list:
            #print('hassku')
            sku_item = SkuItem()
            sku_item["original_price"] = items["original_price"]
            sku_item["current_price"] = items["current_price"]

            sku_item["url"] = response.url
            attributes = SkuAttributesItem()
            other = dict()
            other.update({'language':select['lan']})
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

        # print(items)
        # # # # # yield items
        # check_item(items)
        yield items

        # detection_main(
        #     items=items,
        #     website=website,
        #     num=10,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
