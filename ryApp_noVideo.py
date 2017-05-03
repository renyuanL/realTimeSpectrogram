'''
ryApp_noVideo.py
暫把 video 關掉，因為小台電腦的 videoCapture 出了點狀況！
2016/07/28

ryApp.py

這支程式是我第一次寫出頻譜的作品，
值得紀念，現在跑起來還是覺得很穩。
主要是基於 pygame
2016/07/27

2014/04/20

運用 RyAudio.py 的即時語音頻譜。

This program use many Chinese names
for variables, functions and classes

First presentation
on PyCon APAC 2014

Adapted from the following tasks

================
影音一起處理
================
ryCameraMic01.py
----------------

做了那麼久的 DSP，
這次終於能把視訊與音訊兜在一起。

呂仁園，2014/03/30
'''
#
# This program refered much from the following tutorial program
#
# 1. Basic image capturing and displaying using the camera module
'''
Pygame Tutorials
Camera Module Introduction

by Nirav Patel
nrp@eclecti.cc

Revision 1.0, May 25th, 2009

http://www.pygame.org/docs/tut/camera/CameraIntro.html

http://www.pygame.org/docs/ref/camera.html

'''
import  pygame           as pg
#import  pygame.camera    as pgCam
from    pygame.locals import *

import pylab        as pl
import colorsys
import time

import ryAudio    as ra
#
# 這個 ryAudio 是我們的私房模組，
# 引入 pyaudio
#
# 專門用來 錄音, 放音, 
# 以及簡單的聲音特徵擷取。
#

def 頻率轉顏色(頻率, 倍數= 1):

    頻率 *= 倍數
    r, g, b= colorsys.hsv_to_rgb(頻率, 1, 0.9)
    r = int(r*256)%256
    g = int(g*256)%256
    b = int(b*256)%256
    顏色= (r,g,b)

    return 顏色

