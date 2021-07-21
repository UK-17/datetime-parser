import os
from typing import Dict, List, Optional
import re
import datetime
import time
import requests
import logging
from dateutil.relativedelta import relativedelta


def get_weekday(day):
    return days.index(day[:3].lower()) + 1

def get_next_dayofweek_datetime(date_time, dayofweek):
    start_time_w = date_time.isoweekday()
    target_w = get_weekday(dayofweek)
    if start_time_w < target_w:
      day_diff = target_w - start_time_w
    else:
        day_diff = 7 - (start_time_w - target_w)

    return date_time + datetime.timedelta(days=day_diff)

count = 0
days  = ["mon","tue","wed","thu","fri","sat","sun"]

def process_date_time(utterance:str, date_of_pickup, time_of_pickup):
    business_hours = []
    last_proposed_data = None
    datetime_range = []
    import time
    if business_hours.__len__()==0:
        business_hours.append(datetime.time(8,0))
        business_hours.append(datetime.time(17,0))
    
    today = datetime.datetime.now()

    # check to remove 'may' in user utterance ELSE it was being captured as MAY month
    # USER : May I/ May we have an appointment for tomorrow
    # USER : I amy/ We may come at 3 pm tomorrow
    # USER : 2 p.m. maybe/ may be
    # USER : May I have an appointment for 3rd of May
    if utterance.lower().find('may i')!=-1:
        utterance = utterance.replace('may i','')
    if utterance.lower().find('may we')!=-1:
        utterance = utterance.replace('may we','')
    if utterance.lower().find('i may')!=-1:
        utterance = utterance.replace('i may','')
    if utterance.lower().find('we may')!=-1:
        utterance = utterance.replace('we may','')
    if utterance.lower().find('may be')!=-1:
        utterance = utterance.replace('may be','')
    if utterance.lower().find('maybe')!=-1:
        utterance = utterance.replace('maybe','')

    t1 = time.time()
    req = requests.post(os.getenv("DATETIME_PARSER_ENDPOINT","https://voicetest.vengage.ai/msp/get_date_and_time"),json={'sentence':utterance.lower()})
    t2 = time.time()
    latency = t2-t1
    # print('Latency for datetime parsing: {} seconds'.format(latency))
    json_response = req.json()
    result = json_response['result']
    raw_data = result

    # User >> I can come at 11 tomorrow (without am/pm)
    # Two set of dictionaries in a list are returned from datetime parser. One for 11am and other for 11pm. 
    # P.M. time is returned first in the list. Then A.M. time
    # In cases where user asks time between 8 and 11, list is swapped with a.m. time before p.m. time 
    if result.__len__()==2 and result[0]['time']!='' and result[1]['time']!='':
        n=0
        for dateTimeParserResult_Item in result:
            time = dateTimeParserResult_Item['time']
            time = time.split('-')
            time = time[0]
            time = time.split(':')
            hour = int(time[0])
            swap_list = [8,9,10,11]
            for dateTimeParserResult_Item in swap_list:
                if dateTimeParserResult_Item == hour:
                    n+=1
                    break

        if n%2!=0:
            result[0],result[1] = result[1],result[0]

    # print("Datetime raw parsing result:{}, Last proposed data:{}".format(result, last_proposed_data))
    processed_result =[]

    # pre-process the message for meeting the application requirements.
    # in cases where dictionery does not have any of the 5 keys, code below adds them with Null value
    for dateTimeParserResult_Item in result:

        # Set all the mandatory fields in datetime parsed result.
        # it may happen that one of these fields is missing in result.
        mandatory_fields = ['day','month','text','time','week']
        for each in mandatory_fields:
            if each not in dateTimeParserResult_Item:
                dateTimeParserResult_Item[each] = ""

        dateTimeParserResult_Item['>>'] = False
        dateTimeParserResult_Item['<<'] = False

        # print("\tProcessing:{}".format(dateTimeParserResult_Item))

        weekDays = ("monday","tuesday","wednesday","thursday","friday","saturday","sunday")
        months = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}

        today = datetime.date.today()
        day_ = int(today.strftime("%d"))
        month_ = int(today.strftime("%m"))
        year_ = int(today.strftime("%Y"))
        # year = today.strftime("%Y")
        
        # process month if found in parsed result
        if dateTimeParserResult_Item['month'].__len__()>0:
            month = dateTimeParserResult_Item['month']

            # User: I can come after two months. DatetimeParser result: >>M+2
            # User: I can come after second month. DatetimeParser result: >>M2
            if month.find('>>') != -1:
                if month.find('+'):
                    month = month.split('+')
                    month_add = int(month[1])+1
                    date = today + relativedelta(months=month_add)
                    date_start_of_month = 1
                    month = int(date.strftime("%m"))
                    year = int(date.strftime("%Y"))
                    first_date_of_asked_month = datetime.date(year,month,date_start_of_month)
                    date_month = first_date_of_asked_month

                else:
                    month_add = int(month[:3])+1
                    date = today + relativedelta(months=month_add)
                    date_start_of_month = 1
                    month = int(date.strftime("%m"))
                    year = int(date.strftime("%Y"))
                    first_date_of_asked_month = datetime.date(year,month,date_start_of_month)
                    date_month = first_date_of_asked_month
            
            elif month.find('<<') != -1:
                pass

            # response is in format 'M+1'
            elif month.find('+') != -1:
                month = month.split('+')
                month_add = int(month[1])

                date = today + relativedelta(months=month_add)
                date_start_of_month = 1
                month = int(date.strftime("%m"))
                year = int(date.strftime("%Y"))
                first_date_of_asked_month = datetime.date(year,month,date_start_of_month)
                date_month = first_date_of_asked_month
                

            # response is a month name. Example: 'February'
            elif month[0:3].lower() in months:
                month = (months[month[0:3]])
                date_start_of_month = 1
                year = year_
                first_date_of_asked_month = datetime.date(year,month,date_start_of_month)
                # date set to today if user asks for slot in current month and date is earlier than today
                date_month = first_date_of_asked_month
                if first_date_of_asked_month<today:
                    year+=1
                    first_date_of_asked_month = datetime.date(year,month,date_start_of_month)
                    date_month = first_date_of_asked_month
                # print("Revised date: {}".format(first_date_of_asked_month))


            else:
                month_add = int(month[:3])
                date = today + relativedelta(months=month_add)
                date_start_of_month = 1
                month = int(date.strftime("%m"))
                year = int(date.strftime("%Y"))
                first_date_of_asked_month = datetime.date(year,month,date_start_of_month)
                date_month = first_date_of_asked_month

            if dateTimeParserResult_Item['week'].__len__()==0 and dateTimeParserResult_Item['day'].__len__()==0:
                day_date = date_month
        
        # process week if found in parsed result
        if dateTimeParserResult_Item['week'].__len__()>0:
            week = dateTimeParserResult_Item['week']
            # set initial date for processing week
            if dateTimeParserResult_Item['month'].__len__()>0:
                date = date_month
            else:
                date = today

            if week.find('<<') != -1:
                date_week = date

            elif week.find('>>') != -1:
                if week.find('+') != -1:
                    data = week.split('+')
                    count = int(data[1])
                    next_date = today + datetime.timedelta(days = (count*7))
                    date_week = next_date
                    
                else:
                    count = int(week[3:])
                    day_count_today = date.weekday()
                    days_to_monday_of_asked_week = 7*(count+1)-day_count_today
                    date_on_monday_of_asked_week = date + datetime.timedelta(days=days_to_monday_of_asked_week)
                    date_week = date_on_monday_of_asked_week

            else:
                # {sentence:after two weeks, response:'W+2'} or {sentence:'after 2nd week', response:'W2+1'}
                if week.find('+') != -1:
                    data = week.split('+')
                    week = data[0]
                    number = data[1]

                    # {sentence:'after 2nd week', response:'W2+1'}
                    if week.__len__()>=2:
                        regex = re.compile("W")
                        count = regex.sub('',week)
                        count = int(count)
                        next_date = today + datetime.timedelta(days = (count*7))
                        date_week = next_date
                    
                    # {sentence:after two weeks, response:'W+2'}
                    elif week.__len__()==1:
                        count = int(number)
                        day_count_today = date.weekday()
                        days_to_monday_of_asked_week = 7*count-day_count_today
                        date_on_monday_of_asked_week = date + datetime.timedelta(days=days_to_monday_of_asked_week)
                        # print('Date on monday of asked week: {}'.format(date_on_monday_of_asked_week))
                        date_week = date_on_monday_of_asked_week

                # {utterance:2nd week, response:'W2'}
                else:
                    count = int(week[1:])
                    day_count_today = date.weekday()
                    days_to_monday_of_asked_week = 7*count-day_count_today
                    date_on_monday_of_asked_week = date + datetime.timedelta(days=days_to_monday_of_asked_week)
                    date_week = date_on_monday_of_asked_week


            if dateTimeParserResult_Item['day'].__len__()==0:
                day_date = date_week


        # process day if found in parsed result along with week. {sentence:next week thursday } {response:week:'W+1', day:'thursday}
        if dateTimeParserResult_Item['month'].__len__()>0 or dateTimeParserResult_Item['week'].__len__()>0 and dateTimeParserResult_Item['day'].__len__()>0:
            if dateTimeParserResult_Item['month'].__len__()>0 and dateTimeParserResult_Item['week'].__len__()>0:
                date = date_week
            elif dateTimeParserResult_Item['month'].__len__()==0 and dateTimeParserResult_Item['week'].__len__()>0:
                date = date_week
            elif dateTimeParserResult_Item['month'].__len__()>0 and dateTimeParserResult_Item['week'].__len__()==0:
                date = date_month

            isoday = date.weekday()
        
            if dateTimeParserResult_Item['day'].__len__()>0:
                day_date = get_next_dayofweek_datetime(today,dateTimeParserResult_Item['day']).strftime("%Y-%m-%d")

        # /------------------------------------------------/
        #          if only day in dt parser reponse
        # /------------------------------------------------/
        day = dateTimeParserResult_Item['day']

        # if utterance does not have any month or week values. Example: 'i need an appointment on tuesday'. response:'tuesday'
        if dateTimeParserResult_Item['month'].__len__()==0 and dateTimeParserResult_Item['week'].__len__()==0:
            if dateTimeParserResult_Item['day']=='' and last_proposed_data is not None:
                last_proposed_date = last_proposed_data['from'].strftime("%Y-%m-%d")
                # day_date = (datetime.datetime.today+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                
            if dateTimeParserResult_Item['day']=='' and last_proposed_data is None:
                dateTimeParserResult_Item['day'] = "tomorrow"

            day = dateTimeParserResult_Item['day'].lower()
            # TODO: this logic needs to be removed once the output from datetime parser is fixed.

            # hack: to make sure application does not break.
            if isinstance(dateTimeParserResult_Item['day'],list):
                day = dateTimeParserResult_Item['day'][0]

            # sentence: 'before/after 15th of december' response:{day:'>>15/12/2020'}
            if day.find("/") != -1:
                sign = day[0:2]
                if sign == '<<':
                    date = day[2:]
                elif sign == '>>':
                    date = day[2:]
                else:
                    date = day

                data = date.split('/')
                day_ = int(data[0])
                month_ = int(data[1])
                year_ = int(data[2])
                
                date = datetime.date(year_,month_,day_)

                if sign == '<<':
                    date_from = today
                    date_to = date - datetime.timedelta(days=1)
                    day_date = date_from.strftime("%Y-%m-%d")
                elif sign == '>>':
                    date_from = date + datetime.timedelta(days=1)
                    date_to = ''
                    day_date = date_from.strftime("%Y-%m-%d")
                else:
                    date_from = date
                    day_date = date_from.strftime("%Y-%m-%d")

            # datetime parsed results of type 'today', 'tomorrow', 'tomorrow+1' 'sunday'
            if day.lower() == 'today':
                day_date = today.strftime("%Y-%m-%d")
            elif day.lower() == 'tomorrow' or day.lower() == '>>today':
                day_date = (today+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            elif day.lower() == 'tomorrow+1': # day after tomorrow
                day_date = (today+datetime.timedelta(days=2)).strftime("%Y-%m-%d")
            elif day.find('>>today+') != -1: # add today+days
                days_add=day.lower().split('+')
                days_to_add = int(days_add[1])
                day_date = (today+datetime.timedelta(days=days_to_add+1)).strftime("%Y-%m-%d")
            elif day.find('>>tomorrow+') != -1: # add today+days
                days_add=day.lower().split('+')
                days_to_add = int(days_add[1])
                day_date = (today+datetime.timedelta(days=days_to_add+2)).strftime("%Y-%m-%d")            
            elif day.find('>>today') != -1: # add today+days
                day_date = (today+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            elif day.find('>>tomorrow') != -1: # add today+days
                day_date = (today+datetime.timedelta(days=2)).strftime("%Y-%m-%d")
            elif day.find('today+') != -1: # add today+days
                days_add=day.lower().split('+')
                days_to_add = int(days_add[1])
                day_date = (today+datetime.timedelta(days=days_to_add)).strftime("%Y-%m-%d")
            elif day.find('tomorrow+') != -1: # add today+days
                days_add=day.lower().split('+')
                days_to_add = int(days_add[1])
                day_date = (today+datetime.timedelta(days=days_to_add+1)).strftime("%Y-%m-%d")
            
            elif day[:3].lower() in days: # convert day to deterministc date
                day_date = get_next_dayofweek_datetime(today,day[:3]).strftime("%Y-%m-%d")

            # sentence: 'anything after'. response:{day:'>>', time:'>>'}. Day value should be nil. Hack to compensate that
            if day.find('>>') != -1:
                day_add = day[:2]
                day = day[2:]
                if day.find('+') != -1:
                    days_ = day.split('+')
                    day = days_[0].lower()
                    days_add = int(days_[1]) + 1

                else:
                    day = day.lower()
            
        time_range = dateTimeParserResult_Item['time']

        if isinstance(time_range,list) and time_range.__len__()>0:
            if time_range[0].find('<<') !=-1 or time_range[0].find('>>') !=-1:
                time_range = str(time_range[0])

                dateTimeParserResult_Item['>>'] = True
                dateTimeParserResult_Item['<<'] = True
                
                if (time_range).find('>>') != -1:
                    hours_to_add = 1
                    from_ = last_proposed_data['from']
                    from_ = from_ + datetime.timedelta(hours=hours_to_add)
                    from_ = from_.strftime('%H:%M')

                    to_ = business_hours[1].strftime('%H:%M')
                    
                    time_range=from_+'-'+to_

                elif (time_range).find('<<') != -1:
                    hours_to_subtract = 1

                    from_ = last_proposed_data['from']
                    from_ = from_ - datetime.timedelta(hours=hours_to_subtract)
                    from_ = from_.strftime('%H:%M')
                    
                    to_ = last_proposed_data['to']
                    to_ = to_ - datetime.timedelta(hours=hours_to_subtract)
                    to_ = to_.strftime('%H:%M')
                    
                    time_range=from_+'-'+to_

        if isinstance(time_range,str) and time_range.__len__()>0 and time_range.find('+') != -1:
            if (time_range).find('>>') != -1:
                if time_range.find('+')!=-1:
                    time_range = time_range.split('+')
                    hours_to_add = int(time_range[1])

                from_ = last_proposed_data['from']
                from_ = from_ + datetime.timedelta(hours=hours_to_add)
                from_ = from_.strftime('%H:%M')

                to_ = business_hours[1].strftime('%H:%M')
                
                time_range=from_+'-'+to_

            elif (time_range).find('<<') != -1:
                if time_range.find('+')!=-1:
                    time_range = time_range.split('+')
                    hours_to_subtract = int(time_range[1])

                from_ = last_proposed_data['from']
                from_ = from_ - datetime.timedelta(hours=hours_to_subtract)
                from_ = from_.strftime('%H:%M')

                to_ = last_proposed_data['to']
                to_ = to_ - datetime.timedelta(hours=hours_to_subtract)
                to_ = to_.strftime('%H:%M')
                
                time_range=from_+'-'+to_

            elif time_range.find('+'):
                time_range = time_range.split('+')
                hours_to_add = int(time_range[1])

                from_ = last_proposed_data['from']
                from_ = from_ + datetime.timedelta(hours=hours_to_add)
                from_ = from_.strftime('%H:%M')

                to_ = last_proposed_data['to']
                to_ = to_ + datetime.timedelta(hours=hours_to_add)
                to_ = to_.strftime('%H:%M')
                
                time_range=from_+'-'+to_
        
        
        if isinstance(time_range,list) or isinstance(time_range,str) and time_range.__len__() == 0:
            time_range = ['08:00-17:00']
            time_range = time_range[0].split('-')
            time_range.append(time_range[0])
            time_range.append(time_range[1])
        elif isinstance(time_range,list) and time_range.__len__() > 0:
            time_range = time_range[0].split("-")
            if time_range.__len__()==1:
                time_range.append(time_range[0])
            elif time_range.__len__()==2:
                time_range.append(time_range[0])
                time_range.append(time_range[1])
        elif isinstance(time_range,str):
            time_range = time_range.split("-")
            if time_range.__len__()==1:
                time_range.append(time_range[0])
            elif time_range.__len__()==2:
                time_range.append(time_range[0])
                time_range.append(time_range[1])
        
        date_range = []
        date_from = str(day_date)

        date_range.append(date_from)

        datetime_range = []
        datetime_range.append(datetime.datetime.strptime(" ".join([date_range[0],time_range[0]]),"%Y-%m-%d %H:%M"))
        datetime_range.append(datetime.datetime.strptime(" ".join([date_range[0],time_range[1]]),"%Y-%m-%d %H:%M"))
        datetime_range.sort()


        processed_result.append({'value':{'day':day, 'start':datetime_range[0],'end':datetime_range[1],'raw_result':dateTimeParserResult_Item}})
    return raw_data, processed_result

def translate_range(utterance:str):
    raw_data, processed_result = process_date_time(utterance,None,None)
    start = processed_result[0]['value']['start']
    end = processed_result[0]['value']['end']
    translation = datetime.datetime.strftime(start,'%I:%M %p, %d-%b-%Y') + ' to ' + datetime.datetime.strftime(end,'%I:%M %p, %d-%b-%Y')
    return {"utterance":utterance,"start_datetime":start,"end_datetime":end,"translation":translation}


if __name__=="__main__":

    utterance,raw_data, processed_result = process_date_time("Anything between 11am to 2pm next week",None,None)
    print("\n")
    print(utterance)
    print(raw_data)
    print(processed_result[0]['value'])