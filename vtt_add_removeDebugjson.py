import os, json, sys, re , copy
#Author: Xiaoqiu2451 QQ:2451437216


def getTimeScale(path: str) -> float:
    with open(os.path.join(path, 'manifest.mpd'), encoding='utf-8') as f:
        mdpFile = f.read()
    timescale = re.search(r'(?<=timescale=\")\d*(?=\")', mdpFile)
    print(f'时间放大基准: {timescale}')
    return float(timescale.group())

def getVTTFileList(path: str, TimeScale: float) -> list[tuple]:
    subtitlePath = os.path.join(path, 'manifest_subtitle_vtt_yue')
    with open(os.path.join(path, os.path.join(subtitlePath, 'raw.json')), encoding='UTF-8') as f:
        rawjsonInfo = json.load(f)
    VTTFiles = list()
    for vttsubtitle in rawjsonInfo['segments']:
        vttSegmentNum = vttsubtitle['url'].split('/')[-1].split('-')[1].split('.')[0]  #别动就对了
        VTTFiles.append((os.path.join(subtitlePath, vttsubtitle['name']), int(vttSegmentNum) / TimeScale))
        print(f'VTT文件: {vttsubtitle["name"]}, 基准时间:{int(vttSegmentNum) / TimeScale}')
    return VTTFiles

def getTimeStamp(isoform: str) -> float:  #将ISO时间格式转为时间戳
    stamp = 0.0
    hour, minute, second = map(lambda x: float(x.replace(',', '.')), isoform.split(':'))
    stamp += hour*3600 + minute*60 + second
    return stamp

def readVTTSubtitle(VTTFiles: list):
    subtitles = list()
    for vttFilePath, VTTstartTime in VTTFiles:
        with open(vttFilePath, encoding='UTF-8') as f:
            vttFileLine = map(lambda x: x.strip(), f.readlines())
        tmpTime = ''  #先声明一下
        tmpSubtitle = ''
        for line in vttFileLine:
            if ' --> ' in line:  #为时间轴
                tmpTime = line
            elif line != '' and tmpTime:  #为字幕
                if tmpSubtitle:
                    tmpSubtitle += '\n' + line
                elif not tmpSubtitle:
                    tmpSubtitle = line
            elif line == '' and tmpTime and tmpSubtitle:
                starttime, endtime = map(getTimeStamp, tmpTime.split(' --> '))
                subtitles.append(copy.copy((starttime + VTTstartTime, endtime + VTTstartTime, tmpSubtitle)))
                #print(tmpSubtitle, starttime, starttime + VTTstartTime,endtime, endtime + VTTstartTime)
                tmpTime = ''  #先声明一下
                tmpSubtitle = ''
    return subtitles

def stampToISOForm(stamp: float) -> str:
    seconds = stamp % 60
    secondInt = str(seconds).split('.')[0].rjust(2, '0')
    secondFloat = str(seconds).split('.')[1].ljust(3, '0')[:3]
    hours = int(stamp // 3600)
    minutes = int(stamp // 60 - hours * 60)
    return str(hours).rjust(2, '0') + ':' + str(minutes).rjust(2, '0') + ':' + secondInt + '.' + secondFloat

def writeVTTFile(subtitles: list, path: str) -> None:
    VTTFilePath = os.path.abspath(os.path.basename(path) + '.vtt')  #以文件名作为最后整合的文件
    VTTFileIO = open(VTTFilePath,'w',encoding='UTF-8')
    VTTFileIO.writelines(('WEBVTT', '\n\n'))  #VTT头
    while subtitles:  #我们需要干涉下一个的字幕作为对比 于是无法使用for
        starttime, endtime, text = subtitles.pop(0)
        if subtitles and subtitles[0][2] == text:
            if subtitles[0][0] - endtime < 0.1:  #设置偏差值 在偏差值内的在合并
                endtime = subtitles.pop(0)[1]  #这样只能去除一次重复的 不过应该够用了
        tmpList = (stampToISOForm(starttime), ' --> ', stampToISOForm(endtime), '\n', text, '\n\n')
        VTTFileIO.writelines(tmpList)
    if sys.platform == 'win32':
        os.system(f'explorer {os.path.dirname(VTTFilePath)}')
    print(f'已统合完成 文件保存在 {VTTFilePath}')




def inputFolder() -> str:
    #获取文件夹 如果argv不存在
    path = input('请输入文件夹链接（可以拖入） ')
    if path.startswith('"'):
        path = path[1:-1]  #去除"
    return path

if __name__=='__main__':
    if len(sys.argv) == 1:
        path = inputFolder()
    else:
        path = sys.argv[1]
    assert os.path.exists(os.path.join(path, 'manifest.mpd')) and os.path.exists(os.path.join(path, 'manifest_subtitle_vtt_yue')), "manifest.mpd文件或者manifest_subtitle_vtt_yue文件夹不存在!请检查您输入的文件夹是否包含!"
    VTTFiles = getVTTFileList(path, getTimeScale(path))
    subtitles = readVTTSubtitle(VTTFiles)
    writeVTTFile(subtitles, path)