import scrapy

class TestSpider(scrapy.Spider):
    name = 'test'
    start_urls = ['http://example.com']

    def parse(self, response):
        yield {'title': response.xpath('//title/text()').get()}
