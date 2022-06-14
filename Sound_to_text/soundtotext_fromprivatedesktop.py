from re import I
import sys, os, pathlib
from tracemalloc import start
from unittest import result

import soundfile as sf
import speech_recognition as sr
from io import BytesIO
import time
import math

from pydub import AudioSegment
from pydub.silence import split_on_silence

import binascii

from janome.tokenizer import Tokenizer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer # 元のアカウントだとエラーが出てる
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity

# =====================================================
# グローバル変数の定義
global soundtime
global soundduration
soundtime = [1]
soundduration = []


# =====================================================
# 説明
# Aviutlでカット編集まで終了した動画に対して、テキスト生成を行ったexoファイルを作成する
# 手順①　カット編集まで終了した動画の音声のみをエクスポート
# 手順②　音声のみをエクスポートしたファイルを読み込み、音声認識を行う
# 手順③　音声認識結果を台本データと照合して文字データの修正を行う
# 手順④　文字データをexoファイルとして出力する

# 手順①ではbgmを無効化したうえでエクスポートする

# ====================================================================

# exoファイルのテンプレートパラメータ
# ショート動画用
exedit_short ='[exedit]\n'\
'width=1080\n'\
'height=1920\n'\
'rate=30\n'\
'scale=1\n'\
'length=1796\n'\
'audio_rate=44100\n'\
'audio_ch=2\n'

# exoファイルのオブジェクトごとのテンプレートパラメータ
# ショート動画用
templete_short='[{}]\n'\
'start={}\n'\
'end={}\n'\
'layer=11\n'\
'overlay=1\n'\
'camera=0\n'\
'[{}]\n'\
'_name=テキスト\n'\
'サイズ=66\n'\
'表示速度=0.0\n'\
'文字毎に個別オブジェクト=0\n'\
'移動座標上に表示する=0\n'\
'自動スクロール=0\n'\
'B=0\n'\
'I=0\n'\
'type=0\n'\
'autoadjust=0\n'\
'soft=1\n'\
'monospace=0\n'\
'align=4\n'\
'spacing_x=0\n'\
'spacing_y=0\n'\
'precision=1\n'\
'color=ffffff\n'\
'color2=000000\n'\
'font=源ノ角ゴシック JP\n'\
'text={}\n'\
'[{}]\n'\
'_name=標準描画\n'\
'X=0.0\n'\
'Y=847.0\n'\
'Z=0.0\n'\
'拡大率=100.00\n'\
'透明度=0.0\n'\
'回転=0.00\n'\
'blend=0\n'

# =====================================================
# exoファイルのオブジェクトごとのテンプレートパラメータ
exedit ='[exedit]\n'\
'width=1440\n'\
'height=1080\n'\
'rate=30\n'\
'scale=1\n'\
'length=11420\n'\
'audio_rate=44100\n'\
'audio_ch=2\n'

templete='[{}]\n'\
'start={}\n'\
'end={}\n'\
'layer=7\n'\
'overlay=1\n'\
'camera=0\n'\
'[{}]\n'\
'_name=テキスト\n'\
'サイズ=46\n'\
'表示速度=0.0\n'\
'文字毎に個別オブジェクト=0\n'\
'移動座標上に表示する=0\n'\
'自動スクロール=0\n'\
'B=0\n'\
'I=0\n'\
'type=0\n'\
'autoadjust=0\n'\
'soft=1\n'\
'monospace=0\n'\
'align=1\n'\
'spacing_x=0\n'\
'spacing_y=0\n'\
'precision=1\n'\
'color=ffffff\n'\
'color2=000000\n'\
'font=源ノ角ゴシック JP\n'\
'text={}\n'\
'[{}]\n'\
'_name=標準描画\n'\
'X=0.0\n'\
'Y=271.0\n'\
'Z=0.0\n'\
'拡大率=100.00\n'\
'透明度=0.0\n'\
'回転=0.00\n'\
'blend=0\n'


