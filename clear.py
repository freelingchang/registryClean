#!/usr/bin/python3
import os
import re
import json
import shutil

rootDir = '/data/docker/test/docker/registry/v2/repositories'
baseDir = '/data/docker/test/docker/registry/v2/blobs/sha256'

def getImageList():
    imageList = os.listdir(rootDir) 
    return imageList

def isIndexFile(blob):
    indexDir = blob[0:2]
    blobFilePath = os.path.join(baseDir,indexDir,blob,"data")
    try:
        f = open(blobFilePath,'rb')
    except:
        return False
    line = f.read(10)
    content = ""
    try:
        content = line.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if re.search('^{',content):
        return True
    else:
        return False

def getLinkFileBlob(shaValue):
    indexDir = shaValue[0:2]
    blobFilePath = os.path.join(baseDir,indexDir,shaValue,"data")
    f = open(blobFilePath)
    content = f.read()
    f.close()
    content_d = json.loads(content)
    #新增的在config 里面的一层配置层
    configDigest = content_d['config']
    if 'layers' not in content_d:
        return [shaValue]
    blob_list_content = content_d['layers']
    blob_list_content.append(configDigest)
    blob_list = []
    for line in blob_list_content:
        blob = line['digest'].split(":")[1]
        #blob = line.values()[0].split(":")[1]
        if not isIndexFile(blob):
            blob_list.append(blob)
        else:
            blob_list.append(blob)
            blob_list.extend(getLinkFileBlob(blob))
    return blob_list


def getTagLayer(imageName, tagName):
    blob = {}
    tagDir = os.path.join(rootDir, imageName, '_manifests/tags')
    datafileLinkFile = os.path.join(tagDir, tagName, 'current/link')
    if not os.path.exists(datafileLinkFile):
        return
    f = open(datafileLinkFile)
    c = f.readline()
    f.close()
    shaValue = c.split(":")[1]
    blobList = getLinkFileBlob(shaValue)
    blobList.append(shaValue)
    return blobList


def getTaqsLayer(imageName):
    tagBlobs = []
    tagDir = os.path.join(rootDir, imageName, '_manifests/tags')
    if not os.path.exists(tagDir):
        return
    tagList = os.listdir(tagDir)
    for tagName in tagList:
        blob = getTagLayer(imageName, tagName)
        if blob:
            tagBlobs.extend(blob)
    return list(set(tagBlobs))


def getUsageLayer(imageList):
    usageLayer = []
    for imageName in imageList:
        layer = getTaqsLayer(imageName)
        if layer:
            usageLayer.extend(layer)
    usageLayer = list(set(usageLayer))
    f = open('use.txt', 'w+')
    for line in usageLayer:
        f.write(line + '\n')
    f.close()
    
    return usageLayer

def walk(rootDir):
    filelist = []
    for lists in os.listdir(rootDir):
        dirpath = os.path.join(rootDir, lists)
        if os.path.isdir(dirpath):
            tmplist = walk(dirpath)
            if tmplist:
                filelist.extend(tmplist)
        else:
            if not isIndexFile(dirpath):
                filelist.append(dirpath)
    return filelist

def getDiskFile():
    filelist = walk(baseDir)
    blobs = []
    for line in filelist:
        blob = line.split("/")[-2]
        blobs.append(blob)
    blobs = ids = list(set(blobs))
    f = open('walklist.txt','w+')
    for line in blobs:
        f.write(line+'\n')
    f.close()
    return blobs

def getAllUsageLayer():
    imageList = getImageList()
    layperList = getUsageLayer(imageList)
    return layperList

def getNoUseageFile():
    noUsage = []
    layperList = getAllUsageLayer()
    BlobFileAll = getDiskFile()
    for i in BlobFileAll:
        if i not in layperList:
            noUsage.append(i)
    return noUsage

def rmBlobFile(blobList):
    for key in blobList:
        indexDir = key[0:2]
        blobFilePath = os.path.join(baseDir,indexDir,key)
        #blobpath = basedir+'/'+index_dir+'/'+key
        if key:
            if not os.path.exists(blobFilePath):
                continue
            shutil.rmtree(blobFilePath)

if __name__ == "__main__":
    noUsage = getNoUseageFile()
    rmBlobFile(noUsage)

