# coding:utf-8

# tkinter是python内置的简单gui库，实现打开文件夹、确认删除等操作十分方便
from tkinter.filedialog import askdirectory
# 导入创建的工具类
from simplebboxlabeling import simplebboxlabeling

if __name__ == '__main__':
    dir_with_images = askdirectory(title='where is the images?')
    labeling_task = simplebboxlabeling(dir_with_images)
    labeling_task.start()