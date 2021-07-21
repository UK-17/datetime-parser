import logging
import sys
import os
import requests
import json
import re
import datetime
from pathlib import Path
sys.path.append(os.path.realpath(os.path.relpath("../..")))
from app.model.schemas import DateUtterance
from app.data import Data
logger = logging.getLogger(__name__)



data = Data()

conversion_dictionary = data.conversion_dictionary
scale_tens = data.scale_tens
year_list = data.year_list
num_2_word = data.number_to_word


def _checkifmonthpresent(dob):


    if dob!='':
        result = re.findall("january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec",dob.lower())

    result_=None
    if result !=[]:
        
        if len(result[0])>3:
            result_ = datetime.datetime.strftime(datetime.datetime.strptime(result[0],'%B'),"%m")
        else:
            result_ = datetime.datetime.strftime(datetime.datetime.strptime(result[0],'%b'),"%m")

    if result==[]:
        retVal = False
    else:
        retVal= True
        logger.info("Extracted month from text is :{} and replacement string is :{}".format(result_,result))
        dob = dob.lower().replace(result[0],"")
        logger.info("DOB is  now :{}".format(dob))

    return retVal,result_,dob

def _getvalidyear(dob):
    ret_year=[]
    retVal=-1
    is_valid_year= False
    if dob!='':
        result = re.findall('(?P<year>[0-9]{4})',dob)

    if result !=[]:  
        for yr in result:
            is_valid_year=validateyear(yr)
            if is_valid_year:
                dob = dob.replace(yr,"")
                retVal= yr
                return is_valid_year,retVal,dob
    

    return is_valid_year,retVal,dob

def _getdaywithsuffix(dob):
    if dob!='':
        result = re.findall('[0-9]{1,2}(?=th|rd|st|nd)',dob)
    

    if result ==[]:
        retVal = False
    else:
        retVal = True
        is_day = validateday(result[0])
        if is_day:
            dob = dob.replace(result[0],"",1)
        else:
            if len(result)==2:
                is_day = validateday(result[1])
                if is_day:
                    dob = dob.replace(result[1],"",1)
                
            
        
    logger.info("Date with suffix:{}".format(result))
    return retVal,result,dob

def getdaywithspaceassuffix(dob):
    ret_day=''
    if dob!='':
        result = re.findall('^[0-9]{1,2}[0-9\w+](?=\s)',dob)
        logger.info("Length of date result:{}".format(len(result)))

        if result ==[]:
            retVal = False
        else:
            retVal = True
    logger.info("Date with space:{}".format(result))
    return retVal,result

def handlemultiplevalues(day_month,is_month):
    day_extracted,month_extracted ='',''
    if not is_month:
        #Case of month not extracted
        day_extracted = day_month[0]
        month_tracted = day_month[1]
        if int(day_extracted)<=31:
            logger.info("Correct Day extracted")
        else:
            logger.info("Looks day is wrong")
    else:
    
        day_extracted = day_month[0]
        month_extracted =-1

    return day_extracted,month_extracted

def _getnumeralsfromtext(eachline):
    if eachline!='':
        logger.info("Inside _getnumeralsfromtext:{}".format(eachline))
        # find 2 digit and 1 digit
        #onedigit = re.findall('(?<!\d)(\d{2})(?!\d)',x)

        result = re.findall("[0-9]{1}",eachline)
    
    return(result)

