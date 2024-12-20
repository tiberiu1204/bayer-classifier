import scrapy


class ArticlesSpider(scrapy.Spider):
    name = "pressone"

    def start_requests(self):
        base_url = "https://pressone.ro/categorie"
        subdirs = ["/mediu/", "/opinii/", "/stiri/", "/lifestyle/",
                   "/orase/", "/dezinformare/", "/international/", "/tineri/"]
        urls = [base_url + subdir for subdir in subdirs]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_pages)

    def parse_pages(self, response):
        if response.status == 404:
            return
        NUM_PAGES = 5
        base = ["mediu", "opinii", "stiri", "lifestyle", "orase",
                "dezinformare", "international", "tineri"]
        category = {"mediu": "diverse", "opinii": "politica", "stiri": "diverse", "lifestyle": "diverse",
                    "orase": "diverse", "dezinformare": "politica", "international": "politica", "tineri": "diverse"}
        last = response.url.strip('/').split('/')[-1]
        if last in base:
            for page_num in range(2, NUM_PAGES + 1):
                href = f"{response.url.strip('/')}/{page_num}"
                yield response.follow(href, callback=self.parse_pages)
        else:
            last = response.url.strip('/').split('/')[-2]

        titles = response.xpath(
            '//main//a'
            '[contains(@class, "text-decoration-none")]'
            '[contains(@class, "text-black")]'
        )
        article_arr = []
        for title in titles:
            article_arr.append({
                "href": title.xpath('@href').get(),
                "title": title.xpath('./h3/text()').get()
            })

        for article in article_arr:
            yield response.follow(article["href"],
                                  callback=self.parse_articles,
                                  meta={"title": article["title"], "category": category[last]})

        print(f'Scraped {len(article_arr)} articles from {response.url}')

    def parse_articles(self, response):
        yield {
            "title": response.meta.get("title"),
            "category": response.meta.get("category"),
            "text": response.xpath(
                '//article//*[contains(@class, "font-primary")]//text()'
            ).re(r'[\w-]+')
        }
