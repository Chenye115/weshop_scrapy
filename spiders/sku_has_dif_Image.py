# -*- coding: utf-8 -*-
import re
import json
import time
import html
import scrapy
import demjson
import requests
from hashlib import md5
from scrapy.selector import Selector
from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util import item_check
from overseaSpider.util.utils import isLinux, filter_text
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'birddogsnguns'

class BirddogsngunsSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['birddogsnguns.com']
    # start_urls = ['http://birddogsnguns.com/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 4
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(BirddogsngunsSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "汀幡")

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
            #'overseaSpider.middlewares.AiohttpMiddleware': 543,
            #'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },
        'HTTPCACHE_POLICY': 'overseaSpider.middlewares.DummyPolicy',
    }
    def filter_html_label(self,text):
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

    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://birddogsnguns.com/index.php?main_page=index&cPath=1',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    def start_requests(self):
        url_list = [
            'https://birddogsnguns.com/index.php?main_page=index&cPath=1',
            'https://birddogsnguns.com/index.php?main_page=index&cPath=2'
        ]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
                headers=self.headers
            )

        # url = "https://birddogsnguns.com/index.php?main_page=product_info&cPath=1&products_id=2"
        # yield scrapy.Request(
        #    url=url,
        #    callback=self.parse_detail,
        #     headers=self.headers
        # )

    def parse(self, response):
        url_list = response.xpath('//td[@class="productListing-data"]/a/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                headers=self.headers
            )

    # def parse_list(self, response):
    #     """列表页"""
    #     url_list = response.xpath("").getall()
    #     url_list = [response.urljoin(url) for url in url_list]
    #     if url_list:
    #         for url in url_list:
    #             print(url)
    #             yield scrapy.Request(
    #                 url=url,
    #                 callback=self.parse_detail,
    #             )

            # split_str = ''
            # base_url = response.url.split(split_str)[0]
            # page_num = int(response.url.split(split_str)[1])+1
            # next_page_url = base_url + split_str + str(page_num)
            # next_page_url = response.xpath("").get()
            # if next_page_url:
            #    next_page_url = response.urljoin(next_page_url)
            #    print("下一页:"+next_page_url)
            #    yield scrapy.Request(
            #        url=next_page_url,
            #        callback=self.parse_list,
            #    )

    def parse_detail(self, response):
        """详情页"""
        # res = requests.get(sku_url)
        # sku_res = Selector(text=res.text)
        # title = response.xpath("//meta[@property='og:title']/@content").get()
        # description = response.xpath("//meta[@property='og:description']/@content").get()
        # image = response.xpath("//meta[@property='og:image']/@content").get()

        items = ShopItem()
        items["url"] = response.url
        #json_str = response.xpath('//script[@type="application/ld+json"]/text()').get()
        #json_data = json.loads(json_str)
        #brand = json_data["brand"]["name"]
        #price = json_data["offers"]["price"]
        #description = json_data["description"]
        # re.findall("", response.text)[0]
        original_price = response.xpath('//h2[@id="productPrices"]/span[@class="productBasePrice"]/text()').get()
        if original_price:
            original_price = self.filter_html_label(original_price)
            original_price = original_price.replace(',', '')
            if '$' in original_price:
                original_price = original_price.strip('$')
                original_price = self.filter_html_label(original_price)
            current_price = original_price
            items["original_price"] = original_price
            items["current_price"] = current_price
            items["brand"] = ''
            name = response.xpath('//h1[@id="productName"]/text()').get()
            name = self.filter_html_label(name)
            items["name"] = name
            des = response.xpath('//div[@id="productDescription"]//text()').getall()
            description = ''
            for i in des:
                a = self.filter_html_label(i)
                if a != '':
                    description += a
            items["description"] = description
            items["source"] = 'birddogsnguns.com'
            js_all =response.xpath('//script/text()').getall()
            images_list = []
            for i in js_all:
                if 'img src="images' in i:
                    a = i.split('img src="')[1].split('"')[0]
                    a = 'https://birddogsnguns.com/'+a
                    if a not in images_list:
                        images_list.append(a)
                        break
            # images_list = [response.urljoin(i) for i in images_list]
            items["images"] = images_list

            Breadcrumb_list = response.xpath('//div[@id="navBreadCrumb"]/a/text()').getall()
            items["cat"] = name
            detail_cat = "/".join(Breadcrumb_list)
            detail_cat = detail_cat+'/'+name
            items["detail_cat"] = detail_cat


            # attributes_list = list()
            # tr_list = response.xpath("")
            # for tr in tr_list:
            #     k = tr.xpath("./th/text()").get()
            #     k = self.filter_text(k)
            #     v_list1 = tr.xpath("./td/text()").getall()
            #     v_list = []
            #     for i in v_list1:
            #       a =self.filter_text(i)
            #       v_list.append(a)
            #     v = "".join(v_list)
            #     attributes = k+""+v
            #     attributes_list.append(attributes)
            # items["attributes"] = attributes_list

            # items["about"] = response.xpath("").get()
            # items["care"] = response.xpath("").get()
            # items["sales"] = response.xpath("").get()

            sku_list = list()
            sku_optionAll =response.xpath('//div[@class="attribBlock"]//div[@class="back"]//label')
            sku_option = {}
            if sku_optionAll:
                for i in sku_optionAll:
                    a = i.xpath('./text()').get()
                    a = self.filter_html_label(a)
                    b = i.xpath('./img/@src').get()
                    if b:
                        b = 'https://birddogsnguns.com/' +b
                    sku_option[a]=b
            if sku_option:
                for keys,values in sku_option.items():
                    pri = current_price
                    if '$' in keys:
                        pri_temp = keys.split('$')[1].split(')')[0]
                        pri_temp = self.filter_html_label(pri_temp)
                        pri_temp = pri_temp.replace(',','')
                        pri_temp = float(pri_temp)

                        pri = str(float(current_price)+pri_temp)
                    imgs = []
                    if values:
                        imgs.append(values)
                    sku_item = SkuItem()
                    sku_item["original_price"] = pri
                    sku_item["current_price"] = pri
                    sku_item["imgs"] = imgs
                    sku_item["url"] = response.url
                    sku_item["sku"] = keys
                    attributes = SkuAttributesItem()
                    other = dict()
                    other['option'] = keys
                    attributes["other"] = other
                    sku_item["attributes"] = attributes
                    sku_list.append(sku_item)

            # size_list = response.xpath("").getall()
            # color_list = response.xpath("").getall()
            # if size_list:
            #     for size in size_list:
            #         if color_list:
            #             for color in color_list:
            #                 sku_item = SkuItem()
            #                 sku_item["original_price"] = items["original_price"]
            #                 sku_item["current_price"] = items["current_price"]
            #                 attributes = SkuAttributesItem()
            #                 attributes["colour"] = color
            #                 attributes["size"] = size
            #                 other = dict()
            #                 attributes["other"] = other
            #                 sku_item["attributes"] = attributes
            #                 sku_list.append(sku_item)
            #         else:
            #             sku_item = SkuItem()
            #             sku_item["original_price"] = items["original_price"]
            #             sku_item["current_price"] = items["current_price"]
            #             attributes = SkuAttributesItem()
            #             attributes["size"] = size
            #             other = dict()
            #             attributes["other"] = other
            #             sku_item["attributes"] = attributes
            #             sku_list.append(sku_item)
            # else:
            #     if color_list:
            #         for color in color_list:
            #             sku_item = SkuItem()
            #             sku_item["original_price"] = items["original_price"]
            #             sku_item["current_price"] = items["current_price"]
            #             attributes = SkuAttributesItem()
            #             attributes["colour"] = color
            #             other = dict()
            #             attributes["other"] = other
            #             sku_item["attributes"] = attributes
            #             sku_list.append(sku_item)

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

            # item_check.check_item(items)
            # detection_main(
            #     items=items,
            #     website=website,
            #     num=self.settings["CLOSESPIDER_ITEMCOUNT"],
            #     skulist=True,
            #     skulist_attributes=True)
            # print(items)
            yield items
