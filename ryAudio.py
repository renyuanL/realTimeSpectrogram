'''
ryAudio.py
==========
呂仁園
------
2014/04/20
----------

ryAudio00.py
2014/04/08
2014/03/19
-----------
ry音世界00.py

ryaudio.py
即時 音訊 錄放音 物類
2014/0317

'''
#
# Python standard modules
#
import math
import time
import threading as th

#
# PyAudio
#
import pyaudio   as pa

#
# Pylab 
#(Numpy, Scipy, Matplotlib)
#
import scipy.signal
import pylab     as pl

#
# my major audio class
#
class RyAudio:
    '''
    This class help you 
    to get audio signal from microphone 
    and do some simple processing in real time.
    
    class name | aliase
    RyAudio | 音類

    e.g.

    >>> anAudio= RyAudio()
    >>> anAudio.start()
    >>> # put your code here after
    >>> #time.sleep(10)
    >>> anAudio.x
    >>> anAudio.en
    >>> anAudio.f0
    >>> anAudio.xBuf
    >>> anAudio.specgram
    >>> # finally, you should stop it
    >>> anAudio.stop()
    
    >>> #你也可以用中文變數名稱
    >>> 音= 音類()
    >>> 音.開始()
    >>> # 把程式碼放在底下。
    >>> # time.sleep(10)
    >>> 音.x  # 振幅
    >>> 音.en # 能量
    >>> 音.f0 # 基頻, 基本頻率
    >>> 音.xBuf # 振幅暫存區, 一段暫存區的振幅
    >>> 音.specgram # 頻譜暫存區, 一段暫存區的頻譜
    >>> #最後，你要記得「停止」它
    >>> 音.停止()

    '''

    def __init__(self, Fs= 16000, TinSec= 10):
        '''
        Fs: 取樣頻率，預設值為 16000，
        TinSec: 保存語音長度，預設值為 10 sec
        '''
        print('RyAudio use %s'%pa.get_portaudio_version_text())
        
        self.Fs= Fs
        self.spBufferSize=           1024
        self.fftWindowSize= self.spBufferSize

        self.aP= pa.PyAudio()
        self.iS= pa.Stream(PA_manager= self.aP, input= True, rate= self.Fs, channels= 1, format= pa.paInt16)
        self.oS= pa.Stream(PA_manager= self.aP, output= True, rate= self.Fs, channels= 1, format= pa.paInt16)
        self.iTh= None
        self.oTh= None

        #self.sound=     None
        #self.soundTime= 0
        self.gettingSound= True
        self.playingSound= True

        self.t= 0
        self.b= None  # byte string
        self.x= None  # ndarray
        self.fft= None
        self.f0= 0#None
        self.en= 0#None
        self.fm= 0#None # frequency mean
        self.fv= 0#None # frequency var
        self.fs= 0#None # frequency std
        self.enP= 0#None # AllPass
        self.enPL= 0#None # LowPass
        self.enPH= 0#None # HighPass

        self.entropy= 0#None

        self.frameI=   0

        #self.frameN= self.spBufferSize/4  #1024/4 = 256
        self.TinSec= TinSec #10 # sec
        self.frameN= self.Fs*self.TinSec/self.spBufferSize #self.spBufferSize/4  #1024/4 = 256
        self.frameN= int(self.frameN)

        self.specgram= pl.random([self.frameN, self.spBufferSize/2])

        self.xBuf= pl.random([self.frameN, self.spBufferSize])

    def getSound(self):
        '''
        抓音，作即時 DSP，算出 en, f0, fft

        利用 self.gettingSound 來中止內部無窮迴圈。
        '''

        print('self.gettingSound= ',self.gettingSound)
        #global globalSound, globalSoundTime, globalGettingSound, iS

        spBufferSize=  self.spBufferSize
        fftWindowSize= self.fftWindowSize

        t0= time.time()
        while (self.gettingSound is True): # 利用 self.gettingSound= False 來中止此無窮迴圈。

            #
            # 抓音只需一行，抓成 bytestring
            #
            self.b= b= self.iS.read(spBufferSize) # 1024

            #
            # 以下是開始作即時 DSP 了。
            #
            #
            # bytestring --> int16 --> float32
            #
            x= pl.fromstring(b,'int16')
            x= x.astype('float32')
            
            #
            # 新鮮的語音波形， 趕快存下來，才能原音重現。
            #
            self.xBuf[self.frameI%self.frameN]= x

            #
            # --> zeroMean (zeroMean 最好不要在這裡做，因為這裡只有 1 個 frame)
            #
            #mu= x.mean()
            #x -= mu

            #
            # 自從 開始錄音以來所經歷的時間，以秒為單位。
            #
            t= time.time()-t0 # sec

            #
            # hamming window
            #
            x *= scipy.signal.hamming(len(x))
            #
            # 能量，訊號的平方的平均值。
            #
            en= (x*x).mean()

            #
            # 訊號的複數頻譜， 只保存 一半 的 頻率資訊
            #
            xFFT= pl.fft(x)[0:spBufferSize/2] # for x be real, a half range of fft is enough

            #
            # 訊號的功率頻譜(正實數值)， 如上，只保存 一半 的 頻率資訊
            #
            xP=   pl.absolute(xFFT*xFFT.conj()) # Power spectrum
            sumXp= xP.sum()

            self.t= t   # 自從 開始錄音以來所經歷的時間，以秒為單位。
            self.x= x   # 當下的語音振幅值。 (1 個 音框)
            self.en= en # 當下的語音能量值。
            self.fft= xFFT # 當下的 fft 複數頻譜

            #
            # 從當下 第 .frameI 音框，往前算 .frameN 個 音框 的 功率頻譜 (正實數) 以及 語音振幅值。
            #
            self.specgram[self.frameI%self.frameN]= xP
            
            #
            # 在這裡存下的語音 已經被 hamming window 破壞！！必須提前 存下來才行。
            #
            # self.xBuf[self.frameI%self.frameN]= x

            #
            # 當下 第 .frameI 音框，遞增。
            #
            self.frameI +=1

            #
            # 簡單的 基本頻率 fundamental frequency (f0) 抽取 演算法。
            #
            startF0= spBufferSize/16
            
            self.f0=  startF0 + xP[startF0:spBufferSize/4].argmax() # 0< f0 < spBufferSize/2

            # 頻率 範圍， 0<= k < spBufferSize/2
            k= pl.arange(spBufferSize/2)

            # 頻率平均值
            self.fm=  (xP*k).sum()/sumXp

            # 頻率變異數
            self.fv=  (xP*k**2).sum()/sumXp - self.fm**2

            # 頻率標準差
            self.fs=  self.fv**0.5

            # 頻率亂度 (entropy)
            self.entropy= -(xP*pl.log(xP/sumXp)).sum()/sumXp

            #
            # 把 f0 歸一化 (0< f0 < 0.5) # 注意，以下算式只會讓 f0 最大為 0.5
            # f0=1 代表 訊號取樣頻率(Fs)= 16000 Hz, in the default case
            # f0=0.5 就代表 真實的 f0= 0.5*Fs = 8000 Hz, in the default case
            self.f0 /= self.spBufferSize

            #
            # fm 也可以 類似的歸一化
            #
            self.fm /= self.spBufferSize

            #
            # fv, fs 也如法炮製，但意義不易明白，我也沒運用過，先放著，以後有機會再詳細研究。
            #
            self.fv /= self.spBufferSize # this is not much meaningful
            self.fs /= self.spBufferSize

            #
            # 功率頻譜的全通(all-pass)平均，低通(low-pass)平均，高通(high-pass)平均
            #
            self.enP= xP.mean()
            self.enPL= xP[0:spBufferSize/16].mean()
            self.enPH= xP[spBufferSize/16:].mean()

            #
            #
            # 簡單的 DSP 先做到這裡，還有一些較複雜的比如Formant, mfcc, 更準的 f0 等，需要查閱參考資料。
            #
            #

        print('self.gettingSound= ',self.gettingSound)
        self.iS.stop_stream()

    def playSound(self):
        '''
        放音，

        利用 self.playingSound 來中止內部無窮迴圈。
        '''

        self.playingSound= True

        #
        # 邊錄音，邊放音，但放音時 delay 一下，大約 .frameN//10 的時間 (約 1 秒)
        #
        i= self.frameI - self.frameN//10

        while (self.playingSound is True): # 利用 self.playingSound= False 來中止此無窮迴圈。

            #
            # 取出 要放音 的聲音資料，1個音框 (frame)，第 i 個音框。
            #
            x= self.xBuf[i%self.frameN]

            #
            # 轉換格式
            #
            x= x.astype('int16')

            #
            # 再轉成 bytestring
            #
            b= x.tostring()

            #
            # 真正放音就這一行
            #
            self.oS.write(b)

            #i+=1

            #
            # 邊錄音，邊放音，但放音時 delay 一下，大約 .frameN//10 的時間 (約 1 秒)
            #
            # 取用 .frameI 來決定下一個放音音框，強迫 放音音框 與 錄音音框 的同時性，(雖然是相差 .frameN//10)
            #
            i= self.frameI - self.frameN//10
            pass

        print('self.playingSound= ',self.playingSound)
        self.oS.stop_stream()

    def startGet(self):
        '''
        開始收音，用 多線 程式技巧。
        '''
        self.iTh= th.Thread(target= self.getSound)
        self.iTh.start()
        #
        # self.getSound() 中的 錄音迴圈 即將開始，
        # 只能利用 self.gettingSound= False 來中止此無窮迴圈。
        #
        pass

    def startPlay(self):
        '''
        開始放音，用 多線 程式技巧。
        '''
        self.oTh= th.Thread(target= self.playSound)
        self.oTh.start()
        #
        # self.playSound() 中的 放音迴圈 即將開始，
        # 只能利用 self.playingSound= False 來中止此無窮迴圈。
        #
        pass

    def start(self):
        '''
        同時開始錄音，以及放音，
        2個分開的執行線。
        '''
        print('RyAudio will start Get and Play....')
        self.startGet()
        self.startPlay()
        print('RyAudio is started ....')

    def stop(self):
        '''
        結束，停止，收放音。
        這個停止聲音的動作對系統的穩定度而言很重要，
        需要小心看待。
        '''
        self.gettingSound = False
        self.playingSound = False

        #
        # the above 2 message are sent to make getSound() and playSound() stop
        # need to wait for their stopping
        #

        #
        # wait for iS and oS is closed
        #
        # self.aP.terminate()
        #
        print('RyAudio.stop is waiting for iS and oS are both stopped ...')

        while not (self.iS.is_stopped() and self.oS.is_stopped() ):
              #print('wait for iS and oS are both stopped')
              pass

        self.iS.close()
        self.oS.close()
        self.aP.terminate()

        print('RyAudio.stop has been completed.')

    #
    # 建立 中文函數別名。
    #

    開始收音= 開始錄音=  startGet
    開始放音=            startPlay
    開始=                start
    結束= 停止=          stop
    pass