class 影音類:

    幕寬, 幕高= 幕寬高= size = ( 640, 480 )

    def __init__(它):

        pg.init()
        #pgCam.init()

        它.幕= pg.display.set_mode( 它.幕寬高, 0 )
        pg.display.set_caption('ryApp.py, using RyAudio, on PyCon APAC 2014, by Renyuan Lyu')

        #它.啟動視訊()

        它.啟動音訊()

    def 啟動視訊(它, 攝影機編號= 0):
        #
        # gets a list of available cameras.
        #
        它.攝影機群= pgCam.list_cameras()

        print ('攝影機群= ',它.攝影機群)

        if 它.攝影機群 == []:
            raise ValueError("歹勢，無 攝影機。Sorry, no cameras detected. ")

        try:
            攝影機id= 它.攝影機群[攝影機編號]
        except IndexError:
            攝影機id= 它.攝影機群[0]
        #
        # creates the camera of the specified 幕寬高 and in RGB, or HSV colorspace
        #
        它.攝影機= pgCam.Camera(攝影機id, 它.幕寬高, 'HSV') #"RGB")

        #
        # starts the camera
        #
        # 這行與我們取音訊的精神很相像，應該就是 多線 的做法。
        #
        #
        它.攝影機.start()

        #
        # create a surface 作為 攝影畫面 to capture to.
        # for performance purposes,
        # you want the bit depth to be the same
        # as that of the display surface.
        #
        它.攝影畫面= pg.surface.Surface(它.幕寬高, 0, 它.幕)

    def 取視訊且顯示於幕(它, 鍵盤= None):
        #
        # 原裝 取視訊 函數
        #
        它.攝影畫面= 它.攝影機.get_image(它.攝影畫面)

        #
        # 加入 一點 影像 處理
        # 如： 左右翻轉, 邊界偵測, 取平均 等等
        #

        #
        # 左右翻轉
        #
        它.攝影畫面= a= pg.transform.flip(它.攝影畫面, True, False)

        #
        # 邊界偵測
        #
        '''
        laplacian(Surface, DestSurface = None) -> Surface
        '''
        if 鍵盤 == K_a:
            它.攝影畫面= b= pg.transform.laplacian(a)
        #
        # 取平均
        #
        '''
        pygame.transform.average_surfaces()
        find the average surface from many surfaces.
        average_surfaces(Surfaces, DestSurface = None, palette_colors = 1) -> Surface
        '''

        if 鍵盤 == K_b:
            它.攝影畫面= b= pg.transform.laplacian(a)
            它.攝影畫面= c= pg.transform.average_surfaces([a,b])
        #
        # 顯示於幕
        #
        它.幕.blit(它.攝影畫面, (0,0))

    def 啟動音訊(它):

        它.音= ra.音類()
        它.音.開始()

        #
        # for specgram, 頻譜， 調色盤，把 頻譜值 對應到顏色。
        #

        寬高= 它.音.specgram.shape

        它.音幕= pg.Surface( 寬高, depth= 8) # for specgram

        調色盤= []
        for n in range(256):

            頻率= n/256
            色= 頻率轉顏色(頻率)

            調色盤+= [色]

        它.音幕.set_palette(調色盤)

        它.能量點列表= [(0,0)]
        它.頻率點列表= [(0,0)]

    def 取音訊且顯示頻譜於幕(它, 鍵盤= None):

        能量=    它.音.en
        頻率=    它.音.f0 # 也可用 .fm, .f0

        #頻率 *=2

        長度= 能量**0.5 *0.1

        x= 10 # 它.幕寬//2 # int(t*0.1)%它.幕寬

        y= 頻率 * 它.幕高  #
        y= 它.幕高 - y     #

        色= 頻率轉顏色(頻率)

        方形= (x, y, 長度, 10)

        #pg.draw.rect(它.幕, 色, 方形)

        #
        # 主要 畫頻譜 的技術 在此！ 另有 調色盤 要在 啟動音訊時 先做好。
        #
        頻譜= 它.音.specgram

        #
        # up_down flip, 頻譜上下對調，讓低頻在下，高頻在上，比較符合直覺。
        #
        頻譜= 頻譜[:,-1::-1]

        #
        # 這個 頻譜 大小要如何自動調整才能恰當的呈現在螢幕上，還有待研究一下。
        #
        頻譜= (pl.log(頻譜)+10)*10

        #
        # 錦上添花
        #
        # 加這行讓頻譜會轉，有趣！！
        #
        if 鍵盤 == K_e:
            頻譜= pl.roll(頻譜, -int(它.音.frameI % 它.音.frameN), axis=0)

        #
        # pygame 的 主要貢獻:  頻譜 ---> 音幕
        #
        pg.surfarray.blit_array(它.音幕, 頻譜.astype('int'))

        #
        # pygame 的 次要貢獻: 調整一下 寬高 音幕 ---> aSurf
        #
        aSurf= pg.transform.scale(它.音幕, (它.幕寬, 它.幕高)) #//4))

        #
        # 黏上幕  aSurf ---> display
        #

        #aSurf= pg.transform.average_surfaces([aSurf, 它.攝影畫面])
        它.幕.blit(aSurf, (0,0))

        pg.draw.rect(它.幕, 色, 方形)  
        #這行是音高 f0, 原本在之前畫，但發現會被頻譜擋住，就移到此處。

        #
        # 把攝影畫面 黏上去，1/4 螢幕就好了，不要太大，以免宣賓奪主。
        #
        #### bSurf= pg.transform.scale(它.攝影畫面, (它.幕寬//4, 它.幕高//4)) #//4))
        #### 它.幕.blit(bSurf, (0,0))

        #
        # 江永進的建議，在頻譜前畫一條白線，並把能量、頻率軌跡畫出。
        #
        if 鍵盤 == K_f:
            x= (它.音.frameI % 它.音.frameN)  * 它.幕寬 / 它.音.frameN
            h= 它.幕高
            pg.draw.line(它.幕, pg.Color('white'),(x,h),(x,0) , 2)

            y= 長度
            y= h-y

            z= 頻率
            z= h-z

            if 它.音.frameI % 它.音.frameN == 0:
                它.能量點列表 = [(x,y)]
                它.頻率點列表 = [(x,z)]
            else:
                if 它.能量點列表[-1] != (x,y):
                    它.能量點列表 += [(x,y)]
                if 它.頻率點列表[-1] != (x,z):
                    它.頻率點列表 += [(x,z)]
                pass

            if len(它.能量點列表)>1 :
                pg.draw.lines(它.幕, pg.Color('black'), False, 它.能量點列表, 1)

            if len(它.頻率點列表)>1:
                pg.draw.lines(它.幕, pg.Color('blue'),  False,  它.頻率點列表, 2)

    def 滑鼠游標顯示音訊能量及頻率(它, 滑鼠x, 滑鼠y, 鍵盤= None):

        音訊能量= 它.音.en**0.5 *0.01

        #
        # 這個 音訊能量 大小 有點難控制，
        # 如何 讓它 獨立於 電腦 硬體，不隨環境而變，
        # 是一門藝術，還要再修。
        #
        大小=         max(10, 音訊能量 )
        位置及大小=  (滑鼠x - 大小/2, 滑鼠y - 大小/2, 大小, 大小)

        頻率=     它.音.f0 # .f0 # .f0 是基本頻率；.fm 是平均頻率
        #頻率*=    2  # *2 是為了 視覺上的 解析度

        色=      頻率轉顏色(頻率)

        pg.draw.ellipse(它.幕, 色, 位置及大小)
        pg.display.update()

        if 鍵盤 == K_i:
            print('滑鼠游標= (%d, %d), 音訊能量= %.1f, 頻率= %.3f '%(滑鼠x, 滑鼠y, 大小, 頻率))

    def 主迴圈(它):

        簡單控制方法='''
        用 K_abcd 來控制視訊處理
        用 K_efgh 來控制音訊處理
        用 K_ijk 來控制滑鼠處理
        '''
        print('簡單控制方法= ', 簡單控制方法)

        滑鼠按著=      False
        滑鼠x= 滑鼠y=  0
        鍵盤=          None

        主迴圈執行中=  True

        while 主迴圈執行中:
            #
            # 取得 使用者 輸入 事件
            #
            事件群= pg.event.get()

            #
            # 處理 使用者 輸入 事件
            #
            for e in 事件群:
                #
                # 首先 優先處理 如何結束，優雅的結束！
                #
                # 用滑鼠點擊 X (在 視窗 右上角) 結束！
                #
                if e.type in [QUIT]:
                    主迴圈執行中= False
                #
                # 用鍵盤 按 Esc (在 鍵盤 左上角) 結束！
                #
                if e.type in [KEYDOWN]:
                    鍵盤= e.key
                    if e.key in [K_ESCAPE]:
                        主迴圈執行中= False
                if e.type in [KEYUP]:
                    鍵盤= None
                #
                # 以下 3 個 if , 用來 處理 滑鼠
                #
                if e.type in [MOUSEBUTTONDOWN]:
                    滑鼠按著= True
                    滑鼠x, 滑鼠y= x,y= e.pos

                if e.type in [MOUSEBUTTONUP]:
                    滑鼠按著= False
                    滑鼠x, 滑鼠y= x,y= e.pos

                if e.type in [MOUSEMOTION]:
                    if (滑鼠按著 is True):
                        滑鼠x, 滑鼠y= x,y= e.pos
            #
            # 視訊
            #
            #它.取視訊且顯示於幕(鍵盤) # 用 K_abcd 來控制視訊處理

            #
            # 音訊
            #
            它.取音訊且顯示頻譜於幕(鍵盤) # 用 K_efgh 來控制音訊處理

            #
            # 滑鼠
            #
            if (滑鼠按著 is True):  # 用 K_ijk 來控制滑鼠處理
                它.滑鼠游標顯示音訊能量及頻率(滑鼠x, 滑鼠y, 鍵盤) 
            #
            # 畫面更新
            #
            pg.display.flip()
        #
        # 跳出主迴圈了
        #
        print('主迴圈執行中= ', 主迴圈執行中)
        #它.攝影機.stop()
        它.音.結束()
        pg.quit()

if __name__ == '__main__':
    影音類().主迴圈()