# 文章中の漢数字を数値に変換する
def kansuji2num(text):
    # 漢数字を数値に変換する
    text = text.replace('一', '1')
    text = text.replace('二', '2')
    text = text.replace('三', '3')
    text = text.replace('四', '4')
    text = text.replace('五', '5')
    text = text.replace('六', '6')
    text = text.replace('七', '7')
    text = text.replace('八', '8')
    text = text.replace('九', '9')
    text = text.replace('十', '10')
    return text



def filec(message1, iDir):
    # モジュールのインポート
    import os, tkinter, tkinter.filedialog, tkinter.messagebox

    # ファイル選択ダイアログの表示
    root = tkinter.Tk()
    root.withdraw()
    # ファイル選択ダイアログを最前面に表示
    root.attributes("-topmost", True)
    fTyp = [("","*")]
    # iDir = os.path.abspath(os.path.dirname(__file__))
    tkinter.messagebox.showinfo(message1,'処理ファイルを選択してください！')
    file = tkinter.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)

    # 処理ファイル名の出力
    #tkinter.messagebox.showinfo('○×プログラム',file)
    #print(file)
    return(file)

# ====================================================================

def cut_over_soudfile(chunks, filename, output_dir):
    kaisuu = 0
    # 分割したデータの長さを出力
    sec = 0
    for i in range(len(chunks)):
        s = len(chunks[i])  # データの長さ
        sec += s
    print('split duration is ' + str(sec/1000) + ' sec')
    # 分割したデータ毎にファイルに出力
    for i, chunk in enumerate(chunks):
        # 取得したファイルのタイム
        # print('切り出した音声の長さ：'+ str(round(chunk.duration_seconds,1)))
        # 無音場面がないためタイムが合わない状態で出力される
        # そのため、無音データを時間を追加して記録する
        if len(soundtime) > 0:
            soundtime.append(round((soundtime[len(soundtime)-1])+(chunk.duration_seconds),1))
            soundduration.append(round(chunk.duration_seconds,1))
        else:
            soundtime.append(round(chunk.duration_seconds,1))
            soundduration.append(round(chunk.duration_seconds,1))
        # duration
        duration_in_milliseconds = len(chunk)
        # ファイルサイズが大きい場合に分割する
        if duration_in_milliseconds > 400000:
            print(duration_in_milliseconds)
            print("長すぎる音声ファイル")
            # split sound in 200-second slices and export
            for ii, slice in enumerate(chunk[::200000]):
                with open(output_dir + filename + str(kaisuu).zfill(3) + ".wav" , "wb") as f:
                    slice.export(f, format="wav")
                    kaisuu += 1
        else:
            file_path = output_dir + filename + str(kaisuu).zfill(3) + '.wav'
            chunk.export(file_path, format="wav")
            kaisuu += 1

# 入力した音声ファイルを無音分割して個別のwavファイルとして保存する
def sound_to_file(sound, filename, output_dir):
    # 1s当たり30frameで記録をとる
    # 16文字が1行には限界なので、1行に収める

    # wavデータの分割（無音部分で区切る）
    # min_silence_len=2000  2000ms以上無音なら分割
    # silence_thresh=-40    -40dBFS以下で無音と判定
    # keep_silence=600      分割後500msは無音を残す
    # 無音を残すkeep_silenceを長めにとらないと、音声認識上ですき間が開いてしいやすくなる
    # あとはmin_silence_len, silence_threshの調整が必要
    # 無音を残す
    chunks_true = split_on_silence(sound, min_silence_len = 700,
    silence_thresh = -40, keep_silence = True)
    # 無音を残さない
    # chunks_false = split_on_silence(sound, min_silence_len = 700,
    # silence_thresh = -40, keep_silence = False)
    cut_over_soudfile(chunks_true, filename + '_true', output_dir)
    # cut_over_soudfile(chunks_false, filename + '_false', output_dir)


