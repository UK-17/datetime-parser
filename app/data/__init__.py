import logging
import sys
import os
from pathlib import Path
sys.path.append(os.path.realpath(os.path.relpath("../..")))
logger = logging.getLogger(__name__)
import json

class Data:
    def __init__(self):
        utterance_2_number = Path(f"{os.path.realpath(os.path.relpath('../'))}/datetime-parser/app/data/mapping.json")
        logger.info("utterance  2 number is {}".format(utterance_2_number))

        
        
        self.conversion_dictionary = dict()
        self.scale_tens =dict()
        self.year_list = list()
        
        with open(utterance_2_number) as f:
            word2numeralmap= json.load(f)
            #logger.info("Data uploaded:{}".format(word2numeralmap))

        self.conversion_dictionary = word2numeralmap[0]['conversion_dictionary'][0]
        
        self.scale_tens = word2numeralmap[0]['scale_tens'][0]
        
        self.year_list = word2numeralmap[0]['year_list']
        self.number_to_word = word2numeralmap[0]['number_to_word'][0]