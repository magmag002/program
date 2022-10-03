
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
    text1=re.sub("０", "0", text1)
    text1=re.sub("１", "1", text1)
    text1=re.sub("２", "2", text1)
    text1=re.sub("３", "3", text1)
    text1=re.sub("４", "4", text1)
    text1=re.sub("５", "5", text1)
    text1=re.sub("６", "6", text1)
    text1=re.sub("７", "7", text1)
    text1=re.sub("８", "8", text1)
    text1=re.sub("９", "9", text1)
    

    return(text1)



def text_tag(text):
    #予測がいつまでなのかを取得(基本的に　３．　OO年度連結業績予測などになっているため，それを元に取得)
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


# In[4]:


def create_text_list(text):

    #tableタグで囲まれた部分をリストに入れる
    text_list = []
    table_cnt_first=0
    table_cnt_end=0
    non_text_list = []
    non_table_cnt_first=0
    append_text=""
    non_text=""
    for i in range(1,len(text)):
        if text[i-8:i] == "tableend":
        #tableタグに囲まれた文章をlistに追加
            table_cnt_end = i-8
            append_text=text[table_cnt_first:table_cnt_end]+"\n"
            append_text=re.sub("trend\ntrend","trend\n",append_text)
            append_text=re.sub("tableendtable","",append_text)
            append_text=re.sub(r'\n+', "\n",append_text)
            append_text=re.sub(r'\ntrend\nNone',"",append_text)
            #append_text=re.sub(r'\nNonetrend',"",append_text)
            text_list.append(append_text)
            table_cnt_first=0
            table_cnt_end=0
            #tableタグに囲まれている部分を追加したので囲まれていない部分のカウント初期化
            non_table_cnt_first=i

    #tableタグの始まりの判定    
        elif text[i-5:i] == "table":
            if table_cnt_first==0:
                table_cnt_first=i

            #tableタグに囲まれていない部分をlistに追加
            non_text=text[non_table_cnt_first:i-5]
            non_text_list.append(non_text)
    
    #listの中に（注）がある部分は削除する         
    pop_list=[]
    cnt=0
    for i in text_list:

        #if "(注)" in i :
          #  pop_list.append(cnt)
        if "(参考)" in i:
            pop_list.append(cnt)
        elif "(役職名)" in i:
            pop_list.append(cnt)
        cnt +=1

    for i in pop_list[::-1]:
        #print(i)
        text_list.pop(i)
    return(text_list,non_text_list)


# In[5]:


def create_table_list(text_list,column_dic):
    new_li=[]
    n_cnt=0
    col=""
    column_li=[i for i in column_dic.keys()]
    #一番可能性が高い表をlistのトップに持ってくる
    for cnt,table in enumerate(text_list):
        n_cnt=0
        col=""
        for i,word in enumerate(table,1):
            if word=="\n":
                #columnになる可能性のある単語がcolumn辞書に存在する場合は高い確率で目的の表であると考えられる
                col = table[n_cnt:i-1]
                #col= re.sub("trend","",col)
                if col in column_li:
                    new_li.append(table)
                    break
                n_cnt=i
    return(new_li)


# In[6]:


def create_list(table_list):
    number_list = []
    col_list=[]
    number = []
    col=""
    num_cnt=0
    col_cnt=0
    len_col=0
    add_col=0
    non_cnt=0
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
                
        #col_listの先頭がNoneでなければNoneを追加
        if (col_list!=[]) and col_list[non_cnt]!="None":
            #col_list.insert(len(column),"None")
            col_list.insert(non_cnt,"None")
            non_cnt=len(col_list)
            
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
                    
    #[col_list.insert(k, col_list[k]) for k in range(len_col-1,-1,-1)]
    
    return(col_list,number_list)


# In[7]:


def create_NoneAndCol(column,number):
    #columnをNoneを起点に分ける
    number_list=[]
    column_list=[]
    pop_list=[]
    cn=1
    for i in range(1,len(column)):
        if column[i] =="None":
            column_list.append(column[cn:i])
            cn=i+1
        elif i==len(column)-1:
            column_list.append(column[cn:i+1])
            
            
    #numberにNoneを入れる
    for cnt,num in enumerate(number):
        #if len(num) <3:
          #  pop_list.append(cnt)
        if ("円銭" in num) or ("百万円" in num):
            if "None" not in num:
                num.insert(0,"None")
        
        #後々Noneがあるとエラーになるのでいらないものは削除
        if num[0] != "None":
            num[0] = re.sub("None","",num[0])
        number_list.append(num)
        

    for i in pop_list[::-1]:
        #print(i)
        number_list.pop(i)
    return(column_list,number_list)


# In[8]:


