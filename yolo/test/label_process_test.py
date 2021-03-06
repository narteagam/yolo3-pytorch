import os
from pathlib import Path

import torch
from torch.utils import data

from yolo import dataset, utils, model, detect


def calculate_score(root, confidence_thresh=0.8, iou_thresh=0.5):
    """

    :param root:
    :param confidence_thresh:
    :param iou_thresh:
    :return:
    """
    ds = dataset.Dataset(root, augmentation=False)
    num_class = ds.class_num
    batch_size = 1

    data_iter = data.DataLoader(ds, batch_size=batch_size, shuffle=False)
    base_filename = Path('../../img/res/validation')
    input_size = (416, 416)
    anchors = [(8, 25), (12, 29), (14, 44)]
    grid_size = 13
    stride = input_size[0] // grid_size
    if not base_filename.exists():
        base_filename.mkdir()

    total_object_num = torch.zeros(num_class, dtype=torch.float32)
    total_detect_num = torch.zeros(num_class, dtype=torch.float32)
    total_true_detect_num = torch.zeros(num_class, dtype=torch.float32)
    for i, (img, label, _, _) in enumerate(data_iter):
        target = utils.prepare_target(label, anchors, num_class, grid_size, stride)
        model.process_detection(target, grid_size, stride, anchors)
        label[..., :4] *= input_size[0]
        _object_num, _detect_num, _true_detect_num = utils.count_prediction(target, label, num_class, confidence_thresh,
                                                                            iou_thresh)
        total_object_num += _object_num.float()
        total_detect_num += _detect_num.float()
        total_true_detect_num += _true_detect_num.float()

    precision = total_true_detect_num / total_detect_num
    recall = total_true_detect_num / total_object_num

    return precision, recall


def label_process_test():
    """
    test label process code
    :return:
    """
    root = '../data/opening_detection/train'
    ds = dataset.Dataset(root, augmentation=False)
    num_class = ds.class_num
    batch_size = 1
    data_iter = data.DataLoader(ds, batch_size=1, shuffle=False)
    base_filename = Path('../img/res/validation')
    input_size = (416, 416)
    anchors = [(8, 25), (12, 29), (14, 44)]
    grid_size = 13
    stride = input_size[0] // grid_size
    if not base_filename.exists():
        base_filename.mkdir()

    for i, (img, label, _, _) in enumerate(data_iter):
        target = utils.prepare_target(label, anchors, num_class, grid_size, stride)
        model.process_detection(target, grid_size, stride, anchors)
        prediction = utils.transform_prediction(target, 0.8, 0.4, 64)

        img = img.numpy()
        for b in range(batch_size):
            image = img[b]
            pred = prediction[b]
            detect.draw_single_prediction(image,
                                          pred,
                                          out_filename=os.path.join(base_filename, str(i) + '.png'),
                                          input_shape=input_size)


if __name__ == '__main__':
    root = '../../data/opening_detection/train'
    precision, recall = calculate_score(root)

    mean_precision = torch.mean(precision)
    mean_recall = torch.mean(recall)
    print(f'precision: {mean_precision}')
    print(f'recall: {mean_recall}')
