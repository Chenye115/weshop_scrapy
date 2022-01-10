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

website = 'novanatural'
# 全流程解析脚本

class NovanaturalSpider(scrapy.Spider):
    name = website
    allowed_domains = ['novanatural.com']
    start_urls = ['https://www.novanatural.com/']

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
        super(NovanaturalSpider, self).__init__(**kwargs)
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
            'https://www.novanatural.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://novanatural.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//a[@class='header-menu-level2-anchor']")
        #url_list = [response.urljoin(url) for url in url_list]
        for url_item in url_list:
            url=url_item.xpath("./@href").get()
            url=response.urljoin(url)
            cata=url_item.xpath("./text()").get()
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                meta={'cata':cata},
            )

    def parse_list(self, response):
        cata=response.meta.get('cata')
        #网站没有翻页
        """列表页"""
        url_list = response.xpath("//div[@class='facets-items-collection-view-cell-span3']//a[@class='facets-item-cell-grid-link-image']/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={'cata':cata},
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

    def parse_detail(self, response):
        cata=response.meta.get('cata')
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]

        current_price = response.xpath("//span[@class='product-views-price-lead']//text()").getall()
        current_price=''.join(current_price)
        current_price=self.filter_text(self.filter_html_label(current_price))
        if "$" in current_price:
            current_price.replace("$","")
        current_price=current_price.split("$")[1]
        current_price=current_price.split(" ")[0]
        original_price = response.xpath("//small[@class='product-views-price-old']/text()").get()
        if original_price:
            original_price=original_price
        else:
            original_price=current_price
        if "$" in original_price:
            original_price=original_price.split("$")[-1]
        items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        items["brand"] = ''
        items["name"] = response.xpath("//h1[@class='product-details-full-content-header-title']/text()").get()

        attributes = []
        attr_list = response.xpath("//div[@class='product-details-information-additional-information']/div")
        for attr in attr_list:
            attr_key = attr.xpath("./b/text()").get()
            attr_value = attr.xpath("./text()").get()
            attributes.append(self.filter_html_label(attr_key)+self.filter_html_label(attr_value))
        items["attributes"] = attributes

        #items["about"] = response.xpath("").get()
        des=response.xpath("//div[@class='product-details-information-content-container']//text()").getall()
        des=''.join(des)
        des=self.filter_text(self.filter_html_label(des))
        items["description"] =des




        Breadcrumb_list = response.xpath("//ul[@class='global-views-breadcrumb']/li//text()").getall()
        for n in range(len(Breadcrumb_list)):
            Breadcrumb_list[n]=Breadcrumb_list[n].strip()
        breadcrumb='/'.join(Breadcrumb_list)
        breadcrumb=self.filter_text(self.filter_html_label(breadcrumb))
        items["cat"] = cata
        items["detail_cat"] = Breadcrumb_list[0]+'/'+cata

        sku_list = list()
        url_api='https://www.novanatural.com/'+response.xpath("//body/img[1]/@src").get()
        response_api=requests.get(url_api)
        sku_detail=json.loads(response_api.text)
        print(sku_detail)


        items["source"] = 'novanatural.com'

        images_list=[]
        # images=sku_detail['items'][0]['itemimages_detail']['urls']
        p=str(sku_detail['items'][0]['itemimages_detail'])
        # print('p'+p)
        # print(p)
        find=re.findall(r"'url': '(.*?)'}",p)
        # print('555')
        # print(images)
        # print(find)
        # for key in images:
        #     print(key)
        #     image=key['url']
        #     images_list.append(image)

        items["images"] = find

        if isinstance(sku_detail['items'][0],dict)==True:
            option_list=sku_detail['items'][0]
            # print(111,option_list)
            # try :
            if 'matrixchilditems_detail' in option_list.keys():
                option_choose=option_list['matrixchilditems_detail'],
                print('hassku')
                option_choose_list=option_choose
                # print(type(option_choose_list))
                option_choose_list=list(option_choose_list)
                # print(type(option_choose_list))
                # print('222')
                # print(option_choose_list)
                option_choose_list=option_choose_list[0]
                # print(option_choose_list)
                for i in option_choose_list:
                    print('333')
                    print(i)
                    print('333')
                    sku_item = SkuItem()
                    print(i['onlinecustomerprice_detail']['onlinecustomerprice'])
                    sku_price=str(i['onlinecustomerprice_detail']['onlinecustomerprice'])
                    sku_item["original_price"] = sku_price
                    sku_item["current_price"] = sku_price

                    sku_item["sku"] = i['itemid']

                    sku_item["url"] = response.url

                    attributes = SkuAttributesItem()
                    if 'custitem_color' in i.keys():
                        attributes["colour"] = i['custitem_color']
                    if 'custitem_size' in i.keys():
                        attributes["size"] = i['custitem_size']
                    if 'custitem_option' in i.keys():
                        other=dict()
                        other.update({'custitem_option':i['custitem_option']})
                        attributes["other"] = other
                    # if i['custitem_color']:
                    #     print('has color')
                    #     attributes["colour"] = i['custitem_color']
                    #
                    # else:
                    #     if i['custitem_size']:
                    #         print('has size')
                    #         attributes["size"] = i['custitem_size']
                    #     else:
                    #         if i['custitem_option']:
                    #             other=dict()
                    #             other.update({'custitem_option':i['custitem_option']})
                    #         else:
                    #             print('yyy')

                    sku_item["attributes"] = attributes
                    sku_list.append(sku_item)


            # except Exception as ex:
            #     print('444')
            #     print(ex)
            #     pass


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
        #
        # detection_main(
        #     items=items,
        #     website=website,
        #     num=10,
        #     skulist=True,
        #     skulist_attributes=True,
        # )
        # print(items)
