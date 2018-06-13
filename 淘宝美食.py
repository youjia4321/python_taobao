# -*- coding:utf-8 -*-
__author__ = 'youjia'
__date__ = '2018/6/6 17:16'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from pyquery import PyQuery as pq
import pymongo
from 爬虫及算法.taobao.config import *

browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(browser, 10)
browser.set_window_size(1400, 900)

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_TABLE]


def search():
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        inputs = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#q")))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#J_TSearchForm > div.search-button > button")))
        inputs.send_keys("美食")
        submit.click()
        total = wait.until(EC.presence_of_all_elements_located
                           ((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.total")))
        get_products()
        return total[0].text
    except TimeoutException:
        return search()


def next_page(page_number):
    print('正在翻页', page_number)
    try:
        inputs = wait.until(EC.presence_of_element_located
                            ((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input")))
        submit = wait.until(EC.element_to_be_clickable
                            ((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit")))
        inputs.clear()
        inputs.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element
                   ((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > ul > li.item.active > span"), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    # 判断页面是否加载完成
    wait.until(EC.presence_of_element_located
               ((By.CSS_SELECTOR, "#mainsrp-itemlist .items .item")))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'images': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text().replace('\n', ''),
            'deal': item.find('.deal-cnt').text(),
            'title': item.find('.title').text().replace('\n', ' '),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        # print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MongoDB成功：', result)
    except Exception:
        print('存储MongoDB失败：', result)


def main():
    try:
        total = search()
        total_page = int(re.compile('(\d+)').search(total).group(1))
        # print(total_page)
        for i in range(2, 4):
            next_page(i)
    except Exception:
        print('出错了')
    finally:
        browser.close()


if __name__ == "__main__":
    main()