# 粗い照合を行う
def janome_process_rough(text,daihons):
    def hinshi(ds,wakati_list):
        wakati = ''
        t = Tokenizer()
        for token in t.tokenize(ds):  # 形態素解析
            hinshi = (token.part_of_speech).split(',')[0]  # 品詞情報
            hinshi_2 = (token.part_of_speech).split(',')[1]
            if hinshi in ['名詞']:  # 品詞が名詞の場合のみ以下実行
                if not hinshi_2 in ['空白','*']:
                # 品詞情報の2項目目が空白か*の場合は以下実行しない
                    word = str(token).split()[0]  # 単語を取得
                    if not ',*,' in word:  # 単語に*が含まれない場合は以下実行
                        wakati = wakati + word +' '
                        # オブジェクトwakatiに単語とスペースを追加
        wakati_list.append(wakati) # 分かち書き結果をリストに追加
        return wakati_list
    wakati_list = []
    wakati_list = hinshi(text, wakati_list)
    for ds in daihons:
        wakati_list = hinshi(ds, wakati_list)
    wakati_list_np = np.array(wakati_list) # リストをndarrayに変換
    compare_list = compare_from_vector(wakati_list_np)
    match_value = sorted(compare_list)[-2]
    del compare_list[0]                    # 検証元の要素を削除
    indexs = [i for i, x in enumerate(compare_list) if x == match_value]
    # 値が１つだけ取得できた場合
    if len(indexs) == 1:
        daihon_target = daihons[indexs[0]]
    # 値が１つだけ取得できた場合以外、想定外の事象
    else:
        print('error please check progrom.\nselected [1]')
        daihon_target = text
    return daihon_target

# 詳細な照合を行う
def janome_process_detailed(text, daihon_target):
    def hinshi_detailed(text, wakati_list):
        t = Tokenizer()
        wakati = ''
        # print("========== " + text + " ===========")
        for token in t.tokenize(text):  # 形態素解析
            hinshi = (token.part_of_speech).split(',')[0]  # 品詞情報
            hinshi_2 = (token.part_of_speech).split(',')[1]
            word = str(token).split()[0]  # 単語を取得
            # print("対象:"+str(token).split()[0]+"\n品詞1:"+hinshi+"\n品詞2:"+hinshi_2)
            if hinshi in ['名詞','感動詞','助詞']:  # 品詞が名詞の場合のみ以下実行
                if not hinshi_2 in ['空白']:
                # 品詞情報の2項目目が空白か*の場合は以下実行しない
                    if not ',*,' in word:  # 単語に*が含まれない場合は以下実行
                        wakati = wakati + word +' '
                        # オブジェクトwakatiに単語とスペースを追加
                    else:
                        print('除外した単語:' + word)
        wakati_list.append(wakati) # 分かち書き結果をリストに追加
        return wakati_list
    wakati_list = []
    # 音声認識したテキストデータ
    wakati_list = hinshi_detailed(text, wakati_list)
    # 台本のテキストデータと音声認識したテキストデータを照合する
    try:
        wakati_list = hinshi_detailed(daihon_target, wakati_list)
        wakati_list_np = np.array(wakati_list) # リストをndarrayに変換
        compare_list = compare_from_vector(wakati_list_np)
        # 本来であれば精度が高ければ台本の文言をそのまま入力したいが…
        # 台本に忠実に話しているのであればそれが自動テロップのあるべき姿なのでは…？
        # 今のところ台本の文言をそのまま入力している　どうしたらいいんだ…？
        if compare_list[1] < 0.3:
            print('精度低：音声認識優先')
            print(compare_list[1])
            result = text
        elif compare_list[1] > 0.7:
            print('精度高：音声認識優先')
            print(compare_list[1])
            result = text
        else:
            print('精度中：音声認識優先')
            print(compare_list[1])
            result = text
    except:
        print('error please check progrom.\nselected [1]')
        print(wakati_list)
        result = text
    return result


