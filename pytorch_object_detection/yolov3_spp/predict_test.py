import torch
import cv2
import numpy as np
import time
from matplotlib import pyplot as plt
from utils import img_utils
from utils import torch_utils
from utils import utils
from models import Darknet
from draw_box_utils import draw_box


def main():
    img_size = 512  # 必须是32的整数倍 [416, 512, 608]
    cfg = "cfg/yolov3-spp.cfg"
    weights = "weights/yolov3-spp-ultralytics-{}.pt".format(img_size)
    img_path = "test.jpg"
    input_size = (img_size, img_size)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    model = Darknet(cfg, img_size)
    model.load_state_dict(torch.load(weights, map_location=device)["model"])
    model.to(device)

    model.eval()

    # init
    img = torch.zeros((1, 3, img_size, img_size), device=device)
    model(img)

    img_o = cv2.imread(img_path)  # BGR
    assert img is not None, "Image Not Found " + img_path

    img = img_utils.letterbox(img_o, new_shape=input_size, auto=True, color=(0, 0, 0))[0]
    # Convert
    img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
    img = np.ascontiguousarray(img)

    img = torch.from_numpy(img).to(device).float()
    img /= 255.0  # scale (0, 255) to (0, 1)
    img = img.unsqueeze(0)  # add batch dimension

    t1 = torch_utils.time_synchronized()
    pred = model(img)[0]  # only get inference result
    t2 = torch_utils.time_synchronized()
    print(t2 - t1)

    pred = utils.non_max_suppression(pred, conf_thres=0.3, iou_thres=0.6, multi_label=True)[0]
    t3 = time.time()
    print(t3 - t2)

    # process detections
    pred[:, :4] = utils.scale_coords(img.shape[2:], pred[:, :4], img_o.shape).round()
    print(pred.shape)

    bboxes = pred[:, :4].detach().numpy()
    scores = pred[:, 4].detach().numpy()
    classes = pred[:, 5].detach().numpy().astype(np.int) + 1

    category_index = dict([(i + 1, str(i + 1)) for i in range(90)])
    img_o = draw_box(img_o[:, :, ::-1], bboxes, classes, scores, category_index)
    plt.imshow(img_o)
    plt.show()

    img_o.save("test_result.jpg")


if __name__ == "__main__":
    main()



