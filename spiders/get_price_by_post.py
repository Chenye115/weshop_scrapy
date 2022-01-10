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

website = 'indoboard'

class IndoboardSpider(scrapy.Spider):
    name = website
    # allowed_domains = ['indoboard.com']
    # start_urls = ['http://indoboard.com/']

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
        super(IndoboardSpider, self).__init__(**kwargs)
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
        'authority': 'www.indoboard.com',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'stencil-config': '{}',
        'x-xsrf-token': '56b309cbc1eb4c79fd7282f5e54ee48e8e9235e341a49d6232e8fb917ee16000',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'stencil-utils',
        'stencil-options': '{"render_with":"products/bulk-discount-rates"}',
        'sec-ch-ua-platform': '"macOS"',
        'accept': '*/*',
        'origin': 'https://www.indoboard.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.indoboard.com/original-flo-deck-and-cushion/',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': 'SHOP_SESSION_TOKEN=uqutrnemk6a2pne3copfn1vnne; fornax_anonymousId=be1d89d3-1429-4eec-834a-7e5d53d9b0a0; XSRF-TOKEN=56b309cbc1eb4c79fd7282f5e54ee48e8e9235e341a49d6232e8fb917ee16000; ajs_user_id=null; ajs_group_id=null; ajs_anonymous_id=%222744e7f3-4525-473a-a3f9-69345e47a72a%22; _ga=GA1.2.2003874330.1640850082; _gid=GA1.2.878252227.1640850082; Fera.Api.ServerNum=1; banana_stand_visitor_id=9511e038-3197-4a3f-afd1-13d605b63f03; STORE_VISITOR=1; SL_C_23361dd035530_VID=sr8-E1qtMN; SL_C_23361dd035530_KEY=a21f14fcc3de54dfdc27a12e3934d9a6b239668b; SL_C_23361dd035530_SID=pmW-Z3jXnJ; _fbp=fb.1.1640850683405.1737835813; tracker_device=5778acd2-2c8d-47ea-90dd-51402c6de6a2; lastVisitedCategory=255; __kla_id=eyIkcmVmZXJyZXIiOnsidHMiOjE2NDA4NTAwOTMsInZhbHVlIjoiaHR0cDovLzIwLjgxLjExNC4yMDg6ODAwMC8iLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cuaW5kb2JvYXJkLmNvbS8ifSwiJGxhc3RfcmVmZXJyZXIiOnsidHMiOjE2NDA4NTEzMTcsInZhbHVlIjoiaHR0cDovLzIwLjgxLjExNC4yMDg6ODAwMC8iLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cuaW5kb2JvYXJkLmNvbS8ifX0=; __atuvc=2%7C52; __atuvs=61cd65071e8e4487001; Shopper-Pref=0A75BAFE5E15E58DBEC217046ED7057F5BA51866-1641456118278-x%7B%22cur%22%3A%22USD%22%7D; _gali=attribute_swatch_215_547',
    }
    def product_dict(self, **kwargs):
        keys = kwargs.keys()
        vals = kwargs.values()
        for instance in itertools.product(*vals):
            yield dict(zip(keys, instance))
    def start_requests(self):
        url_list = [
            'https://www.indoboard.com/'
        ]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
            )

        # url = "https://www.indoboard.com/mini-kicktail-deck/"
        # yield scrapy.Request(
        #    url=url,
        #    callback=self.parse_detail
        # )

    def parse(self, response):
        url_list = response.xpath('//ul[@class="navPages-list"]/li[position()<3]//a/@href').getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            # print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath('//ul[@class="productGrid"]/li//figure[@class="card-figure"]/a/@href').getall()
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
        original_price = response.xpath('//div[@class="productView-price"]//span[@class="price price--rrp"]/text()').get()
        current_price = response.xpath(
            '//div[@class="productView-price"]//span[@class="price price--withoutTax"]/text()').get()
        current_price = self.filter_html_label(current_price)
        original_price = self.filter_html_label(original_price)
        if 'From' in original_price:
            original_price = original_price.strip('From')
            original_price = self.filter_html_label(original_price)
        if 'From' in current_price:
            current_price = current_price.strip('From')
            current_price = self.filter_html_label(current_price)
        if '-' in current_price:
            current_price = current_price.split('-')[0]
            current_price = self.filter_html_label(current_price)
        if original_price:
            if original_price != 'None':
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
        brand = response.xpath('//h2[@class="productView-brand"]/a/span/text()').get()
        if brand:
            brand = self.filter_html_label(brand)
        else:
            brand = ''
        items["brand"] = brand
        name = response.xpath('//h1[@class="productView-title"]/text()').get()
        name = self.filter_html_label(name)
        items["name"] = name
        des = response.xpath('//div[@class="short-description full"]//text()').getall()
        description = ''
        for i in des:
            a = self.filter_html_label(i)
            if a != '':
                description = description + '  ' + a
        description = description.strip('  ')
        items["description"] = description
        items["source"] = 'indoboard.com'
        images_list = response.xpath('//ul[@class="productView-thumbnails"]/li/a/@data-image-gallery-zoom-image-url').getall()
        if images_list:
            images_list = images_list
        else:
            images_list = response.xpath('//div[@class="productViewImage"]//figure[@class="productView-image"]/@data-zoom-image').getall()
        # images_list = [response.urljoin(i) for i in images_list]
        items["images"] = images_list

        Breadcrumb_list = response.xpath('//ol[@class="breadcrumbs"]/li/a/span/text()').getall()
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
            sku_url = 'https://www.indoboard.com/remote/v1/product-attributes/' + product_id

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
                    imgs = []
                    if 'image' in sku_res.keys():
                        img = sku_res.get('image')
                        if img:
                            if 'data' in img.keys():
                                img = img.get('data').replace('{:size}', '1280x1280')
                                imgs.append(img)
                    pri = sku_res.get('price').get('without_tax').get('formatted')
                    pri = self.filter_html_label(pri)
                    pri = pri.replace(',', '')
                    if '$' in pri:
                        pri = pri.strip('$')
                        pri = self.filter_html_label(pri)
                    ori = ''
                    if 'rrp_without_tax' in sku_res.get('price').keys():
                        ori = sku_res.get('price').get('rrp_without_tax').get('formatted')
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
                    sku_item["imgs"] = imgs
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
