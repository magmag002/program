#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pylab as plt
import math
import csv

#選択行削除
import re
from xml.sax.saxutils import unescape

def normalize_XBRL(XBRL):
    with open(XBRL, encoding='utf-8') as f:
        html = f.read()
    # 「（」「）」はすべて半角に
    html = html.replace("（", "(")
    html = html.replace("）", ")")
    #tableタグだけ残す，それ以外のタグで囲まれていない部分を削除
    html  = re.sub("<table", "table\n<", html)
    html  = re.sub("</table", "tableend\n<", html)
    html  = re.sub("<br />", "", html)
    html  = re.sub("<td", "td<", html)
    html  = re.sub("</td>", "tdend\n", html)
    html  = re.sub("</tr>", "trend", html)

    text=""
    for i in html:
        text=text+i
        if i ==">":
            text=re.sub("<.*>", "", text)
            text=re.sub("{.*}", "", text)
            if text[-1:]!="\n":
                text = text+"\n"
    text1=text

    #テキスト処理
    text1=re.sub("&#160;", "None", text1)
    text1=re.sub("△\n", "-", text1)
    text1=re.sub("△", "-", text1)
    text1=re.sub(".root", "-", text1)
    text1=re.sub(",", "", text1)
    text1=re.sub("．", ".", text1)
    text1=re.sub("\ufeff\n", "", text1)
    text1=re.sub("－", "None", text1)
    text1=re.sub("：", "", text1)
    text1=re.sub(" ", "", text1)
    text1=re.sub("\n\n", "\n", text1)
    text1=re.sub("　", "", text1)

    return(text1)

def text_tag(text):
    #予測がいつまでなのかを取得
    pre_cnt=0
    pre = ""
    for i in range(len(text),-1,-1):
        if "連結業績予想(" in text[i-7:i]:
            pre_cnt=i
            break
    for i in range(pre_cnt,-1,-1):
        if "." in text[i-1:i]:
            pre = text[i:pre_cnt-1]
            break

    #tdで囲まれた部分の改行は削除して，tdを削除
    tx=""
    text1=""
    td_flag=False
    for i in text:
        #print(i)
        if "tdend" in text1:
            td_flag=False
        if "td" in text1:
            td_flag=True

        if td_flag:
            if i=="\n":
                i=""
        text1+=i
    text1=re.sub("tdend", "", text1)
    text1=re.sub("td", "\n", text1)
    text1=re.sub(r"\n+", "\n", text1)
    return(text1,pre)

def create_text_list(text):
    
    #tableタグで囲まれた部分をリストに入れる
    text_list = []
    cnt_first=0
    cnt_end=0
    append_text=""
    for i in range(1,len(text)):
        if text[i-8:i] == "tableend":
            cnt_end = i-8
            append_text=text[cnt_first:cnt_end]+"\n"
            append_text=re.sub("trend\ntrend","trend\n",append_text)
            append_text=re.sub("tableendtable","",append_text)
            append_text=re.sub(r'\n+', "\n",append_text)
            text_list.append(append_text)
            cnt_first=0
            cnt_end=0
        elif text[i-5:i] == "table":
            if cnt_first==0:
                cnt_first=i
    
    #listの中に（注）がある部分は削除する         
    pop_list=[]
    cnt=0
    for i in text_list:

        if "(注)" in i :
            pop_list.append(cnt)
        elif "(参考)" in i:
            pop_list.append(cnt)
        elif "(役職名)" in i:
            pop_list.append(cnt)
        cnt +=1

    for i in pop_list[::-1]:
        #print(i)
        text_list.pop(i)
    return(text_list)


def create_table_list(text_list):
    #\nが１０個以下の部分は表ではないので削除
    table_list = []
    kari_list = []
    pop_cnt = 0
    end_flag=False
    for i in text_list:
        if i.count("\n") > 9:
            table_list.append(i)
    #発行株式数の表だけ作りが違うため今回は削除
    table_list = table_list[:6]

    #配当金のグラフは変則的なので最後に回す
    for cnt, i in enumerate(table_list):
        if "配当金" in i:
            text = i
            if "配当金総額" in text:
                end_flag=True
            text= text.replace("(","")
            text = text.replace(")","")
            text = re.sub("連結trend","連結",text)
            kari_list=text
            pop_cnt = cnt

        if "通期" in i:
            table_list[cnt]= table_list[cnt].replace("売上高","check売上高")
            break
    table_list.pop(pop_cnt)
    table_list.append(kari_list)
    #tableが出てきたら削除
    #最初のtrendまでに\nが一回しか出ていなければ削除
    return(table_list,end_flag)          

