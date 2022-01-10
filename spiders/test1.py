# -*- coding: utf-8 -*-
import html
import re
import json
import time
import scrapy
import demjson
import requests
from hashlib import md5
from scrapy.selector import Selector
from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util import item_check
from overseaSpider.util.utils import isLinux, filter_text
from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem

website = 'beut'

class BeutSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['beut.co']
    # start_urls = ['http://beut.co/']

    @classmethod
    def update_settings(cls, settings):
        # settings.setdict(getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None) or {}, priority='spider')
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["CLOSESPIDER_ITEMCOUNT"] = 5
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            custom_debug_settings["HTTPCACHE_DIR"] = "/Users/cagey/PycharmProjects/mogu_projects/scrapy_cache"
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(BeutSpider, self).__init__(**kwargs)
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
            'https://www.beut.co.uk/furniture/living-room-hall.html',
            'https://www.beut.co.uk/furniture/dining-room-furniture.html',
            'https://www.beut.co.uk/furniture/home-office.html',
            'https://www.beut.co.uk/furniture/outdoor-furniture.html',
            'https://www.beut.co.uk/designer-wallpaper.html',
            'https://www.beut.co.uk/coordonne-core-edo-mural-wallpaper.html',
            'https://www.beut.co.uk/lighting.html',
            'https://www.beut.co.uk/homeware.html',
            'https://www.beut.co.uk/outdoor.html'
        ]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
            )

        # url = "https://www.beut.co.uk/coordonne-core-edo-mural-wallpaper.html"
        # yield scrapy.Request(
        #    url=url,
        #     callback=self.parse_detail
        # )

    def parse(self, response):
        url_list = response.xpath('//div[@class="row products-grid"]/div/a[@class="product-image"]/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )
        next_page_url = response.xpath('//a[@title="Next"]/@href').get()
        if next_page_url:
            # print("下一页:" + next_page_url)
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
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
        original_price = response.xpath('//div[@class="product-shop"]/div[@class="price-box"]//p[@class="old-price"]/span[@class="price"]/text()').get()
        if original_price:
            original_price =self.filter_text(self.filter_html_label(original_price))
        else:
            original_price = response.xpath('//div[@class="product-shop"]/div[@class="price-box"]//span[@class="regular-price"]/span[@class="price"]/text()').get()
            original_price=self.filter_text(self.filter_html_label(original_price))

        current_price= response.xpath('//div[@class="product-shop"]/div[@class="price-box"]//p[@class="special-price"]/span[@class="price"]/text()').get()
        if current_price:
            current_price=self.filter_text(self.filter_html_label(current_price))
        else:
            current_price = original_price
        items["original_price"] = original_price.replace("£","").replace(",","")
        items["current_price"] = current_price.replace("£","").replace(",","")
        brand = response.xpath('//div[@class="product-brand"]/text()').get()
        if brand:
            brand = self.filter_text(brand)
        else:
            brand = website
        items["brand"] = brand
        name = response.xpath('//div[@class="product-shop"]/div[@class="product-name"]/h1/text()').get()
        name = self.filter_text(name)
        items["name"] = name
        des = response.xpath('//dl[@id="collateral-tabs"]//text()').getall()
        # description = ''
        # for i in des:
        #     a = self.filter_text(i)
        #     if a != '':
        #         description += a
        description=self.filter_text(self.filter_html_label(' '.join(des)))
        items["description"] = description
        items["source"] = website
        images_list = response.xpath('//div[@id="amasty_gallery"]/a/@data-zoom-image').getall()
        # images_list = [response.urljoin(i) for i in images_list]
        items["images"] = images_list

        Breadcrumb_list = response.xpath('//div[@class="breadcrumbs"]/ul/li/a/text()').getall()
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = "/".join(Breadcrumb_list)


        attributes_list = list()
        tr_list = response.xpath('//div[@class="info-block features"]//tbody/tr')
        for tr in tr_list:
            k = tr.xpath("./th/text()").get()
            k = self.filter_text(k)
            v_list1 = tr.xpath("./td/text()").getall()
            v_list = []
            for i in v_list1:
              a =self.filter_text(i)
              v_list.append(a)
            v = "".join(v_list)
            attributes = k+":  "+v
            attributes_list.append(attributes)
        items["attributes"] = attributes_list

        # items["about"] = response.xpath("").get()
        # items["care"] = response.xpath("").get()
        # items["sales"] = response.xpath("").get()

        sku_list = list()
        json_all =response.xpath('//script').getall()
        sku_json =''
        sku_option = []
        for i in json_all:
            if ' AmConfigurableData' in i:
                sku_json = i.split('AmConfigurableData(')[1].split('catch(ex){}')[0].strip().strip('}').strip().strip(');')
                sku_json =demjson.decode(sku_json)
        if sku_json:
            for i in sku_json.keys():
                if type(sku_json[i]) == dict:
                    if 'price' in sku_json[i].keys():
                        di = {}
                        pri = sku_json.get(i).get('price')
                        pri = '£'+str(pri)
                        img_url = sku_json.get(i).get('media_url')
                        name = sku_json.get(i).get('name')
                        di['name'] = name
                        di['pri'] = pri
                        di['img_url'] = img_url
                        sku_option.append(di)
        if sku_option:
            for i in sku_option:
                headers = {
                    'authority': 'www.beut.co.uk',
                    'content-length': '0',
                    'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'accept': 'text/javascript, text/html, application/xml, text/xml, */*',
                    'x-prototype-version': '1.7',
                    'x-requested-with': 'XMLHttpRequest',
                    'sec-ch-ua-platform': '"macOS"',
                    'origin': 'https://www.beut.co.uk',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.beut.co.uk/flos-ic-c-w2-ceiling-wall-light-outdoor.html',
                    'accept-language': 'zh-CN,zh;q=0.9',
                    'cookie': 'frontend=7g8s7ullm60hmmr4uki1kt88h3; external_no_cache=1; _uetsid=17ca89503e1111ecb811dfbfad63af88; _uetvid=14d109c03af411ec8e5547b7995b1d22',
                }
                sku_res = requests.post(i.get('img_url'), headers=headers)
                html = Selector(text=sku_res.text)
                img = html.xpath('//div[@id="amasty_gallery"]/a/@data-zoom-image').getall()
                sku_item = SkuItem()
                sku_item["original_price"] = i.get('pri').replace("£","")
                sku_item["current_price"] = i.get('pri').replace("£","")
                sku_item["inventory"] = None
                sku_item["imgs"] = img
                sku_item["url"] = response.url
                sku_item["sku"] = i.get('name')
                attributes = SkuAttributesItem()
                other = dict()
                other['option'] = i.get('name')
                attributes["other"] = other
                sku_item["attributes"] = attributes
                sku_list.append(sku_item)


        #for sku in original_sku_list:


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
        #
        # detection_main(
        #     items=items,
        #     website=website,
        #     num=self.settings["CLOSESPIDER_ITEMCOUNT"],
        #     skulist=True,
        #     skulist_attributes=True)
        # print(items)
        # item_check.check_item(items)
        yield items
