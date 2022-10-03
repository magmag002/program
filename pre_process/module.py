#!/usr/bin/env python
# coding: utf-8

# In[2]:
import csv
import MeCab
import urllib
import re
import unicodedata
import nltk
from nltk.corpus import wordnet
import pandas as pd
from operator import itemgetter


def lower_text(text):
    return text.lower()

def normalize_unicode(text, form='NFKC'):
    normalized_text = unicodedata.normalize(form, text)
    return normalized_text

def normalize_number(text):
    # 連続した数字を0で置換
    replaced_text = re.sub(r'\d+', '0', text)
    return replaced_text

def normalize_etc(normalized_text):
    # 「（」「）」はすべて半角に
    normalized_text= normalized_text.replace("(", "(")
    normalized_text = normalized_text.replace(")", ")")
    # 「（」「）」はすべて半角に
    normalized_text = normalized_text.replace("／", "/")
    normalized_text= normalized_text.replace("−", "-")
    normalized_text = normalized_text.replace("：", ":")
    #()の中身を削除
    normalized_text=re.sub(r'\([^)]*\)', '', normalized_text)
    normalized_text=re.sub("\【.+?\】", "", normalized_text)
    normalized_text=re.sub("\「.+?\」", "", normalized_text)
    # URL削除
    normalized_text= re.sub(r'(https?)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)', "",normalized_text)
    return normalized_text

#単語頻出度カウント
def WordFrequencyCount(word,wordFreq_dic):
        if word in wordFreq_dic:
            wordFreq_dic[word] +=1
 
        else:
            wordFreq_dic.setdefault(word, 1)
        return wordFreq_dic

def textParser_class_dic(text,wordFreq_dic):

    ## 分かち書きのみ
    tagger = MeCab.Tagger('-Owakati -d  /opt/homebrew/lib/mecab/dic/mecab-ipadic-neologd -u /opt/homebrew/lib/mecab/dic/userdic/userdic.dic ')

    ## バージョン２：品詞毎に取得
    #word_count = 0
    sentense = ""
    node = tagger.parseToNode(text)
    while node:
        #指定した品詞(category)のみ原型で抽出
        if node.feature.split(",")[0] == "動詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)

        elif node.feature.split(",")[0] == "名詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)

        elif node.feature.split(",")[0] == "形容詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)
         
        elif node.feature.split(",")[0] == "助動詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)
                
        else:pass
        node = node.next

    return (sentense,wordFreq_dic)

def textParser_class(text):

    ## 分かち書きのみ
    tagger = MeCab.Tagger('-Owakati -d  /opt/homebrew/lib/mecab/dic/mecab-ipadic-neologd -u /opt/homebrew/lib/mecab/dic/userdic/userdic.dic ')

    ## バージョン２：品詞毎に取得
    #word_count = 0
    sentense = ""
    node = tagger.parseToNode(text)
    while node:
        #指定した品詞(category)のみ原型で抽出
        if node.feature.split(",")[0] == "動詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                #wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)

        elif node.feature.split(",")[0] == "名詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                #wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)

        elif node.feature.split(",")[0] == "形容詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                #wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)
         
        elif node.feature.split(",")[0] == "助動詞":
            if node.feature.split(",")[6] !="*":
                sentense += " "+node.feature.split(",")[6] 
                #wordFreq_dic=WordFrequencyCount(node.feature.split(",")[6],wordFreq_dic)
                
        else:pass
        node = node.next

    return (sentense)
    
def create_stopwords():
    stopwords=[]
    # Defined by SlpothLib
    slothlib_path = 'http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/Japanese.txt'
    slothlib_file = urllib.request.urlopen(slothlib_path)
    slothlib_stopwords = [line.decode("utf-8").strip() for line in slothlib_file]
    slothlib_stopwords = [ss for ss in slothlib_stopwords if not ss==u'']

    # Merge and drop duplication
    stopwords += slothlib_stopwords
    stopwords = list(set(stopwords))

    return(stopwords)
    