def create_list(table_list):
    number_list = []
    col_list=[]
    number = []
    col=""
    num_cnt=0
    col_cnt=0
    len_col=0
    add_col=0
    for table in table_list:
        if "table" in table:
            table=table[table.find("table")+5:]
        for i in range(0,len(table)):
            if table[i:i+5] !="trend":
                if table[i:i+1] == "\n":
                    col=table[col_cnt+1:i]
                    add_col+=1
                    if col=="" and col_list!=[] and len_col==0:
                        len_col=len(col_list)
                    if col!="":
                        col_list.append(col)
                    col_cnt=i
            else:
                col=table[col_cnt+1:i]
                col_list.append(col)
                #追加したコラムが１つだけなら削除してやり直し
                if add_col==1:
                    add_col=0
                    col_list.pop(-1)
                    col_cnt=i+5
                    continue
                add_col=0
                num_cnt=i+5
                break   
        #column以降にある数字の部分を回す
        for i in range(num_cnt,len(table)+1):
            if table[i:i+1] == "\n":
                if table[i-5:i]=="trend":
                    if number!=[]:
                        number.append(table[num_cnt+1:i-5])
                        number_list.append(number)
                        number=[]
                        num_cnt=i

                elif table[i-5:i]!="trend":
                    number.append(table[num_cnt+1:i])
                    num_cnt=i
    
    [col_list.insert(k, col_list[k]) for k in range(len_col-1,-1,-1)]
    
    return(col_list,number_list)


def create_None(column,number):
    #Noneが連続している場合は削除
    drop_list=[]
    number_list=[]
    for i in range(0,len(column)):
        if column[i] =="None":
            #if column[i+1]=="None":
            drop_list.append(i)
    for i in drop_list[::-1]:
        #print(i)
        column.pop(i)
        
    #numberにNoneを入れる
    for num in number:
        if "円銭" in num or "百万円" in num:
            if "None"  not in num:
                num.insert(0,"None")
        number_list.append(num)
    
    return(column,number)


def create_DataFrame(number,end_flag):
    new_df = pd.DataFrame
    new_df2 = pd.DataFrame
    new_df3 = pd.DataFrame
    new_df4=pd.DataFrame
    kari_df = pd.DataFrame
    index_list = ["None"]
    df4_flag=False
    #学期末なら空リスト，それ以外なら，頭に追加
    if end_flag:
        index2_list=[]
    else:
        index2_list=["None"]
        
    marge_cnt = 0
    number_cnt = 1
    cnt = 0
    none_cnt=0
    flag=False
    flag_data=False
    #indexが同じ部分は横につなげる
    for i in range(1,len(number[number_cnt])):
        number_cnt +=1
        if number[i][0]== "None":
            new_df = pd.DataFrame([number[k][1:] for k in range(0,3)],index=[index_list])
            marge_cnt = i
            break
        else:
            index_list.append(number[i][0])
            cnt=i+1
    #同じインデックスでは横に並べる
    len_num = len(index_list)
    k = 1
    for i in range(cnt,len(number)):
        if number[i][0]==index_list[k]:
            k+=1
            if k ==len_num:
                kari_df = pd.DataFrame([number[marge_cnt+j][1:] for j in range(0,i-marge_cnt+1)],index=[index_list])
                new_df=pd.concat([new_df,kari_df],axis=1)
                marge_cnt = i+1
                k=1
                flag=True
        elif number[i][0] =="None":
            none_cnt=i
        elif number[i][0]!="None" and flag:
            [index2_list.append(number[k][0]) for k in range(i-1,len(number))]
            cnt=i
            break
     #それ以外を別のDataFrameに   
    for i in range(none_cnt,len(number)-1):
        if number[i+1][0]=="None":
            new_df2 = pd.DataFrame([number[none_cnt+k][1:] for k in range(0,i-none_cnt+1)],index=[index2_list[0:i-none_cnt+1]])
            none_cnt=i+1
            break
    
    #dataftame３
    if end_flag:
        #dataftame３
        for i in range(none_cnt,len(number)-1):
            if number[i+1][0]=="None":
                new_df3 = pd.DataFrame([number[none_cnt+k][1:] for k in range(0,i-none_cnt+1)],
                                       index=index2_list[new_df2.shape[0]:new_df2.shape[0]+i-none_cnt+1])
                none_cnt=i
                flag_data = True
                break

        new_df3 = pd.DataFrame([number[none_cnt+k][1:] for k in range(0,i-none_cnt+2)],
                               index=index2_list[new_df2.shape[0]:new_df2.shape[0]+i-none_cnt+2])
        
    else:
        for i in range(none_cnt,len(number)-1):
            if number[i+1][0]=="None":
                new_df3 = pd.DataFrame([number[none_cnt+k][1:] for k in range(0,i-none_cnt+1)],
                                       index=index2_list[new_df2.shape[0]:new_df2.shape[0]+i-none_cnt+1])
                none_cnt=i
                flag_data = True
                break

        if flag==False:
            #print(number[i:],none_cnt,i)
            #print(index2_list[new_df2.shape[0]:new_df2.shape[0]+i-none_cnt+1])
            new_df3 = pd.DataFrame([number[none_cnt+k][1:] for k in range(0,i-none_cnt+2)],
                                   index=index2_list[new_df2.shape[0]-1:new_df2.shape[0]+i-none_cnt+1])

        if none_cnt != len(number):
            new_df4=pd.DataFrame([number[none_cnt+k][1:] for k in range(1,len(number)-none_cnt)],
                                 index=[index2_list[-(len(number)-none_cnt-1):]])
            df4_flag=True

    return(new_df,new_df2,new_df3,new_df4,df4_flag)