def create_index(number):
    index_list=[[]*i for i in range(0,len(number))]
    in_cnt=0
    index_list[in_cnt].append("None")

    for i in range(1,len(number)):
        if number[i][0]== "None":
            in_cnt+=1
            index_list[in_cnt].append("None")
        else:
            index_list[in_cnt].append(number[i][0])
    return(index_list)


# In[9]:


def create_new_number_list(number,column_list):
    new_num=[]
    cn=0
    for cnt,num in enumerate(number):
        if num[0]== "None":
            if len(new_num)!=len(column_list):
                if len(column_list[cn])>2:

                    for i in range(0,len(num),2):
                        if i>len(column_list[cn])-1:
                            continue
                        if (len(num)-1) > (len(column_list[cn])):
                            column_list[cn].insert(i,column_list[cn][i])

                        else:
                            break
                new_num.append([column_list[cn][k]+num[k+1] for k in range(0,len(column_list[cn]))])
                new_num[cn].insert(0,"None")
                number[cnt]=new_num[cn]
                if cn!=len(column_list)-1:
                    cn+=1
    
    return(number)


# In[126]:


def create_DataFrame(number,index_list):
    #最大でも４つまでの表しか作成しない．目的の表は２つだけなので
    new_df1 = pd.DataFrame
    new_df2 = pd.DataFrame
    new_df3 = pd.DataFrame
    new_df4=pd.DataFrame
    new_df = pd.DataFrame
    cn=1
    num_cnt=0
    for cnt,index in enumerate(index_list):

        if index!=[] and cn==1:
            new_df1=pd.DataFrame([number[k][1:] for k in range(num_cnt,len(index)+num_cnt)],index=index)
            num_cnt+=len(index)
            cn+=1
            continue
        elif index!=[] and cn==2:
            new_df2=pd.DataFrame([number[k][1:] for k in range(num_cnt,len(index)+num_cnt)],index=index)
            num_cnt+=len(index)
            #インデックスが同じなら合わせる
            if index==index_list[cnt-1]:
                new_df=pd.concat([new_df1,new_df2],axis=1)
            else:
                cn+=1

        elif index!=[] and cn==3:
            new_df3=pd.DataFrame([number[k][1:] for k in range(num_cnt,len(index)+num_cnt)],index=index)
            num_cnt+=len(index)
            cn+=1
        elif index!=[] and cn==4:
            new_df4=pd.DataFrame([number[k][1:] for k in range(num_cnt,len(index)+num_cnt)],index=index)
            break
    #dfがNoneだったらdf1を出力
    if str(type(new_df))=="<class 'type'>": 
        return(new_df1,new_df2,new_df3,new_df4)
          
    else:
        return(new_df,new_df2,new_df3,new_df4)


# In[11]:


def reset_column(df1,df2):
    sh1=df1.shape
    sh2 = df2.shape
    #column1をリセット
    df1.columns = range(sh1[1])
    #column2をリセット
    df2.columns = range(sh2[1])
    
    return(df1,df2)


# In[148]:


def reset_column1(df1):
    sh1=df1.shape

    #column1をリセット
    df1.columns = range(sh1[1])

    return(df1)


# In[72]:


def select_df(df2,df3,df4,pre_term):
    
    try:
        if ("通期" in str(df2.index)) or( "予想" in str(df2.index ))or("累計" in str(df2.index)):
            return(df2)
        elif ("通期" in str(df3.index)) or( "予想" in str(df3.index ))or("累計" in str(df3.index)): 
            return(df3)
        elif ("通期" in str(df4.index)) or( "予想" in str(df4.index ))or("累計" in str(df4.index)):
            return(df4)
        
        else:
            index_list=[]
            index_list = [i for i in df2.index]
            for j in index_list:
                if pre_term[:4] in j:
                    return(df2)
                pass
            
            index_list = [i for i in df3.index]
            for j in index_list:
                if pre_term[:4] in j:
                    return(df3)
                pass
            
            index_list = [i for i in df4.index]
            for j in index_list:
                if pre_term[:4] in j:
                    return(df4)
                pass
    except:
        pass


# In[68]:


def select_df2(df,df2,df3,df4):
    if str(type(df))=="<class 'NoneType'>":
        try:
            if "累計" in str(df2.index) or "累計" in str(df2.index):
                return(df2)
            elif "累計" in str(df3.index) or "累計" in str(df3.index):
                return(df3)
            elif "累計" in str(df4.index) or "累計" in str(df4.index):
                return(df4)
        except:
            pass


# In[14]:


