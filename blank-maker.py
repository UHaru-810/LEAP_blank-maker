import csv
import requests
from bs4 import BeautifulSoup
import re
from time import sleep

def scraping(orig_word):
    url = 'https://www.ei-navi.jp/dictionary/content/' + orig_word
    html = requests.get(url)

    # 探索して見つかった単語を保持
    searched_set = set()

    soup = BeautifulSoup(html.text, 'html.parser')
    # クラスが"pattern"のdiv内のすべてのli要素を見つける
    li_elements = soup.select('.pattern li')
    # 各li要素のテキストコンテンツを抽出する
    for li in li_elements:
        text = li.get_text(strip=True)
        jp_pattern = re.compile('[\u3040-\u309F\u30A0-\u30FF一-龠々〆〤]+')  # 日本語のUnicode範囲を指定
        # 日本語・発音記号を排除した英単語のみを追加
        tmp = re.sub(jp_pattern, '', text)
        # more, mostが空欄になるのを防ぐ
        if tmp.split()[0] != 'more' and tmp.split()[0] != 'most':
            searched_set.add(re.sub(jp_pattern, '', text).split()[0])

    return searched_set


# words.csvの読み込み
with open('words.csv', 'r', newline='', encoding='utf-8-sig') as file:
    # CSVファイルの読み込み
    reader = csv.reader(file)

    #単語のリストに加える
    words = []
    for element in reader:
        words.append(element[0]) #1列しかないため[0]

# sentences.csvの読み込み
with open('sentences.csv', 'r', newline='', encoding='utf-8-sig') as file:
    # CSVファイルの読み込み
    reader = csv.reader(file)

    #例文のリストに加える
    sentences = []
    for element in reader:
        sentences.append(element[0]) #1列しかないため[0]

# 例文の空欄を作成済みかを記録する
    finished = [False] * len(sentences)
# 結果(空欄例文と正解)を入れる二次元配列
    result = [['', '']] * len(sentences)
# 全会一致する単語が見つかった時のindex
    prev_index = 0

for word in words:
    # 探索した単語のリスト
    searched_list = list(scraping(word))

    # 検索時にうまくいくように原形をリスト変換後最後に追加
    searched_list.append(word)
    prev_index = 0
    
    for index, sentence in enumerate(sentences):
        # 空欄が作成済み または prev_indexが0でないかつ単語が違うものになったらcontinue (別の場所での意図しない同単語の使用による誤動作を防ぐ)
        # 本当は>1にしたいところではあるが、Not Foundを考慮して>6 (1つの単語の例文の最大数=6)
        if (finished[index] or (prev_index != 0 and index - prev_index > 6)): 
            continue
        # 初期の状態では見つからなかったこととすることで、そのあと更新されなければ見つからなかったと判定
        result[index] = [sentence, 'Not Found'] 
        for searched_word in searched_list:
            # 単語境界または文頭・文末の正規表現
            bd_pattern_lw = re.compile(rf'(\b|^|-){re.escape(searched_word)}(\b|$|-)') 
            bd_pattern_cp = re.compile(rf'(\b|^|-){re.escape(searched_word.capitalize())}(\b|$|-)') # 先頭が大文字

            if re.search(bd_pattern_lw, sentence):
                blank_sentence = sentence.replace(searched_word, '(　　)') # (　)で置き換え
                finished[index] = True # 空欄作成済みにする　
                result[index] = [blank_sentence, searched_word] # 結果の配列に追加(空欄例文, 正解)
                prev_index = index
                print('{} / {}\033[32m  {}%  \033[0m{} : \033[36m{}\033[0m'.format(index+1, len(sentences), int((index+1)/len(sentences)*100), blank_sentence , searched_word)) # 進捗表示
                break
            elif re.search(bd_pattern_cp, sentence): # 先頭に大文字を含む単語を含むとき
                blank_sentence = sentence.replace(searched_word.capitalize(), '(　　)') # (　)で置き換え
                finished[index] = True # 空欄作成済みにする
                result[index] = [blank_sentence, searched_word.capitalize()]
                prev_index = index
                print('{} / {}\033[32m  {}%  \033[0m{} : \033[36m{}\033[0m'.format(index+1, len(sentences), int((index+1)/len(sentences)*100), blank_sentence , searched_word.capitalize())) # 進捗表示
                break
    sleep(0.5)

# CSVファイル書き出し
with open('output.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerows(result)

print('\033[32m', 'COMPLETED!', '\033[0m')