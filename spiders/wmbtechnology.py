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

website = 'wmbtechnology'
# 全流程解析脚本

class WmbtechnologySpider(scrapy.Spider):
    name = website
    allowed_domains = ['wmbtechnology.com']
    start_urls = ['https://wmbtechnology.com/']

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
        super(WmbtechnologySpider, self).__init__(**kwargs)
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
            'https://wmbtechnology.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://wmbtechnology.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//div[@class='mainmenu']/ul/li/a/@href").getall()
        url_list.pop(0)
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        #没有翻页
        url_list = response.xpath("//div[@class='catalog_one active js-list_product']/div/a/@href").getall()
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
        #next_page_url = response.xpath("").get()
        #if next_page_url:
        #   next_page_url = response.urljoin(next_page_url)
        #    print("下一页:"+next_page_url)
        #    yield scrapy.Request(
        #        url=next_page_url,
        #        callback=self.parse_list,
        #    )

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
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        original_price = response.xpath("//form[@id='form_singleProduct']/input[@name='_price_nc']/@value").get()
        if original_price:
            original_price=original_price.split("$")[-1]
        current_price = response.xpath("//form[@id='form_singleProduct']/input[@name='_salePrice_nc']/@value").get()
        if current_price:
            current_price=current_price.split("$")[-1]
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        items["brand"] = 'wmbtechnology.com'
        items["name"] = response.xpath("//h1[@itemprop='name']/text()").get()

        #tab_bodies
        des = response.xpath("//div[@class='tab_bodies']/div[1]//text()").getall()
        # print(des)
        des=des[:-5]
        des=' '.join(des)
        des=self.filter_text(self.filter_html_label(des)).replace("_","")
        items["description"]=des

        items["source"] = 'wmbtechnology.com'
        images_list = response.xpath("//div[@class='img_scroller']/div/span/img/@data-src-desctop").getall()
        items["images"] = images_list

        Breadcrumb_list = response.xpath("//div[@class='breadcrumbs']//a/text()").getall()
        br='/'.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = br

        sku_list = list()
        color_dic={}
        type_dic={}
        have_sku = response.xpath("//div[@class='js-product-sku product-sku js-empty-sku-view']/div/div[1]/text()").getall()
        sku_option_list_choose = response.xpath("//div[@class='js-product-sku product-sku js-empty-sku-view']/div")
        print(have_sku)
        if len(have_sku)>0:
            print('hassku')
            sku_dict = {}
            for i in range(len(have_sku)):
                sku_option_list = sku_option_list_choose[i].xpath("./div[2]/div/span")
                if sku_option_list:
                    sku_opts=[]
                    sku_title = have_sku[i].strip()
                    if 'olor'  in sku_title:
                        for n in range(len(sku_option_list)):
                            color_name=sku_option_list[n].xpath("./img/@title").get()
                            color_img=sku_option_list[n].xpath("./img/@data-img").getall()
                            if color_img:
                                color_dic.update({color_name:color_img})
                            sku_opts.append(color_name)
                        sku_dict[sku_title] = sku_opts
                    elif 'ype' in sku_title:
                        for n in range(len(sku_option_list)):
                            color_name=sku_option_list[n].xpath("./img/@title").get()
                            color_img=sku_option_list[n].xpath("./img/@data-img").getall()
                            if color_img:
                                type_dic.update({color_name:color_img})
                            sku_opts.append(color_name)
                        sku_dict[sku_title] = sku_opts
                    else:
                        for n in range(len(sku_option_list)):
                            opts=sku_option_list[n].xpath("./@data-title").get()
                            sku_opts.append(opts)
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
                    if 'olor' in k:
                        attributes["colour"] = v
                        sku_item['imgs']=color_dic[v]
                    elif 'ize' in k:
                        attributes["size"] = v
                    elif 'ype' in k:
                        other[k] = v
                        sku_item['imgs']=type_dic[v]
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
        #     num=5,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)
