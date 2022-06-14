import sys,os,time
import binascii
import re


def Read_exo_file(exo_file):
    with open(exo_file, 'r', errors='ignore') as f:
        exo_texts = f.readlines()
    result = False
    for t in exo_texts:
        if "シーン" in t:
            result = True
            break
    return result

# シーン:タイトルのexoファイルから最終タイムとその文字のリストを作成する
# シーン:タイトルはexoファイル内に「シーン」という文字列を含まない
def Get_title(exo_file_list):
    lines = []
    lines2 = []
    for ex in exo_file_list:
        exo_title = Read_exo_file(ex)
        # exo_title = false の場合、シーン:タイトルのexoファイルである
        if exo_title == False:
            # exoファイルの中身を読み込み
            with open(ex, 'r', encoding='utf-8', errors='ignore') as f:
                for s_line in f:
                    a = re.search("^text=", s_line)
                    if a is None:
                        continue
                    # テキスト変換
                    text = s_line.replace("text=","").strip()
                    b = binascii.unhexlify(text)
                    s = str(b.decode("utf-16"))
                    lines.append(s)
            with open(ex, 'r', errors='ignore') as f:
                # ==================================
                for s_line in f:
                    if "start" in s_line:
                        start_time = s_line.replace("start=","").strip()
                        lines2.append(start_time)
            print(lines)


# 処理全体を記述する関数
def main():
    # 2つのexoファイルを受け取る
    if len(sys.argv) > 1:
        exo_file_list = sys.argv[1:]
    else:
        exo_file_list = [r"D:\My folder\youtube\006_自動化実験\エクスポートテスト.exo",r"D:\My folder\youtube\006_自動化実験\エクスポートテスト2.exo"]
    # exoファイルの中身を読み込む
    # シーン:タイトルから最終タイムとその文字のリストを作成する
    exo_title = Get_title(exo_file_list)
    # シーン:タイトルの最終タイムとその文字のリストを作成する
    # シーン:Rootのシーン10のスタートタイムとその文字のリストを作成する
    # スタートタイムよりもタイトルの最終タイムが小さい文字を取得してリストを作成する
    # スタートタイムをmm:ss形式に修正する
    # メモ帳に出力する

if __name__ == '__main__':
    main()