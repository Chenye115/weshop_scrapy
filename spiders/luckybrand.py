# -*- coding: utf-8 -*-
import re
import requests
from overseaSpider.util.scriptdetection import detection_main
import time
import json
import scrapy
from hashlib import md5
from copy import deepcopy
from overseaSpider.util.utils import isLinux
from scrapy.selector import Selector


from overseaSpider.items import ShopItem, SkuItem, SkuAttributesItem
from lxml import etree

website = 'luckybrand'

class OverseaSpider(scrapy.Spider):
    name = website
    # start_urls = ['https://www.luckybrand.com/']


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
  'authority': 'search.ullapopken.com',
  'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
  '_ffo': 'aHR0cHM6Ly93d3cudWxsYXBvcGtlbi5jb20=',
  '_fft': '376402932471690',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
  '365a6e6255567049784e': 'RwizSMZwAr30LHkIgYw5ILmVmhsBLDKQ3fYD7veo1Ji8W7ONQuusUPBtFA99GL, QpK6X9ZC1QxkNcvysbzAchgi49PfhYKOa7CU37j1Hs5N8tYqq3LXDeSM2WCy3g',
  'accept': 'application/json',
  'sec-ch-ua-mobile': '?0',
  '3965466e48766e774e41': '0.6310120250066094',
  '494a323349726f754263': 'ZsP3Y26ci7NepkhOsX6ci7NeQAY13yKNga5DpkhOsXXv4C8S9y9UtM',
  'sec-ch-ua-platform': '"Windows"',
  'origin': 'https://www.ullapopken.com',
  'sec-fetch-site': 'same-site',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.ullapopken.com/',
  'accept-language': 'zh-CN,zh;q=0.9',
  'Cookie': 'JSESSIONID=1488CF6BF37C01FE8F1872395902DCB5'
}


    is_debug = True
    custom_debug_settings = {
        # 'CLOSESPIDER_ITEMCOUNT': 10,  # 检测个数
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
                       u'\u200A', u'\u202F', u'\u205F','\r\n\r\n','/','**','>>','\\n\\t\\t',', ','\\n        ',
                       '\\n\\t  ','\\xa0','>']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text

    def start_requests(self):
        url_list = ["https://www.luckybrand.com/jeans?page=999",
                    "https://www.luckybrand.com/womens?page=999",
                    "https://www.luckybrand.com/mens?page=999",
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
    #     url_list = response.xpath("//div[@id='sgTilesContent']//a/@href").getall()
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
        detail_url_list = response.xpath("//div[@class='product-tile__media-container component-overlay component-overlay--center']/a/@href").getall()
        # detail_url_list = [response.urljoin(url) for url in detail_url_list]
        if detail_url_list:
            # print(f"当前商品列表页有{len(detail_url_list)}条数据")
            # detail_url = "https://www.saje.com/natural-mists/"
            for detail_url in detail_url_list:
                # if not detail_url == "https://www.saje.com/natural-mists/":

                detail_url = response.urljoin(detail_url)
                # detail_url = "https://www.luckybrand.com/mid-rise-sweet-straight/7W12559.html"
                # print("详情页url:"+detail_url)
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail,
                    headers=self.headers,
                )

            # base_url = response.url.split("?p=")[0]
            # page_id = int(response.url.split("?p=")[1]) + 1
            # next_page_url = base_url + "?p=" + str(page_id)
            # if next_page_url:
            #     next_page_url = response.urljoin(next_page_url)
            #     # print("下一页:" + next_page_url)
            #     yield scrapy.Request(
            #         url=next_page_url,
            #         callback=self.parse_list,
            #         headers=self.headers,
            #     )
        # else:
        #     print(f"商品列表页无数据!:{response.url}")

        # next_page_url = response.xpath(
        #     "//li[@class='c-pgn__item c-pgn__item--next-page c-pgn__item--hasdots-left']/a/@href").get()
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
        # judge_1 = response.xpath("//div[@class='image-gallery__hero']/a/img/@src").getall()
        # # if not judge_1:
        # #     judge_1 = response.xpath("//div[@class='product-detail-block']/div[@class='product-price order-item-price ptwotext ']/span[@class='price-sales ']/text()").getall()
        # # print(judge_1)
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
        # if not "https://img.ebyrcdn.net/1014369-1145152-800.jpg" in judge_1:
        #     if not "CallforPricing" in judge_2:
        #         if not "/assets/img/no-product-image.6e2fe503eb36ed9453c761807b64ffcf.svg" in judge_3:
        #             if not "/assets/img/coming-soon.1d4bb2875a17e008864583ffb095b8bb.svg" in judge_4:

        # brand = response.xpath("//div[@class='vendor__body d-flex align-items-center rounded-10']//strong/text()").get()
    #     if brand == "_":
    #         brand = ""
        # if not brand:
        #     brand = response.xpath("//div[@class='proLogo']/span/text()").get()
        # brand = brand.split(":")[0]
        # brand_list = re.findall('"brand":.*?name": "(.*?)"',response.text,re.S)
        brand_list = re.findall('"brand":"(.*?)","category"', response.text)
        brand = "".join(brand_list)
        # brand_all = response.xpath("//div[@class='productdetail product annex-cloud']/@data-productdetails").get()
        # brand = re.findall('"brand":"(.*?)","category"', brand_all)
        # brand = "".join(brand)
        # brand = ""
        # print(brand)
        items["brand"] = brand
        # print(brand)
        name = response.xpath("//div[@class='pdp-main__section gutter--small-only-normal']/h1/text()").get()
        name = name.replace("\n", "").replace("\xa0", "").replace("\u200b","").replace("    ","")
        items["name"] = name


        original_price = []
        original_price_list = response.xpath("//div[@class='price flex--inline flex-flow-wrap']/span[@class='price__original text-decoration--strike strike-through list']/span/text()").getall()
        for i in original_price_list:
            i = self.filter_text(i)
            # i = i.replace("US","")
            original_price.append(i)


        # original_price_list = response.xpath("//div[@class='row pdp__pricing']/div[@class='col']/span[@class='price price--rrp i-rrp-price']/text()").getall()
        # current_price = response.xpath("//div[@class='price-list']/span[@class='price price--highlight']/text()").get()
        # if not current_price:
        #     current_price = response.xpath("//div[@class='price-list']/span[@class='price']/text()").get()

        current_price_list = []
        current_price_list_all = response.xpath("(//div[@class='price flex--inline flex-flow-wrap']/span[@class='price__sales sales']/span)[1]/text()").getall()
        # if not current_price_list_all:
        #     current_price_list_all = response.xpath("//div[@class='product-header__price-info']//div[@class='product-price-panel__price-wrap']/div[@class='product-price-panel__price']/text()").getall()
        # current_price_list = str(current_price_list).replace(" ", "")
        for i in current_price_list_all:
            i = self.filter_text(i)
            # i = i.replace("US","")
            current_price_list.append(i)
        current_price = "".join(current_price_list)
        # current_price = current_price_str.replace(" ", "").replace("\n", "").replace("/", "")
        #     current_price = "$" + current_price.split("$")[1]
        # else:
        #     current_price = "".join(current_price_list)

        # current_price_str = "".join(current_price_list)
        # current_price = current_price_str.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")
        # current_price = current_price.replace("/", "").replace("\xa0","").replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")
        # current_price = "$" + current_price.split("$")[-1]

        current_price = current_price.replace(" ", "").replace("*","").replace("$","")
        current_price = current_price.replace("\n", "")
        current_price = current_price.replace("/", "")
        current_price = current_price.replace("от", "")
        current_price = current_price.replace("\xa0", "")
        # print(current_price)

        # if "." in current_price:
        #     current_price_new = current_price.replace(".", ",")  # 1,099,95
        #     current_price_1 = current_price_new.split(",")[0]  # 1
        #     current_price_2 = current_price_new.split(",")[1]  # 099
        #     current_price_3 = current_price_new.split(",")[2]  # 95
        #     # print(current_price_1)
        #     # print(current_price_2)
        #     # print(current_price_3)
        #     current_price = current_price_1 + "," + current_price_2 + "." + current_price_3
        # else:
        #     current_price = current_price.replace(",", ".")
        # current_price = "₽" + current_price.split("₽")[-1]
        # current_price = current_price + "€"



        if  original_price_list:
            original_price_str = "".join(original_price_list)
            original_price = original_price_str.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")
            original_price = original_price.replace("/", "").replace("\xa0", "").replace("*", "").replace("$","")
            # if "~" in original_price:
            #     original_price = original_price.split("~")[1]
            # else:
            #     original_price = original_price.split(":")[1]
            # print(original_price)
            # if original_price == "":
            #     original_price = current_price
            # if "." in original_price:
            #     original_price_new = original_price.replace(".", ",")  # 1,099,95
            #     original_price_1 = original_price_new.split(",")[0]  # 1
            #     original_price_2 = original_price_new.split(",")[1]  # 099
            #     original_price_3 = original_price_new.split(",")[2]  # 95
            #     original_price = original_price_1 + "," + original_price_2 + "." + original_price_3
            # else:
            #     original_price = original_price.replace(",", ".")
            # original_price = "₽" + original_price.split("₽")[-1]
            # for i in original_price_list:
            #     if i:
            #         original_price = i.replace(" ","")
            #         original_price = original_price.replace("\n","")
        else:
            original_price = current_price
        # original_price = current_price

        # detail_cat = response.xpath("//ul[@class='breadcrumbs p-0 text-left mb-3']/li/a/text()").getall()

        detail_cat = []
        detail_cat_all = response.xpath("//div[@class='pdp__breadcrumbs gutter--small-only-normal display--small-up']/ol/li/a/text()").getall()
        # # if not detail_cat_all:
        # #     detail_cat_all = response.xpath("//ul[@class='bx-breadcrumb breadcrumbs']//span/text()").getall()

        for i in detail_cat_all:
            i = self.filter_text(i)
            detail_cat.append(i)

        s1 = "/"
        detail_cat = s1.join(detail_cat)
        # items["detail_cat"] = "Home" + "/" + name
        items["detail_cat"] = detail_cat + "/" + name
        # items["detail_cat"] = detail_cat
        # items["detail_cat"] = "BRANDS" + "/" + detail_cat
        # items["detail_cat"] = "Home" + "/" + detail_cat + "/" + name
        items["cat"] = name

        # items["detail_cat"] = ''
        # items["cat"] = ''

        # images_list_all = re.findall('"img":"(.*?)","', response.text)
        #
        # images_list_1 = []
        # images_list = []
        #
        # for i in images_list_all:
        #     i = i.replace("\\", "")
        #     if not "h/q" in i:
        #         images_list_1.append(i)
        # for j in images_list_1:
        #     if not j in images_list:
        #         images_list.append(j)




        # images_list = response.xpath("//div[@class='swiper-wrapper']/a[@class='swiper-slide']/@href").getall()
        # items["images"] = images_list
        images_list = []
        # images_list_1 = response.xpath("//div[@class='owl-carousel thumbs-slider']/div/img/@src").getall()
        # for image in images_list_1:
        #     image = "https://www.krasotkapro.ru" + image
        #     image = image.replace("86x86","440x440")
        #     images_list.append(image)

        images_list_1 = response.xpath("//ul[@class='product-gallery product-gallery--pdp slider--pre-layout-1 slider--arrows-inner slider--arrows-center slider--dots-inner list--reset']/li/button/img/@src").getall()
        # images_list_1 = re.findall("data-images='\[\"(.*?)\"\]'",response.text)
        # images_list_1 = images_list_1.split('\",\"')
        # if not images_list_1:
        #     # images_list_1 = response.xpath("//picture[@class='o-picture js-mainImage']/img/@src").getall()
        #     images_list_1 = re.findall("Square&quot;:&quot;(.*?)&quot;",response.text)
        # if images_list_1:
        for i in images_list_1:
            # i = "https:" + i
            # if "," in i:
            #     i = i.split(",")[0]
            # i = "http://www.statue.com" + i
            # i = i.replace("\\", "")
            # i = i.replace("\",\"","\',\'")
            # i = i.split(",")[0]
            # if not "svg" in images_list:
            if not i in images_list:
                images_list.append(i)

        # if not images_list_1:
        #     images_list_1 = response.xpath("//div[@class='prodetailUpRImg']/img/@src").getall()
        #     for image_1 in images_list_1:
        #         image_2 = "https://www.mmoga.net" + image_1
        #         image = image_2.split(";")[0]
        #         image = image + "." + image_2.split(".")[3]
        #         # r = requests.get(image)
        #         # if r.status_code == 404:
        #         #     image = image + ".png"
        #         images_list.append(image)


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

        # sku_judge = response.xpath("//td[@class='label']/label/text()").get()
        # if sku_judge:
        #     images_list_2 = response.xpath("//div[@class='jet-woo-product-gallery__image-item']//a[@class='jet-woo-product-gallery__image-link ']/@href").getall()
        # else:
        #     images_list_2 = response.xpath("//div[@class='jet-woo-product-gallery__image ']/a[@class='jet-woo-product-gallery__image-link ']/@href").getall() #无sku多图
        #     if not images_list_2:
        #         images_list_2 = response.xpath("//div[@class='jet-woo-product-gallery-grid col-row']//div[@class='jet-woo-product-gallery__image jet-woo-product-gallery__image--with-zoom']/a[@class='jet-woo-product-gallery__image-link ']/@href").getall()  #单图和无sku多图
        # for image in images_list_2:
        #     # image = "https:" + image
        #     if not "gif" in image:
        #         images_list.append(image)
        # for images in images_list_all:
        #     # image = "https:" + image
        #     if "https" in images:
        #         images = images.replace("S","L")
        #         images_list.append(images)
        # print(images_list_2)
        # print(images_list)
        items["images"] = images_list

        items["url"] = response.url
        items["original_price"] = str(original_price)
        items["current_price"] = str(current_price)
        items["source"] = website


        # judge = response.xpath("//div[@class='ec-base-button btnArea']/span//text()").getall()
        descripiton = []
        description_1 = response.xpath("//div[@class='pdp__details-text']/p/text()").getall()
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

        Inseam_list_all = response.xpath("//div[@class='product-attribute product-attribute__swatches product-attribute--dimension gutter--small-only-normal ']/div[@class='product-attribute__contents product-attribute__contents__swatch flex flex-flow-wrap']/button/span/text()").getall()
        Inseam_list = []
        for key in Inseam_list_all:
            # if not ("-" in key):
                key = self.filter_text(key)
                Inseam_list.append(key)

        # color_list_all = response.xpath("//div[@class='option-field']//select[@id='plating-color']/option/text()").getall()
        # if not color_list_all:
        #     color_list_all = response.xpath("//div[@class='swatch-attribute-options clearfix']/div[@class='included-color']/@title").getall()
        # color_list_all = re.findall('"id":".....","label":"(.*?)","products"', response.text)
        # color_list = []
        # for key in color_list_all:
        #     if not "--" in key:
        #         key = self.filter_text(key)
        #         # key = key.split(" from")[0]
        #         color_list.append(key)
        #
        size_list_all = response.xpath("//div[@class='product-attribute product-attribute__swatches product-attribute--size gutter--small-only-normal ']/div[@class='product-attribute__contents product-attribute__contents__swatch flex flex-flow-wrap']/button/span/text()").getall()
        # if not size_list_all:
        #     size_list_all = response.xpath("//ul[@class='size-select clearfix ring']/li/text()").getall()
        # if not size_list_all:
        #     size_list_all = response.xpath("//div[@class='option-field']//select[@id='ring-size']/option/text()").getall()
        size_list = []
        for key in size_list_all:
            # if not "--" in key:
                key = self.filter_text(key)
                size_list.append(key)
        # sku_len = len(size_list)
        # sku_value_1 = response.xpath("//meta[@property='og:url']/@content").get()
        # sku_value_1 = sku_value_1.split("https://kargl.shop/detail/index/sArticle/")[1]
        # sku_value_2 = response.xpath("//div[@class='product--configurator']//select/option/@value").getall()
        # # print(sku_value_2)
        # for i in range(0, sku_len):
        #     if size_list:
        #         # print(attribute_value)
        #         url = "https://kargl.shop/detail/index/sArticle/" + sku_value_1 + "/sCategory/89?group%5B15%5D=" + sku_value_2[i] + "&template=ajax"
        #         res = requests.get(url=url, headers=self.headers)
        #         html = Selector(text=res.text)
        #         original_price = html.xpath("//meta[@itemprop='price']/@content").get()
        #         original_price = original_price + "€"
        #         current_price = html.xpath("//meta[@itemprop='price']/@content").get()
        #         current_price = current_price + "€"
        #         size = size_list[i]
        #
        #         sku_item = SkuItem()
        #         sku_item["original_price"] = original_price
        #         sku_item["current_price"] = current_price
        #         sku_item["url"] = response.url
        #         sku_item["imgs"] = []
        #
        #         attributes = SkuAttributesItem()
        #         # attributes["colour"] = color
        #         attributes["size"] = size
        #         sku_item["attributes"] = attributes
        #         sku_list.append(sku_item)
        #     else:
        #         sku_item = SkuItem()
        #         sku_item["original_price"] = original_price
        #         sku_item["current_price"] = current_price
        #         sku_item["url"] = response.url
        #         sku_item["imgs"] = []

        # if color_list:
        #     for color in color_list:
        #         sku_item = SkuItem()
        #         sku_item["original_price"] = original_price
        #         sku_item["current_price"] = current_price
        #         sku_item["url"] = response.url
        #         sku_item["imgs"] = []
        #
        #         attributes = SkuAttributesItem()
        #         attributes["colour"] = color
        #         # attributes["size"] = size
        #         sku_item["attributes"] = attributes
        #         sku_list.append(sku_item)
        # else:
        #     sku_item = SkuItem()
        #     sku_item["original_price"] = original_price
        #     sku_item["current_price"] = current_price
        #     sku_item["url"] = response.url
        #     sku_item["imgs"] = []

        if Inseam_list:
            for Inseam in Inseam_list:
                if size_list:
                    for size in size_list:
                        sku_item = SkuItem()
                        sku_item["original_price"] = original_price
                        sku_item["current_price"] = current_price
                        sku_item["url"] = response.url
                        sku_item["imgs"] = []
                        attributes = SkuAttributesItem()
                        # attributes["colour"] = color
                        other = {'Inseam': Inseam}
                        attributes["other"] = other
                        attributes["size"] = size
                        sku_item["attributes"] = attributes
                        sku_list.append(sku_item)
                else:
                    sku_item = SkuItem()
                    sku_item["original_price"] = original_price
                    sku_item["current_price"] = current_price
                    sku_item["url"] = response.url
                    sku_item["imgs"] = []
                    attributes = SkuAttributesItem()
                    # attributes["colour"] = color
                    other = {'Inseam': Inseam}
                    attributes["other"] = other
                    sku_item["attributes"] = attributes
                    sku_list.append(sku_item)
        elif size_list:
            for size in size_list:
                sku_item = SkuItem()
                sku_item["original_price"] = original_price
                sku_item["current_price"] = current_price
                sku_item["url"] = response.url
                sku_item["imgs"] = []
                attributes = SkuAttributesItem()
                # other = {'option': other}
                attributes["size"] = size
                sku_item["attributes"] = attributes
                sku_list.append(sku_item)


        items["sku_list"] = sku_list
        # items["care"] = care
        # items["measurements"] = [measurement_1+measurement_2+measurement_3+measurement_4+measurement_5+measurement_6]
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

        detection_main(items=items, website=website, num=self.settings["CLOSESPIDER_ITEMCOUNT"], skulist=True,
                       skulist_attributes=True)

        print(items)
        yield items