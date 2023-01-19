#!/usr/bin/env python
import requests
import sys
import os
from lib.mongo import get_pending_queue, get_completed_jobs
from lib.payload import Payload
from lib.file import check_folder

"""
output dir structure should be

model_name
-> album_name
--> image1.jpg
--> image2.jpg
"""

def download_image(url):
    """
    probably should sanitize image here
    also should check content type is correct
    """
    print ("downloading: %s" % url)
    r = requests.get(url, allow_redirects=True)
    return r.content


def save_image(filename, data):
    with open(filename, "wb") as f:
        f.write(data)

def get_work():
    print("getting some work")
    record = get_pending_queue().find_one()
    if record is None:
        print("no work to do, exiting")
        exit(1)
    return Payload(record)

def make_count(at, max_zero=6):
    """
    since the filesystem will stop sorting correctly if you do not have
    preceding 0 in a number, we will fill with the appropriate 
    amount of 0's
    """
    
    chars = str(at)
    amount_of_zeroes = max_zero - len(chars)
    
    # low file count, doesn't matter so just return the number
    if amount_of_zeroes <= 0: return chars
    return "0"*amount_of_zeroes + chars

def complete_work(payload):
    pending = get_pending_queue()
    jobs = get_completed_jobs()

    if not payload.mongo(): 
        print("something is wrong this is not a mongo object")
        exit(1)
    
    if pending.find_one({"_id": payload.unique_id}) is None:
        print("this payload is not in the pending queue.. wtf?")
        print(payload)
    
    # first add to completed because if there's duplicates there who cares
    # unset _id field..

    print("inserting into completed jobs collection")
    jobs.insert_one(payload.dict())
    print ("deleting from pending queue")
    pending.delete_one({"_id": payload.unique_id})
    print ("done")
    



if __name__ == "__main__":
    OUTPUT_DIRECTORY = os.path.join(os.getcwd(), "static/save")
    if not check_folder(OUTPUT_DIRECTORY): exit(1)
    work = get_work()
    model_path = os.path.join(OUTPUT_DIRECTORY, work.model)
    full_path = os.path.join(OUTPUT_DIRECTORY, work.model, work.album)
    
    if not check_folder(model_path): os.mkdir(model_path)
    if check_folder(full_path): 
        print("something is wrong, this album already exists?")
        print(work)
        exit(1)

    os.mkdir(full_path)

    count = 1
    total_images = len(work.images)

    print("time to save some images")
    print("saving to directory: %s" % full_path)
    print("model name is: %s" % work.model)
    print("album name is: %s" % work.album)

    for image in work.images:
        file_name = make_count(count, len(str(total_images)))
        full_file = os.path.join(full_path, file_name + ".jpg") 
        count += 1
        data = download_image(image)
        print("saving as: %s" % full_file)
        save_image(full_file, data)

    print("done saving")

    complete_work(work)

    