def compare_from_vector(wakati_list_np):
    vectorizer = TfidfVectorizer(token_pattern=u'\\b\\w+\\b')
    transformer = TfidfTransformer()# transformerの生成。TF-IDFを使用
    tf = vectorizer.fit_transform(wakati_list_np) # ベクトル化
    tfidf = transformer.fit_transform(tf) # TF-IDF
    tfidf_array = tfidf.toarray()
    cs = cosine_similarity(tfidf_array,tfidf_array)  # cos類似度計算
    cs_list = cs.tolist()   # numpy配列を通常の配列に変換
    compare_list = cs_list[0]   # 元データと比較した要素のみを取得
    return compare_list

# 音声認識したファイルと台本データとの照合を行って正確度の高いテキストデータを生成
# 照合って何だ…？
# 誤差の値が大きい場合は、音声認識したデータと台本データが違うということであるので、台本データを優先する
# 引数は音声認識した文字データ
# まずは大まかな照合を行い、その後あたりをつけた台本データと詳細な照合を行う
# 台本のデータと大きく乖離している＞アドリブの部分のみ音声認識のデータを採用し、そのほかは台本データを参照する
def compare_daihon(text,lines):
    # 仮台本データ
    daihon_datas = lines
    # 台本データの中から適合するデータを抽出する
    daihon_target = janome_process_rough(text,daihon_datas)
    # 適合するデータと詳細な照合を行う
    result = janome_process_detailed(text, daihon_target.replace('\n',''))
    return result


# 音声認識を行う
def file_to_text(files, output_dir):
    r = sr.Recognizer()
    # foo = open('myfile.txt', 'a')
    text1 = None
    n=0
    texts = []
    for f in files:
        # print("読み込みファイル:" + f)
        # with sr.AudioFile("output_audio_file_0" + f'{n:02}'  + ".wav") as source:
        with sr.AudioFile(os.path.join(output_dir,f)) as source:
            audio = r.record(source)
            try:
                text = r.recognize_google(audio, language='ja-JP', show_all=False)
                # foo.write('\n')
                # foo.write(str(text))
                print("音声認識No{}:{}".format(n+1, text))
            except sr.RequestError as e:
                print(str(n) + ":Could not request results from Google Speech Recognition service; {0}".format(e))
                # foo.write("\n" + str(n) + ":Could not request results from Google Speech Recognition service; {0}".format(e))
                continue
            except:
                # foo.write("\n" + str(e) + ":" + str(n) + '--kesson--' + "\n")
                n+=1
                texts.append('')
                continue
            n+=1
            # print('置換する前:'+text)
            text = text.replace(' ','')
            text = kansuji2num(text)
            # print('置換した後:'+text)
            texts.append(text)
    # foo.close()
    return texts

# exoファイルに適用できる文字コードに変換
def encode_text(text):
    # UTF-16にエンコード＆16進数文字列(bytes)に変換
    byte_hex = binascii.hexlify(text.encode('UTF-16'))
    # デコード
    str_hex = byte_hex.decode()[4:]
    # 4096文字分の固定長形式にするため0埋め
    result = str_hex + "0" * (4096 - len(str_hex))
    return result

# 台本データを読み込んでベクトル比較を行う
def vectorization_of_daihon(results):
    result_list = []
    daihon_file = filec('台本ファイルを選択してください')
    with open(daihon_file,'r', encoding="utf-8") as f:
        lines = f.readlines()
        lines = [a for a in lines if a != '\n']  # 改行コードを削除
    for res in results:
        result = ''
        if res != '':
            result = compare_daihon(res,lines)
    return result_list

