from selenium import webdriver
from bs4 import BeautifulSoup
import telegram
import threading


def get_page_source(url):
    lock.acquire()
    driver.get(url)
    result = BeautifulSoup(driver.page_source, "html.parser")
    lock.release()
    return result


def get_product_sales(products, begin, end):
    for i in range(begin, end):
        URL = "https://www.coupang.com/np/categories/178397?eventCategory=breadcrumb&eventLabel=&page=" + str(i + 1)
        products_page = get_page_source(URL)

        discounts = products_page.find_all("span", class_="ccid-txt")

        for discount in discounts:
            product = discount.find_parents("a", class_="baby-product-link")
            name = product[0].find("div", class_="name")
            price = product[0].find("strong", class_="price-value")
            link = "https://www.coupang.com" + product[0].attrs["href"]
            product_page = get_page_source(link)
            icons = product_page.find_all("img", class_="benefit-ico")

            cards = []
            for icon in icons:
                begin_index = icon.attrs["src"].find("/web/")
                end_index = icon.attrs["src"].find("@")
                cards.append(icon.attrs["src"][begin_index + 5 : end_index])

            products.append((name.string.replace("    ", ""), price.string, discount.string, cards))

    print("Thread", int(begin / page_per_thread), "end")


options = webdriver.ChromeOptions()
options.add_argument("headless")
options.add_argument("window-size=1920x1080")
options.add_argument("disable-gpu")
options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
)
options.add_argument("lang=ko_KR")
options.add_argument("log-level=2")

driver = webdriver.Chrome("chromedriver", options=options)
driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5]}})")
driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")
driver.execute_script(
    "const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};"
)


products = []
threads = []
thread_count = 8
page_per_thread = 2
lock = threading.Lock()

for i in range(thread_count):
    t = threading.Thread(target=get_product_sales, args=(products, i * page_per_thread, (i + 1) * page_per_thread))
    t.start()
    threads.append(t)

for t in threads:
    t.join()


bot = telegram.Bot(token="1365832253:AAFzSq4nAiqBxCHhN-o6Dy_N2c8WBuFX8eo")
chat_id = bot.getUpdates()[-1].message.chat.id
text = ""

for name, price, discount, cards in products:
    text += name + price + "\n" + discount + "\n" + str(cards) + "\n"

bot.sendMessage(chat_id=chat_id, text=text)
print(text)

driver.quit()
