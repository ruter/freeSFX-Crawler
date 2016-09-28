# -*- coding: UTF-8 -*-

import sys
import os
import re
import math
import urllib
import urllib2
import requests
import cookielib

# 解决输出乱码问题
reload(sys)
sys.setdefaultencoding("utf8")

class SFX():

    def __init__(self):
        self.rootDir = os.getcwd() + "/freeSFX/"
        self.header = self.__initHeader()
        self.base_url = 'http://www.freesfx.co.uk'
        self.session_requests = requests.session()

    def __initHeader(self):
        headers = {
            'Host': 'www.freesfx.co.uk',
            'Origin': 'http://www.freesfx.co.uk',
            'Referer': 'http://www.freesfx.co.uk/login/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
        }
        return headers

    def signIn(self):
        """
        登录网站获取cookie
        :return:
        """
        login_url = 'http://www.freesfx.co.uk/login/'
        form_data = {
            'username': 'xxxxx',
            'password': 'xxxxx',
            'login': 'Log in'
        }
        self.session_requests.post(
            login_url,
            data=form_data,
            headers=self.header
        )

    def getCategories(self):
        """
        获取音效的小分类
        如果分类旁的数量为0则不保存
        :return: 一个包含所有分类的列表[{'category': '分类名', 'link': 'http://对应的链接/', 'pages': 1}]
        """
        cate_url = self.base_url + '/soundeffects/'
        self.header['Referer'] = ''
        try:
            print '正在抓取所有分类信息...'
            result = self.session_requests.get(cate_url, headers=self.header)
            result.encoding = 'utf-8'
            cate_html = result.text

            print '状态:', result.status_code
        except Exception as e:
            print "发生异常:", e
            return

        categories = []
        # 从HTML中正则解析分类及链接
        cate_pattern = r'<li><a href="/\w+/(\w+/)">(\w+) </a><span class="info" style="margin-left:5px;">\((\d+)\)</span> </li>'
        cate_list = re.compile(cate_pattern).findall(cate_html)
        if len(cate_list) == 0:
            print '解析失败: 没有找到任何分类'
            return

        for cate in cate_list:
            if cate[2] != '0':
                cate_dict = {}
                cate_dict['category'] = cate[0]
                cate_dict['link'] = cate_url + cate[1]
                cate_dict['pages'] = int(math.ceil(int(cate[2]) / 15.0))
                categories.append(cate_dict)
        return categories

    # def getPages(self, pages):
    #     """
    #     获取当前分类下最大页码数
    #     :return: 页码数
    #     """
    #     # 15条数据一页，向上取整
    #     return math.ceil(pages / 15.0)

    def getInfo(self, info_url):
        """
        获取音频的名称和下载链接
        :return: 一个包含音频名称和下载链接的列表[{'id': '12345', 'title': 'mp3', 'link': 'www.a.com'}]
        """
        try:
            print '正在抓取音频信息...'
            result = self.session_requests.get(info_url, headers=self.header)
            result.encoding = 'utf-8'
            info_html = result.text

            print '状态:', result.status_code
        except Exception as e:
            print "发生异常:", e
            return

        all_info = []
        # 从HTML中正则解析名称及链接
        info_pattern = r'id="(\d+)" class="player"></a></td><td><h2>(\w+.*?)</h2>.*?<a href="(/download/\?type=mp3&id=\d+)" class="dl">Download MP3</a>'
        info_list = re.compile(info_pattern).findall(info_html)
        if len(info_list) == 0:
            print '解析失败: 没有找到任何音频信息'
            return

        for info in info_list:
            info_dict = {}
            info_dict['id'] = info[0]
            info_dict['title'] = info[1]
            info_dict['link'] = self.base_url + info[2]
            all_info.append(info_dict)
        return all_info

    def downloadMP3(self, down_url):
        """
        下载MP3音频文件
        :return: MP3文件
        """
        down_url += '&eula=true'
        try:
            print '下载音频中...'
            r = self.session_requests.get(down_url, headers=self.header)
            print '下载成功'
        except Exception as e:
            print '下载失败: [%s]' % e
            return
        return r.content

    def saveMP3(self, category, pid, title, down_url):
        """
        写入MP3文件到对应分类目录下
        :return:
        """
        folder_path = self.rootDir + category
        file_path = folder_path + '%s_%s.mp3' % (title.replace(' ', ''), pid)
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                print '文件已经存在, 跳过此文件继续执行...'
                return
            if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
                os.mkdir(folder_path)
                print '分类目录创建成功:', folder_path
            mp3 = self.downloadMP3(down_url)
            with open(file_path, "wb") as code:
                code.write(mp3)
            print '音频文件已保存:', file_path
        except Exception as e:
            print '保存文件异常: [%s] 跳过此文件继续执行...' % e

if __name__ == "__main__":

    print '*' * 10, 'START', '*' * 10

    freeSFX = SFX()
    if not os.path.exists(freeSFX.rootDir) or not os.path.isdir(freeSFX.rootDir):
        os.mkdir(freeSFX.rootDir)
        print '存储目录创建成功:', freeSFX.rootDir

    freeSFX.signIn()
    categories = freeSFX.getCategories()

    for category in categories:
        print '正在抓取分类[%s]下的音频...' % category['category']
        for i in range(1, category['pages'] + 1):
            print '正在抓取第[%d]页数据...' % i
            link = category['link'] + '/?p=%d' % i
            info_list = freeSFX.getInfo(link)
            for info in info_list:
                freeSFX.saveMP3(category['category'], pid=info['id'], title=info['title'], down_url=info['link'])

    print '*' * 10, 'END', '*' * 10










