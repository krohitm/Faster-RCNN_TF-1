# Import the required modules
#import dlib
#import cv2
import argparse
import get_pts_for_ims
import numpy as np
import os
import csv
import matplotlib.pyplot as plt
#import re


def annotate(home_dir):
    #print "in annotate"
    all_image_names = []
    _,directories,_ = os.walk(home_dir).next()
    directories.sort()
    #print directories

    for directory in directories:
        #print directory
        full_path = os.path.join(home_dir, directory)
        _,_,files = os.walk(full_path).next()
        files.sort()
        full_file_names = ['{0}'.format(os.path.join(full_path,file_name)
            ) for file_name in files]
        all_image_names = all_image_names + full_file_names

    start = 0
    coords = []
    
    if os.path.isfile(os.path.join(home_dir, 'person_bbox.csv')):
        with open (os.path.join(home_dir, 'person_bbox.csv'), 'r') as f:
            print "Reading existing bbox file"
            reader = csv.reader(f, delimiter = ',')
            for row in reader:
                coords.append(row)
        f.close()
        del coords[0]
        
        i = 0
        while i < len(coords) and start == 0:
            if max(map(float, coords[i][1:5])) == 0:
                del coords[i]
                start = i
            i += 1
    #frame_counter = 0 #to skip frames and later extrapolate in between
    for i in range(start, len(all_image_names)):
        #if frame_counter < 5:
        #    frame_counter +=
        cur_fname=[all_image_names[i]]
        img=plt.imread(cur_fname[0])
        points=get_pts_for_ims.run(img,np.array([0,0,0,0]), str(i))
        points = cur_fname + points
        coords.append(points)

        if max(map(float, points[1:5])) == 0:
            break

    with open (os.path.join(home_dir, 'person_bbox.csv'), 'w') as f:
        print "Writing bboxes to bbox file"
        f.write('image_name,x_min,y_min,x_max,y_max\n')
        writer = csv.writer(f, delimiter = ',')
        writer.writerows(coords)
    f.close()


if __name__=='__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--parent_folder", required=True, help="Path to parent folder")

    args = vars(ap.parse_args())
    parent_folder = args['parent_folder']
    annotate(parent_folder)