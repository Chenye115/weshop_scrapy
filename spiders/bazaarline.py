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

website = 'bazaarline'
# 全流程解析脚本


#有SKU 无翻页
class BazaarlineSpider(scrapy.Spider):
    name = website
    allowed_domains = ['bazaarline.com']
    art_urls = ['http://www.bazaarline.com/']

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
        super(BazaarlineSpider, self).__init__(**kwargs)
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
            'http://www.bazaarline.com/',
        ]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
            )

        #url = "http://bazaarline.com/"
        #yield scrapy.Request(
        #    url=url,
        #)

    def parse(self, response):
        url_list = response.xpath("//div[@id='display_menu_2']/ul/li/a/@href").getall()
        url_list = [response.urljoin(url) for url in url_list]
        for url in url_list:
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
            )

    def parse_list(self, response):
        """列表页"""
        url_list = response.xpath("//td[@class='v65-productDisplay-cell v65-productName']/a/@href").getall()
        # for n in range(len(url_list_temp)):
        #     if(n%5==0):
        #         url=url_list_temp[n].xpath(".//td[@valign='top']/a/@href").get()
        #         print(url)
        #         url_list.append(url)
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

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url
        # price = re.findall("", response.text)[0]
        #re.search(r'"brand":"(.*?)","', response.text).group(1)
        ori=re.search(r'<div class="product_productprice">(.*?)</div>',response.text).group(1)
        original_price = response.xpath("//font[@class='text colors_text']/div[@class='product_productprice'][1]/text()").get()
        # print("1111")
        # print(ori)
        ori=ori.split("$")[-1].strip()
        # print(ori)
        # for n in range(len(original_price)):
        #     original_price[n]=self.filter_text(self.filter_html_label(original_price[n]))
        # #original_price=''.join(original_price)
        # #original_price=original_price[4]
        # current_price = response.xpath("//div[@class='product_saleprice']//text()").getall()
        #
        # if current_price:
        #     pass
        # else:
        #     current_price=original_price
        # items["original_price"] = "" + str(original_price) if original_price else "" + str(current_price)
        # items["current_price"] = "" + str(current_price) if current_price else "" + str(original_price)
        ori=self.filter_text(self.filter_html_label(ori))
        try:
            cui=re.search(r'<div class="product_saleprice">(.*?)</span>',response.text).group(1)
        except:
            #<font class="text colors_text">As Low As (R):</font> $<span itemprop='price' content='1.00'>1.00</span>
            cui=re.search(r'<font class="text colors_text">As Low As(.*?)</span>',response.text).group(1)
            #print('error')
            # print(response.url)
            # print(cui)
        # print('2222')
        # print(cui)
        cui=self.filter_text(self.filter_html_label(cui))
        # print(cui)
        cui=cui.split("$")[-1].strip()
        # print(cui)
        items["current_price"]=cui
        items["original_price"]=ori
        items["brand"] = 'bazaarline'
        items["name"] = response.xpath("//font[@class='productnamecolorLARGE colors_productname']/span/text()").get()
        attributes = list()
        #items["attributes"] = attributes
        #items["about"] = response.xpath("").get()

        des=response.xpath("//div[@id='ProductDetail_ProductDetails_div2']//text()").getall()
        des=''.join(des)
        des=self.filter_text(self.filter_html_label(des))
        items["description"] = des

        #items["care"] = response.xpath("").get()
        #items["sales"] = response.xpath("").get()
        items["source"] = 'bazaarline.com'

        images_list = response.xpath("//span[@id='altviews']/a/@href").getall()
        if images_list:
        #//img[@id='product_photo']/@src
            for n in range(0,len(images_list)):
                images_list[n]='https:'+images_list[n]
            items["images"] = images_list
        else:
            images_list = response.xpath("//img[@id='product_photo']/@src").getall()
            for n in range(0,len(images_list)):
                images_list[n]='https:'+images_list[n]
            items["images"] = images_list

        Breadcrumb_list = response.xpath("//td[@class='vCSS_breadcrumb_td']/b/a/text()").getall()
        for i in Breadcrumb_list:
            i=i.strip()
        strr='/'
        breadcrumb_list=strr.join(Breadcrumb_list)
        items["cat"] = Breadcrumb_list[-1]
        items["detail_cat"] = breadcrumb_list

        #label_list_img=response.xpath("//table[@id='options_table']/tbody/tr[2]/td[1]/a")
        label_list_value=response.xpath("//table[@id='options_table']//select/option")
        color_list=[]
        for i in label_list_value:
            #img=[]
            #img.append(label_list_img[n].xpath("./img/@src")).get()
            color=i.xpath("./text()").get()
            #color_list.append({'color':color,'img':img})
            color_list.append(color)

        print('color_list:')
        print(color_list)


        sku_list = list()
        for sku in color_list:
            sku_item = SkuItem()
            sku_item["original_price"] = items["original_price"]
            sku_item["current_price"] = items["current_price"]

            #imgs = list()
            #sku_item["imgs"] = sku['img']
            sku_item["url"] = response.url

            attributes = SkuAttributesItem()
            attributes["colour"] = sku


            sku_item["attributes"] = attributes
            sku_list.append(sku_item)

        items["sku_list"] = sku_list
        items["measurements"] = ["Weight: None", "Height: None", "Length: None", "Depth: None"]
        status_list = list()
        status_list.append(items["url"])
        #status_list.append(items["original_price"])
        #status_list.append(items["current_price"])
        status_list = [i for i in status_list if i]
        status = "-".join(status_list)
        items["id"] = md5(status.encode("utf8")).hexdigest()

        items["lastCrawlTime"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        items["created"] = int(time.time())
        items["updated"] = int(time.time())
        items['is_deleted'] = 0


        # print(items)
        # check_item(items)
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
