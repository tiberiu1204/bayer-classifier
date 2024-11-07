import scrapy


class ArticlesSpider(scrapy.Spider):
    name = "recorder"

    def start_requests(self):
        base_url = "https://recorder.ro"
        subdirs = ["/stirile-zilei/",]
        urls = [base_url + subdir for subdir in subdirs]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_pages)

    def parse_pages(self, response):
        NUM_PAGES = 8
        last = response.url.split('/')[-3]
        if last != "page":
            for page_num in range(2, NUM_PAGES + 1):
                href = f'{response.url}page/{page_num}'
                yield response.follow(href, callback=self.parse_pages)

        unproc_articles = response.xpath(
            "//*[string-length(@id) > 0 and translate(@id, '0123456789', '') = '']/div/div[2]/div[2]")

        proc_articles = []
        for article in unproc_articles:
            proc_articles.append({
                "href": article.xpath('a/@href').get(),
                "title": article.xpath('a/h2/text()').re(r'[A-Z][\w ,.;:\'\'\"\"\-\!\?]+')
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
            "category": "politica",
            "text": response.xpath(
                "//*[starts-with(@id, 'post-') and translate(substring-after(@id, 'post-'), '0123456789', '') = '']/div/h2/text() | "
                "//*[starts-with(@id, 'post-') and translate(substring-after(@id, 'post-'), '0123456789', '') = '']/div/p/text()"
            ).re(r'[\w-]+')
        }
