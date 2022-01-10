# -*- coding: utf-8 -*-
import re

import demjson
import requests
from overseaSpider.util.scriptdetection import detection_main
import time
import json
import scrapy
from hashlib import md5
from copy import deepcopy
from overseaSpider.util.utils import isLinux
from scrapy.selector import Selector
from overseaSpider.util.item_check import check_item

from overseaSpider.items import ShopItem, SkuItem, SkuAttributesItem
from lxml import etree

website = 'elago'

class OverseaSpider(scrapy.Spider):
    name = website
    # start_urls = ['http://elago.com']


    @classmethod
    def update_settings(cls, settings):
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug', False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(OverseaSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "彼得")
        self.headers = {
  'authority': 'www.galleryatthepark.org',
  'cache-control': 'max-age=0',
  'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"Windows"',
  'upgrade-insecure-requests': '1',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'navigate',
  'sec-fetch-user': '?1',
  'sec-fetch-dest': 'document',
  'referer': 'https://www.galleryatthepark.org/adult-workshops',
  'accept-language': 'zh-CN,zh;q=0.9',
  'cookie': 'crumb=BXDuttEyu9JzOTk4MzhmYTFjMmE3YzYwODFjMjM5MTIwZDcyYzZm; ss_cvr=e00a7097-f852-40a8-b2ac-9946ede16818|1639894502220|1639894502220|1639900123364|2; ss_cvt=1639900123364',
  'if-none-match': 'W/"24b7d6786c7228b68090f816f328adbc--gzip"'
}


    is_debug = True
    custom_debug_settings = {
        # 'CLOSESPIDER_ITEMCOUNT': 5,  # 检测个数
        'MONGODB_COLLECTION': website,
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'DEBUG',
        'COOKIES_ENABLED': False,
        # 'HTTPCACHE_EXPIRATION_SECS': 14 * 24 * 60 * 60, # 秒
        'DOWNLOADER_MIDDLEWARES': {
            #'overseaSpider.middlewares.PhantomjsUpdateCookieMiddleware': 543,
            #'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },

    }
    def filter_text(self, input_text):
        input_text = re.sub(r'[\t\n\r\f\v]', ' ', input_text)
        input_text = re.sub(r'<.*?>', ' ', input_text)
        filter_list = [u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000-', u'\u200a',
                       u'\u2028', u'\u2029', u'\u202f', u'\u205f', u'\u3000', u'\xA0', u'\u180E',
                       u'\u200A', u'\u202F', u'\u205F','\r\n\r\n','**','>>','\\n\\t\\t',', ','\\n        ',
                       '\\n\\t  ','\\xa0','>']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text

    def start_requests(self):
        url_list = ["https://www.elago.com/new-products",
                    "https://www.elago.com/phone-accessories",
                    "https://www.elago.com/apple-tv",
                    "https://www.elago.com/apple-watch-strap",
                    "https://www.elago.com/magsafe",
                    "https://www.elago.com/m-stand_iphone",
                    "https://www.elago.com/mount",
                    "https://www.elago.com/macbook",
                    "https://www.elago.com/car-mount",
                    "https://www.elago.com/stylus-grip  ",
                    "https://www.elago.com/desk-collection",
                    ]
        for url in url_list:
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                headers=self.headers,
            )

    # def parse(self, response):
    #     """主页"""
    #     # json_data = json.loads(response.text)
    #     # json_data = defaultdict(lambda: None, json_data)
    #     url_list = response.xpath('//div[@class="sqs-block-content"]/div/figure/a/@href').getall()
    #     url_list = [response.urljoin(url) for url in url_list]
    #     for url in url_list:
    #         # url = url + "?sortBy=newest&page=1"
    #         # print(url)
    #         # url = "https://www.romanchic.com/category/romanchic/100/"
    #         yield scrapy.Request(
    #             url=url,
    #             callback=self.parse_list,
    #             headers=self.headers,
    #         )

    def parse_list(self, response):
        """商品列表页"""
        detail_url_list = response.xpath('//div[@class="ProductList-grid clear"]/div/a/@href').getall()
        # if not detail_url_list:
        #     detail_url_list = response.xpath("//div[@class='tovarphoto']/a/@href").getall()
        # detail_url_list = [response.urljoin(url) for url in detail_url_list]
        if detail_url_list:
            # print(f"当前商品列表页有{len(detail_url_list)}条数据")
            # detail_url = "https://www.saje.com/natural-mists/"
            for detail_url in detail_url_list:
                # if not detail_url == "https://www.saje.com/natural-mists/":
                detail_url = response.urljoin(detail_url)
                # detail_url = "https://www.newbreedfurniture.com/shelving/wall-mounted-shelving"
                # print("详情页url:"+detail_url)
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail,
                    headers=self.headers,
                )


            # base_url = response.url.split("&start=")[0]
            # page_id = int(response.url.split("&start=")[1]) + 48
            # next_page_url = base_url + "&start=" + str(page_id)
            # if next_page_url:
            #     next_page_url = response.urljoin(next_page_url)
            #     # print("下一页:" + next_page_url)
            #     yield scrapy.Request(
            #         url=next_page_url,
            #         callback=self.parse_list,
            #         headers=self.headers,
            #     )
            # else:
            #   print(f"商品列表页无数据!:{response.url}")

            # next_page_url = response.xpath("//li[@class='page-item page-item--next']/a/@href").get()
            # if next_page_url:
            #     next_page_url = response.urljoin(next_page_url)
            #     # print("下一页:"+next_page_url)
            #     yield scrapy.Request(
            #         url=next_page_url,
            #         headers=self.headers,
            #         callback=self.parse_list,
            #     )

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        # print(response.text)
        # judge_1 = response.xpath('//div[@class="pdpcta-btns"]/div/a/text()').getall()
        # # if not judge_1:
        # #     judge_1 = response.xpath("//div[@class='product-detail-block']/div[@class='product-price order-item-price ptwotext ']/span[@class='price-sales ']/text()").getall()
        # print(judge_1)
        # judge_1 = str(judge_1).replace(" ", "")
        # judge_2 = response.xpath("//div[@class='cfp']/h2/text()").getall()
        # judge_2 = str(judge_2).replace(" ", "")
        # # # judge_2 = str(judge_2).replace(" ", "")
        # judge_3 = []
        # judge_3_list = response.xpath("//td[@align='center']/img/@src").getall()
        # judge_3 = response.xpath("//div[@class='image-gallery__hero']/img/@src").getall()
        # judge_4 = response.xpath("//div[@class='purchase-info']/div[@class='pre-order-coming-soon']/img/@src").getall()
        # for i in judge_3_list:
        #     i = "http:" + i
        #     judge_3.append(i)
        # # judge_4_list = response.xpath("//div[@class='row pdp__pricing']/div[@class='col']/span[@class='price  price--fullprice  i-sale-price']/text()").getall()
        # # judge_4 = "".join(judge_4_list)
        # print(judge_3)
        # if "Make A Trade" in judge_1:
        #     if not "CallforPricing" in judge_2:
        #         if not "/assets/img/no-product-image.6e2fe503eb36ed9453c761807b64ffcf.svg" in judge_3:
        #             if not "/assets/img/coming-soon.1d4bb2875a17e008864583ffb095b8bb.svg" in judge_4:

        # brand = response.xpath('//meta[@itemprop="brand"]/@content').get()
        # if brand == "_":
        #     brand = ""
        # if not brand:
        #     brand = response.xpath("//div[@class='proLogo']/span/text()").get()
        # brand = brand.split(":")[0]
        # brand_list = re.findall('"brand":.*?name": "(.*?)"',response.text,re.S)
        brand_list = re.findall('"brand":"(.*?)"', response.text)
        brand = "".join(brand_list)
        # brand_all = response.xpath("//div[@class='productdetail product annex-cloud']/@data-productdetails").get()
        # brand = re.findall('"brand":"(.*?)","category"', brand_all)
        # print(brand)
        items["brand"] = brand
        # print(brand)
        name = response.xpath('//section[@class="ProductItem-details"]/h1/text()').get()
        name = name.replace("\n", "").replace("\xa0", "").replace("\u200b","").replace("    ","").replace("\u3000","")
        items["name"] = name

        # original_price = []
        # original_price_list = response.xpath('//div[@class="price"]//span[@class="older-price"]//span[@class="minmaxprice"]/text()').getall()
        # for i in original_price_list:
        #     i = self.filter_text(i)
        #     # i = i.replace("￥","")
        #     original_price.append(i)

        current_price_list = []
        current_price_list_all = response.xpath('//div[@class="product-price"]/span/text()').getall()
        for i in current_price_list_all:
            i = self.filter_text(i)
            current_price_list.append(i)
        current_price = "".join(current_price_list)

        current_price = current_price.replace(" ", "").replace("*","").replace("$","").replace(",","")
        current_price = current_price.replace("\n", "")
        current_price = current_price.replace("/", "")
        current_price = current_price.replace("от", "")
        current_price = current_price.replace("\xa0", "")
        # print(current_price)

        # if  original_price_list:
        #     original_price_str = "".join(original_price_list)
        #     original_price = original_price_str.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")
        #     original_price = original_price.replace("/", "").replace("\xa0", "").replace("*", "").replace("$","").replace(",","")
        # else:
        #     original_price = current_price
        original_price = current_price


        detail_cat = []
        detail_cat_all = response.xpath('//div[@class="ProductItem-nav-breadcrumb"]/a/text()').getall()
        # # if not detail_cat_all:
        # #     detail_cat_all = response.xpath("//ul[@class='bx-breadcrumb breadcrumbs']//span/text()").getall()

        for i in detail_cat_all:
            i = self.filter_text(i)
            # i.replace("\u3000","")
            detail_cat.append(i)

        s1 = "/"
        detail_cat = s1.join(detail_cat)
        # items["detail_cat"] = "Home" + "/" + name
        # items["detail_cat"] = detail_cat + "/" + name
        items["detail_cat"] = detail_cat
        # items["detail_cat"] = "BRANDS" + "/" + detail_cat
        # items["detail_cat"] = "Home" + "/" + detail_cat + "/" + name
        items["cat"] = name

        images_list = []
        images_list_1 = response.xpath('//div[@class="ProductItem-gallery-slides"]/div/img/@data-src').getall()
        # images_list_1 = re.findall("data-images='\[\"(.*?)\"\]'",response.text)
        # images_list_1 = images_list_1.split('\",\"')
        # if not images_list_1:
        #     # images_list_1 = response.xpath("//picture[@class='o-picture js-mainImage']/img/@src").getall()
        #     images_list_1 = re.findall("Square&quot;:&quot;(.*?)&quot;",response.text)
        # if images_list_1:
        for i in images_list_1:
            if not i in images_list:
                images_list.append(i)

        # images_list_2 = response.xpath("//div[@class='gt_item-detail gt_clearfix']/div[@class='gt_detail_image']//ul[@class='gt_scroll-list gt_slide-inner']/li//img/@data-original").getall()
        # for i in images_list_2:
        #     # i = "https:" + i
        #     # if "," in i:
        #     #     i = i.split(",")[0]
        #     # i = "http://www.statue.com" + i
        #     # i = i.replace("\\", "")
        #     # i = i.replace("\",\"","\',\'")
        #     # i = i.split(",")[0]
        #     # if not "svg" in images_list:
        #     if not i in images_list:
        #         images_list.append(i)


        # page = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
        # # print(page)
        # if page:
        #     json_data = json.loads(page)
        #     len_image = len(json_data["props"]["pageInfo"]["data"]["product"]["images"])
        #     # print(len_image)
        #     for i in range(0,len_image):
        #         images_list_2 = json_data["props"]["pageInfo"]["data"]["product"]["images"][i]["src"]["original"]
        #         images_list.append(images_list_2)

        # images_list_2 = response.xpath("//div[@class='image-gallery__thumbnails']/a/img/@data-src").getall()
        # for j in images_list_2:
        #     # j = "https:" + j
        #     # if not "gif" in j:
        #     #     if not "VIDEO" in j:
        #     j = j.replace("-45","-800")
        #     if not "svg" in j:
        #         if not j in images_list:
        #             images_list.append(j)
        items["images"] = images_list

        items["url"] = response.url
        items["original_price"] = str(original_price)
        items["current_price"] = str(current_price)
        items["source"] = "elago.com"


        # judge = response.xpath("//div[@class='ec-base-button btnArea']/span//text()").getall()
        descripiton = []
        description_1 = response.xpath('//div[@class="ProductItem-details-excerpt"]//text()').getall()
        # if not description_1:
        #     description_1 = response.xpath("//div[@class='product-description__text']//text()").getall()
        # if not description_1:
        #     description_1 = response.xpath("(//div[@class='uk-width-1-1']/div[@class='uk-panel']/article)[2]/p//text()").getall()
        # if not description_1:
        #     description_1 = response.xpath("//div[@id='divTabOzellikler']/div[@class='urunTabAlt']/ul/li//text()").getall()

        # if not description_1:
        #     description_1 = response.xpath("//div[@class='product-short-description']/div/text()").getall()
        # if not description_1:
        #     description_1 = response.xpath("//div[@class='product-short-description']/h4/text()").getall()
        for i in description_1:
            # if not ("SOLD OUT" == judge):
               i = self.filter_text(str(i)).replace("\\","")
               descripiton.append(i)
        # description_2 = response.xpath("//div[@class='product attribute description']//p//text()").getall()
        # for j in description_2:
        #     # if not ("SOLD OUT" == judge):
        #     j = self.filter_text(str(j))
        #     descripiton.append(j)
        items["description"] = "".join(descripiton)
        # if not description_1:
        #     print(response.url)
        # print(descripiton)

        sku_list = list()
        page = response.xpath('//div[@class="product-variants"]/@data-variants').get()
        if page:
            json_data = json.loads(page)
            for i in range(0, len(json_data)):
                other_dic = {}
                for key in json_data[i]["attributes"].keys():
                    sth_name = key
                    sth_id = json_data[i]["attributes"][key]
                    other = {f'{sth_name}': sth_id}
                    other_dic.update(other)

                price = json_data[i]["priceMoney"]["value"]
                sku_item = SkuItem()
                sku_item["original_price"] = price
                sku_item["current_price"] = price
                sku_item["url"] = response.url
                sku_item["imgs"] = []

                attributes = SkuAttributesItem()
                attributes["other"] = other_dic
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

        # detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True,
        #                skulist_attributes=True)

        # print(items)
        # check_item(items)
        yield items