def create_column(df1,df2,df3,df4,column,end_flag,df4_flag):
    sh1=df1.shape
    sh2 = df2.shape
    sh3=df3.shape
    sh4=df4.shape
    column2=[]
    column3=[]
    column4=[]
    col_cnt=0
    #column1をリセット
    df1.columns = range(sh1[1])
    df1.columns=[column[i] + df1[i][0] for i in range(0,sh1[1])]

    if "check" in column[sh1[1]]:
        column[sh1[1]] = re.sub("check","",column[sh1[1]])
        column2=column[sh1[1]:sh1[1]+int(sh2[1]/2)+1]
        [column2.insert(k, column2[k]) for k in range(len(column2)-2,-1,-1)]
        df2.columns=[column2[i] + df2[i][0] for i in range(0,sh2[1])]

        #column3の作成
        column3=column[sh1[1]+int(sh2[1]/2)+1:]
        if end_flag:
            for cnt,i in enumerate(column3):
                if "四半期末" in i:
                    col_cnt=cnt
                    break
            column3=column[sh1[1]+int(sh2[1]/2)+1+col_cnt:]
            for i in range(1,cnt+1):
                column3.append(column[sh1[1]+int(sh2[1]/2)+1+i])
        #column3をリセット
        df3.columns = range(sh3[1])
        df3.columns=[column3[i] + df3[i][0] for i in range(0,sh3[1])]
    
    else:
        #column2の作成
        column2=column[sh1[1]:sh1[1]+sh2[1]]
        #column2をリセット
        df2.columns = range(sh2[1])
        df2.columns=[column2[i] + df2[i][0] for i in range(0,sh2[1])]

        column[sh1[1]+sh2[1]] = re.sub("check","",column[sh1[1]+sh2[1]])
        column3=column[sh1[1]+sh2[1]:sh1[1]+sh2[1]+int(sh3[1]/2)+1]
        [column3.insert(k, column3[k]) for k in range(len(column3)-2,-1,-1)]
        df3.columns=[column3[i] + df3[i][0] for i in range(0,sh3[1])]
        
        #column4
        if df4_flag:
            #print(column[-sh4[1]:])
            column4 = column[-sh4[1]:]
            df4.columns = range(sh4[1])
            df4.columns=[column4[i] + df4[i][0] for i in range(0,sh4[1])]
    
    return(df1,df2,df3,df4)


def select_df(df2,df3,df4):
    try:
        if "通期" in df2.index or "予想" in df2.index:
            return(df2)
        elif "通期" in df3.index or "予想" in df3.index:
            return(df3)
        elif "通期" in df4.index or "予想" in df4.index:
            return(df4)
    except:
        pass

