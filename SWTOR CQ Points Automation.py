# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 11:14:05 2020

@author: James Altemus
"""
import pytesseract

import pyautogui as agui
import numpy as np
import pandas as pd

from PIL import Image
from time import sleep
from datetime import datetime

def progress(done, complete):
    # A simple progress bar the takes the amount of processes and the total
    # amount of porcesses needed
    finished = (done/complete)*100
    print('\r' + '|' + ((u'\u2588')*(int(finished))).ljust(99) + '| {0:.2f}%'.format(finished, 100), end='')


def guild_scroll():
    # Performs one scroll through the guild roster
    for i in range(12):
        agui.scroll(-20)


def id_roster(top_corner = 'CornerTop.png', bot_corner = 'CornerBot.png'):
    # Uses images of the diagnally adjacent corners of the guild window to
    # identify the location of the guild window. Returns a tuple for creating
    # the bounding box in pillow's format
    top = agui.locateOnScreen(top_corner, confidence = 0.9)
    bot = agui.locateOnScreen(bot_corner, confidence = 0.9)
    return (top[0], top[1], bot[0]+bot[2]-top[0], bot[1]+bot[3]-top[1])


def id_scroll(bar_id_pic = 'Scroll_Bar.png'):
    # Locates the scroll bar ussing an image and moves the cursor there
    offline_loc = agui.locateOnScreen(bar_id_pic, confidence = 0.9)
    offline_x, offline_y = agui.center(offline_loc)
    agui.moveTo(offline_x, offline_y)


def contrast_eval(pix, comp_val, invert_only):
    if invert_only:
        ## Only performs an inversion of the pixel values
        return [255-pix[0],255-pix[1],255-pix[2]]
    else:
        ## Transforms the value of all pixels to the maximum of each RGB value
        ## and inverts the resultant value
        pix = 255-max([pix[0],pix[1],pix[2]])
        if pix < comp_val:
            ## Ensures the value of the pixel is not too low
            pix = max(pix-comp_val/3,0)
            return [pix, pix, pix]
        else:
            ## Ensures the pixel value is not too high
            pix = min(pix+20,255)
            return [pix, pix, pix]


def increase_contrast(roster):
    # Transforms an image of the roster into columns containing arrays of
    # the pixel values
    
    ## Convert to pixel values
    np_roster = np.array(roster)
    net_pictures = []
    nm_rows = []
    lg_nm_rows = []
    rnk_rows = []
    cq_pt_rows = []
    ## Split into relevant columns
    count = 0
    for r in range(len(np_roster)):
        ## Update the count and drift score to maintain and avvount for
        ## variable sizing in the guild roster rows
        count+=1
        drift = np.round(count/100)
        ## Check to see if a new row needs to be registered
        if (count-6+drift)%25 == 0:
            ## Save previous row to output and confirm data type
            nm_roster = np.array(nm_rows, dtype = np.uint8)
            lg_nm_roster = np.array(lg_nm_rows, dtype = np.uint8)
            rnk_roster = np.array(rnk_rows, dtype = np.uint8)
            cq_pt_roster = np.array(cq_pt_rows, dtype = np.uint8)
            
            net_pictures.append((Image.fromarray(nm_roster),
                                 Image.fromarray(lg_nm_roster),
                                 Image.fromarray(rnk_roster),
                                 Image.fromarray(cq_pt_roster)))
            ## Initiate new rows
            nm_rows = []
            lg_nm_rows = []
            rnk_rows = []
            cq_pt_rows = []
        
        ## Take relevant row and check transformation type
        r = np_roster[r]
        invert_only = np.any(r[:1235] > 200)
        ## Initiate lists
        nm_cols = []
        lg_nm_cols = []
        rnk_cols = []
        cq_pt_cols = []
        ## Eval pixel transformation and append appropriate column
        for c in range(len(r)):
            if 50 < c <= 180:
                pix = contrast_eval(r[c],150,invert_only)
                nm_cols.append(pix)
            elif 295 < c <= 415:
                pix = contrast_eval(r[c],150,invert_only)
                lg_nm_cols.append(pix)
            elif 930 < c <= 1035:
                pix = contrast_eval(r[c],150,invert_only)
                rnk_cols.append(pix)
            elif 1130 < c <= 1235:
                pix = contrast_eval(r[c],150,invert_only)
                cq_pt_cols.append(pix)
            else:
                continue
        ## Append to current rows
        nm_rows.append(nm_cols)
        lg_nm_rows.append(lg_nm_cols)
        rnk_rows.append(rnk_cols)
        cq_pt_rows.append(cq_pt_cols)
    ## Return output minus title row
    return net_pictures[1:]


def pic_to_text(image_list, path):
    # Converts the pixel value array to an image then to text
    output = []
    name_error = []
    total_error = []
    ## Loop through rows
    for image_tuple in image_list:
        char = []
        ## Loop through columns
        for image in image_tuple:
            ## Use pytesseract to convert to text
            pytesseract.pytesseract.tesseract_cmd = path
            TESSDATA_PREFIX = path[:-10]
            char.append(pytesseract.image_to_string(image, lang='eng'))
        if char[0] == '':
            if char[2] == '' and char[3] == '':
                ## Check is no information was registered
                total_error.append(image_tuple[0])
            else:
                ## Check for specific errors
                name_error.append(image_tuple[0])
        output.append(char)
    ## Return outputs and errors seperately
    return output, total_error, name_error


def parse_roster(text):
    # Analyses and formats the text to ensure readability
    error = []
    nm = []
    lg_nm = []
    rank = []
    cq = []
    for char in text:
        ## Remove invalid punctuation
        char[0] = char[0].replace('‘','')
        char[0] = char[0].replace(':','')
        char[0] = char[0].replace('’',"'")
        
        char[1] = char[1].replace('‘','')
        char[1] = char[1].replace(':','')
        char[1] = char[1].replace('’',"'")
        
        char[2] = char[2].replace('‘','')
        char[2] = char[2].replace(':','')
        char[2] = char[2].replace('’',"'")
        
        ## Check for proper number recognition
        if char[3] in ['o', 'O', '']:
            char[3] = '0'
        char[3] = char[3].replace(',','')
        char[3] = char[3].replace('.','')
        if char[3].isnumeric():
            char[3] = int(char[3])
        else:
            error.append(char[0])
            char[3] = 999999999
        
        ## Append the final output lists with the appropriate values
        nm.append(char[0])
        lg_nm.append(char[1])
        rank.append(char[2])
        cq.append(char[3])
    
    ## Returns a tuple of the lists and the error list
    return (nm, lg_nm, rank, cq), error


def check_repeat(name, roster):
    # Checks to ensure the roster values do not overlap when reaching the
    # end of the scrolling range. Splits the list to avoid duplicates
    if name in roster[0]:
        pos = roster[0].index(name)+1
        roster = (roster[0][pos:], roster[1][pos:],
                  roster[2][pos:], roster[3][pos:])
    return roster


def correct(loc, roster):
    # Accepts a correction CSV file, and sorts through the duplicate values to
    # ensure proper counting
    
    ## Load file and format
    correction = pd.read_csv(loc)
    correction.columns = ["Character", "Legacy", "Rank", "CQ"]
    
    ## Unpack roster tuple
    Rchar = roster[0]
    Rleg = roster[1]
    Rrank = roster[2]
    Rcq = roster[3]
    ## Iterate through all corrections
    for i in range(len(correction)):
        char = correction['Character'][i]
        ## If the error is from the reading the conquest points
        if char in Rchar:
            idx = Rchar.index()
            Rcq[idx] = int(correction[correction['Character'] == char]['CQ'])
        ## If the error is due to complete unreadability
        else:
            row = correction.loc[i]
            Rchar.append(row['Character'])
            Rleg.append(row['Legacy'])
            Rrank.append(row['Rank'])
            Rcq.append(row['CQ'])
    return (Rchar, Rleg, Rrank, Rcq)


def output_file(filename, roster_cols):
    # Creates a dataframe to manupulate and perfomr analysis then outputs a CSV
    final = pd.DataFrame({'Character Name': roster_cols[0],
                         'Legacy Name': roster_cols[1],
                         'Guild Rank': roster_cols[2],
                         'Character CQ Points': roster_cols[3]})
    ## Calculate legacy name CQ score
    temp_df = final.groupby('Legacy Name').sum()
    ## Append Legacy score to end of data frame
    leg_cq = []
    for leg_nm in final['Legacy Name']:
        leg_cq.append(temp_df.loc[leg_nm][0])
    final['Legacy CQ Points'] = leg_cq
    ## Output CSV
    final.to_csv(filename, index = False)



def gather_cq_points():
    print('This program will scroll through the guild roster and gather the CQ point information.\n')
    print('This program requires tesseract. Please ensure tesseract is installed before continuing.')
    print('Tesseract can be downloaded from: https://github.com/tesseract-ocr/tesseract/blob/master/README.md')
    print('For Windows, Tesseract can be downloaded from: https://github.com/UB-Mannheim/tesseract/wiki\n')
    print('If tesseract is installed in C:/Program Files/Tesseract-OCR/tesseract press any key to continue')
    print('otherwise please enter the installation location now.')
    ## Get tesseract directory from user
    tess_install = input()
    if tess_install == '':
        tess_install  = 'C:/Program Files/Tesseract-OCR/tesseract'
    
    ## Get guild name for file naming
    print('Please enter the guild name.')
    guildname = input()
    
    ## Get member count to configure scroll count
    print('Please enter the number of members in the guild.')
    member_count = int(input())
    total_scrolls = int(np.ceil(member_count/24))
    
    ## Query formatting compliance
    print('Before you continue be sure SWTOR is set up as followed:')
    print('  * The guild window must be open')
    print('  * Show offline members should be selected')
    print('  * The last column should be set to CQ points')
    print('  * The second to last column should be set to rank')
    print('  * Ensure the guild window is completely visable and unobstructed by anything including this program. resize if needed')
    print('\nIf the following are done, press any key to continue...')
    input()
    ## Pause to give the user time to step away from the mouse
    print('Now processing the guild roster. Do not touch the mouse, keyboard, or computer...\n')
    sleep(3)
    ## Getting size and number of scrolls
    progress(0,total_scrolls)
    roster_area = id_roster()
    id_scroll()
    
    ## Creating storage lists
    img_error = []
    nam_error = []
    text_error = []
    
    char_name = []
    legacy_name = []
    guild_rank = []
    cq_points = []
    ## Perform screen capture analysis to transform to text
    for i in range(total_scrolls):
        roster = agui.screenshot(region=roster_area)
        roster = increase_contrast(roster)
        roster, ierr, nerr = pic_to_text(roster, tess_install)
        nam_error.append(nerr)
        img_error.extend(ierr)
        roster, err = parse_roster(roster)
        text_error.extend(err)
        
        if char_name:
            roster = check_repeat(char_name[-1], roster)
        
        char_name.extend(roster[0])
        legacy_name.extend(roster[1])
        guild_rank.extend(roster[2])
        cq_points.extend(roster[3])
        
        guild_scroll()
        progress(i+1,total_scrolls)
    
    ## Crate file name and data tuple
    filename = guildname+'_Guild_Roster_'+str(datetime.today())[:10]+'.csv'
    final = (char_name, legacy_name, guild_rank, cq_points)
    
    ## Raise reading errors to user
    while True:
        print('\n{0} errors were caught. Would you like to display them? y/n'.format(len(img_error) + len(text_error)))
        ans = input()
        if ans.lower() in ['yes','y','yeah','yea']:
            print('Please create a CSV file containing the following informaiton')
            print('Ensure the CSV columns are "Character Name", "Legacy Name", "Guild Rank", "Character CQ Points"')
            print('Press any key to show the names with unreadable CQ point counts:')
            input()
            ## Raise errors concerning unreadable numbers or 
            for err in text_error:
                print(err)
            print('Press any key to show the name pictures of completely uncreadable rows:')
            input()
            ## Raise errors where nothing was detected
            for err in img_error:
                err.show()
            break
        elif ans.lower() in ['no', 'n', 'nah', 'naw', 'nope', 'negative']:
            break
    
    ## Query user for corrections and accept corrections
    print('If you have corrected the errors, please input the path to the CSV file containing the missing data otherwise enter "no".')
    print('E.g. C:Users\Documents\Guild_Correction\Missing.csv')
    loc = input()
    if loc.lower() not in ['no', 'n', 'nah', 'naw', 'nope', 'negative']:
        final = correct(loc, final)
        print('Thank you for the corrections. Outputing the final result...')
    else:
        print('You have chosen not to account for errors. Outputing the final result...')
    
    ## Output CSV file
    output_file(filename, (char_name, legacy_name, guild_rank, cq_points))
    print('The guild roster has been saved as '+filename)
    
    ## Raise additionall naming errors
    print('The following names were not able to be registered, thought other aspects were.')
    print('You will need to manually add them to the CSV file. They will be shown now:')
    sleep(2)
    for err in nam_error:
        err.show()
    print('\nDownload complete. Press any key to close')
    input()