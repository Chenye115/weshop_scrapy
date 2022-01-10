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

website = 'newfoundland-dog-breed-store'
# 全流程解析脚本

class newfoundland_dog_breed_store(scrapy.Spider):
    name = website
    # allowed_domains = ['newfoundland-dog-breed-store']
    start_urls = 'https://www.newfoundland-dog-breed-store.com/'


    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 6
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            # custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(newfoundland_dog_breed_store, self).__init__(**kwargs)
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
            "https://www.newfoundland-dog-breed-store.com/",
        ]
        for url in url_list:
           print(url)
           yield scrapy.Request(
              url=url,
           )

    def parse(self, response):
        url_list = response.xpath("//a[@class='dropdown-toggle']/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//h2[@class='product-name']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

    def get_attributes(self, response):
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
        original_price = response.xpath("//meta[@property='product:price:amount']/@content").get()
        current_price = response.xpath("//meta[@property='product:price:amount']/@content").get()
        items["original_price"], items["current_price"] = self.clear_price(original_price, current_price)
        if not items["current_price"]:
            return
        items["brand"] = response.xpath("//meta[@property='product:brand']/@content").get()
        if not items["brand"]:
            items["brand"] = ''
        items["name"] = response.xpath("//div[@class='product-info__title']/h1/text()").get()
        # items["attributes"] = self.get_attributes(response)
        # abt = response.xpath("").getall()
        # abt = self.remove_space_and_filter(abt)
        # items["about"] = ' '.join(abt)
        des = response.xpath("//div[@id='description']//p//text()").getall()
        des = self.remove_space_and_filter(des)
        items["description"] = ' '.join(des)
        # items["care"] = response.xpath("").get()
        # items["sales"] = response.xpath("").get()
        source = self.start_urls.split("www.")[-1].split("//")[-1].replace('/', '')
        items["source"] = source
        images_list = response.xpath("//li[contains(@class,'additionalImages')]//img/@data-src").getall()
        images_list = [response.urljoin(i) for i in images_list]
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//div[@class='breadcrumb-inner']//li//a//text()").getall()
        Breadcrumb_list.append(items['name'])
        Breadcrumb_list = self.remove_space_and_filter(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = '/'.join(Breadcrumb_list)

        sku_list = list()
        have_sku = response.xpath("//div[@class='wrapperAttribsOptions']")
        if have_sku:
            sku_dict = {}
            for skuoption in have_sku:
                sku_title = skuoption.xpath(".//label[@class='attribsSelect']/text()").get()
                sku_opts = skuoption.xpath(".//option//text()").getall()
                if not sku_title:
                    sku_title = skuoption.xpath(".//span[@class='option-label']/text()").get()
                    if not sku_title:
                        continue
                    sku_opts = skuoption.xpath(
                        ".//label[contains(@class,'product-color-name') or contains(@class,'attribsRadioButton')]/text()").getall()
                    sku_opts = self.remove_space_and_filter(sku_opts)
                sku_dict[sku_title] = sku_opts
            org_sku_list = list(self.product_dict(**sku_dict))
            for sku in org_sku_list:
                sku_item = SkuItem()
                attributes = SkuAttributesItem()
                other = dict()
                sku_item["url"] = response.url
                add_price = 0.00
                for k, v in sku.items():
                    if '+$' in v:
                        add_price += float(v.split("+$")[1].replace(")", '').strip())
                    if k == 'Size':
                        attributes["size"] = v
                    elif k == 'Color':
                        attributes["colour"] = v
                    else:
                        other[k] = v
                sku_item["original_price"] = str("{:.2f}".format(float(items["original_price"]) + add_price))
                sku_item["current_price"] = str("{:.2f}".format(float(items["current_price"]) + add_price))
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

        yield items
        # print(items)
        # check_item(items)
        # detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True,
        #                 skulist_attributes=True)
