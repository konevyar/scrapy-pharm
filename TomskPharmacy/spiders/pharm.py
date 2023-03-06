import scrapy
import re
import datetime
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urljoin


class PharmSpider(CrawlSpider):
    name = "pharm"
    allowed_domains = ["apteka-ot-sklada.ru"]
    # Список категорий тваров
    start_urls = [
        "https://apteka-ot-sklada.ru/catalog/sredstva-gigieny/uhod-za-polostyu-rta/zubnye-niti_-ershiki", 
        "https://apteka-ot-sklada.ru/catalog/kontaktnye-linzy-i-ochki/linzy-ezhednevnye",
        "https://apteka-ot-sklada.ru/catalog/perevyazochnye-sredstva/binty/binty-meditsinskie",
        "https://apteka-ot-sklada.ru/catalog/sredstva-gigieny/mylo/mylo-zhidkoe",
        ]

    rules = (
        # Переход в карточку товара
        Rule(LinkExtractor(restrict_xpaths="//div[@class='goods-card__name text text_size_default text_weight_medium']/a"), callback="parse_item", follow=True),
        # Переход на следующую страницу
        Rule(LinkExtractor(restrict_xpaths="//a[contains(@class,'ui-pagination__link ui-pagination__link_direction')]")),
        )
    
    def start_requests(self):
        for url in self.start_urls:
            # Указание локации пользователя
            headers = {"X-User-Location": "Tomsk",}
            yield scrapy.Request(url, headers=headers)
    
    def parse_item(self, response):
        # Получение данных
        timestamp = datetime.datetime.now()
        url = response.url
        title = response.css("h1[class='text text_size_display-1 text_weight_bold'] span[itemprop='name']::text").get()
        marketing_tags = []
        if response.css(".ui-tag.text.text_weight_medium.ui-tag_theme_secondary::text").get():
            marketing_tags.append(response.css(".ui-tag.text.text_weight_medium.ui-tag_theme_secondary::text").get().strip())
        section = response.xpath("//ul[@class='ui-breadcrumbs__list']/li/a/span/span[@itemprop='name']/text()")[-3:].extract()
        price_original = None if response.css(".goods-offer-panel__cost::text").get() is None else float(re.sub(r'[^\d.]', '', response.css(".goods-offer-panel__cost::text").get()))
        in_stock = False if response.css(".goods-offer-panel__cost::text").get() is None else True
        main_image = urljoin(response.url, response.xpath("//div[@class='goods-gallery__active-picture-area goods-gallery__active-picture-area_gallery_trigger']/img/@src").get())
        description = None if response.css("div[class='custom-html content-text'] p::text").get() is None else "".join([x.strip() for x in response.css("div[class='custom-html content-text'] p::text").getall()])
        country_of_origin = response.css("span[itemtype='location']::text").get()
        
        # Итоговый словарь
        yield {
            "timestamp": timestamp,  # Текущее время в формате timestamp
            #"RPC": "",  # {str} Уникальный код товара
            "url": url,  # {str} Ссылка на страницу товара
            "title": title,  # {str} Заголовок/название товара (если в карточке товара указан цвет или объем, необходимо добавить их в title в формате: "{название}, {цвет}")
            "marketing_tags": marketing_tags,  # {list of str} Список тэгов, например: ['Популярный', 'Акция', 'Подарок'], если тэг представлен в виде изображения собирать его не нужно
            #"brand": "",  # {str} Брэнд товара
            "section": section,  # {list of str} Иерархия разделов, например: ['Игрушки', 'Развивающие и интерактивные игрушки', 'Интерактивные игрушки']
            "price_data": {
                #"current": 0.,  # {float} Цена со скидкой, если скидки нет то = original
                "original": price_original,  # {float} Оригинальная цена
                #"sale_tag": ""  #{str} Если есть скидка на товар то необходимо вычислить процент скидки и записать формате: "Скидка {}%"
            },
            "stock": {
                "in_stock": in_stock,  # {bool} Должно отражать наличие товара в магазине
                #"count": 0 # {int} Если есть возможность получить информацию о количестве оставшегося товара в наличии, иначе 0
            },
            "assets": {
                "main_image": main_image,  # {str} Ссылка на основное изображение товара
                #"set_images": [],  # {list of str} Список больших изображений товара
                #"view360": [],  # {list of str}
                #"video": []  # {list of str} 
            },
            "metadata": {
                "__description": description,  # {str} Описание товар
                # Ниже добавить все характеристики которые могут быть на странице тоавара, такие как Артикул, Код товара, Цвет, Объем, Страна производитель и т.д.
                #"АРТИКУЛ": "A88834",
                "СТРАНА ПРОИЗВОДИТЕЛЬ": country_of_origin
            }
            #"variants": 1,  # {int} Кол-во вариантов у товара в карточке (За вариант считать только цвет или объем/масса. Размер у одежды или обуви варинтами не считаются)
        }
