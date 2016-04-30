#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os.path
import subprocess
import re
import requests

from getpass import getpass
from bs4 import BeautifulSoup

# set Redmine Top URL
domain = "path.to.redmine_domain"   # ex. www.redmine.org
#domain = "www.redmine.org"   # ex. www.redmine.org
base_url = u"http://{0}".format(domain)
base_dir = "./{0}/issues/".format(domain)

# ログイン有無(True:必要, False:不要)
isLogin = False

# チケット番号を記載したファイル名を記載
issues_id_list = "issues_id_list.txt"

# wget用の一時ファイル
wgetlist_name = "wget_list.txt"


def main():
    # チケットIDの取得とwget用のURLを作成
    issues_ids = []
    with open(issues_id_list, 'r') as f_r, open(wgetlist_name,'w') as f_w:
        for line in f_r:
            issues_ids.append(line.strip())
            s = '{0}/issues/{1}\n'.format(base_url,line.strip())
            f_w.write(s)

    # 対象がなければ終了
    if not issues_ids:
        print "no issue id"
        return

    # Redmineログイン
    if isLogin:
        username = raw_input('username: ')
        password = getpass('password: ')
        payload = {'username' : username, 'password' : password}

        # wget用ログイン
        cmd = "wget {0} --save-cookies=cookies.txt --keep-session-cookies".format(base_url + "/login")
        subprocess.call(cmd, shell=True)
        # wget実行
        cmd = "wget -pk -E -nc -w 3 --load-cookies=cookies.txt -i{0}".format(wgetlist_name)
        subprocess.call(cmd, shell=True)

        # 添付ファイル用ログイン
        r = requests.post(base_url + "/login", data=payload)

    else:
        # wget実行
        cmd = "wget -pk -E -nc -w 3 -i{0}".format(wgetlist_name)
        subprocess.call(cmd, shell=True)

    # 添付ファイル取得
    for issues_id in issues_ids:
        #解析するHTMLファイルパス
        target_html = base_dir + issues_id + ".html"
        #downloadファイルの格納先
        download_dir = base_dir + issues_id

        print "[{0}]start.".format(issues_id)
        if os.path.isfile(target_html):
            d = RedmineIssues(target_html,download_dir)
            d.downloadItems()
        else:
            print "htmlfile not exists."
        print "[{0}]end.".format(issues_id)


class RedmineIssues(object):

    def __init__(self,target_html,download_dir):
        self.download_urls = []
        self.target_html = target_html
        self.download_dir = download_dir
        self.__parseHTML()

    def __parseHTML(self):
        with open(self.target_html,'r') as file:
            html = file.read()

            soup = BeautifulSoup(html,'html.parser')

            # 添付ファイルの要素を抽出
            attachment_elements = soup.find_all('a', {'class': 'icon icon-attachment'})
            print attachment_elements

            pattern = u'href=".*?(/attachments/.*?)">'
            # download_lists = []
            for attachment in attachment_elements:
                search_href = re.search(pattern,str(attachment))
                if search_href:
                    download_url = base_url + search_href.group(1)
                    self.download_urls.append(download_url)

            print self.download_urls

        # for url in download_lists:
        #     # self.download_urls.append(base_url + url)
        #     self.download_urls.append(unicode(url,'utf-8'))

    def downloadItems(self):
        if self.download_urls: # one or more download file exitsts
            if not os.path.exists(self.download_dir):
                os.mkdir(self.download_dir)

            # ファイルのダウンロード
            for download_url in self.download_urls:

                # 負荷をかけないようにスリープ
                time.sleep(3)

                file_name = download_url.split("/")[-1]

                r = requests.get(download_url)
                if r.status_code == 200:
                    with open(self.download_dir + "/" + file_name, 'w') as file:
                        file.write(r.content)
                    print "downloaded file:{0}".format(file_name)
                else:
                    print "download error"
        else: #no download files
            print "download file not exists."


if __name__ == '__main__':
    main()
