import scrapy


class ArticlesSpider(scrapy.Spider):
    name = "antena3"

    def start_requests(self):
        base_url = "https://www.antena3.ro"
        subdirs = ["/externe/", "/politica/", "/actualitate/",
                   "/life/", "/sport/"]
        urls = [base_url + subdir for subdir in subdirs]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_pages)

    def parse_pages(self, response):
        NUM_PAGES = 5
        base = ["externe", "politica", "actualitate", "life", "sport"]
        last = response.url.split('/')[-2]
        if last in base:
            for page_num in range(2, NUM_PAGES + 1):
                href = f'{response.url}pagina-{page_num}'
                yield response.follow(href, callback=self.parse_pages)
        titles = response.xpath('//article/h2/a')
        article_arr = []
        for title in titles:
            article_arr.append({
                "href": title.xpath('@href').get(),
                "title": title.xpath('text()').get()
            })

        # TODO: Filter

        for article in article_arr:
            yield response.follow(article["href"],
                                  callback=self.parse_articles,
                                  meta={"title": article["title"]})
        print(f'Scraped {len(article_arr)} articles from {response.url}')

    def parse_articles(self, response):
        yield {
            "title": response.meta.get('title'),
            "text": response.xpath(
                '//div[contains(@class, "text")]//p//text()'
            ).re(r'[\w-]+')
        }