def _getnumeralsaspattern(eachline,is_day,is_month,is_year):
    day_dob = -1 
    month_dob = -1 
    year_dob =-1


    if eachline!='':
        logger.info("Inside _getnumeralsaspattern:{}".format(eachline))
        # find 2 digit and 1 digit

        
        iter = re.finditer('(?<!\d)(\d{1}|\d{2}|\d{4})(?!\d)',eachline)
        result = [m.group() for m in iter]
        res_len= len(result)
        if is_month:#month is already calculated
            if res_len==2:
                day_dob = _returnValue(result,0,1)
                is_day = validateday(day_dob)
                if is_day:
                    year_dob= _returnValue(result,1,2)
                    if len(year_dob)==4:
                        is_year = validateyear(year_dob)
                        if not is_year:
                            year_dob =-1
                    elif len(year_dob)==2:
                        year_dob,is_year = _getproperformat(year_dob,'year')
                        is_year = validateyear(year_dob)
                        if not is_year:
                            year_dob =-1

            logger.info("Output from _getnumeralaspattern day:{},month:{},year:{}".format(day_dob,month_dob,year_dob))  
            return(is_day,is_month,is_year,day_dob,year_dob)
        else:
            if res_len==3:
                day_dob = _returnValue(result,0,1)
                is_day = validateday(day_dob)
                if is_day:
                    month_dob = _returnValue(result,1,2)
                    is_month = validatemonth(month_dob)
                    if is_month:
                        year_dob = _returnValue(result,2,3)
                        if len(year_dob)==4:
                            is_year = validateyear(year_dob)
                            if not is_year:
                                year_dob =-1
                                is_month=False
                                month_dob =-1
                                is_day = False
                                day_dob=-1
                        elif len(year_dob)==2:
                            logger.info("year dob after extraction:{}".format(year_dob))
                            year_dob,is_year = _getproperformat(year_dob,'year')
                            logger.info("year dob after extraction:{}".format(year_dob))
                            is_year = validateyear(year_dob)
                            if not is_year:
                                year_dob =-1
                                is_month=False
                                month_dob =-1
                                is_day = False
                                day_dob=-1
                        else:
                            year_dob=-1
                            is_year = False
                            is_day = False
                            is_month = False
                            day_dob=-1
                            month_dob=-1

                    else:
                        is_day = False
                        day_dob = -1
                            
            logger.info("Output from _getnumeralaspattern day:{},month:{},year:{}".format(day_dob,month_dob,year_dob))  
            return(is_day,is_month,is_year,day_dob,month_dob,year_dob)

def _returnValue(date_list,start_indx,end_indx):
    retVal=''
    for i in range(start_indx,end_indx):
        retVal = retVal+date_list[i]
    logger.info("Retval is :{}".format(retVal))
    return retVal

def validateyear(year_):
    retVal=True
    if len(year_)==4:
        if int(year_)<int(datetime.datetime.strftime(datetime.datetime.now(),"%Y"))-100 or int(year_)>int(datetime.datetime.strftime(datetime.datetime.now(),"%Y")) :
            retVal =False
    elif len(year_)==2:
        if int(year_)>int(datetime.datetime.strftime(datetime.datetime.now(),"%y")) and int(year_)<int(datetime.datetime.strftime(datetime.datetime.now(),"%y"))+10:
            retVal =False
    else:
        retVal =False
        logger.info("Cant Handle Year")
    
    return retVal
    
def validatemonth(month_):
    retVal=True

    if int(month_)>12 or int(month_)<=0:
        retVal =False
    
    return retVal

def validateday(day_):
    retVal=True
    logger.info("Day is :{}".format(day_))
    if int(day_)>31 or int(day_)<=0:
        retVal =False
    
    return retVal

def _getproperformat(val,type):
    logger.info("val is :{}, type is :{}".format(val,type))
    logger.info("Inside get proper format:{}::{}".format(val,type))
    is_valid= True
    if val !=[] and val is not  None:
        
        if type=='year':
            if len(str(val))==2:
                if int(val)>=30 and int(val)<=99:
                    
                    newval= '19'+str(val)
                elif int(val)>=0 and int(val)<=int(datetime.datetime.strftime(datetime.datetime.now(),'%y')):
                    newval= '20'+str(val)
                elif int(val)==-1:
                    is_valid = False
                    newval = '1900'
            elif len(str(val))==4:
                newval = val
            elif len(val)==1:
                newval = '200'+str(val)
            else:
                newval = '1900'
            
        elif type=='month':
            if int(val)<0:
                is_valid= False
                newval='01'
            else:
                if len(str(val))==1:
                    newval = '0'+str(val)
                else:
                    newval= val
            
        elif type=='day':
            if int(val)<0:
                is_valid= False
                newval='01'
            else:
                if len(str(val))==1:
                    newval = '0'+str(val)
                else:
                    newval= val
    else:
        is_valid =False
        if type=='year':
            newval='1900'
        elif type=='month':
            newval='01'
        else:
            newval='01'

    
    return newval,is_valid

