# coding: utf-8

"""
物体检测标注小工具
基本思路：
对要标注的图像建立一个窗口循环，然后每次循环的时候对图像进行一次复制，
鼠标在画面上画框的操作、画好的框的相关信息在全局变量中保存，
并且在每个循环中根据这些信息，在复制的图像上重新画一遍，然后显示这份复制的图像。
简化的设计过程：
1、输入是一个文件夹的路径，包含了所需标注物体框的图片。
如果图片中标注了物体，则生成一个相同名称加额外后缀_bbox的文件，来保存标注信息。
2、标注的方式：按下鼠标左键选择物体框的左上角，松开鼠标左键选择物体框的右下角，
按下鼠标右键删除上一个标注好的物体框。
所有待标注物体的类别和标注框颜色由用户自定义。
如果没有定义则默认只标注一种物体，定义该物体名称为object。
3、方向键 ← 和 → 键用来遍历图片， ↑ 和 ↓ 键用来选择当前要标注的物体，
delete键删除一种脏图片和对应的标注信息。
自定义标注物体和颜色的信息用一个元组表示
第一个元素表示物体名字
第二个元素表示bgr颜色的tuple或者代表标注框坐标的元祖
利用repr()保存和eval()读取
"""

"""
一些说明：
1. 标注相关的物体标签文件即 .labels 结尾的文件，需要与所选文件夹添加到同一个根目录下
一定要注意这一点，否则无法更新标注物体的类型标签，致使从始至终都只有一个默认物体出现
我就是这个原因，拖了两三天才整好，当然也顺便仔细的读了这篇代码。同时也学习了@staticmethod以及相应python的decorator的知识。
可以说，在曲折中前进才是棒的。
2. .labels文件为预设物体标签文件，其内容具体格式为:
'object1', (b, g, r)
'object2', (b, g, r)
'object3', (b, g, r)……
具体见文后图片。
3. 最后生成的标注文件，在文后会有，到时再进行解释。
"""

import os
import cv2
# tkinter是python内置的简单gui库，实现打开文件夹、确认删除等操作十分方便
# from tkmessagebox import askyesno
from tkinter.messagebox import askyesno
# 定义标注窗口的默认名称
window_name = 'simple bounding box labeling tool'
# 定义画面刷新帧率
fps = 24
# 定义支持的图像格式
supported_formats = ['jpg', 'jpeg', 'png']
# 定义默认物体框的名字为object，颜色为蓝色，当没有用户自定义物体时，使用该物体
default_color = {'object': (255, 0, 0)}
# 定义灰色，用于信息显示的背景和未定义物体框的显示
color_gray = (192, 192, 192)
# 在图像下方多处bar_height的区域，用于显示信息
bar_height = 16
# 上下左右,delete键对应的cv2.waitkey()函数的返回值
# key_up = 2490368
# key_down = 2621440
# key_left = 2424832
# key_right = 2555904
# key_delete = 3014656
key_up = 119
key_down = 115
key_left = 97
key_right = 100
key_delete = 32
# 空键用于默认循环
key_empty = 0
get_bbox_name = '{}.bbox'.format