def create_token(text,stopwords):
    token=[]
    for w in text:
        if not w in stopwords:
            token.append(w)
    return(token)

#いか感情分析
def _make_dict():
    #ファイルのパスは動かしているメインのプログラムから見た場所になるためこれで良い
    df_word_dict = pd.read_csv('./pre_process/dic/list_word_out.csv',encoding='cp932')#名詞
    df_wago_dict = pd.read_csv('./pre_process/dic/list_wago_out.csv',encoding='cp932')#用言
    df_polarity_dict = pd.read_csv('./pre_process/dic/polarity_dic.csv',encoding='utf-8')#金融極性辞書

    word_dict = {}
    for pair_list in df_word_dict[['word','score']].values.tolist():
        if pair_list[1] !='0':
            word_dict[pair_list[0]] = pair_list[1]

    wago_dict = {}
    for pair_list in df_wago_dict[['word','score']].values.tolist():
        if pair_list[1] !='0':
            wago_dict[pair_list[0]] = pair_list[1]
            
    p_dict = {}
    for pair_list in df_polarity_dict[['word','score']].values.tolist():
        if pair_list[1] !='0':
            p_dict[pair_list[0]] = pair_list[1]

    return word_dict,wago_dict,p_dict

#dicがJなら日本語極性辞書，Pなら金融極性辞書
def pos_neg(dic,text_list):
    #辞書呼び出し
    word_dict,wago_dict,p_dict = _make_dict()
    #否定語の作成
    NEGATION = ('ない', 'ず', 'ぬ','ん')
    #score listの作成
    score_list=[]
    #NEGATIONとそれによるスコア反転前のスコアを返す
    return_list=[]
    pn_cnt= 0# word_dict　に対応する感情値の数
    negation_len = []
    pn_score = 0
    #辞書選択
    if dic == "J":
        
        #辞書選択
        for word in text_list:
            if word in word_dict:
                score_list.append(word_dict[word])
                return_list.append(word_dict[word])
                pn_cnt+=1
                
            elif word in wago_dict:
                score_list.append(wago_dict[word])
                return_list.append(wago_dict[word])
                pn_cnt+=1
            elif word in NEGATION:
                score_list.append(0)
                return_list.append("NEGATION")
                negation_len.append(len(score_list)-1)

            else:
                score_list.append(0)
                return_list.append(None)
    
    #辞書選択
    if dic =="F":
        
        for word in text_list:
            
            if word in NEGATION:
                score_list.append(0)
                return_list.append("NEGATION")
                negation_len.append(len(score_list)-1)
            elif word in p_dict:
                score_list.append(p_dict[word])
                return_list.append(p_dict[word])
                pn_cnt+=1
            
            else:
                score_list.append(0)
                return_list.append(None)
    
    #scoreの算出
    if negation_len!=[]:
        #negationがあったときの処理
        for i in negation_len:
            score_list[i-1] *= -1
            pn_score += sum(score_list[:i-1])

    if pn_cnt!=0:
        pn_score = sum(score_list) / pn_cnt
    else:
        pn_score=0
        
    return(return_list,pn_score)

def return_dic(text,wordFreq_dic):
    stopwords=create_stopwords()
    norm_text = normalize_unicode(text)
    norm_text = normalize_number(norm_text)
    norm_text = lower_text(norm_text)
    norm_text = normalize_etc(norm_text)
    new_text,wordFreq_dic=textParser_class_dic(norm_text,wordFreq_dic)
    return(new_text,wordFreq_dic)

def text_all(text):
    stopwords=create_stopwords()
    norm_text = normalize_unicode(text)
    norm_text = normalize_number(norm_text)
    norm_text = lower_text(norm_text)
    norm_text = normalize_etc(norm_text)
    new_text=textParser_class(norm_text)
    new_text=new_text.split()
    return_token=create_token(new_text,stopwords)
    return return_token