#
# 建立 中文物類別名。
#
音類= RyAudio

#
# 本模組到此結束。
#

#
# 寫幾個示範函數。
#

def demo00():
    '''
    展示最簡單的多線錄放音功能。
    '''
    #
    # 首先，要啟動音訊裝置。
    #

    音= 音類()
    音.開始()

    print('主線 睡 10 秒，音線 錄放音 10 秒。')

    time.sleep(10) # 主線 睡 10 秒，音線 進入 錄放音 狀態

    print('主線 醒來，音線 即將結束。')

    音.結束()

def demo01():
    '''
    錄放音後，把音訊 en, f0 用 pylab 畫出來。
    '''
    #
    # 首先，要啟動音訊裝置。
    #
    音= 音類()  # must (1)
    音.開始()

    #
    # 音 啟動之後 如何抓住？ 
    # 請看以下範例。 抓 T= 10 秒
    #
    T= 10 # sec
    t0= time.time()
    n= 0
    音訊= []
    while time.time()-t0< T:

        t=  音.t   # 時間 (sec)
        en= 音.en  # 能量 (energy, en)
        f0= 音.f0  # 基頻 (fudamental frequency, f0)
        音訊+= [(n, t, en, f0)]

        # control sampling period, 
        # 0.01 sec for en and f0, that is enough
        time.sleep(0.01)  

    # collecting the audio info to plot
    tL= [t  for (n, t, en, f0) in 音訊]
    eL= [en  for (n, t, en, f0) in 音訊]
    fL= [f0  for (n, t, en, f0) in 音訊]
    
    # Using Pylab to plot it
    pl.subplot(211); pl.plot(tL, eL)
    pl.subplot(212); pl.plot(tL, fL)
    pl.show()

    #
    # 程式結束前要記得把 音 停止。
    #
    音.停止()