def make_frame_text(results, soundtime, soundduration):
    # フレームとテキスト情報をまとめた配列
    frame_text_list = []
    frame_text_list.append(['開始フレーム','終了フレーム','テキスト'])
    for r in range(len(results)):
        t = results[r]
        try:
            # 002.開始フレーム
            start_frame = soundtime[r] * 30
            print("開始フレーム:" + str(start_frame))
        except:
            start_frame = start_frame + 30
            print("開始フレーム:" + str(start_frame))
        # 003.終了フレーム
        if r == len(results)-1:
            try:
                end_frame = soundtime[r] * 30 + soundduration[r] * 30
                print("最終フレーム:" + str(end_frame))
            except:
                end_frame = end_frame + 30
                print("終了フレーム:" + str(end_frame))
        else:
            try:
                end_frame = (soundtime[r+1] * 30) - 1
                print("終了フレーム:" + str(end_frame))
            except:
                end_frame = end_frame + 30
                print("終了フレーム:" + str(end_frame))
        frame_text_list.append([start_frame,end_frame,t])
    return frame_text_list

def optimize_result_list(result_list):
    # 適当に分割すると文字数が短すぎるパターンがあるので対応する
    def split_hinsi(hinshi_2_list):
        val = ''
        ct = 0
        # 格助詞までで区切った文字を結合して文字数を測る
        # 30回繰り返したら強制的に脱出する
        while len(val) < 7:
            try:
                index = hinshi_2_list.index('格助詞')
            except:
                index = ''
            # 格助詞が見つからない場合は1を代入
            if index == '':
                index = 1
            val = ''.join([keitai_list[kl][2] for kl in range(len(hinshi_2_list)) if kl <= index])
            if len(val) < 7:
                hinshi_2_list[index]=''
            ct += 1
            if ct > 30:
                break
            # print(index)
        new_text = []
        remaining = []
        for kl in range(len(keitai_list)):
            if kl <= index:
                new_text.append(keitai_list[kl][2])
            else:
                remaining.append(keitai_list[kl][2])
        created_text = ''.join(new_text)
        remaining_text = ''.join(remaining)
        del hinshi_2_list[0:index+1]
        del keitai_list[0:index+1]
        return created_text, remaining_text

    opt_list = []
    t = Tokenizer()
    for r in range(len(result_list)):
        if r > 0:
            start = result_list[r][0]
            end = result_list[r][1]
            text = result_list[r][2]
            # テキストデータの文字数が27文字以下の場合はそのまま追加する
            # 27文字以上の場合は、形態素解析をかけて、結果に応じて文字とフレームを分割する
            if len(text) <= 27:
                opt_list.append(result_list[r])
            else:
                keitai_list = []
                hinshi_2_list = []
                new_text_list =[]
                # 形態素解析
                for token in t.tokenize(text):  # 形態素解析
                    hinshi = (token.part_of_speech).split(',')[0]  # 品詞情報
                    hinshi_2 = (token.part_of_speech).split(',')[1]
                    word = str(token).split()[0]  # 単語を取得
                    hinshi_2_list.append(hinshi_2)
                    keitai_list.append([hinshi,hinshi_2,word])
                print(keitai_list)
                # 格助詞を見つける なかった場合はエラーとなる
                # 関数化してループしないといけないな
                remaining = text
                while len(remaining) >=27:
                    # 格助詞で分割
                    new_text, remaining = split_hinsi(hinshi_2_list)
                    new_text_list.append(new_text)
                    print(len(remaining))
                    # print(new_text)
                    # print(remaining)
                new_text_list.append(remaining)
                print(''.join(new_text_list))
                separation_ct = len(new_text_list)
                add_time = math.floor((end - start) / (separation_ct))
                # 分割前
                for i in range(len(new_text_list)):
                    if i == len(new_text_list)-1:
                        opt_list.append([start,end,new_text_list[i]])
                    else:
                        opt_list.append([start,start+add_time,new_text_list[i]])
                        start += add_time + 1
    return opt_list





