import _init_paths
import tensorflow as tf
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import os, sys, cv2, csv
import argparse
from networks.factory import get_network
plt.switch_backend('agg')


CLASSES = ('__background__',
           #'aeroplane', 'bicycle', 'bird', 'boat',
           #'bottle', 'bus', 'car', 'cat', 'chair',
           #'cow', 'diningtable', 'dog', 'horse',
           #'motorbike', 
           'person'#, 'pottedplant',
           #'sheep', 'sofa', 'train', 'tvmonitor'
           )


#CLASSES = ('__background__','person','bike','motorbike','car','bus')

boundaries = []

def vis_detections(im, image_dir, image_name, class_name, dets,ax, thresh=0.5):
    """Draw detected bounding boxes."""
    inds = np.where(dets[:, -1] >= thresh)[0]
    if len(inds) == 0:
        return

    for i in inds:
        bbox = dets[i, :4]
        x_min, y_min, x_max, y_max = bbox[0], bbox[1], bbox[2], bbox[3]
        #print image_dir
        #print im
        boundaries.append(np.array([os.path.join(image_dir, image_name)
            , x_min, y_min, x_max, y_max]))
        score = dets[i, -1]

        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]),
                          bbox[2] - bbox[0],
                          bbox[3] - bbox[1], fill=False,
                          edgecolor='red', linewidth=3.5)
            )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(class_name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=14, color='white')

    ax.set_title(('{} detections with '
                  'p({} | box) >= {:.1f}').format(class_name, class_name,
                                                  thresh),
                  fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.draw()


def demo(sess, net, image_dir, image_name):
    """Detect object classes in an image using pre-computed object proposals."""

    im_file = os.path.join(image_dir, image_name)
    im = cv2.imread(im_file)

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(sess, net, im)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    im = im[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(im, aspect='equal')

    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
	#print dets
        vis_detections(im, image_dir, image_name, cls, dets, ax, thresh=CONF_THRESH)

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Faster R-CNN demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                        default='VGGnet_test')
    parser.add_argument('--model', dest='model', help='Model path',
                        default=' ')

    args = parser.parse_args()

    return args
if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()

    if args.model == ' ':
        raise IOError(('Error: Model not found.\n'))
        
    # init session
    sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
    # load network
    net = get_network(args.demo_net)
    # load model
    saver = tf.train.Saver(write_version=tf.train.SaverDef.V1)
    saver.restore(sess, args.model)
   
    #sess.run(tf.initialize_all_variables())

    print '\n\nLoaded network {:s}'.format(args.model)

    # Warmup on a dummy image
    im = 128 * np.ones((300, 300, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(sess, net, im)

    #home_dir = '/data0/krohitm/posture_dataset/scott_vid/images'
    home_dir = '/home/krohitm/code/Faster-RCNN_TF/temp/images'
    dirpaths,dirnames,_ = os.walk(home_dir).next()

    dirnames.sort()

    for dirpath, directory in zip(dirpaths, dirnames):
        image_dir = os.path.join(home_dir,directory)
        #print image_dir
        _,_,all_images = os.walk(image_dir).next()
        all_images.sort()
        
        try:
            os.mkdir(os.path.join(home_dir, '../detections/{0}'.format(directory)))
        except OSError:
            print "Directory {0} already exists".format(directory)

        for im_name in all_images:
            plt.close('all')
            print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
            print 'Getting bounds for {0}/{1}'.format(directory, im_name)
            demo(sess, net, image_dir, im_name)
            plt.savefig('{0}/../detections/{1}/{2}'.format(home_dir, directory, im_name), 
                bbox_inches='tight')

    boundaries = np.asarray(boundaries)

    with open (os.path.join(home_dir, '../detections/bbox.csv'), 'w') as f:
        print "Writing bboxes to actual identified bboxes file"
        f.write('image_name, x_min,y_min,x_max,y_max\n')
        writer = csv.writer(f, delimiter = ',')
        writer.writerows(boundaries)
    f.close()
    #plt.show()
    #plt.savefig('/data0/krohitm/posture_dataset/scott_vid/images/detections/{0}.jpg'.format((str(i+1)).zfill(7)), bbox_inches='tight')

