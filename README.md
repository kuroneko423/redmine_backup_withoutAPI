# はじめに
RedmineのAPIを利用できない状況において、csvではなく、
見た目毎そのまま残しておきたい状況へ対処するためのもの。
チケットに相当するhtmlファイル、および添付ファイルを取得する。
Redmineで用意されているAPIを利用せず、
wgetおよびpythonのrequestsにて１ファイルずつゆっくり取得する。
なお、本来はAPIを利用して実行すべきであり
どの程度Redmineサーバ側に負荷がかかるか次第で使い方に注意すること。

## 構成
1. issues_id_list.txt
2. redmine_backup_withoutAPI.py

1はバックアップしたいチケット番号のリストを記載したものである。
ここに記載されたチケット番号が取得対象となる。
2はプログラム本体。

## 前提
* wgetが実行可能であること
* pythonの下記モジュールがインストール(pip install)されていること
  * requests
  * urllib
  * BeautifulSoup 4
* Python 2.7.11で動作確認
* Redmineにログイン可能であること

## 実行方法
構成に示した２つファイルを同一ディレクトリ配下に格納して実施する。
実行方法は下記の通り。

    # python redmine_backup_withoutAPI.py

実行すると、ソースコードと同一配下にバックアップが格納される。
