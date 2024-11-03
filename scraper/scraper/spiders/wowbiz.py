import scrapy


class ArticlesSpider(scrapy.Spider):
    name = "wowbiz"

    def start_requests(self):
        base_url = "https://www.wowbiz.ro"
        subdirs = ["/exclusiv/", "/video/", "/stiri-actualitate/", "/sport/", "/bani/",
                   "/stiri-economie/", "/stiri-politica/"]
        urls = [base_url + subdir for subdir in subdirs]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_pages)

    def parse_pages(self, response):
        unproc_articles = response.xpath(
            '//*[@id="container"]/div[2]/div/main/div/article')
        proc_articles = []
        for article in unproc_articles:
            proc_articles.append({
                "href": article.xpath('a/@href').get(),
                "title": article.xpath('.//h2/span/text()').re(r'[A-Z][\w ,.;:\'\'\"\"\-\!\?]+')
            })

        # TODO: Filter

        for article in proc_articles:
            yield response.follow(article["href"],
                                  callback=self.parse_articles,
                                  meta={"title": article["title"]})
        print(f'Scraped {len(proc_articles)} articles from {response.url}')

    def parse_articles(self, response):
        yield {
            "title": response.meta.get("title"),
            "text": response.xpath(
                '//*[@id="container"]/div[2]/div/main[2]/div/h2/text() |'
                '//*[@id="container"]/div[2]/div/main[2]/div/p/text() |'
                '//*[@id="container"]/div[2]/div/main[2]/div/em/text()'
            ).re(r'\w+')
        }