def create_df1_column(df1,column_list):
    df1_col=[ i for i in df1.columns]
    cnt_0 = df1_col.count(0)
    new_col=[]
    cnt=1
    end=0
    try:
        for zero_cnt in range(0,cnt_0):
            for i in range(cnt,len(df1_col)):
                if df1_col[i]==0:
                    #columnとdfの長さが同じ時（表１）
                    if len(column_list[zero_cnt]) == i:
                        new_col= column_list[0]
                    #columnとdfの長さが同じ時（表２）
                    elif (zero_cnt!=0) and (len(column_list[zero_cnt]) == i-end+1):
                        new_col= column_list[0]
                    else:
                        cnt=i+1
                        break
                #エラーが起きないように最後になったらforを抜ける        
                elif i==len(df1_col)-1:
                    cnt=i+3
                    break
            #抜けた後，column数が同じならそのまま加える
            if (len(column_list[zero_cnt]) == i-end+1):
                for k in column_list[zero_cnt]:
                    new_col.append(k)
            else:
                #0の手前までのcolumnを作成
                cn=0
                for j in range(end,cnt-1):
                    if j %2==0:
                        new_col.append(column_list[zero_cnt][cn])
                    else:
                        new_col.append(column_list[zero_cnt][cn])
                        cn+=1
                end=j+2
        df1.loc["index"]=new_col
    except:
        df1.loc["index"]=new_col
    return(df1,zero_cnt+1)


# In[15]:


def create_df_column(df1,column_list,zero_cnt):
    try:
        df_col=[ i for i in df.columns]
        new_col=[]
        cn=0
        for i in range(zero_cnt,len(column_list)):
            new_col=[]
            cn=0
            for j in range(0,len(df_col)):
                if cn < len(column_list[i]):
                    #print(j)
                    if j %2==0:
                        new_col.append(column_list[i][cn])
                        #print(column_list[i][cn])
                    else:
                        new_col.append(column_list[i][cn])
                        #print(column_list[i][cn])
                        cn+=1

            if  len(df_col)==len(new_col):
                df.loc["index"]=new_col
                break
        return(df1)
    except:
        return(df1)


# In[16]:


def check_text(text_list,non_text):
    new_text_list=[]
    new_text=""

    for txt in text_list:
        if txt.count("。")>=1:
            new_text+=txt
    new_text_list.append(new_text)
    
    new_text=""
    for txt in non_text:
        if txt.count("。")>=1:
            new_text+=txt
    new_text_list.append(new_text)
    
    return(new_text_list)


# In[17]:


def NoPredict_or(NoPredict_text):
    cnt=0
    cnt=0
    for i in NoPredict_text:
        if ("未定"in i)or ("控え" in i) or ("困難" in i)or("M&A" in i) or("コロナウイルス" in i) or("合理的に算出" in i)or("非連結" in i)or("IFRS" in i)or("精査中" in i):
            cnt+=1
        elif ("速やかに開示" in i) or ("開示する予定"in i)or ("ＩＦＲＳ" in i):
            cnt+=1
    if cnt>0:
        return(True)
    else:
        return(False)


# In[18]:


def tuki_reset(number):
    for cnt,li in enumerate(number):
        if "通期" in li:
            if li[0]!="通期":
                number[cnt].remove("通期")
                number[cnt+1].insert(0,"通期")
    return(number)


# In[19]:


def trend_reset(number):
    for cnt,li in enumerate(number):
        for cnt2,li2 in enumerate(li):
            if "trend" in li2:
                number[cnt].pop(cnt2)
                break
    return(number)


# In[151]:


def main(file): 
    col_dic={
    "売上高":"Sales",
    "営業利益":"Operating",
    "事業利益":"Business",
    "経常利益":"Ordinary",
    "親会社株主に帰属する当期純利益":"ParentNetIncome",
    "親会社株主に帰属する四半期純利益":"QuarterParentNetIncome",
    "1株当たり当期純利益":"OneNetIncome",
    "1株当たり四半期純利益":"QuarterOneNetIncome"

    }
    li=[]
    NoPreFlag=False
    errFlag=False
    try:
        text=normalize_XBRL(file)
        text,pre_term = text_tag(text)
        text_list,non_text=create_text_list(text)
        NoPredict_text=check_text(text_list,non_text)
        table_list=create_table_list(text_list,col_dic)
        column,number=create_list(table_list)
        column_list,number = create_NoneAndCol(column,number)
        number=tuki_reset(number)
        number=trend_reset(number)
        index_list=create_index(number)
        df1,df2,df3,df4=create_DataFrame(number,index_list)
        df=select_df(df2,df3,df4,pre_term)
        df1,zero_cnt,=create_df1_column(df1,column_list)
        df=create_df_column(df,column_list,zero_cnt)
        df1=reset_column1(df1)
        df=reset_column1(df)
        if str(type(df))=="<class 'NoneType'>":
            if NoPredict_or(NoPredict_text):
                NoPreFlag=True
        #else:
            #df=reset_column1(df)
    except:
        errFlag=True
        if str(type(df))=="<class 'NoneType'>":
            if NoPredict_or(NoPredict_text):
                NoPreFlag =True
                    
    return(df1,df,pre_term,NoPredict_text,NoPreFlag,errFlag,table_list)