def create_df(file):
    text=normalize_XBRL(file)
    text,pre_term = text_tag(text)
    text_list=create_text_list(text)
    table_list,end_flag=create_table_list(text_list)
    column,number=create_list(table_list)
    column,number = create_None(column,number)
    df1,df2,df3,df4,flag=create_DataFrame(number,end_flag)
    df1,df2,df3,df4=create_column(df1,df2,df3,df4,column,end_flag,flag)
    df=select_df(df2,df3,df4)
    
    return(df1,df,pre_term)


def create_only_DataFrame(number,end_flag):
    new_df = pd.DataFrame
    kari_df = pd.DataFrame
    index_list = ["None"]
    df4_flag=False
    #学期末なら空リスト，それ以外なら，頭に追加
    if end_flag:
        index2_list=[]
    else:
        index2_list=["None"]
        
    marge_cnt = 0
    number_cnt = 1
    cnt = 0
    none_cnt=0
    flag=False
    flag_data=False
    #indexが同じ部分は横につなげる
    for i in range(1,len(number[number_cnt])):
        number_cnt +=1
        if number[i][0]== "None":
            new_df = pd.DataFrame([number[k][1:] for k in range(0,3)],index=[index_list])
            marge_cnt = i
            break
        else:
            index_list.append(number[i][0])
            cnt=i+1
    #同じインデックスでは横に並べる
    len_num = len(index_list)
    k = 1
    for i in range(cnt,len(number)):
        if number[i][0]==index_list[k]:
            k+=1
            if k ==len_num:
                kari_df = pd.DataFrame([number[marge_cnt+j][1:] for j in range(0,i-marge_cnt+1)],index=[index_list])
                new_df=pd.concat([new_df,kari_df],axis=1)
                marge_cnt = i+1
                k=1
                flag=True
        elif number[i][0] =="None":
            none_cnt=i
        elif number[i][0]!="None" and flag:
            [index2_list.append(number[k][0]) for k in range(i-1,len(number))]
            cnt=i
            break

    return(new_df)

def create_only_column(df1,column,end_flag):
    sh1=df1.shape
    col_cnt=0
    #column1をリセット
    df1.columns = range(sh1[1])
    df1.columns=[column[i] + df1[i][0] for i in range(0,sh1[1])]
    
    return(df1)

def create_df1(file):
    text=normalize_XBRL(file)
    text,pre_term = text_tag(text)
    text_list=create_text_list(text)
    table_list,end_flag=create_table_list(text_list)
    column,number=create_list(table_list)
    column,number = create_None(column,number)
    df1=create_only_DataFrame(number,end_flag)
    df1=create_only_column(df1,column,end_flag)
    
    return(df1,pre_term)

def predict_text(text):
    text  = re.sub("tableend", "", text)
    text = re.sub("table", "", text)
    text  = re.sub("tdend", "", text)
    text  = re.sub("trend", "", text)
    text  = re.sub("td", "", text)
    text  = re.sub("\n", "", text)
    
    #予測がいつまでなのかを取得
    pre_cnt=0
    pre = ""
    for i in range(0,len(text)):
        if "連結業績予想" in text[i-6:i]:
            pre_cnt=i-6
            break
    for i in range(pre_cnt,len(text)):
        if "。" in text[i-1:i]:
            pre = text[pre_cnt:i]
            break
    return(pre)

def none_df2(pre):
    if ("未定" in pre) or ("不透明" in pre) or ("困難" in pre) or ("非連結" in pre)or ("速やかに公表" in pre)or ("記載しておりません" in pre)or ("速やかに開示" in pre):
        df2 = pd.DataFrame([pre],columns=["text"])
        return(df2)
    elif ("開示" in pre) and ("おりません" in pre):
        df2 = pd.DataFrame([pre],columns=["text"])
    else:
        df2="program_err"
        return(df2)
    
#df2が作成不可の場合はdf1のみ作成するプログラム    
def main(file):
           
    text=normalize_XBRL(file)
    text,pre_term = text_tag(text)
    text_list=create_text_list(text)
    table_list,end_flag=create_table_list(text_list)
    column,number=create_list(table_list)
    column,number = create_None(column,number)
    try:
        df1,df2,df3,df4,flag=create_DataFrame(number,end_flag)
        df1,df2,df3,df4=create_column(df1,df2,df3,df4,column,end_flag,flag)
        df=select_df(df2,df3,df4)
        return(df1,df2,pre_term)
    
    except:
        df1=create_only_DataFrame(number,end_flag)
        df1=create_only_column(df1,column,end_flag)
        pre=predict_text(text)
        df2=none_df2(pre)
        return(df1,df2,pre_term)



