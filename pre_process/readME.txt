使用するプログラムと同じフォルダにこのファイルごと置いてください

moduleに関数が格納されている
dicに日本語極性辞書と金融極性辞書が格納

import pre_process.module
で使用可能

text_all（text)でテキストを分かち書きしたlistに返り値として送る

これで帰ってきたlistをpos_neg(dic,text_list)で感情分析を行う
第１返り値が極性単語の場所と極性値のlist
第２返り値が感情値となっている

dicは”J"が日本語極性辞書
”F”が金融極性辞書

例）
import pre_process.module as pp
token = pp.text_all（text)
pn_list,pn_score=pp.pos_neg("J",token)