import time

from django.conf import settings
from lxml import etree
import requests
from PIL import Image
from pytesseract import pytesseract
from selenium import webdriver

from pyvirtualdisplay import Display
from retry import retry


@retry(tries=2)
def get_news():
    url = settings.NEWS_URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
        'Referer': 'http://www.nuc.edu.cn'
    }
    response = requests.get(url, headers=headers, timeout=3)
    text = response.content.decode('utf-8')
    html = etree.HTML(text)
    news = html.xpath('//div[@class="list_con_rightlist"]/ul/li')
    result = list()
    for li in news:
        new = dict()
        new['url'] = li.xpath('a/@href')[0].replace('..', 'http://www.nuc.edu.cn').replace('#tips', '')
        new['title'] = li.xpath('a/text()')[0]
        new['date'] = li.xpath('span/text()')[0][5:]
        result.append(new)
    return result


@retry(tries=3)
def get_cookies(username, password):
    """获取个人门户cookie"""
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('window-size=1920x1080')  # 指定浏览器分辨率
        options.add_argument(
            'user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"')
        driver = webdriver.Chrome(
            executable_path='/media/wxl/a84d5450-ee22-469c-a813-c774821af033/wangxl/chromedriver/chromedriver',
            options=options)
        # 访问个人门户登录页
        print('----------正在访问登录页面----------')
        driver.delete_all_cookies()
        driver.get(settings.LOGIN_URL)
        # 获取验证码图片
        print('----------正在获取验证码----------')
        imgelement = driver.find_element_by_xpath('//*[@id="captchaimg"]')
        locations = imgelement.location
        sizes = imgelement.size
        rangle = (int(locations['x']), int(locations['y']), int(
            locations['x'] + sizes['width']), int(locations['y'] + sizes['height']))
        path1 = '/home/wxl/Desktop/test' + str(2)
        path2 = '/home/wxl/Desktop/test' + str(3)
        path3 = '/home/wxl/Desktop/tx'
        path4 = '/home/wxl/Desktop/dl'
        driver.get_screenshot_as_file(str(path1) + '.png')

        # 保存验证码图片
        img = Image.open(str(path1) + ".png")
        jpg = img.crop(rangle)
        jpg.save(str(path2) + ".png")

        # 识别验证码图片
        print('----------正在识别验证码----------')
        image = Image.open(str(path2) + ".png")
        image.load()
        code = pytesseract.image_to_string(image)

        # 填写登录信息，并登录
        print('----------正在登录----------')
        driver.find_element_by_xpath('//*[@id="username"]').clear()
        driver.find_element_by_xpath('//*[@id="username"]').send_keys(username)
        driver.find_element_by_xpath('//*[@id="password"]').clear()
        driver.find_element_by_xpath('//*[@id="password"]').send_keys(password)
        driver.find_element_by_xpath('//*[@id="j_captcha_response"]').clear()
        driver.find_element_by_xpath('//*[@id="j_captcha_response"]').send_keys(code)

        driver.get_screenshot_as_file(path3 + '.png')

        driver.find_element_by_xpath(
            '//*[@id="thetable"]/div[7]/span[1]/input[3]').click()
        time.sleep(2)

        driver.get_screenshot_as_file(path4 + '.png')
        driver.find_element_by_id('134871694799031620').click()
        print('----------登录成功-----------')
        time.sleep(2)
        print('--------获取cookies---------')
        driver.switch_to.window(driver.window_handles[1])
        cookies = driver.get_cookies()
        print('--------退出浏览器-----------')
        driver.quit()

        display.stop()
        return cookies[0]
    except Exception as e:
        print(e)
        return None


def get_info(url, cookies):
    """获取学生信息"""
    try:
        jar = requests.cookies.RequestsCookieJar()
        jar.set(cookies['name'], cookies['value'], domain=cookies['domain'], path=cookies['path'])
        print('访问成绩数据')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': '202.207.177.39:8089',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://202.207.177.39:8089/menu/menu.jsp',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
        }
        info = requests.get(url, headers=headers, cookies=jar)
        return info.content.decode('gbk')
    except Exception:
        return None
