# -*- coding: utf-8 -*-
import logging
import re
import json
import time
import scrapy
import requests
from hashlib import md5

from scrapy.http.response import html

from overseaSpider.items import ShopItem, SkuAttributesItem, SkuItem
from overseaSpider.util.scriptdetection import detection_main
from overseaSpider.util.utils import isLinux

website = 'choies'

#没有修改
def get_sku_price(product_id, attribute_list):
    """获取sku价格"""
    url = 'https://thecrossdesign.com/remote/v1/product-attributes/{}'.format(product_id)
    data = {
        'action': 'add',
        'product_id': product_id,
        'qty[]': '1',
    }
    for attribute in attribute_list:
        data['attribute[{}]'.format(attribute[0])] = attribute[1]
    response = requests.post(url=url, data=data)
    return json.loads(response.text)['data']['price']['without_tax']['formatted']



class ChoiesSpider(scrapy.Spider):
    name = website
    allowed_domains = ['choies.com']
    start_urls = ['https://www.choies.com/beauty-c-1019']

    @classmethod
    def update_settings(cls, settings):
        custom_debug_settings = getattr(cls, 'custom_debug_settings' if getattr(cls, 'is_debug',
                                                                                False) else 'custom_settings', None)
        system = isLinux()
        if not system:
            # 如果不是服务器, 则修改相关配置
            custom_debug_settings["HTTPCACHE_ENABLED"] = False
            custom_debug_settings["MONGODB_SERVER"] = "127.0.0.1"
        settings.setdict(custom_debug_settings or {}, priority='spider')

    def __init__(self, **kwargs):
        super(ChoiesSpider, self).__init__(**kwargs)
        self.counts = 0
        setattr(self, 'author', "守约")

    is_debug = True
    custom_debug_settings = {
        'MONGODB_COLLECTION': website,
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'DEBUG',
        'COOKIES_ENABLED': True,
        # 'HTTPCACHE_EXPIRATION_SECS': 14 * 24 * 60 * 60, # 秒
        'DOWNLOADER_MIDDLEWARES': {
            # 'overseaSpider.middlewares.PhantomjsUpdateCookieMiddleware': 543,
            # 'overseaSpider.middlewares.OverseaspiderProxyMiddleware': 400,
            'overseaSpider.middlewares.OverseaspiderUserAgentMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'overseaSpider.pipelines.OverseaspiderPipeline': 300,
        },
    }

    # def filter_html_label(self, text):  # 洗description标签函数
    #     label_pattern = [r'<div class="cbb-frequently-bought-container cbb-desktop-view".*?</div>', r'(<!--[\s\S]*?-->)', r'<script>.*?</script>', r'<style>.*?</style>', r'<[^>]+>']
    #     for pattern in label_pattern:
    #         labels = re.findall(pattern, text, re.S)
    #         for label in labels:
    #             text = text.replace(label, '')
    #     text = text.replace('\n', '').replace('\r', '').replace('\t', '').replace('  ', '').strip()
    #     return text

    def filter_html_label(self, text, type):
        text = str(text)
        # 注释，js，css
        filter_rerule_list = [r'(<!--[\s\S]*?-->)', r'<script[\s\S]*?</script>', r'<style[\s\S]*?</style>']
        for filter_rerule in filter_rerule_list:
            html_labels = re.findall(filter_rerule, text)
            for h in html_labels:
                text = text.replace(h, ' ')
        html_labels = re.findall(r'<[^>]+>', text)  # html标签单独拿出
        if type == 1:
            for h in html_labels:
                text = text.replace(h, ' ')
        filter_char_list = [
            u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000', u'\u200a', u'\u2028', u'\u2029', u'\u202f', u'\u205f',
            u'\u3000', u'\xA0', u'\u180E', u'\u200A', u'\u202F', u'\u205F', '\t', '\n', '\r', '\f', '\v',
        ]
        for f_char in filter_char_list:
            text = text.replace(f_char, '')
        text = html.unescape(text)
        text = re.sub(' +', ' ', text).strip()
        return text

    def filter_text(self, input_text):
        filter_list = [u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000-', u'\u200a',
                       u'\u2028', u'\u2029', u'\u202f', u'\u205f', u'\u3000', u'\xA0', u'\u180E',
                       u'\u200A', u'\u202F', u'\u205F']
        for index in filter_list:
            input_text = input_text.replace(index, "").strip()
        return input_text

    def parse(self, response):
        """获取全部分类"""
        #//*[@id="navPages-552"]/li[1]
        #category_urls = response.xpath("//li[@class='navPage-childList-item']/a/@href").getall()
        category_urls = response.xpath("//dl[@class='nav-ul01']/dd/a/@href").getall()
        for category_url in category_urls:
            yield scrapy.Request(url='https://www.choies.com'+category_url, callback=self.parse_list)
            logging.info('当前爬取的目录'+category_url)

    def parse_list(self, response):
        """商品列表页"""
        #//*[@id="product_ul"]/li[30]
        detail_url_list = response.xpath("//div[@class='pro-list']/ul[@id='product_ul']/li/div[3]/a/@href").getall()
        print(detail_url_list)
        #//*[@id="product_ul"]/li[1]/div[3]/a
        for detail_url in detail_url_list:
            yield scrapy.Request(url=detail_url, callback=self.parse_detail)
            logging.info('当前爬取的商品url'+detail_url)
        #//*[@id="pagination"]/ul/li[2]
        next_page_url = response.xpath("//div[@id='pagination']/ul/li[@class='last']/a/@href").get()
        if next_page_url:
            yield scrapy.Request(url=response.url+ next_page_url, callback=self.parse_list)
            logging.info('下一页url：' + detail_url)

    def parse_detail(self, response):
        """详情页"""
        items = ShopItem()
        items["url"] = response.url

        price = response.xpath("//div[@class='price-box']/p/span/span/text()").get()
        price = price if '-' not in price else price.split('-')[0]
        items["original_price"] = price.replace(',', '').strip()
        items["current_price"] = items["original_price"]

        name = response.xpath("//div[@class='pro-right']/h3/text()").get()
        items["name"] = name



        #cat是什么意思
        cat_list = response.xpath('//div[@class="crumbs"]/div/a/text()').getall()
        if cat_list:
            cat_list = [cat.strip() for cat in cat_list if cat.strip()]#
            #这是一句什么函数
            items["cat"] = cat_list[-1]
            items["detail_cat"] = '/'.join(cat_list)

        description = response.xpath("//div[@id='tab-detail']/text()|//div[@id='tab-detail']/br/text()").getall()
        items["description"] = self.filter_text(self.filter_html_label(''.join(description)))
        items["source"] = website


        images_list = response.xpath('//li[@class="list-item"]/a/img/@bigimg').getall()
        items["images"] = images_list


        #lable用来传参的 最终是为了完成什么业务的？
        size_list = []
        attr_id = 0
        size_list = response.xpath('//ul[@class="drop-down-list size-list JS-showcon1"]/li/@id').getall()
        # for label in label_list:
        #     key = label.xpath('./label[1]/text()').get().strip().replace(':', '').lower()
        #     values = label.xpath('./label')[1:]#这个取值不确定啥意思
        #     if 'size' in key:
        #         attr_id = values[0].xpath('./following-sibling::input[1]/@name').get()#这个下标？
        #         size_list = [{'id': v.xpath('./@data-product-attribute-value').get(), 'value': v.xpath('./span[1]/text()').get().strip()} for v in values]
        #         #v是哪来的

        product_id = re.search(r'"product_id":"(.*?)",', response.text).group(1)
        #这一句正则没有看明白 group1？ search搜索的范围是response.text
        #lable为了传size-list size-list为了搞定SKU
        sku_list = list()#创建了一个空列表
        #空列表怎么遍历？
        for size in size_list:
            sku_info = SkuItem()
            sku_attr = SkuAttributesItem()
            sku_attr["size"] = size
            #price = get_sku_price(product_id, [(attr_id, size['id'])])
            price = response.xpath("//div[@class='price-box']/p/span/span/text()").get()
            sku_info["current_price"] = price
            sku_info["original_price"] = price
            sku_info["attributes"] = sku_attr
            sku_list.append(sku_info)
        items["sku_list"] = sku_list

        #商品尺寸信息
        items["measurements"] = ["Weight: None", "Height: None", "Length: None", "Depth: None"]
        status_list = list()
        status_list.append(items["url"])
        status_list.append(items["original_price"])
        status_list.append(items["current_price"])
        status_list = [i for i in status_list if i]
        status = "-".join(status_list)#
        items["id"] = md5(status.encode("utf8")).hexdigest()#这个ID为什么要这样处理--存储哈希值作为唯一标识

        #爬虫脚本运行信息
        items["lastCrawlTime"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        items["created"] = int(time.time())
        items["updated"] = int(time.time())
        items['is_deleted'] = 0
        # detection_main(items=items, website=website, num=10, skulist=True, skulist_attributes=True)
        print(items)
        yield items