def _getvaliddate(year_,month_,day_):
    logger.info("{},{},{}".format(year_,month_,day_))
    year_,is_year_valid = _getproperformat(year_,'year')
    month_,is_month_valid = _getproperformat(month_,'month')
    day_,is_day_valid = _getproperformat(day_,'day')
    logger.info("Returned Values: Year{},Month:{},Day:{}".format(year_,month_,day_))

    dob = str(year_)+'-'+str(month_)+'-'+str(day_)
    
    return dob,is_year_valid,is_month_valid,is_day_valid

def consume(iterator, n):
    "Advance the iterator n-steps ahead. If n is none, consume entirely."
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)

def number2word(text):
    new_text = []
    for each in text.split(' '):
        if each.isnumeric():
            logger.info(each)
            try:
                replaced_text = re.sub(each,num_2_word[str(each)],each)
                new_text.append(replaced_text)
            except:
                new_text.append(each)
        else:
             new_text.append(each)
    text= " ".join([w for w in new_text])
    logger.info(text)
    return text

def word2number(text):
    # check if two thousand occurs
    text = re.sub('two thousand|two-thousand','two_thousand',text)
    text = re.sub('nineteen hundred|nineteen-hundred','nineteen_hundred',text)
    numstr= re.split('[ \-]+',text)
    #text.split(' ')
    token_val=[]
    numwords={}
    convert=0
    

    #print("After split on space::{}".format(numstr))
    add_next_one =False
    loop_ = iter(range(len(numstr)))
    extracted_number=[]
    for key_index in loop_:
        
        if numstr[key_index] in scale_tens.keys():#check if the number is in the list like twenty,thirty etc
            #this will fail for two_thousand five
            if key_index<=len(numstr)-1:
                if numstr[key_index-1] in year_list and not add_next_one:
                
                    convert = int(conversion_dictionary[numstr[key_index-1]])*100 + int(conversion_dictionary[numstr[key_index]])
                    extracted_number.pop()#delete last added year value
                    extracted_number.append(str(convert))
                    add_next_one = True
                elif add_next_one:
                    convert = convert+ int(conversion_dictionary[numstr[key_index]])
                    add_next_one = True
                elif numstr[key_index] in ['two_thousand','nineteen_hundred'] and not add_next_one:
                    convert = int(conversion_dictionary[numstr[key_index]])
                    logger.info("Value in when index is of two_thousand:{}".format(convert))
                    extracted_number.append(str(convert))
                    add_next_one = True
                else:
                    convert = int(conversion_dictionary[numstr[key_index]])
                    extracted_number.append(str(convert))
                    add_next_one = True
        elif numstr[key_index] in conversion_dictionary.keys():#convert stand alone number words
            logger.info("checking for regular word in numeric:{}".format(numstr[key_index]))
            if add_next_one:
                logger.info("convert is :{}".format(convert))
                logger.info("extracted_number is :{}".format(extracted_number))
                convert = convert + int(conversion_dictionary[numstr[key_index]])
                #what if we have and
                extracted_number.pop()
                add_next_one = False
                extracted_number.append(str(convert))
            else:
            #print(numstr[key_index])
                extracted_number.append(conversion_dictionary[numstr[key_index]])    
        else:# return other ords as it is
            if not re.findall('and|&',numstr[key_index],re.IGNORECASE):
                extracted_number.append(numstr[key_index])    
        
    #print(extracted_number)
    

    replaced_list = [conversion_dictionary[number_words] if number_words in year_list else number_words for number_words in extracted_number ]        
    word_for_num = " ".join(each_token for each_token in replaced_list)
    #word_for_num="Hi"
    return word_for_num



