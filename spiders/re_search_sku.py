# -*- coding: utf-8 -*-
import html
import re
import itertools
import json
import time
import scrapy
import requests
from hashlib import md5
from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util.item_check import check_item
from overseaSpider.util.utils import isLinux
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'pacificmsi'
# 全流程解析脚本

class pacificmsi(scrapy.Spider):
    name = website
    # allowed_domains = ['pacificmsi']
    start_urls = 'https://www.pacificmsi.com/'


    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 8
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            # custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(pacificmsi, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "流冰")

    is_debug = True
    custom_debug_settings = {
        'MONGODB_COLLECTION': website,
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'DEBUG',
        'COOKIES_ENABLED': False,
        'HTTPCACHE_ENABLED': True,
         # 'HTTPCACHE_EXPIRATION_SECS': 7 * 24 * 60 * 60, # 秒
        #'DOWNLOAD_HANDLERS': {
        #'https': 'scrapy.core.downloader.handlers.http2.H2DownloadHandler',
        #},
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

    def clear_price(self,org_price,cur_price,Symbol='$'):
        """价格处理"""
        if not org_price and not cur_price:
            return None, None
        org_price = org_price.split('-')[0] if org_price and '-' in org_price else org_price
        cur_price = cur_price.split('-')[0] if cur_price and '-' in cur_price else cur_price
        if org_price:
            org_price = str(org_price).replace(Symbol, '').replace(' ', '').replace(',', '.').strip()
        if cur_price:
            cur_price = str(cur_price).replace(Symbol, '').replace(' ', '').replace(',', '.').strip()
        org_price = org_price if org_price and org_price != '' else cur_price
        cur_price = cur_price if cur_price and cur_price != '' else org_price
        if org_price.count(".") > 1:
            org_price =list(org_price)
            org_price.remove('.')
            org_price = ''.join(org_price)
        if cur_price.count(".") > 1:
            cur_price =list(cur_price)
            cur_price.remove('.')
            cur_price = ''.join(cur_price)
        return org_price, cur_price

    def product_dict(self,**kwargs):
        # 字典值列表笛卡尔积
        keys = kwargs.keys()
        vals = kwargs.values()
        for instance in itertools.product(*vals):
            yield dict(zip(keys, instance))

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
            u'\u3000', u'\xA0', u'\u180E', u'\u200A', u'\u202F', u'\u205F',u'\u200b',u'\x9d','\t', '\n', '\r', '\f', '\v',
        ]
        for f_char in filter_char_list:
            text = text.replace(f_char, '')
        text = re.sub(' +', ' ', text).strip()
        return text

    def remove_space_and_filter(self,l):
        # 洗列表文本
        new_l = []
        for i,j in enumerate(l):
            k = self.filter_html_label(j)
            if k == '':
                continue
            # if not k.strip().endswith('.') and not k.strip().endswith(':') and not k.strip().endswith(',') \
            #         and not k.strip().endswith('?') and not k.strip().endswith('!'):
            #     k = k+'.'
            new_l.append(k)
        return new_l

    def start_requests(self):
        url_list = [
            "https://www.pacificmsi.com/shop",
        ]
        for url in url_list:
           print(url)
           yield scrapy.Request(
              url=url,
           )

    def parse(self, response):
        url_list = response.xpath("//li[@class='nested-category-breadcrumb-list-item']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        cate = response.xpath("//h2[contains(@class,'nested-category-title')]/text()").get().strip()
        url_list = response.xpath("//a[@class='grid-item-link']/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={'cate':cate}
            )


    def get_attributes(self,response):
        # 处理attributes
        attributes_l = list()
        attr_key = response.xpath("").getall()
        org_attr_value = response.xpath("")
        attr_value = []
        for i, org_attr in enumerate(org_attr_value):
            attr_list = org_attr.xpath(".//text()").getall()
            attr_list = self.remove_space_and_filter(attr_list)
            if len(attr_list) > 0:
                attr_v = ''.join(attr_list)
                attr_value.append(attr_v)
            else:
                if i < len(attr_key):
                    del attr_key[i]
                    continue
        for i in range(len(attr_key)):
            attributes_l.append(attr_key[i] + ":" + attr_value[i])
        return attributes_l

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath(
            "//div[@class='product-info-price']//span[@data-price-type='oldPrice']//text()").get()
        current_price = response.xpath(
            "//section[contains(@class,'product-details')]//div[@class='product-price']/span/text()").get()
        items["original_price"], items["current_price"] = self.clear_price(original_price, current_price)
        if not items["current_price"]:
            return
        items["brand"] = 'PMSI'
        items["name"] = response.xpath("//h1[contains(@class,'ProductItem-details-title')]/text()").get().strip()
        items["name"] = items["name"].replace("\n",' ')
        # attributes = response.xpath("//div[@id='product-description']//li//text()").getall()
        # attributes = self.remove_space_and_filter(attributes)
        # items["attributes"] = attributes
        items["description"] = response.xpath("//section[@class='ProductItem-additional']//div[@class='sqs-block-content']//text()").getall()
        items["description"] = self.remove_space_and_filter(items["description"])
        items["description"] = ''.join(items["description"])
        items["source"] = website

        img_data = response.xpath("//div[@class='ProductItem-gallery-slides-item']/img/@data-src").getall()
        items["images"] = img_data

        cate = response.meta.get("cate")
        Breadcrumb_list = ['Shop',cate,items['name']]
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = '/'.join(Breadcrumb_list)
        sku_list = list()
        try:
            have_sku = re.search(r'"product":(.*?),"showAnnouncementBar"', response.text).group(1)
        except:
            have_sku = None
        if have_sku:
            product_str = have_sku
            product_json = json.loads(product_str)
            if len(product_json['variants']) > 1:
                for sku in product_json['variants']:
                    sku_item = SkuItem()
                    attributes = SkuAttributesItem()
                    other = dict()
                    sku_item["url"] = response.url
                    sku_item["original_price"] = sku['price']['decimalValue']
                    sku_item["current_price"] = sku['salePrice']['decimalValue']
                    if sku_item["current_price"] == '0.00':
                        sku_item["current_price"] = sku_item["original_price"]
                    sku_item["sku"] = sku["sku"]
                    try:
                        sku_item["imgs"] = sku['mainImage']['url']
                    except:
                        pass
                    for k, v in sku['attributes'].items():
                        if k == 'Size':
                            attributes['size'] = v
                        elif k == 'Color':
                            attributes['colour'] = v
                        else:
                            other[k] = v
                    if len(other) > 0:
                        attributes['other'] = other
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

        yield items
        # print(items)
        # check_item(items)
        # detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True,
        #                 skulist_attributes=True)
