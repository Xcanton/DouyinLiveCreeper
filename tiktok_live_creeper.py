import os
import sys
import time
from selenium import webdriver
from PIL import Image
from PIL import ImageChops
import numpy as np
import math
import operator
from functools import reduce


chromedriver_path= r'D:\idea\Projects\Creeper\Config\chromedriver.exe'
sys.path.append(chromedriver_path)

def initial_chrome_driver(visualize: bool = False, scrollbar: bool = False,
                          img_enable: bool = False, implicitly_wait: tuple = (True, 5)):

    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
    chrome_options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug

    if visualize:
        chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
    if scrollbar:
        chrome_options.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
    if img_enable:
        chrome_options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度

    browser = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    if implicitly_wait[0]:
        browser.implicitly_wait(implicitly_wait[1])  # implicitly_wait等待5秒，最多等待5s，超过5秒就会报错
    return browser

def getFodderSize(file_path):
    return (sum((sum((os.path.getsize(os.path.join(root, file)) for file in files if not os.path.islink(os.path.join(root, file)))) for root, _, files in os.walk(file_path))))

def compare_2_photo(path1, path2)-> bool:
    image1=Image.open(path1)
    image2=Image.open(path2)
    #     diff=ImageChops.difference(image1,image2)
    #     print(diff)
    #     return diff.getbbox() is not None
    h1 = image1.histogram()
    h2 = image2.histogram()
    result = math.sqrt(reduce(operator.add, list(map(lambda a,b: (a-b)**2, h1, h2)))/len(h1) )
    return not result==0

former_dict=dict()
driver = initial_chrome_driver()

while getFodderSize(r"D:\idea\Projects\Creeper\TiktokLive") < 4*1024*1024*1024:
    is_all_closed = True
    windows = driver.window_handles
    for window in windows:
        if window not in former_dict.keys():
            former_dict[window] = None

        driver.switch_to.window(window)
        file_name = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time())) + ".jpg"
        cur_path = os.path.join(r"D:\idea\Projects\Creeper\TiktokLive\screenshot", file_name)

        live_box = driver.find_element_by_xpath('//*[@id="_douyin_live_scroll_container_"]/div/div[2]/div[1]/div[1]/div[2]/div/div')
        if live_box.find_element_by_tag_name("video").get_attribute("playsinline"):
            live_box.screenshot(cur_path)
            if former_dict[window] is not None:
                if compare_2_photo(former_dict[window], cur_path):
                    former_dict[window] = cur_path
                    is_all_closed = False
                else:
                    os.remove(cur_path)
            else:
                is_all_closed = False
                former_dict[window] = cur_path
    if is_all_closed:
        break
    time.sleep(2)