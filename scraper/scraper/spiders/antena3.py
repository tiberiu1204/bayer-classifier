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
        category = {"externe": "politica", "politica": "politica",
                    "actualitate": "diverse", "life": "diverse", "sport": "sport"}
        last = response.url.strip('/').split('/')[-1]
        if last in base:
            for page_num in range(2, NUM_PAGES + 1):
                href = f'{response.url}pagina-{page_num}'
                yield response.follow(href, callback=self.parse_pages)
        else:
            last = response.url.strip('/').split('/')[-2]

        titles = response.xpath('//article//a')
        article_arr = []
        for title in titles:
            article_arr.append({
                "href": title.xpath('@href').get(),
                "title": title.xpath('text()').get()
            })

        for article in article_arr:
            yield response.follow(article["href"],
                                  callback=self.parse_articles,
                                  meta={"title": article["title"], "category": category[last]})
        print(f'Scraped {len(article_arr)} articles from {response.url}')

    def parse_articles(self, response):
        yield {
            "title": response.meta.get('title'),
            "category": response.meta.get('category'),
            "text": response.xpath(
                '//div[contains(@class, "text")]//p//text()'
            ).re(r'[\w-]+')
        }