# 定义物体框标注工具类
class simplebboxlabeling:
    def __init__(self, data_dir, fps=fps, windown_name=window_name):
        self._data_dir = data_dir
        self.fps = fps
        self.window_name = windown_name if windown_name else window_name

        # pt0 是正在画的左上角坐标, pt1 是鼠标所在坐标
        self._pt0 = None
        self._pt1 = None
        # 表明当前是否正在画框的状态标记
        self._drawing = False
        # 当前标注物体的名称
        self._cur_label = None
        # 当前图像对应的所有已标注框
        self._bboxes = []
        # 如果有用户自己定义的标注信息则读取，否则使用默认的物体和颜色
        label_path = '{}.labels'.format(self._data_dir)
        self.label_colors = default_color if not os.path.exists(label_path) else self.load_labels(label_path)
        # self.label_colors = self.load_labels(label_path)
        # 获取已经标注的文件列表和未标注的文件列表
        imagefiles = [x for x in os.listdir(self._data_dir) if x[x.rfind('.') + 1:].lower() in supported_formats]
        labeled = [x for x in imagefiles if os.path.exists(get_bbox_name(x))]
        to_be_labeled = [x for x in imagefiles if x not in labeled]

        # 每次打开一个文件夹，都自动从还未标注的第一张开始
        self._filelist = labeled + to_be_labeled
        self._index = len(labeled)
        if self._index > len(self._filelist) - 1:
            self._index = len(self._filelist) - 1

    # 鼠标回调函数
    def _mouse_ops(self, event, x, y, flags, param):
        # 按下左键，坐标为左上角，同时表示开始画框，改变drawing，标记为true
        if event == cv2.EVENT_LBUTTONDOWN:
            self._drawing = True
            self._pt0 = (x, y)
        # 松开左键，表明画框结束，坐标为有效较并保存，同时改变drawing，标记为false
        elif event == cv2.EVENT_LBUTTONUP:
            self._drawing = False
            self._pt1 = (x, y)
            self._bboxes.append((self._cur_label, (self._pt0, self._pt1)))
        # 实时更新右下角坐标
        elif event == cv2.EVENT_MOUSEMOVE:
            self._pt1 = (x, y)
        # 按下鼠标右键删除最近画好的框
        elif event == cv2.EVENT_RBUTTONUP:
            if self._bboxes:
                self._bboxes.pop()

    # 清除所有标注框和当前状态
    def _clean_bbox(self):
        self._pt0 = None
        self._pt1 = None
        self._drawing = False
        self._bboxes = []

    # 画标注框和当前信息的函数
    def _draw_bbox(self, img):
        # 在图像下方多出bar_height的区域，显示物体信息
        h, w = img.shape[:2]
        canvas = cv2.copyMakeBorder(img, 0, bar_height, 0, 0, cv2.BORDER_CONSTANT, value=color_gray)
        # 正在标注的物体信息，如果鼠标左键已经按下，则像是两个点坐标，否则显示当前待标注物体的名
        label_msg = '{}: {}, {}'.format(self._cur_label, self._pt0, self._pt1) \
            if self._drawing \
            else 'current label: {}'.format(self._cur_label)
        # 显示当前文件名，文件个数信息
        msg = '{}/{}: {} | {}'.format(self._index + 1, len(self._filelist), self._filelist[self._index], label_msg)
        cv2.putText(canvas, msg, (1, h+12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        # 画出已经标好的框和对应名字
        for label, (bpt0, bpt1) in self._bboxes:
            label_color = self.label_colors[label] if label in self.label_colors else color_gray
            cv2.rectangle(canvas, bpt0, bpt1, label_color, thickness=2)
            cv2.putText(canvas, label, (bpt0[0]+3, bpt0[1]+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, label_color, 2)
        # 画正在标注的框和对应名字
        if self._drawing:
            label_color = self.label_colors[self._cur_label] if self._cur_label in self.label_colors else color_gray
            if (self._pt1[0] >= self._pt0[0]) and (self._pt1[1] >= self._pt1[0]):
                cv2.rectangle(canvas, self._pt0, self._pt1, label_color, thickness=2)
            cv2.putText(canvas, self._cur_label, (self._pt0[0] + 3, self._pt0[1] + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, label_color, 2)
        return canvas

    # 利用repr()函数导出标注框数据到文件
    @staticmethod
    def export_bbox(filepath, bboxes, img):

        data_dir_path = os.path.abspath(os.path.join(filepath, ".."))
        file_name = os.path.basename(filepath).replace(".bbox", "")

        if bboxes:
            with open(filepath, 'w') as f:
                for bbox in bboxes:

                    if not os.path.exists(os.path.join(data_dir_path, bbox[0])):
                        os.makedirs(os.path.join(data_dir_path, bbox[0]))
                    bbox_cut = img[bbox[1][0][0]:bbox[1][1][0], bbox[1][1][1]:bbox[1][0][1]]
                    cv2.imwrite(os.path.join(data_dir_path, bbox[0], "{}.jpg".format(file_name)), bbox_cut)

                    line = repr(bbox) + '\n'
                    f.write(line)
        elif os.path.exists(filepath):
            os.remove(filepath)

    # # 利用repr()函数导出标注框数据到文件
    # @staticmethod
    # def export_bbox(filepath, bboxes):
    #     if bboxes:
    #         with open(filepath, 'w') as f:
    #             for bbox in bboxes:
    #                 line = repr(bbox) + '\n'
    #                 f.write(line)
    #     elif os.path.exists(filepath):
    #         os.remove(filepath)

    # 利用eval()函数读取标注框字符串到数据
    @staticmethod
    def load_bbox(filepath):
        bboxes = []
        with open(filepath, 'r', encoding="utf-8") as f:
            line = f.readline().rstrip()
            while line:
                bboxes.append(eval(line))
                line = f.readline().rstrip()
        return bboxes

    # 利用eval()函数读取物体及对应颜色信息到数据
    @staticmethod
    def load_labels(filepath):
        label_colors = {}
        with open(filepath, 'r', encoding="utf-8") as f:
            line = f.readline().rstrip()
            while line:
                label, color = eval(line)
                label_colors[label] = color
                line = f.readline().rstrip()
        print(label_colors)
        return label_colors

    # 读取图像文件和对应标注框信息（如果有的话）
    @staticmethod
    def load_sample(filepath):
        img = cv2.imread(filepath)
        bbox_filepath = get_bbox_name(filepath)
        bboxes = []
        if os.path.exists(bbox_filepath):
            bboxes = simplebboxlabeling.load_bbox(bbox_filepath)
        return img, bboxes

    # # 导出当前标注框信息并清空
    # def _export_n_clean_bbox(self):
    #     bbox_filepath = os.path.join(self._data_dir, get_bbox_name(self._filelist[self._index]))
    #     self.export_bbox(bbox_filepath, self._bboxes)
    #     self._clean_bbox()

    # 导出当前标注框信息并清空
    def _export_n_clean_bbox(self, img):
        bbox_filepath = os.path.join(self._data_dir, get_bbox_name(self._filelist[self._index]))
        self.export_bbox(bbox_filepath, self._bboxes, img)
        self._clean_bbox()

    # 删除当前样本和对应的标注框信息
    def _delete_current_sample(self):
        filename = self._filelist[self._index]
        filepath = os.path.join(self._data_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        filepath = get_bbox_name(filepath)
        if os.path.exists(filepath):
            os.remove(filepath)
        self._filelist.pop(self._index)
        print('{} is deleted!'.format(filename))

    # 开始opencv窗口循环的方法，程序的主逻辑
    def start(self):
        # 之前标注的文件名，用于程序判断是否需要执行一次图像读取
        last_filename = ''

        # 标注物体在列表中的下标
        label_index = 0

        # 所有标注物体名称的列表
        labels = list(self.label_colors.keys())

        # 带标注物体的种类数
        n_labels = len(labels)

        # 定义窗口和鼠标回调
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._mouse_ops)
        key = key_empty

        # 定义每次循环的持续时间
        delay = int(1000 / fps)

        # 定义一个假img使其通过编译，后续再执行加载操作
        filename = self._filelist[self._index]
        filepath = os.path.join(self._data_dir, filename)
        img, self._bboxes = self.load_sample(filepath)

        # 只要没有按下delete键，就持续循环
        while key != key_delete:
            # 上下方向键选择当前标注物体
            if key == key_up:
                if label_index == 0:
                    pass
                else:
                    label_index -= 1
            elif key == key_down:
                if label_index == n_labels - 1:
                    pass
                else:
                    label_index += 1
            # 左右方向键选择标注图片
            elif key == key_left:
                # 已经到了第一张图片的话就不需要清空上一张
                if self._index > 0:
                    self._export_n_clean_bbox(img)
                self._index -= 1
                if self._index < 0:
                    self._index = 0
            elif key == key_right:
                # 已经到了最后一张图片的就不需要清空上一张
                if self._index < len(self._filelist) - 1:
                    self._export_n_clean_bbox(img)
                self._index += 1
                if self._index > len(self._filelist) - 1:
                    self._index = len(self._filelist) - 1
            # 删除当前图片和对应标注的信息
            elif key == key_delete:
                if askyesno('delete sample', 'are you sure?'):
                    self._delete_current_sample()
                    key = key_empty
                    continue
            # 如果键盘操作执行了换图片， 则重新读取， 更新图片
            filename = self._filelist[self._index]
            if filename != last_filename:
                filepath = os.path.join(self._data_dir, filename)
                img, self._bboxes = self.load_sample(filepath)
            # 更新当前标注物体名称
            self._cur_label = labels[label_index]
            # 把标注和相关信息画在图片上并显示指定的时间
            canvas = self._draw_bbox(img)
            cv2.imshow(self.window_name, canvas)
            key = cv2.waitKey(delay)
            # if key not in [-1, 0]:
            #     print(key)
            # 当前文件名就是下次循环的老文件名
            last_filename = filename
        print('finished!')
        cv2.destroyAllWindows()
        #如果退出程序，需要对当前文件进行保存
        self.export_bbox(os.path.join(self._data_dir, get_bbox_name(filename)), self._bboxes, img)
        print('labels updated!')