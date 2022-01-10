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

website = 'bellstudios242'
# 全流程解析脚本

class bellstudios242(scrapy.Spider):
    name = website
    # allowed_domains = ['bellstudios242']
    start_urls = 'http://bellstudios242.com/'


    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 2
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            # custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(bellstudios242, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "流冰")
        self.headers={"cookie":"current_cur=EUR"}
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
        # 洗列表
        new_l = []
        for i,j in enumerate(l):
            k = self.filter_html_label(j)
            if k == '' or k == '/' or k == '>':
                continue
            new_l.append(k)
        return new_l

    def remove_space_and_filter2(self,l):
        # 洗文本
        new_l = []
        for i,j in enumerate(l):
            k = self.filter_html_label(j)
            if k == '':
                continue
            if not k.strip().endswith('.') and not k.strip().endswith(':') and not k.strip().endswith(',') \
                    and not k.strip().endswith('?') and not k.strip().endswith('!'):
                k = k+'.'
            new_l.append(k)
        return new_l


    def start_requests(self):
        url_list = [
            "http://bellstudios242.com/",
        ]
        for url in url_list:
           print(url)
           yield scrapy.Request(
               url=url,
               headers=self.headers
           )

    def parse(self, response):
        url_list = response.xpath("//li[contains(@id,'menu-item-')]/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                headers=self.headers
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//div[@class='product-item item-sp']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                headers=self.headers
            )

        next_page_url = response.xpath("//a[@class='next page-numbers']/@href").getall()
        if next_page_url:
            next_page_url = next_page_url[0]
            next_page_url = response.urljoin(next_page_url)
            print("下一页:"+next_page_url)
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_list,
                headers=self.headers
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
        # original_price = response.xpath("//div[@class='oldprice']/span/text()").get()
        # current_price = response.xpath("//div[@class='newprice']/span/text()").get()
        original_price = response.xpath("//form[@id='form_singleProduct']//input[@name='_price']/@value").get()
        current_price = response.xpath("//form[@id='form_singleProduct']//input[@name='_salePrice']/@value").get()
        items["original_price"], items["current_price"] = self.clear_price(original_price, current_price,'€')
        if items["original_price"] == '0.00' or items["original_price"] == '0':
            items["original_price"] = items["current_price"]
        if not items["current_price"]:
            return
        items["brand"] = 'jamscrib.com'
        if not items["brand"]:
            items["brand"] = ''
        items["name"] = response.xpath("//title/text()").get()
        items["name"] = items["name"].split('-')[0].strip()
        des = response.xpath("//div[contains(@class,'item-details')]//div[@class='wrap-content']//li//text()").getall()
        des = self.remove_space_and_filter2(des)
        items["description"] = ''.join(des)
        items["source"] = 'bellstudios242.com'
        images_list = response.xpath("//div[@class='itemadapslider_gallery']//img/@data-lazy").getall()
        if len(images_list) == 0:
            images_list = response.xpath("//div[@class='itemadapslider_gallery']//img/@src").getall()
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//div[@class='breadcrumbs']//a/text()").getall()
        Breadcrumb_list.append(items['name'])
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = '/'.join(Breadcrumb_list)

        sku_list = list()
        try:
            sku_index = re.search(r'window\.sku\s=(.*?);', response.text).group(1)
            sku_all = re.search(r'window\.skuAttr\s=(.*?)};', response.text).group(1)
            sku_index_json = json.loads(sku_index)
            sku_all_json = json.loads(sku_all + '}')
        except:
            sku_index_json = {}
            sku_all_json = {}

        if len(sku_all_json) > 1:
            for sku_k, sku_v in sku_all_json.items():
                sku_item = SkuItem()
                attributes = SkuAttributesItem()
                other = dict()
                sku_item["url"] = response.url
                sku_id_list = sku_k.split(";")
                sku_item["original_price"] = sku_v["price"].replace("€", '').replace("US", '').strip()
                sku_item["current_price"] = sku_v["salePrice"].replace("€", '').replace("US", '').strip()
                if sku_item["original_price"] == '0.00':
                    sku_item["original_price"] = sku_item["current_price"]
                if sku_v["quantity"] and sku_v["quantity"] != '':
                    sku_item["inventory"] = int(sku_v["quantity"])
                sku_item["sku"] = sku_k
                for id in sku_id_list:
                    sku_i = sku_index_json[id]
                    if sku_i['prop_title'] == 'Color':
                        attributes["colour"] = sku_i['title']
                        img = str(sku_i['img']).replace("\\", '').strip()
                        if img != '' and len(img) > 20:
                            sku_item["imgs"] = [img]
                    elif 'Size' in sku_i['prop_title']:
                        attributes["size"] = sku_i['title']
                    else:
                        other[sku_i['prop_title']] = sku_i['title']
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

        # yield items
        print(items)
        check_item(items)
        detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True,
                        skulist_attributes=True)
