# -*- coding: utf-8 -*-
import itertools
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

website = 'elitecoreaudio'

class ElitecoreaudioSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['elitecoreaudio.com']
    # start_urls = ['http://elitecoreaudio.com/']

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
        super(ElitecoreaudioSpider, self).__init__(**kwargs)
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
        'authority': 'elitecoreaudio.com',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'stencil-config': '{}',
        'x-xsrf-token': '1a1d31f656b4208d1bddc726086463d673ea869b9ba6ab827136b46ec46090f9',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'accept': '*/*',
        'x-requested-with': 'XMLHttpRequest',
        'stencil-options': '{"render_with":"products/bulk-discount-rates"}',
        'sec-ch-ua-platform': '"macOS"',
        'origin': 'https://elitecoreaudio.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://elitecoreaudio.com/elite-core-supercat6-quad-reel-rugged-shielded-super-cat6-quad-solid-conductor-cable-on-heavy-duty-reel/',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': 'SHOP_SESSION_TOKEN=sfgc8apk5ob88p8mh2cpjm6hpg; fornax_anonymousId=987cbf88-2d75-40ea-a8aa-64d40f5cf17d; XSRF-TOKEN=1a1d31f656b4208d1bddc726086463d673ea869b9ba6ab827136b46ec46090f9; ajs_user_id=null; ajs_group_id=null; ajs_anonymous_id=%2230763836-1e1e-4dcf-a1d5-318447414481%22; _gcl_au=1.1.1824874214.1640770426; _shg_user_id=111d2e26-588b-4738-8b1d-0d07b30384db; soundestID=20211229093345-zqXGXBdX2LPmoGQYPZU1C1N34f33ac3o9HVSsaffVlJPREs6j; omnisendAnonymousID=dW6bbiAwj4ZUaU-20211229093345; soundest-cart=%7B%22lastProductsCount%22%3A0%7D; STORE_VISITOR=1; _ga=GA1.2.665847567.1640770427; _gid=GA1.2.1641378554.1640770427; _fbp=fb.1.1640770428607.105528205; _shg_session_id=fe31e6c1-8c76-4817-b5fc-03c794a142fb; omnisendSessionID=oj8alGLMgQcUSW-20211229102107; lastVisitedCategory=641; __atuvc=3%7C52; __atuvs=61cc37c38b539d27001; soundest-views=11; Shopper-Pref=2FA84D5113979E3FF8926A44DA9414D3729ABF90-1641378441436-x%7B%22cur%22%3A%22USD%22%7D; _gali=attribute_select_5556',
    }
    def product_dict(self, **kwargs):
        keys = kwargs.keys()
        vals = kwargs.values()
        for instance in itertools.product(*vals):
            yield dict(zip(keys, instance))
    def start_requests(self):
        url_list = [
            'https://elitecoreaudio.com/'
        ]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
            )

        # url = "https://elitecoreaudio.com/elite-core-supercat6-quad-reel-rugged-shielded-super-cat6-quad-solid-conductor-cable-on-heavy-duty-reel/"
        # yield scrapy.Request(
        #    url=url,
        #    callback=self.parse_detail
        # )

    def parse(self, response):
        url_list = response.xpath('//ul[@class="navPages-list navPages-list--categories"]/li//a/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath('//div[@class="products-list row"]//a[@class="product-item-photo"]/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        if url_list:
            for url in url_list:
                # print(url)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )

            # split_str = ''
            # base_url = response.url.split(split_str)[0]
            # page_num = int(response.url.split(split_str)[1])+1
            # next_page_url = base_url + split_str + str(page_num)
        next_page_url = response.xpath('//link[@rel="next"]/@href').get()
        if next_page_url:
           next_page_url = response.urljoin(next_page_url)
           # print("下一页:"+next_page_url)
           yield scrapy.Request(
               url=next_page_url,
               callback=self.parse_list,
           )

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
        original_price = response.xpath(
            '//div[@class="productView-price"]//span[@class="price price--non-sale"]/text()').get()
        current_price = response.xpath(
            '//div[@class="productView-price"]//span[@class="price price--withoutTax"]/text()').get()
        current_price = self.filter_html_label(current_price)
        original_price = self.filter_html_label(original_price)
        if '-' in current_price:
            current_price = current_price.split('-')[0]
            current_price = self.filter_html_label(current_price)
        if original_price:
            if original_price!='None':
                original_price = self.filter_html_label(original_price)
            else:
                original_price = current_price
        else:
            original_price = current_price
        original_price = original_price.replace(',', '')
        current_price = current_price.replace(',', '')
        if '$' in original_price:
            original_price = original_price.strip('$')
            original_price = self.filter_html_label(original_price)
        if '$' in current_price:
            current_price = current_price.strip('$')
            current_price = self.filter_html_label(current_price)
        items["original_price"] = original_price
        items["current_price"] = current_price
        brand = response.xpath('//h6[@class="product-brand"]/text()').get()
        if brand:
            brand = self.filter_html_label(brand)
        else:
            brand = ''
        items["brand"] = brand
        name = response.xpath('//h1[@class="productView-title"]/text()').get()
        name = self.filter_html_label(name)
        items["name"] = name
        des = response.xpath('//div[@id="tab-description"]//text()').getall()
        description = ''
        for i in des:
            a = self.filter_html_label(i)
            if a != '':
                description =description+'  '+a
        description = description.strip('  ')
        items["description"] = description
        items["source"] = 'elitecoreaudio.com'
        images_list = response.xpath('//div[@class="productView-thumbnails"]/div/a/@data-image-gallery-zoom-image-url').getall()
        # images_list = [response.urljoin(i) for i in images_list]
        items["images"] = images_list

        Breadcrumb_list1 = response.xpath('//ul[@class="breadcrumb "]/li/a/text()').getall()
        Breadcrumb_list = []
        for i in Breadcrumb_list1:
            a = self.filter_html_label(i)
            if a:
                Breadcrumb_list.append(a)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = "/".join(Breadcrumb_list)


        # tr_list = response.xpath('')
        # if tr_list:
        #     attributes_list = list()
        #     for tr in tr_list:
        #         k = tr.xpath("./th/text()").get()
        #         k = self.filter_html_label(k)
        #         v_list1 = tr.xpath("./td/text()").getall()
        #         v_list = []
        #         for i in v_list1:
        #           a =self.filter_html_label(i)
        #           v_list.append(a)
        #         v = "".join(v_list)
        #         attributes = k+""+v
        #         attributes_list.append(attributes)
        #     items["attributes"] = attributes_list

        # items["about"] = response.xpath("").get()
        # items["care"] = response.xpath("").get()
        # items["sales"] = response.xpath("").get()

        sku_list = list()
        sku_options = response.xpath(
            "//div[contains(@class,'productView-options')]//form[@enctype='multipart/form-data']//div[@class='form-field']")
        sku_dict = {}
        if sku_options:
            for sku_option in sku_options:
                l = []
                # 取sku种类名字
                sku_opt_name = sku_option.xpath(
                    "./label[@class='form-label form-label--alternate form-label--inlineSmall']/text()[1]").get()
                if sku_opt_name:
                    sku_opt_name = sku_opt_name.strip()
                else:
                    continue
                if sku_opt_name.endswith(":"):
                    sku_opt_name = sku_opt_name[:-1]
                # 取attribute[]值
                sku_opt_attr_name = sku_option.xpath(".//select/@name").get()
                if not sku_opt_attr_name:
                    # 说明选项不是select
                    sku_variant_name_list1 = sku_option.xpath(".//label[@for]//text()").getall()  # 选项名列表
                    sku_variant_name_list = []
                    for i in sku_variant_name_list1:
                        a = self.filter_html_label(i)
                        if a:
                            sku_variant_name_list.append(a)
                    if len(sku_variant_name_list) == 0:
                        sku_variant_name_list1 = sku_option.xpath(".//label/span/@title").getall()
                        sku_variant_name_list = []
                        for i in sku_variant_name_list1:
                            a = self.filter_html_label(i)
                            if a:
                                sku_variant_name_list.append(a)
                    # print(sku_variant_name_list)
                    sku_opts = sku_option.xpath(".//input[@value and not(@value='')]")
                    for i, sku_opt in enumerate(sku_opts):
                        # print(i)
                        sku_opt_attr_name = sku_opt.xpath("./@name").get()
                        sku_attr_id = sku_opt.xpath("./@value").get()
                        sku_name = sku_variant_name_list[i]
                        l.append((sku_opt_attr_name, sku_attr_id, sku_name))
                    if len(l) > 0:
                        sku_dict[sku_opt_name] = l
                else:
                    sku_opts = sku_option.xpath(".//option[@value and not(@value='')]")
                    for sku_opt in sku_opts:
                        sku_attr_id = sku_opt.xpath("./@value").get()
                        sku_name = sku_opt.xpath("./text()").get()
                        l.append((sku_opt_attr_name, sku_attr_id, sku_name))
                    if len(l) > 0:
                        sku_dict[sku_opt_name] = l

            org_sku_list = list(self.product_dict(**sku_dict))
            product_id = response.xpath(
                "//div[contains(@class,'productView-options')]//input[@name='product_id']/@value").get()
            sku_url = 'https://elitecoreaudio.com/remote/v1/product-attributes/' + product_id
            post_data = {
                'action': 'add',
                'product_id': product_id,
                'qty[]': '1'
            }
            if org_sku_list:
                for temp in org_sku_list:
                    size = ''
                    color = ''
                    other_dic = {}
                    for i in temp.keys():
                        att_name = temp.get(i)[0]
                        att_values = temp.get(i)[1]
                        post_data[att_name] = att_values
                        if 'Size' in i:
                            size = temp.get(i)[2]
                        elif 'Color' in i:
                            color = temp.get(i)[2]
                        else:
                            k = i
                            v = temp.get(i)[2]
                            other_dic[k] = v
                    sku_res = requests.post(sku_url, headers=self.headers, data=post_data)
                    sku_res = sku_res.json().get('data')
                    pri = sku_res.get('price').get('without_tax').get('formatted')
                    pri = self.filter_html_label(pri)
                    pri = pri.replace(',', '')
                    if '$' in pri:
                        pri = pri.strip('$')
                        pri = self.filter_html_label(pri)
                    ori = ''
                    if 'non_sale_price_without_tax' in sku_res.get('price').keys():
                        ori = sku_res.get('price').get('non_sale_price_without_tax').get('formatted')
                    if ori:
                        ori = self.filter_html_label(ori)
                        ori = ori.replace(',', '')
                        if '$' in ori:
                            ori = ori.strip('$')
                            ori = self.filter_html_label(ori)
                    else:
                        ori = pri
                    sku_item = SkuItem()
                    sku_item["original_price"] = ori
                    sku_item["current_price"] = pri
                    sku_item["imgs"] = []
                    sku_item["url"] = response.url
                    attributes = SkuAttributesItem()
                    if color:
                        attributes["colour"] = color
                    if size:
                        attributes["size"] = size
                    if other_dic:
                        attributes["other"] = other_dic
                    sku_item["attributes"] = attributes
                    sku_list.append(sku_item)
        #for sku in original_sku_list:
            # sku_item = SkuItem()
            # sku_item["original_price"] = item["original_price"]
            # sku_item["current_price"] = item["current_price"]
            # sku_item["inventory"] = sku["inventory"]
            # sku_item["sku"] = sku["sku"]
            # imgs = list()
            # sku_item["imgs"] = imgs
            # sku_item["url"] = response.url
            # sku_item["sku"] = sku
            # attributes = SkuAttributesItem()
            # attributes["colour"] = sku["name"]
            # attributes["size"] = sku["size"]
            # other = dict()
            # attributes["other"] = other
            # sku_item["attributes"] = attributes
            # sku_list.append(sku_item)

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
