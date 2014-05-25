'''
===========================================
ryApp_en.py   <--  translated <-- ryApp.py
===========================================
Renyuan Lyu, 呂仁園
-------------------
2014/04/21

importing RyAudio.py
Realtime-audio spectrogram。

This program was originally written using many Chinese names
for variables, functions and classes.

For international audience,
it is translated into English.

Note that all Chinese names in the code was translated
by the original author himself;

however, the Chinese comments are translated into English (in parentheses)
by the Google translator,
just for international audience's reference,

I wish some English native speaker can help me to polish it.

This program was first presented on PyCon APAC 2014, Taipei, Taiwan.

Adapted from the following tasks

==================================================
影音一起處理 ( video and Audio processed together)
==================================================

ryCameraMic01.py
----------------

做了那麼久的 DSP，(Do so long DSP,)
這次終於能把視訊與音訊兜在一起。(The pocket was finally able to video and audio together.)

呂仁園 (Renyuan Lyu)，2014/03/30

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
import  pygame.camera    as pgCam
from    pygame.locals import *

import pylab        as pl
import colorsys
import time

import ryAudio    as ra
#
# 這個 ryAudio 是我們的私房模組 (Our Private Module)，
# 引入(importing) pyaudio
#
# 專門用來 錄音, 放音, (Dedicated to recording, playback,)
# 以及簡單的聲音特徵擷取。 (And simple sound feature extraction.)
#

def frequency2color(frequency, scale= 1):

    frequency *= scale
    r, g, b= colorsys.hsv_to_rgb(frequency, 1, 0.9)
    r = int(r*256)%256
    g = int(g*256)%256
    b = int(b*256)%256
    color= (r,g,b)

    return color

class VideoAudio:

    screenWidth, screenHeigth= screenSize= size = ( 640, 480 )

    def __init__(self):

        pg.init()
        pgCam.init()

        self.screen= pg.display.set_mode( self.screenSize, 0 )
        pg.display.set_caption('ryApp.py, using RyAudio, on PyCon APAC 2014, by Renyuan Lyu')

        self.initVideo()

        self.initAudio()

    def initVideo(self, cameraIndex= 0):

        #
        # gets a list of available cameras.
        #
        self.cameras= pgCam.list_cameras()

        print ('cameras= ',self.cameras)

        if self.cameras == []:
            raise ValueError("歹勢，無 攝影機。Sorry, no cameras detected. ")

        try:
            cameraId= self.cameras[cameraIndex]
        except IndexError:
            cameraId= self.cameras[0]

        #
        # creates the camera of the specified screenSize and in RGB, or HSV colorspace
        #
        self.camera= pgCam.Camera(cameraId, self.screenSize, 'HSV') #"RGB")

        #
        # starts the camera
        #
        # 這行與我們取音訊的精神很相像，應該就是 多線 的做法。
        # (We take this line with the spirit of the audio is very similar, it should be is a multi-line approach.)
        #
        self.camera.start()

        #
        # create a surface 作為 videoShot to capture to.
        # for performance purposes,
        # you want the bit depth to be the same
        # as that of the display surface.
        #
        self.videoShot= pg.surface.Surface(self.screenSize, 0, self.screen)

    def takeVideoAndDisplay(self, keyboard= None):


        #
        # 原裝 取視訊 函數 (Take the original video function)
        #
        self.videoShot= self.camera.get_image(self.videoShot)

        #
        # 加入 一點 影像 處理 (Add a little image processing)
        # 如： 左右翻轉, 邊界偵測, 取平均 等等 (Such as: about flip, edge detection, averaging, etc.)
        #

        #
        #
        # 左右翻轉 (Flip around)
        #
        self.videoShot= a= pg.transform.flip(self.videoShot, True, False)

        #
        # 邊界偵測 (Boundary detection)
        #
        '''
        laplacian(Surface, DestSurface = None) -> Surface
        '''
        if keyboard == K_a:
            self.videoShot= b= pg.transform.laplacian(a)


        #
        # 取平均 (Averaging)
        #
        '''
        pygame.transform.average_surfaces()
        find the average surface from many surfaces.
        average_surfaces(Surfaces, DestSurface = None, palette_colors = 1) -> Surface
        '''

        if keyboard == K_b:
            self.videoShot= b= pg.transform.laplacian(a)
            self.videoShot= c= pg.transform.average_surfaces([a,b])
        #
        # 顯示於幕 (Displayed on the screen)
        #
        self.screen.blit(self.videoShot, (0,0))

    def initAudio(self):

        self.audio= ra.RyAudio()
        self.audio.start()

        #
        # for specgram, 頻譜， 調色盤，把 頻譜值 對應到顏色。
        # (Spectrum, color palette, the corresponding value to the color spectrum.)
        #

        size= self.audio.specgram.shape

        self.audioScreen= pg.Surface( size, depth= 8) # for specgram

        palette= []
        for n in range(256):

            frequency= n/256
            color= frequency2color(frequency)

            palette+= [color]

        self.audioScreen.set_palette(palette)

        self.enList= [(0,0)]
        self.f0List= [(0,0)]

    def takeAudioAndDisplay(self, keyboard= None):

        en=    self.audio.en
        frequency=    self.audio.f0 # 也可用 .fm, .f0

        #frequency *=2

        length= en**0.5 *0.1

        x= 10 # self.screenWidth//2 # int(t*0.1)%self.screenWidth

        y= frequency * self.screenHeigth  #
        y= self.screenHeigth - y     #

        color= frequency2color(frequency)

        rect= (x, y, length, 10)

        #pg.draw.rect(self.screen, color, rect)



        #
        # 主要 畫頻譜 的技術 在此！ 另有 palette 要在 啟動音訊時 先做好。
        # (The main draw of the spectrum techniques in this! Another palette to do when you first start the audio.)
        #
        specgram= self.audio.specgram

        #
        # up_down flip, 頻譜上下對調，讓低頻在下，高頻在上，比較符合直覺。
        # (Up and down the spectrum swap, so the next low-frequency, high frequency on, more intuitive.)
        #
        specgram= specgram[:,-1::-1]

        #
        # 這個 specgram 大小要如何自動調整才能恰當的呈現在螢幕上，還有待研究一下。
        # (This specgram how to automatically adjust to the size appropriate for presentation on the screen, what remains to be studied.)
        #
        specgram= (pl.log(specgram)+10)*10

        #
        # 錦上添花 (Icing on the cake)
        #
        # 加這行讓頻譜會轉，有趣！！ (Add this line so that the spectrum will be transferred, fun! !)
        #
        if keyboard == K_e:
            specgram= pl.roll(specgram, -int(self.audio.frameI % self.audio.frameN), axis=0)

        #
        # pygame 的 主要貢獻 (The main contribution):  specgram ---> audioScreen
        #
        pg.surfarray.blit_array(self.audioScreen, specgram.astype('int'))

        #
        # pygame 的 次要貢獻 (Minor contribution): 調整一下 (Adjustments) size audioScreen ---> aSurf
        #
        aSurf= pg.transform.scale(self.audioScreen, (self.screenWidth, self.screenHeigth)) #//4))

        #
        # 黏上幕 (Stick on screen) aSurf ---> display
        #

        #aSurf= pg.transform.average_surfaces([aSurf, self.videoShot])
        self.screen.blit(aSurf, (0,0))

        pg.draw.rect(self.screen, color, rect)  #這行是音高 f0, 原本在之前畫，但發現會被頻譜擋住，就移到此處。

        #
        # 把攝影畫面 黏上去，1/4 螢幕就好了，不要太大，以免宣賓奪主。
        # (The photographic images stick up, 1/4 screen just fine, not too much, lest the Lord declared Bin wins.)
        #
        bSurf= pg.transform.scale(self.videoShot, (self.screenWidth//4, self.screenHeigth//4)) #//4))
        self.screen.blit(bSurf, (0,0))

        #
        # 江永進的建議，在頻譜前畫一條白線，並把能量、頻率軌跡畫出。
        # (Jiang Yong Jin's proposal to draw a white line before the spectrum and the energy and frequency trajectory draw.)
        #
        if keyboard == K_f:
            x= (self.audio.frameI % self.audio.frameN)  * self.screenWidth / self.audio.frameN
            h= self.screenHeigth
            pg.draw.line(self.screen, pg.Color('white'),(x,h),(x,0) , 2)

            y= length
            y= h-y

            z= frequency
            z= h-z

            if self.audio.frameI % self.audio.frameN == 0:
                self.enList = [(x,y)]
                self.f0List = [(x,z)]
            else:
                if self.enList[-1] != (x,y):
                    self.enList += [(x,y)]
                if self.f0List[-1] != (x,z):
                    self.f0List += [(x,z)]
                pass

            if len(self.enList)>1 :
                pg.draw.lines(self.screen, pg.Color('black'), False, self.enList, 1)

            if len(self.f0List)>1:
                pg.draw.lines(self.screen, pg.Color('blue'),  False,  self.f0List, 2)

    def mouseShowEnAndF0(self, mouseX, mouseY, keyboard= None):

        en= self.audio.en**0.5 *0.01

        #
        # 這個 en size 有點難控制， (The en size a bit difficult to control,)
        # 如何 讓它 獨立於 電腦 硬體，不隨環境而變，(How to make it independent of the computer's hardware, do not change with the environment,)
        # 是一門藝術，還要再修。(Is an art, but also re-repair.)
        #

        size=         max(10, en )
        posAndSize=  (mouseX - size/2, mouseY - size/2, size, size)

        frequency=     self.audio.f0 # .f0 # .f0 是基本頻率 (fundamental frequency)；.fm 是平均頻率 (average frequency)
        #frequency*=    2  # *2 是為了 視覺上的 解析度 (for Visual resolution)

        color=      frequency2color(frequency)

        pg.draw.ellipse(self.screen, color, posAndSize)
        pg.display.update()

        if keyboard == K_i:
            print('滑鼠游標= (%d, %d), en= %.1f, frequency= %.3f '%(mouseX, mouseY, size, frequency))

    def mainLoop(self):

        simpleControlMethods='''
        Using(用) K_abcd to control Video Processing (來控制視訊處理)
        Using(用) K_efgh to control Audio Processing (來控制音訊處理)
        Using(用) K_ijk to control Mouse (來控制滑鼠處理)
        '''
        print('simpleControlMethods= ', simpleControlMethods)

        mousePressed=      False
        mouseX= mouseY=  0
        keyboard=          None

        mainLoopIsRunning=  True

        while mainLoopIsRunning:
            #
            # 取得 使用者 輸入 事件 (Get user input events)
            #
            events= pg.event.get()

            #
            # 處理 使用者 輸入 事件 (Handle user input events)
            #
            for e in events:

                #
                # 首先 優先處理 如何結束，優雅的結束！ (How to end the first priority, elegant finish!)
                #
                # 用滑鼠點擊 X (在 視窗 右上角) 結束！ (Right click the X (top right corner of the window) end!)
                #
                if e.type in [QUIT]:
                    mainLoopIsRunning= False

                #
                # 用鍵盤 按 Esc (在 keyboard 左上角) 結束！ (Press Esc (the keyboard top left) end of the keyboard!)
                #
                if e.type in [KEYDOWN]:
                    keyboard= e.key
                    if e.key in [K_ESCAPE]:
                        mainLoopIsRunning= False
                if e.type in [KEYUP]:
                    keyboard= None
                #
                # 以下 3 個 if , 用來 處理 滑鼠 (The following three if, for handling the mouse)
                #
                if e.type in [MOUSEBUTTONDOWN]:
                    mousePressed= True
                    mouseX, mouseY= x,y= e.pos

                if e.type in [MOUSEBUTTONUP]:
                    mousePressed= False
                    mouseX, mouseY= x,y= e.pos

                if e.type in [MOUSEMOTION]:
                    if (mousePressed is True):
                        mouseX, mouseY= x,y= e.pos

            #
            # 視訊 (Video)
            #
            self.takeVideoAndDisplay(keyboard) # 用 K_abcd 來控制視訊處理

            #
            # 音訊 (Audio)
            #
            self.takeAudioAndDisplay(keyboard) # 用 K_efgh 來控制音訊處理

            #
            # 滑鼠 (Mouse)
            #
            if (mousePressed is True):  # 用 K_ijk 來控制滑鼠處理
                self.mouseShowEnAndF0(mouseX, mouseY, keyboard)

            #
            # 畫面更新 (Screen updates)
            #
            pg.display.flip()
        #
        # 跳出主迴圈了 (Out of the main loop)
        #
        print('mainLoopIsRunning= ', mainLoopIsRunning)
        self.camera.stop()
        self.audio.stop()
        pg.quit()

if __name__ == '__main__':

    VideoAudio().mainLoop()
