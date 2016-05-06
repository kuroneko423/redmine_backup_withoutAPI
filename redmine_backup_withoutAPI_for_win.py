#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import os.path
import subprocess
import re
import requests
import urllib

from getpass import getpass
from bs4 import BeautifulSoup

# ドメイン名(wget時のディレクトリ名に相当)
domain = "path.to.domain"   # ex. www.redmine.org
# ドメイン以下のプロジェクト名までのパス
project = "path.to.project"   # ex. redmine

base_url = u"http://{0}/{1}".format(domain,project)
base_dir = "./{0}/{1}/issues/".format(domain,project)

# ログイン有無(True:必要, False:不要)
isLogin = True

# チケット番号を記載したファイル名を記載
issues_id_list = "issues_id_list.txt"

# (一時ファイル)cookiesファイル名
cookies_file_name = "cookies.txt"

# (一時ファイル)loginファイル名
login_file_name = "login.txt"

# (一時ファイル)wget用ファイル
wgetlist_name = "wget_list.txt"

# wait間隔(s)
wait_time = 3

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

    # Redmineインスタンスの作成
    d = Redmine(isLogin)

    # ログインに失敗していたらクローズ
    if d.getResultLogin():
        # htmlファイル取得
        d.wget()

        # 添付ファイル取得
        for issues_id in issues_ids:
            #解析するHTMLファイルパス
            target_html = base_dir + issues_id + ".html"
            #downloadファイルの格納先
            download_dir = base_dir + issues_id

            print "[{0}]start.".format(issues_id)
            if os.path.isfile(target_html):
                d.downloadItems(target_html,download_dir)
            else:
                print "[WARN]htmlfile not exists."
            print "[{0}]end.".format(issues_id)

    # 一時ファイルを削除
    if os.path.exists(cookies_file_name):
        os.remove(cookies_file_name)
    if os.path.exists(login_file_name):
        os.remove(login_file_name)
    if os.path.exists(wgetlist_name):
        os.remove(wgetlist_name)


class Redmine(object):
    u'''Redmineを扱うクラス
    Attributes:
        isLogin:A boolean indicating if Redmine login need
    '''

    def __init__(self,isLogin):
        self.isLogin = isLogin
        self.resultLogin = True
        self.__inputAuth()

    def __inputAuth(self):
        u'''Redmineにログイン処理に必要な情報を取得
        '''
        if self.isLogin:
            self.username = raw_input('username: ')
            self.password = getpass('password: ')
            self.payload = {'username' : self.username, 'password' : self.password}

            # wget用ログイン処理
            cmd = 'wget {0} -O {1} --save-cookies={2} --keep-session-cookies --post-data "username={3}&password={4}"'.format(base_url + "/login",login_file_name,cookies_file_name,self.username,self.password)
            subprocess.call(cmd, shell=True)
            with open(login_file_name,'r') as file:
                html = file.read()
                if not self.__checkError(html):
                    self.resultLogin = False
                    print "[ERROR](wget)login is NG."
                    return

            # Redmineログイン処理
            self.s = requests.session()
            r = self.s.post(base_url + "/login", data=self.payload)
            if r.status_code == 200:
                if not self.__checkError(r.text):
                    self.resultLogin = False
                    print "[ERROR](requests)login is NG."
            else:
                print "[ERROR]status_code : " + r.status_code
                self.resultLogin = False


    def getResultLogin(self):
        u'''ログイン結果を返却。
        '''
        return self.resultLogin


    def __checkError(self,html):
        u'''HTML内にRedmineでのErrorに相当するタグが含まれているかチェックする。
            含まれていた場合にはNG(False)とする。
        '''
        soup = BeautifulSoup(html,'html.parser')
        error_elements = soup.find_all('div', {'class': 'flash error'})
        if error_elements:
            return False
        return True


    def wget(self):
        u'''wgetコマンドを利用してRedmineの該当チケット番号のHTMLファイルを
            丸ごと持ってくる。
        '''
        # Redmineログイン
        if self.isLogin:
            # wget実行
            cmd = "wget -pk -E -nc -w {0} --load-cookies={1} -i {2}".format(wait_time, cookies_file_name, wgetlist_name)
            subprocess.call(cmd, shell=True)
        else:
            # wget実行
            cmd = "wget -pk -E -nc -w {0} -i {1}".format(wait_time, wgetlist_name)
            subprocess.call(cmd, shell=True)


    def __parseHTML(self):
        u'''ダウンロードしたhtmlファイルを解析し、添付ファイルのURLを取得する
        '''
        #初期化
        self.download_urls = []

        with open(self.target_html,'r') as file:
            html = file.read()

            # errorが出ていないかチェック
            if self.__checkError(html):

                # 添付ファイルの要素を抽出
                soup = BeautifulSoup(html,'html.parser')
                attachment_elements = soup.find_all('a', {'class': 'icon icon-attachment'})

                pattern = u'href=".*?(/attachments/.*?)">'
                for attachment in attachment_elements:
                    search_href = re.search(pattern,str(attachment))
                    if search_href:
                        download_url = base_url + search_href.group(1)
                        self.download_urls.append(download_url)
            else:
                print "[ERROR]could not get download urls."


    def downloadItems(self,target_html,download_dir):
        u'''添付ファイルのURLに沿ってファイルを取得する。
            __parseHTMLにて解析した結果のURLを用いる。
            なお、wgetにてhtmlファイルが格納されていることを前提とする。
        '''
        self.target_html = target_html
        self.download_dir = download_dir

        self.__parseHTML()

        if self.download_urls: # one or more download file exitsts
            #ディレクトリがなければ作成
            if not os.path.exists(self.download_dir):
                os.mkdir(self.download_dir)

            for download_url in self.download_urls:
                # 負荷をかけないようにスリープ
                time.sleep(wait_time)

                # download_urlはunicodeなのでそのままでは使えない。
                # unicode->utf-8変換を行い、その後にURLデコードすることで
                # マルチバイト文字に対応する。
                # windowsだとうまく動かないので修正。
                # file_name = urllib.unquote(download_url.split('/')[-1]).encode('utf-8')
                file_name = urllib.unquote(download_url.split('/')[-1].encode('utf-8')).decode('utf-8')

                # ファイルのダウンロード
                if self.isLogin:
                    d = self.s.get(download_url, stream=True)
                else:
                    d = requests.get(download_url, stream=True)
                if d.status_code == 200:
                    with open(self.download_dir + "/" + file_name, 'wb') as file:
                        for chunk in d.iter_content(chunk_size=1024):
                            if chunk:
                                file.write(chunk)
                                file.flush()
                    # print "downloaded file:{0}".format(file_name)
                    print "[INFO]downloaded file:" + file_name
                else:
                    print "[ERROR]download error"
        else: #no download files
            print "[INFO]download file not exists."


if __name__ == '__main__':
    main()