if __name__ == '__main__':
    print("音声認識を開始します")
    # text = compare_daihon("チャンネル登録者数1000人おめでとうございます")
    # print(exedit)
    # print(templete.format('exo_0', 'exo_0', 'exo_0', 'exo_0', 'exo_0', 'exo_0'))
    # 一時的に音声ファイルを出力するフォルダを作成
    # output_dir = os.sys.argv[0]
    result_dir = r"D:\My folder\youtube\006_自動化実験"
    output_dir = r"D:\My folder\youtube\006_自動化実験\output_audios"
    os.makedirs(output_dir, exist_ok=True)
    # 一時的に音声ファイルを出力するフォルダ
    output_dir = output_dir + '/'
    # 入力ファイル
    # ドラッグアンドドロップで渡されたファイルがあればそのファイルを対象に音声認識を実施する
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        file_path = input_file
        print(file_path)
    else:
        file_path = filec('wavファイルを選択してください', result_dir)
    print('ファイルが選択されました')
    # 入力ファイル(ドロップファイル)
    # file_path_drop = sys.argv[1]
    # 入力ファイルのファイル名のみを取得
    filename = pathlib.Path(file_path).stem
    # wavファイルを読み込む命令を実行
    sound = AudioSegment.from_file(file_path, format="wav")
    # sound = AudioSegment.from_file(r"D:\My folder\youtube\test.wav", format="wav")
    # 音声ファイルの切り出し
    # 切り出しが途中までしか行われていないエラー
    sound_to_file(sound, filename, output_dir)
    print('音声認識を開始します')
    # 音声認識
    output_files = os.listdir(output_dir)
    results = file_to_text(output_files, output_dir)
    print('音声認識を終了しました')
    # 台本照合
    # print('台本照合を開始します')
    # results = vectorization_of_daihon(results)
    # print('台本照合を終了しました')
    # print(results)
    # 切り出した音声ファイルを削除
    for f in output_files:
        os.remove(os.path.join(output_dir,f))
    # 切り出した音声ファイルを格納したフォルダを削除
    os.rmdir(output_dir)

    # フレームとテキストの整理
    result_list = make_frame_text(results, soundtime, soundduration)
    # 整理されたフレームとテキストを使って、画面内に収まる文字数で分割する
    result_list = optimize_result_list(result_list)

    # EXOファイルの形式の変換
    # テキストの開始位置がずれているのは無音部分が音声ファイルに取り込まれているため
    # ただし無音部分を削除するとタイミングが合わなくなってしまうため、そのままではいけない
    # このままではいけない、だからこそ、このままではいけないと思っている
    # 無音を取り込んだ音声ファイルと、無音を取り込まない音声ファイルを比較して、開始フレーム・終了フレームを調整してはどうか
    exo_content = []
    for r in range(len(result_list)):
        # テキストをエンコード
        t = encode_text(result_list[r][2])
        print(result_list[r][2])
        # print(t)
        # テンプレートパラメータを記入
        # 001.オブジェクト番号
        obj_num = r
        # 002.開始フレーム
        start_frame = result_list[r][0]
        print("開始フレーム:" + str(start_frame))
        # 003.終了フレーム
        if r == len(results)-1:
            end_frame = result_list[r][1]
            print("最終フレーム:" + str(end_frame))
        else:
            end_frame = result_list[r][1]
            print("終了フレーム:" + str(end_frame))
        # 004.オブジェクト名
        obj_name = "exo_" + str(r)
        # 004．オブジェクト項目
        obj_item = str(r) + '.0'
        # 005.テキスト
        text = t
        # 006.オブジェクト項目
        obj_item2 = str(r) + '.1'
        exo_content.append(templete.format(obj_num, start_frame, end_frame, obj_item, text, obj_item2))
    exo_output = exedit
    for ec in exo_content:
        exo_output += ec
    # print(exo_output)
    exo = os.path.join(result_dir,filename+'.exo')
    with open(exo,mode='w',encoding='shift_jis') as f:
        f.write(exo_output)
    print('end process...')


# =====================================================================

# https://qiita.com/ka201504/items/d7f6d78edaab8c0737c1