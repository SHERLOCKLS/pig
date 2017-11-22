'''
object detection

https://github.com/tensorflow/models/issues/2773 大于0.5才显示
https://github.com/tensorflow/models/tree/master/research/slim
https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md

https://handong1587.github.io/    各种方向的paper列了一堆


运行说明：
    需要先按照官网安装object detection 模块
    将此程序放在object_detection/some_name/ 文件夹下
    注意修改数据读取路径PATH_TO_TEST_IMAGES_DIR和数据保存路径TARGET_FOLDER，然后运行(test_mode = True为调试开发模式，False为pig数据集上的运行模式)
    默认PATH_TO_TEST_IMAGES_DIR中的pig数据集是按照类别分在不同文件夹下，参见video2image.py
程序说明：
    可考虑适当扩展det出的box，以更好地包裹目标，crop时限定不要超出图像边界即可
'''

import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
import cv2
import timeit

print(tf.__version__)
if tf.__version__ != '1.4.0':
  raise ImportError('Please upgrade your tensorflow installation to v1.4.0!')
  
test_mode = False
BATCH_SIZE = 4

sys.path.append("..")
sys.path.append("../..")
from utils import label_map_util
from utils import visualization_utils as vis_util
from utils import visualization_utils as vis_util


# What model to download.
MODEL_NAME = 'faster_rcnn_inception_resnet_v2_atrous_lowproposals_oid_2017_11_08'#'faster_rcnn_inception_resnet_v2_atrous_oid_2017_11_08'#'faster_rcnn_nas_coco_2017_11_08'#'faster_rcnn_resnet101_coco_2017_11_08' #'faster_rcnn_nas_coco_2017_11_08' 'rfcn_resnet101_coco_2017_11_08'# , , 'ssd_inception_v2_coco_2017_11_08'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('../data', 'oid_bbox_trainable_label_map.pbtxt')#'mscoco_label_map.pbtxt')

NUM_CLASSES = 545 #oid_bbox_trainable_label_map.pbtxt, pig is 300, animal is 13

if os.path.exists(PATH_TO_CKPT):
    print("downloaded")
else:
    print("downloading")
    opener = urllib.request.URLopener()
    opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
    
    tar_file = tarfile.open(MODEL_FILE)
    for file in tar_file.getmembers():
      file_name = os.path.basename(file.name)
      if 'frozen_inference_graph.pb' in file_name:
        tar_file.extract(file, os.getcwd())
    


detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')
    


label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)
  

# For the sake of simplicity we will use only 2 images:
# image1.jpg
# image2.jpg
# If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.
if test_mode:
    PATH_TO_TEST_IMAGES_DIR = '../test_images'
    TEST_IMAGE_PATHS = [ os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image{}.jpg'.format(i)) for i in range(5, 7) ]
    # Size, in inches, of the output images.
    IMAGE_SIZE = (18, 12)
else:
    PATH_TO_TEST_IMAGES_DIR = '/home/wayne/python/kaggle/pig_face/src/data/videos_folder_full/'
    TARGET_FOLDER = '/home/wayne/python/kaggle/pig_face/src/data/videos_folder_det_full/'

with detection_graph.as_default():
  with tf.Session(graph=detection_graph) as sess:
    # Definite input and output Tensors for detection_graph
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
    # Each box represents a part of the image where a particular object was detected.
    detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
    # Each score represent how level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
    detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')
    
    if test_mode:
        for image_path in TEST_IMAGE_PATHS:
          image = Image.open(image_path)
          # the array based representation of the image will be used later in order to prepare the
          # result image with boxes and labels on it.
          image_np = load_image_into_numpy_array(image)
          # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
          image_np_expanded = np.expand_dims(image_np, axis=0)
          # Actual detection.
          (boxes, scores, classes, num) = sess.run(
              [detection_boxes, detection_scores, detection_classes, num_detections],
              feed_dict={image_tensor: image_np_expanded})
          
          # Visualization of the results of a detection.
          vis_util.visualize_boxes_and_labels_on_image_array(
              image_np,
              np.squeeze(boxes),
              np.squeeze(classes).astype(np.int32),
              np.squeeze(scores),
              category_index,
              use_normalized_coordinates=True,
              line_thickness=8)
          plt.figure(figsize=IMAGE_SIZE)
          plt.imshow(image_np)
          plt.savefig(image_path.split('.j')[0]+'.png')
          
          im_width = image.width
          im_height = image.height
          ymin = boxes[0,0,0]
          xmin = boxes[0,0,1]
          ymax = boxes[0,0,2]
          xmax = boxes[0,0,3]
          (xminn, xmaxx, yminn, ymaxx) = (np.floor(xmin * im_width), np.ceil(xmax * im_width), np.floor(ymin * im_height), np.ceil(ymax * im_height))
          image_np2 = load_image_into_numpy_array(image)
          cropped = tf.image.crop_to_bounding_box(image_np2, int(yminn), int(xminn), 
                                       int(ymaxx - yminn), int(xmaxx - xminn))
          fname = image_path.split('.j')[0]+'_det.jpg'
          
          im = Image.fromarray(cropped.eval())
          im.save(fname)
          
    else:
        for i in range(1,31): # 1, 31
            os.mkdir(TARGET_FOLDER + str(i))
            print(i)
            TEST_IMAGE = os.listdir(PATH_TO_TEST_IMAGES_DIR + str(i))
            TEST_IMAGE_PATHS = [PATH_TO_TEST_IMAGES_DIR + str(i) + '/' + item for item in TEST_IMAGE]
            image = cv2.imread(TEST_IMAGE_PATHS[0])
            im_width = image.shape[1]
            im_height = image.shape[0]
            
            for j in range(0, len(TEST_IMAGE_PATHS), BATCH_SIZE):
#              time1 = timeit.default_timer()
              images = []
              for k in range(0, BATCH_SIZE):
                  image = cv2.imread(TEST_IMAGE_PATHS[j+k])
                  image = np.expand_dims(image, axis=0)
                  images.append(image)
                  image_np_expanded = np.concatenate(images, axis=0)

#              time2 = timeit.default_timer()
#              print(time2 - time1)
              (boxes, scores, classes, num) = sess.run(
                  [detection_boxes, detection_scores, detection_classes, num_detections],
                  feed_dict={image_tensor: image_np_expanded})
              
#              time3 = timeit.default_timer()
#              print(time3 - time2)
              for k in range(0, BATCH_SIZE):
                  ymin = boxes[k,0,0]
                  xmin = boxes[k,0,1]
                  ymax = boxes[k,0,2]
                  xmax = boxes[k,0,3]
                  (xminn, xmaxx, yminn, ymaxx) = (np.floor(xmin * im_width), np.ceil(xmax * im_width), np.floor(ymin * im_height), np.ceil(ymax * im_height))
                  
                  fname = TARGET_FOLDER + str(i) + '/' + TEST_IMAGE[j+k]          
#                  im = Image.fromarray(images[k][0, int(yminn):int(ymaxx) , int(xminn):int(xmaxx), :])
#                  im.save(fname)
                  cv2.imwrite(fname,images[k][0, int(yminn):int(ymaxx) , int(xminn):int(xmaxx), :])    
#              time4 = timeit.default_timer()
#              print(time4 - time3)