def converttovalidDOB(utterance):
    count_year=0
    count_month=0
    count_day_withsuffix=0
    count_day_nosuffix=0
    is_day = False
    is_month = False
    is_year = False


    
    # data_lines = [[input_data]]
    # logger.info("Data Lines is {}".format(data_lines))

    row_list=[]
    data_list=[]
    valid_daterecords=0
    #for i in index:
    #logger.info("I am here ")
    # this will extract everything before a \t or \n
    dobstr= re.findall("[0-9\s\w\S]+",utterance)
    # used new variable to update as i keep on finding day,month and year
    date_of_birth = dobstr[0]
    logger.info(dobstr)

   
    logger.info("Target String is :{}".format(dobstr))
    """
    Logic is as follows
    easiest is find 2 things
    1. first find month in text-january,february etc
    2. find day with nd,rd,th etc
    3. 4 digit year format
    ## no month in words 
    3. Now minimum numbers to extract all day and year 4 upto 8
        8 8 83 -  4
        12 5 84 - 5
        24 11 84 -6
        8 12 87 -5
        08 02 2001 -8
        2 1 1977 
        02 1 1977
        2 01 1977


    4. if word month found-- min is 3 and max is 6 but in pairs of 1,2 or 2,2 or 1,4 or 2,4
    """

    if dobstr==[]:
        is_month,month_dob = False,'01'
        is_year,year_dob =  False,'1900'
        is_date,day_dob = False,'01'
        rowdata = [dobstr,year_dob,month_dob,day_dob]
        row_list.append(rowdata)
    
    else:    
        logger.info("DOBSTR:{}".format(dobstr[0]))
        #go and convert all words in numbers if possible
        date_of_birth = number2word(date_of_birth)
        date_of_birth = word2number(date_of_birth)
        logger.info("After word 2 number:{}".format(date_of_birth))
        
        
        is_month,month_dob,date_of_birth = _checkifmonthpresent(date_of_birth)
        # if is_month:
        #     is_month = False #setting to false so that date can be extracted

        logger.info("Month Extracted:{}".format(month_dob))  

        if is_month:      
        
            is_day,is_month,is_year,day_dob,year_dob = _getnumeralsaspattern(date_of_birth,is_day,is_month,is_year)
        else:
            is_day,is_month,is_year,day_dob,month_dob,year_dob = _getnumeralsaspattern(date_of_birth,is_day,is_month,is_year)
        




        #find month as text-jan,feb etc
        

        
        # find day as 1st,2nd,3rd,4th. assuming that only day or month have such suffixes
        """
        is_day,day_dob,date_of_birth = _getdaywithsuffix(date_of_birth) #day_dob is a list
        # if format is 9th of 6th of 1988 then day will be extracted as a list with 2 elements
        if len(day_dob)==1:
            day_dob = day_dob[0]
            is_day = validateday(day_dob)
            logger.info("AFTER EXTRACTING th of is_day is :{} and day_dob :{}".format(is_day,day_dob))
           
        
        logger.info("Day Extracted with suffix:{}".format(day_dob))
        
        # get year in 4 year format
        
        
        if not is_month: #if month is not as word then it will look in numbers
            # means month is in number format
            if len(day_dob)>1 and is_day: #assuming dd-mm format
                day_ = day_dob
                day_dob= day_[0] #1st record is day. 
                month_dob = day_[1] #2nd record is month
                is_day = validateday(day_dob) # keep on checking if day extracted is valid
                is_month = validatemonth(month_dob) #keep on checking if month extracted is valid
                # better to check if month is invalid. If a day is invalid it is an invalid month also
                if not is_month: #continuation of above
                    day_dob= day_[1]
                    month_dob = day_[0]
                    is_day = validateday(day_dob)
                    is_month = validatemonth(month_dob)
                    if not is_day or not is_month: # a bit strict test. 
                        day_dob =-1
                        month_dob = -1
            elif len(day_dob)==1 and is_day: # if only one entry as rd,st,th etc
                day_=day_dob
                day_dob = day_[0]
        
        """
                            
        #is_year,year_dob,date_of_birth = _getvalidyear(date_of_birth)# this will extract year if it is in 4 digit format
        #logger.info("if year exists in 4 digit format::{} Extracted:{}".format(is_year,year_dob))
        # code will automatically flow here
        # now what ever is extracted will be removed from date_of_birth
        
        date_numerals = _getnumeralsfromtext(date_of_birth) # this returns all nos from uttered text

        # year is not in 4 digit format or day is a pure number and not psucced by nd,rs,st
        if not is_year and not is_day: # could not find year as 4 digits and no nd,st,rd,th exist
            # means year is not in 4 digit format
            
            logger.info("Date Numerals :{}".format(date_numerals))
            if is_month: # month is already extracted as text
                # year and date in digit--min digits 3 and max=6
                # expected formats mm-yy or m-yy or yy-m or yy-mm
                # not supported 76 may 2
                if len(date_numerals)==3:
                    day_dob = _returnValue(date_numerals,0,1)
                    is_day = validateday(day_dob)#only an invalid date if it is 0
                    if is_day:
                        year_dob = _returnValue(date_numerals,1,3)
                    else:
                        logger.info("No valid day and year found")
                        day_dob = -1
                        year_dob = -1
                elif len(date_numerals)==4: #dd-yy or yy-dd
                    day_dob = _returnValue(date_numerals,0,2)
                    is_day = validateday(month_dob)
                    if is_day:
                        year_dob = _returnValue(date_numerals,2,4)
                    else:
                        day_dob = _returnValue(date_numerals,2,4)
                        year_dob = _returnValue(date_numerals,0,2)
                        is_day = validateday(day_dob)
                        if not is_day:
                            logger.info("Invalid date ")
                else:
                    day_dob =-1
                    year_dob =-1
            else:#month is not in words all date in numbers
                
                #means year, month and day are all in max 2 digit number format and 
                
                # will deal with dd-mm-yyyy, dd-mm-yy or dd-m-yy or m-dd-yy or mm-dd-yy 

                logger.info("Now all date in numerals length of numerals :{}".format(len(date_numerals)))
                if len(date_numerals)>8:#if a number starts with 0 then is it handled
                    logger.info("Invalid Date")
                    day_dob =-1
                    month_dob=-1
                    year_dob =-1
                elif len(date_numerals)==8:#dd-mm-yyyy or mm-dd-yyyy -rest not handled
                    day_dob = _returnValue(date_numerals,0,2)
                    is_day = validateday(day_dob)
                    if is_day:
                        month_dob = _returnValue(date_numerals,2,4)
                        is_month =validatemonth(month_dob)
                        logger.info("Month extratced in 8 digits:{}".format(is_month))
                        if is_month:
                            year_dob= _returnValue(date_numerals,4,8)
                            logger.info("eight digits Day:{} month:{} and Year:{}".format(day_dob,month_dob,year_dob))
                            is_year = validateyear(year_dob)
                            if not is_year:
                                year_dob = -1
                        
                        else:
                            day_dob = _returnValue(date_numerals,2,4)
                            is_day = validateday(day_dob)
                            if is_day:
                                month_dob = _returnValue(date_numerals,0,2)
                                is_month =validatemonth(month_dob)
                                if is_month:
                                    year_dob = _returnValue(date_numerals,4,8)
                                    is_year = validateyear(year_dob)
                                    logger.info("Day:{} month:{} and Year:{}".format(day_dob,month_dob,year_dob))
                                    if not is_year:
                                        year_dob = -1
                                else:
                                    logger.info("Date Not handled")
                                    day_dob =-1
                                    month_dob =-1
                                    year_dob =-1
                    else:
                        day_dob = _returnValue(date_numerals,2,4)
                        is_day = validateday(day_dob)
                        if is_day:
                            month_dob = _returnValue(date_numerals,0,2)
                            is_month =validatemonth(month_dob)
                            if is_month:
                                year_dob= _returnValue(date_numerals,4,8)
                                is_year = validateyear(year_dob)
                                if not is_year:
                                    year_dob = -1
                        
                elif len(date_numerals)==7:#dd-m-yyyy,d-mm-yyyy -rest not handled
                    logger.info("Seven Digit format:{}".format(date_numerals))
                    day_dob = _returnValue(date_numerals,0,2)
                    is_day = validateday(day_dob)
                    if is_day:#else case means first 2 digit is more than 31 or 0
                        month_dob = _returnValue(date_numerals,2,3)
                        is_month =validatemonth(month_dob)
                        logger.info("Month extracted:{}".format(month_dob))
                        if is_month:#if month is valid
                            year_dob= _returnValue(date_numerals,3,7)
                            is_year = validateyear(year_dob)
                            if not is_year:
                                year_dob = -1
                        
                        else:#case like 1101980
                            day_dob = _returnValue(date_numerals,0,1)
                            logger.info("Day extracted seven digit format:{}".format(day_dob))
                            is_day = validateday(day_dob)
                            if is_day:
                                month_dob = _returnValue(date_numerals,1,3)
                                is_month =validatemonth(month_dob)
                                if is_month:
                                    year_dob = _returnValue(date_numerals,3,7)
                                    is_year = validateyear(year_dob)
                                    if not is_year:
                                        year_dob = -1
                                else:
                                    day_dob = _returnValue(date_numerals,1,3)
                                    is_day = validatemonth(day_dob)
                                    if is_day:
                                        month_dob = _returnValue(date_numerals,2,3)
                                        is_month =validatemonth(month_dob)
                                        if is_month:
                                            year_dob = _returnValue(date_numerals,3,7)
                                            is_year = validateyear(year_dob)
                                            if not is_year:
                                                year_dob = -1
                                    else:
                                        logger.info("Date Not handled")
                                        day_dob =-1
                                        month_dob =-1
                                        year_dob =-1
                    else:
                        day_dob = _returnValue(date_numerals,0,1)
                        is_day = validateday(day_dob)
                        if is_day:
                            month_dob = _returnValue(date_numerals,1,3)
                            is_month =validatemonth(month_dob)
                            if is_month:
                                year_dob= _returnValue(date_numerals,3,7)
                                is_year = validateyear(year_dob)
                                if not is_year:
                                    year_dob = -1
                            else:
                                month_dob=-1

                
                elif len(date_numerals)==6:#dd-mm-yy or mm-dd-yy -rest not handled
                    logger.info('This date is all number and 6 digits')
                    day_dob = _returnValue(date_numerals,0,2)
                    is_day = validateday(day_dob)
                    if is_day:
                        month_dob = _returnValue(date_numerals,2,4)
                        is_month =validatemonth(month_dob)
                        
                        if is_month:
                            year_dob= _returnValue(date_numerals,4,6)
                            is_year = validateyear(year_dob)
                            if not is_year:
                                year_dob = -1
                        
                        else:
                            logger.info('Month is not in correct format')
                            day_dob = _returnValue(date_numerals,2,4)
                            is_day = validateday(day_dob)
                            if is_day:
                                month_dob = _returnValue(date_numerals,0,2)
                                is_month =validatemonth(month_dob)
                                if is_month:
                                    year_dob = _returnValue(date_numerals,4,6)
                                    is_year = validateyear(year_dob)
                                    if not is_year:
                                        year_dob = -1
                                else:
                                    logger.info("Date Not handled")
                                    day_dob =-1
                                    month_dob =-1
                                    year_dob =-1
                elif len(date_numerals)==5:#dd-m-yy or m-dd-yy or dd-mm-y  -rest not handled
                    logger.info("XXXXDate_NumeralsXXXX: {}".format(date_numerals))
                    day_dob = _returnValue(date_numerals,0,2)
                    is_day = validateday(day_dob)
                    if is_day:
                        month_dob = _returnValue(date_numerals,2,3)
                        is_month =validatemonth(month_dob)
                        if is_month:
                            year_dob= _returnValue(date_numerals,3,5)
                            is_year = validateyear(year_dob)
                            if not is_year:
                                year_dob = -1
                        else:
                            month_dob = _returnValue(date_numerals,2,4)
                            is_month =validatemonth(month_dob)
                            if is_month:#risky assumption but then so be it
                                year_dob= _returnValue(date_numerals,4,5)
                            else:
                                month_dob =-1
                                year_dob = -1
                        
                    else:
                        day_dob = _returnValue(date_numerals,0,1)
                        is_day = validatemonth(day_dob)
                        if is_day:
                            month_dob = _returnValue(date_numerals,1,3)
                            is_month =validatemonth(month_dob)
                            if is_month:
                                year_dob = _returnValue(date_numerals,3,5)
                                is_year = validateyear(year_dob)
                                if not is_year:
                                    year_dob = -1
                            else:
                                logger.info("Date Not handled")
                                day_dob =-1
                                month_dob =-1
                                year_dob =-1
                elif len(date_numerals)==4: #01/01 kind of cases
                
                    day_dob = _returnValue(date_numerals,0,1)
                    if day_dob =='0':
                        day_dob = _returnValue(date_numerals,0,2)
                        month_dob = '01'
                    else:
                        month_dob = _returnValue(date_numerals,1,2)
                    year_dob = _returnValue(date_numerals,2,4)
                    is_month = validatemonth(month_dob)
                    is_day = validateday(day_dob)
                    if not is_day or not is_month:#this flow should never happen
                        day_dob = _returnValue(date_numerals,1,2)
                        month_dob = _returnValue(date_numerals,0,1)
                        year_dob = _returnValue(date_numerals,2,4)
                        is_month = validatemonth(month_dob)
                        is_day = validatemonth(day_dob)
                        is_year = validateyear(year_dob)
                        if not is_year:
                            logger.info(" Invalid 4 digit format: Year looks badly formed:{}".format(year_dob))
                            year_dob=1900
                        elif not is_month:
                            logger.info("Badly formed month.".format(month_dob,day_dob))
                            month_dob = '01'
                        else:
                            logger.info("Badly formed day.".format(month_dob,day_dob))
                            day_dob = '01'

                        
        elif not is_month and not is_day: # year is in 4 year format 
            logger.info("date numerals :{}".format(date_numerals))
            #now year is available
            # day and month are left
            # minimum digits are 6. if 1 or less then get day if only 1 and none for 0
            #maximum is 8
            if len(date_numerals)==0:
                logger.info(" No day or month")
                day_dob = -1
                month_dob = -1
            elif len(date_numerals)==1:
                logger.info(" Will extract month as day is not bounded by st,rd or nd")
                logger.info("Year value is {}".format(year_dob))
                left_numerals = re.sub(year_dob,'',date_of_birth)
                left_numerals = re.findall('[0-9]+',left_numerals)
                logger.info(left_numerals)
                month_dob = _returnValue(left_numerals,0,1)
                is_month = validatemonth(month_dob)
                if not is_month:
                    logger.info("Looks invalid month say a 0")
                    month_dob =-1

            elif len(date_numerals)==2:
                left_numerals = re.sub(year_dob,'',date_of_birth)
                left_numerals = re.findall('[0-9]{1}',left_numerals)
                logger.info(left_numerals)
                month_dob = _returnValue(left_numerals,0,1)
                if month_dob=='0':
                    logger.info("Month is not valid and we have just a month or day")
                    month_dob= _returnValue(left_numerals,0,2)
                else:
                    day_dob = _returnValue(left_numerals,1,2)

            elif len(date_numerals)==3:
                left_numerals = re.sub(year_dob,'',date_of_birth)
                left_numerals = re.findall('[0-9]{1}',left_numerals)
                logger.info("Date numerals is {} after removing 4 digit year".format(left_numerals))
                day_dob = _returnValue(left_numerals,0,2)
                month_dob = _returnValue(left_numerals,2,3)
                
                is_day = validateday(day_dob)
                if not is_day:
                    day_dob = _returnValue(left_numerals,0,1)
                    month_dob = _returnValue(left_numerals,1,3)
                    is_month = validatemonth(month_dob)
                    if not is_month:
                        logger.info("Invalid Month")
                        # month_dob = _returnValue(left_numerals,2,3)
                        # day_dob = _returnValue(left_numerals,0,2)
                        # is_day = validateday(day_dob)
            else:
                left_numerals = re.sub(year_dob,'',date_of_birth)
                left_numerals = re.findall('[0-9]{1}',left_numerals)
                logger.info(left_numerals)
                day_dob = _returnValue(left_numerals,0,2)
                month_dob = _returnValue(left_numerals,2,4)
                
                is_day = validateday(day_dob)
                is_month = validatemonth(month_dob)
                if not is_day or not is_month:
                    month_dob = _returnValue(left_numerals,0,2)
                    day_dob = _returnValue(left_numerals,2,4)
                    is_day = validateday(day_dob)
                    is_month = validatemonth(month_dob)
        elif not is_day and is_month:
            try:
                left_numerals = re.sub(year_dob,'',date_of_birth)
                left_numerals = re.findall('[0-9]{1}',left_numerals)
                logger.info(left_numerals)
                if len(left_numerals)>1:
                    day_dob = _returnValue(left_numerals,0,2)
                    is_day = validateday(day_dob)
                    if not is_day:
                        day_dob = _returnValue(left_numerals,0,1)
                else:
                    day_dob = _returnValue(left_numerals,0,1)
                
                
            except:
                logger.info("No Month found")
            
            

        elif is_day and not is_month and not is_year:
            
            try:
                #left_numerals = re.sub(year_dob,'',date_of_birth)
                left_numerals = re.sub(day_dob,'',date_of_birth)
                logger.info('DOB remaining is :{}'.format(left_numerals))
                left_numerals = re.findall('[0-9]{1}',left_numerals)
                if len(left_numerals)>1:
                    month_dob = _returnValue(left_numerals,0,2)
                    is_month = validateday(month_dob)
                    if not is_month:
                        month_dob = _returnValue(left_numerals,0,1)
                        year_dob = _returnValue(left_numerals,1,len(left_numerals))
                    else:
                        year_dob = _returnValue(left_numerals,2,len(left_numerals))
                
            except:
                logger.info("No Month found")
        elif is_day and not is_month and is_year:
            
            try:
                left_numerals = re.sub(year_dob,'',date_of_birth)
                left_numerals = re.sub(day_dob,'',left_numerals)
                logger.info('DOB remaining is :{}'.format(left_numerals))
                left_numerals = re.findall('[0-9]{1}',left_numerals)
                if len(left_numerals)>1:
                    month_dob = _returnValue(left_numerals,0,2)
                    is_month = validateday(month_dob)
                    if not is_month:
                        month_dob = _returnValue(left_numerals,0,1)
                
            except:
                logger.info("No Month found")
        elif not is_year and is_day and is_month:
            logger.info("when only year is not available and both day an month are available:{}".format(date_of_birth))
            logger.info("Day {}:Month {}".format(day_dob,month_dob))
            try:
                # left_numerals = re.sub(day_dob,'',dobstr[0])
                # logger.info("Left Numerals:{}".format(left_numerals))
                # left_numerals = re.sub(month_dob,'',left_numerals)
                # logger.info("Left Numerals:{}".format(left_numerals))
                left_numerals = re.findall('[0-9]{2}',date_of_birth)
                logger.info("Left Numerals:{}".format(left_numerals))
                if left_numerals!=[]:
                    year_dob = left_numerals[0]
                    #is_year = validateyear(month_dob)
                else:
                    year_dob =-1
                
            except:
                logger.info("No Year found")
                           
        rowdata = [dobstr,year_dob,month_dob,day_dob]
        row_list.append(rowdata)            
        
    # logger.info("Total Records = {}".format(len(index)))
    # logger.info("Total Months in text  = {}".format(count_month))
    # logger.info("Total Valid Date Records = {}".format(valid_daterecords))
    dob,is_year_valid,is_month_valid,is_day_valid = _getvaliddate(year_dob,month_dob,day_dob)
    #logger.info("Just before returning: {}".format(dob))
    #dob_1 = str(datetime.datetime(int(year_dob),int(month_dob),int(day_dob)).date())
    logger.info("Just before returning: {}".format(dob))

    
    return dob,is_year_valid,is_month_valid,is_day_valid

def get_date(utterance:str):
    date_of_birth,is_year_available,is_month_available,is_day_available = converttovalidDOB(utterance)
    return {"date":date_of_birth}


if __name__ == "__main__":
    format=' %(levelname)-6s | %(message)s | %(funcName)s():%(lineno)-4d'
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,format=format)
    
    #handler.setFormatter(formatter)
    #logging.basicConfig(filename="logging.conf", level=logging.INFO)
    while True:

        utterance=input("Enter any utterance: ")
        #newutterance = number2word(utterance)
        #logger.info("New utterance is :{}".format(newutterance))
        date_of_birth,is_year_available,is_month_available,is_day_available = converttovalidDOB(utterance)
        logger.info("DOB is {}".format(date_of_birth))
        logger.info("is_year is {}".format(is_year_available))
        logger.info("is_month is {}".format(is_month_available))
        logger.info("is_day is {}".format(is_day_available))
