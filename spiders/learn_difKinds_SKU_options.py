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

website = 'holdupdisplays'
# 全流程解析脚本

class holdupdisplays(scrapy.Spider):
    name = website
    # allowed_domains = ['holdupdisplays']
    start_urls = 'https://www.holdupdisplays.com/'


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
        super(holdupdisplays, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "流冰")
        self.headers={'cookie': 'SHOP_SESSION_TOKEN=uug6o6tfhsbg08b4goobub5qtn; fornax_anonymousId=f22c9c42-993e-4fa8-b89e-92bce6e1912c; XSRF-TOKEN=d34ce0e67a2f8866000b6eb6056ae43bdc5bf3f0b47ab7db103b9533d38d27ec; _shg_user_id=33365d66-fc4b-44e0-8355-efa41325104f; _gcl_au=1.1.458256647.1640095586; _gid=GA1.2.1716548032.1640095586; STORE_VISITOR=1; zHello=1; _fbp=fb.1.1640095592079.2104128411; _shg_session_id=dc13ed1c-fbe0-41c9-bcc6-bf7adf8bca14; lastVisitedCategory=31; _ga_ZG9KQBTXXT=GS1.1.1640099471.2.1.1640099751.0; _ga=GA1.2.1640718728.1640095574; __atuvc=3%7C51; __atuvs=61c1eee21255532b001; zCountry=CN; Shopper-Pref=EBEF6C744D117FEE71C5A68535FCE43C011D17FD-1640704593020-x%7B%22cur%22%3A%22USD%22%7D', 'origin': 'https://www.holdupdisplays.com', 'pragma': 'no-cache', 'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'stencil-config': '{}', 'stencil-options': '{"render_with":"products/bulk-discount-rates"}', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36', 'x-requested-with': 'XMLHttpRequest', 'x-xsrf-token': 'd34ce0e67a2f8866000b6eb6056ae43bdc5bf3f0b47ab7db103b9533d38d27ec, d34ce0e67a2f8866000b6eb6056ae43bdc5bf3f0b47ab7db103b9533d38d27ec'}

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
            "https://www.holdupdisplays.com/",
        ]
        for url in url_list:
           print(url)
           yield scrapy.Request(
              url=url,
           )

    def parse(self, response):
        url_list = [
            'https://www.holdupdisplays.com/walnut-gun-wall-bundle-hd103-bw/',
            'https://www.holdupdisplays.com/products/category/gun-racks',
            'https://www.holdupdisplays.com/handgun/',
            'https://www.holdupdisplays.com/archery-racks/',
            'https://www.holdupdisplays.com/misc/',
        ]
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        cate =response.xpath("//h1[@class='page-heading']/text()").get()
        url_list = response.xpath("//h4[@class='card-title']/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={"cate":cate}
            )

        next_page_url = response.xpath("//li[@class='pagination-item pagination-item--next']/a/@href").getall()
        if next_page_url:
            next_page_url = next_page_url[0]
            next_page_url = response.urljoin(next_page_url)
            print("下一页:"+next_page_url)
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_list,
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
            "//div[@class='productView-price']//span[@class='price price--rrp']/text()").get()
        if not original_price or original_price.strip() == '':
            original_price = response.xpath(
                "//div[@class='productView-price']//span[@class='price price--non-sale']/text()").get()
        current_price = response.xpath(
            "//div[@class='productView-price']//span[@class='price price--withoutTax']/text()").get()
        items["original_price"], items["current_price"] = self.clear_price(original_price, current_price)
        if not items["current_price"]:
            return
        items["brand"] = response.xpath("//h2[@class='productView-brand']//span/text()").get()
        if not items["brand"]:
            items["brand"] = ''
        items["name"] = response.xpath("//h1[@class='productView-title']//text()").get()
        # items["attributes"] = self.get_attributes(response)
        # items["about"] = response.xpath("").get()
        des = response.xpath(
            "//div[@id='tab-description']//text()").getall()
        des = self.remove_space_and_filter(des)
        items["description"] = ''.join(des)
        source = self.start_urls.split("www.")[-1].split("//")[-1].replace('/', '')
        items["source"] = source
        images_list = response.xpath("//a[@class='productView-thumbnail-link']/@href").getall()
        items["images"] = images_list

        cate =response.meta.get("cate")
        Breadcrumb_list =['Home',cate]
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = '/'.join(Breadcrumb_list)

        sku_list = list()
        sku_options = response.xpath(
            "//div[contains(@class,'productView-options')]//form[@enctype='multipart/form-data']//div[contains(@class,'form-field')]")
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
                    sku_variant_name_list = sku_option.xpath(".//label[@for]//text()").getall()  # 选项名列表
                    sku_variant_name_list = self.remove_space_and_filter(sku_variant_name_list)
                    if len(sku_variant_name_list) == 0:
                        sku_variant_name_list = sku_option.xpath(".//label/span/@title").getall()
                        sku_variant_name_list = self.remove_space_and_filter(sku_variant_name_list)
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
            if len(org_sku_list) > 0 and len(org_sku_list) <= 50:
                for sku in org_sku_list:
                    post_url = 'https://www.holdupdisplays.com/remote/v1/product-attributes/{}'.format(product_id)
                    post_data = {
                        'action': 'add',
                        'product_id': product_id,
                        'qty[]': 1
                    }
                    sku_item = SkuItem()
                    other = dict()
                    attributes = SkuAttributesItem()
                    sku_item["url"] = response.url
                    for sku_i in sku.values():
                        post_data[sku_i[0]] = sku_i[1]
                    # post_res = scrapy.Request(post_url,body=json.dumps(post_data),method='POST')
                    post_res = requests.post(post_url, data=post_data, headers=self.headers)
                    post_res_json = json.loads(post_res.text)
                    #
                    sku_data = post_res_json["data"]
                    try:
                        org_price = str(sku_data["price"]["rrp_without_tax"]["value"])
                    except:
                        org_price = None
                    cur_price = str(sku_data["price"]["without_tax"]["value"])
                    if not org_price:
                        org_price = cur_price
                    sku_item["original_price"] = str(org_price)
                    sku_item["current_price"] = str(cur_price)
                    if sku_data["sku"] and sku_data["sku"] != 'null':
                        sku_item["sku"] = sku_data["sku"]
                    try:
                        img = sku_data['image']["data"]
                        sku_item["imgs"] = [img.replace("{:size}", '1280x1280')]
                    except:
                        pass
                    for k, v in sku.items():
                        if 'ize' in k:
                            attributes["size"] = v[2]
                        elif 'olo' in k:
                            attributes['colour'] = v[2]
                        else:
                            other[k] = v[2]
                    if len(other) > 0:
                        attributes["other"] = other
                    if len(attributes) > 0:
                        sku_item["attributes"] = attributes
                        sku_list.append(sku_item)
            elif len(org_sku_list) > 0 and len(org_sku_list) > 50:
                for sku in org_sku_list:
                    sku_item = SkuItem()
                    other = dict()
                    attributes = SkuAttributesItem()
                    sku_item["url"] = response.url
                    sku_item["original_price"] = items["original_price"]
                    sku_item["current_price"] = items["current_price"]
                    for k, v in sku.items():
                        if 'ize' in k:
                            attributes["size"] = v[2]
                        elif 'olo' in k:
                            attributes['colour'] = v[2]
                        else:
                            other[k] = v[2]
                    if len(other) > 0:
                        attributes["other"] = other
                    if len(attributes) > 0:
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