def demo02():
    '''
    錄放音後，把音訊 .xBuf , .specgram 用 pylab 畫出來。
    '''

    #global xBuf, spec

    音= 音類()
    音.開始()
    time.sleep(10)
    音.停止()

    xBuf= 音.xBuf
    spec= 音.specgram

    x= xBuf.flatten()
    pl.plot(x)
    pl.show()

    spec= pl.log(spec)
    pl.imshow(spec)
    pl.show()

import turtle as tt

def demo03():
    '''
    利用本模組來聲控小烏龜。
    '''

    ###
    ###   step1 to use RyAudio, 
    ###   generate it
    ###
    音= 音類()
    
    ###
    ###   step2 to use RyAudio, 
    ###   start it
    ###
    音.開始()   
    
    #
    # 中文函數別名
    #
    時間=   time.time
    開根號= math.sqrt
    對數=   math.log
    較小值= min
    
    #
    # turtle module
    # set width and height of the screen
    #
    幕= tt.Screen()
    龜= tt.Turtle()
    W= H= 100
    幕.setworldcoordinates (0, 0, W, H)
    龜.penup()

    #
    # set time buffer, 10 sec is a good choice
    #
    T= 10 # sec
    aMsg= 'get sound for %d sec, please wait...'%T
    print(aMsg)
    龜.write(aMsg)
    
    t= t0= 時間()
    while t - t0< T:
        t= 時間()
        x= (t*10)%W
        
        ###
        ###   step3 to use RyAudio, 
        ###   get infomation (en) from it
        ###
        y= 音.en
        
        if y>0:
            y= 對數(y)
        y= 較小值(y, H)

        龜.goto(x,y)
        龜.dot()

    aMsg='click X to close the screen and stop the sound.'
    print(aMsg)
    龜.color('red')
    龜.write(aMsg)
    
    幕.mainloop()
    
    ###
    ###   step4 to use RyAudio, 
    ###   stop it
    ###
    音.結束() 



if __name__=='__main__':

   #demo00()
   #demo01()
   #demo02()
   demo03()

   pass
