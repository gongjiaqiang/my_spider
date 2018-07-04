# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     get_image_spider
   Description :
   Author :       akulaku
   date：          2018/7/3
-------------------------------------------------
   Change Activity:
                   2018/7/3:
-------------------------------------------------
"""

__author__ = 'akulaku'

import random
import re
import json
import time
import os
from hashlib import md5
from requests_html import HTMLSession
from requests_html import HTML

class SaveImagesInfo(object):
    def __init__(self, total_images=None):
        self.total_images = total_images

    def save_src_data(self):
        with open("images_src_data.txt", "w", encoding="GBK") as f:
            f.write(str(self.total_images))

    def save_image_urls(self):
        try:
            image_list = []
            for item in self.total_images:
                image_dict = {}
                image_url = []
                image_dict["title"] = item["title"]
                for each in item["images_info"]:
                    image_url.append(each["purl"])
                image_dict["image_url"] = image_url
                image_list.append(image_dict)

            with open("image_urls.json", "w", encoding='GBK') as f:
                f.write(json.dumps(image_list))
        except Exception as err:
            print("写入数据失败{}".format(err))


class CrawlSpider(object):
    def __init__(self):
        self.sess = HTMLSession()
        self.headers = {
            "Host": "tieba.baidu.com",
            "Referer": "https://www.baidu.com/",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
        }
        self.params = {
            "kw": "张国荣",
            "tab": "album",
            "subtab": "album_good",
            "cat_id": ""
        }

    def get_category_id(self):
        try:
            resp = self.sess.get(url="http://tieba.baidu.com/f?", params=self.params, headers=self.headers)
            category_list = re.findall('<li cat-id="(.*)"><span>', resp.text)
            return category_list
        except Exception as err:
            print("获取分类失败，错误信息为：{}".format(err))

    def get_tid_info(self):
        category_list = self.get_category_id()
        if not category_list:
            return
        all_tid_list = []
        for cat_id in category_list:
            self.params["cat_id"] = cat_id
            self.params["pagelets"] = 'album/pagelet/album_good'
            self.params["pagelets_stamp"] = "%013d"%(1000 * time.time())
            try:
                resp = self.sess.get(url="http://tieba.baidu.com/f?", params=self.params, headers=self.headers)
                resp.html.render()
                html = HTML(html=resp.html.text)
                tid_list = re.findall(r"/p/\d+", re.sub(r"\\", '', str(html.links)))
                all_tid_list.extend(tid_list)
            except Exception as err:
                print("获取tid失败{}".format(err))
        return all_tid_list

    def get_image_urls(self):
        all_tid_list = self.get_tid_info()
        if not all_tid_list:
            return
        times = 0
        total_pic_list = []
        for item in all_tid_list:
            total_images_dict = {}
            tid = re.search(r"\d+", item).group()
            times += 1
            print("=========第{}次=========".format(times))
            params = {
                "kw": "张国荣",
                "alt": "jview",
                "rn": "200",
                "tid": tid,
                "pn": "1",
                "ps": "1",
                "pe": "40",
                "info": "1",
                "_": "%013d" % (1000 * time.time())
            }
            base_url = "http://tieba.baidu.com/photo/g/bw/picture/list?"
            all_pic_list = []
            try:
                resp = self.sess.get(url=base_url, params=params, headers=self.headers).text
                time.sleep(random.random() + 1)
                resp = json.loads(resp)
                title = resp["data"]["title"]
                print(title)
                pic_list = resp["data"]["pic_list"]
                all_pic_list.extend(pic_list)
                if len(pic_list) < 40:
                    continue
                for i in range(4):
                    ps = 41 + 40 * i
                    pe = 80 + 40 * i
                    params_2 = {
                        "kw": "张国荣",
                        "alt": "jview",
                        "rn": "200",
                        "tid": tid,
                        "pn": "1",
                        "ps": str(ps),
                        "pe": str(pe),
                        "wall_type": "v",
                        "_": "%013d" % (1000 * time.time())
                    }
                    next_resp = self.sess.get(url=base_url, params=params_2, headers=self.headers).text
                    time.sleep(random.random() + 1)
                    next_resp = json.loads(next_resp)
                    next_pic_list = next_resp["data"]["pic_list"]
                    all_pic_list.extend(next_pic_list)
                    if len(next_pic_list) < 40:
                        break
                    elif i == 3 and len(next_pic_list) == 40:
                        params_2["pn"] = "2"
                        params_2["info"] = "1"
                        params_2["ps"] = "1"
                        params_2["pe"] = "40"
                        response = self.sess.get(url=base_url, params=params_2, headers=self.headers).text
                        time.sleep(random.random() + 1)
                        resp_data = json.loads(response)
                        next_pic_list_2 = resp_data["data"]["pic_list"]
                        all_pic_list.extend(next_pic_list_2)
                total_images_dict["title"] = title
                total_images_dict["images_info"] = all_pic_list
                total_pic_list.append(total_images_dict)
            except Exception as err:
                print("获取图片数据失败{}".format(err))

        return total_pic_list

    def save_images_data(self):
        total_pic_list = self.get_image_urls()
        if not total_pic_list:
            return
        save_data = SaveImagesInfo(total_pic_list)
        save_data.save_src_data()
        save_data.save_image_urls()


class DownloadImages(object):
    def __init__(self):
        self.sess = HTMLSession()
        self.headers = {
            # "Host": "tieba.baidu.com",
            # "Referer": "https://www.baidu.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
        }

    def save_image(self, content):
        file_path = "{0}\{1}.{2}".format(os.getcwd(), md5(content).hexdigest(), "jpg")
        # print(file_path)
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(content)
                f.close()
                print("{}下载完成...".format(file_path))

    def download_images(self):
        with open("./image_urls.json") as f:
            data = f.read()
        json_data = json.loads(data)
        if not os.path.exists("./张国荣"):
            os.mkdir("./张国荣")
        os.chdir("./张国荣")
        for item in json_data:
            title = item["title"].encode("utf-8").decode("utf-8")
            print(title)
            if not os.path.exists(title):
                os.mkdir(title)
            os.chdir(title)
            image_url_list = item["image_url"]
            for image_url in image_url_list:
                try:
                    response = self.sess.get(url=image_url, headers=self.headers)
                    time.sleep(random.random() + 0.1)
                    if response.status_code == 200:
                        self.save_image(response.content)
                except ConnectionError:
                    print("下载出错了...")
            os.chdir("../../张国荣")


if __name__ == '__main__':
    downimage = DownloadImages()
    downimage.download_images()
