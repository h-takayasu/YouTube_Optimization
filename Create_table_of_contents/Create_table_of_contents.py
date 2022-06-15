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
    text_lines = []
    time_lines = []
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
                    text_lines.append(s)
            with open(ex, 'r', errors='ignore') as f:
                # ==================================
                for s_line in f:
                    if "start" in s_line:
                        start_time = s_line.replace("start=","").strip()
                        time_lines.append(start_time)
            # タイムとテキストのリストを再生成
            time_lines_new = []
            for t in range(len(text_lines)):
                time_lines_new.append([time_lines[t],text_lines[t].replace("\x00","").replace("ｘ","")])
            print(time_lines_new)
    return time_lines_new

# 読み込んだexoファイルからシーン10のスタートタイムを作成する
def Get_scene(exo_file_list):
    time_lines = []
    for ex in exo_file_list:
        exo_title = Read_exo_file(ex)
        # exo_title = false の場合、シーン:タイトルのexoファイルである
        if exo_title == True:
            with open(ex, 'r', errors='ignore') as f:
                lines = f.readlines()
            # ==================================
            for l in range(len(lines)):
                if "start" in lines[l]:
                    start_time = lines[l].replace("start=","").strip()
                    # シーンであれば
                    if "シーン" in lines[l+6]:
                        if "再生位置" in lines[l+7]:
                            play_position = lines[l+7].replace("再生位置=","").strip()
                        if "10" in lines[l+10]:
                            time_lines.append([start_time,play_position])
    print(time_lines)
    return time_lines

# スタートタイムよりもタイトルの最終タイムが小さい文字を取得してリストを作成する
def Get_time(title_list,scene_list):
    # title_timeがtitle_listのどこにあるかを調べてそのインデックスを返す
    def Get_time_index(title_list,title_time):
        i = 0
        while i < len(title_list):
            flag = False
            if title_time >= title_list[i][0]:
                j = i
                while j < len(title_list):
                    if title_time <= title_list[j][0]:
                        flag = True
                        break
                    j += 1
            if flag == True:
                break
            i += 1
        if j > 0:
            j = j-1
        return j
    result_list = []
    for sl in range(len(scene_list)):
        list_value = scene_list[sl]
        # aviのタイムライン上のタイム
        avi_time = list_value[0]
        # シーン10上のタイム
        title_time = list_value[1]
        index = Get_time_index(title_list,title_time)
        title_text = title_list[index][1]
        result_list.append([avi_time,title_text])
    print(result_list)
    return result_list

# aviutlのタイム表記をmm:ssに変換する
def fix_time(result_list):
    result = []
    for rl in range(len(result_list)):
        time_value = result_list[rl][0]
        time_value = int(time_value) / 30
        # 秒数をmm:ss形式に変換する
        m = time_value // 60
        s = time_value % 60
        fix_time = str(int(m)) + ":" + str(int(s))
        result.append([fix_time,result_list[rl][1]])
    return result

# 処理全体を記述する関数
def main():
    # 2つのexoファイルを受け取る
    if len(sys.argv) > 1:
        exo_file_list = sys.argv[1:]
    else:
        exo_file_list = [r"D:\My folder\youtube\006_自動化実験\エクスポートテスト.exo",r"D:\My folder\youtube\006_自動化実験\エクスポートテスト2.exo"]
    # exoファイルの中身を読み込む
    # シーン:タイトルから最終タイムとその文字のリストを作成する
    title_list = Get_title(exo_file_list)
    # シーン:Rootのシーン10のスタートタイムとその文字のリストを作成する
    scene_list = Get_scene(exo_file_list)
    # スタートタイムよりもタイトルの最終タイムが小さい文字を取得してリストを作成する
    time_list = Get_time(title_list,scene_list)
    unique_list = []
    text_list = []
    for tl in range(len(time_list)):
        text_value = time_list[tl][1]
        if text_value not in text_list:
            unique_list.append(time_list[tl])
            text_list.append(text_value)
    # スタートタイムをmm:ss形式に修正する
    result_list = fix_time(unique_list)
    # プロンプトに出力する
    print('\r\n===============================================')
    print('0:00 はじめに')
    for rl in range(len(result_list)):
        print(result_list[rl][0] + " " + result_list[rl][1])
    print('\r\n===============================================')
    val = input("終了するにはEnterを押してください")


if __name__ == '__main__':
    main()