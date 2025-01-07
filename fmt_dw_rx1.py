from inc_noesis import *
import struct


NOEPY_HEADER = 0x00000024
NOEPY_VERSION2 = 0x0000003C 
NOEPY_VERSION3 = 0x00000074
NOEPY_VERSION4 = 0x00000090
NOEPY_VERSION = 0x00000058


class rwKeyFrame(object):
    def __init__(self):
        self.prevFrame = 0
        self.prevFrameHdrOfs = 0
        self.prevFrameID = 0
        self.time = 0.0
        self.currentFrameHdrOfs = 0
        self.currentID = 0        
        self.nodeID = 0
        self.nextFrameID = -1
        self.quat = NoeQuat()
        self.trans = NoeVec3()


def registerNoesisTypes():
	handle = noesis.register("Darkwatch", ".rx1")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoadModel)
	return 1

def noepyCheckType(data):
        bs = NoeBitStream(data)
        if bs.readInt() != NOEPY_HEADER:
            return 0
        #if bs.readInt() not in (NOEPY_VERSION,NOEPY_VERSION2,NOEPY_VERSION3,NOEPY_VERSION4):
        #    return 0
        return 1

def get_ext_file(dir_path,extension):
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(extension): # ext like ".anm"
                file_list.append(os.path.join(root, file))
    return file_list

def LoadAnims(data, animName, bones,bonesDic):
    bs = NoeBitStream(data)
    hAnim = bs.readInt()
    if hAnim == 0x28:
        #Version = bs.readInt()
        #Frames = bs.readInt()        
        
        #1st line
        xz1 = bs.readInt()
        boneCount = bs.readInt()#количество записей в 1 блоке размером 3float 12bytes
        xz3 = bs.readInt()
        
        #2 line       
        xz4 = bs.readInt() 
        xz5 = bs.readInt() #12
        
        framerate = 30
        TypeID = 0x1103
        #TypeID = bs.readInt()

        # Flags = bs.readInt()
        # Duration = bs.readFloat()
        # framerate = 30
        if TypeID == 0x1103:
             kfBones = readAnimType0x1103(bs,boneCount,bonesDic)
             #print(kfBones)
        return NoeKeyFramedAnim(animName, bones, kfBones, framerate)
        return

def readAnimType0x1103(bs,boneCount,bonesDic):

        #transOffset = NoeVec3.fromBytes(bs.readBytes(12))
        #transScalar = NoeVec3.fromBytes(bs.readBytes(12))
        transScalar = [1.0, 1.0, 1.0]
        transOffset = [0.0, 0.0, 0.0]
        
        keyFrames = []
        kfBones = []
        
        #Frames = 60
        
        blocksQCount = bs.readInt() # 60 количество записей в 2 блоке размером 4float 16bytes
        offsetsBlocksQ = []
        for i in range(boneCount):
                offsetsBlocksQ.append(bs.readInt())
        offsetsBlocksQ.append(blocksQCount)
        #print('offsetsBlocksQ ', offsetsBlocksQ)
        
        rotKfs = []  
        for b in range(blocksQCount):
                kf1 = rwKeyFrame()
                kf1.time = bs.readFloat()
                #print('kf.time ',kf.time)
                # Следующие 8 байт - четыре числа для квартерниона (каждый по 2 байта)
                quat_x, quat_y, quat_z, quat_w = struct.unpack('<hhhh', bs.readBytes(8))

                # Нормализация значений квартерниона в диапазон [-1, 1]
                # quat_x = quat_x / 32767.0
                # quat_y = quat_y / 32767.0
                # quat_z = quat_z / 32767.0
                # quat_w = quat_w / 32767.0
                quat_x = quat_x / 32767.0 
                quat_y = quat_y / 32767.0 
                quat_z = quat_z / 32767.0 
                quat_w = quat_w / 32767.0
                
                kf1.quat = NoeQuat([quat_x,quat_y,quat_z,quat_w]).transpose()
                #kf.quat = NoeQuat([qx,qy,qz,qw])
                #kf.quat = NoeQuat.fromBytes(bs.readBytes(16)).transpose()

                rotKfs.append(NoeKeyFramedValue(kf1.time, kf1.quat))    


        blocksTCount = bs.readInt()
        offsetsBlocksT = [] 
           
        for i in range(boneCount):
                offsetsBlocksT.append(bs.readInt())
        offsetsBlocksT.append(blocksTCount)        
        #print('offsetsBlocksT ', offsetsBlocksT)
    
        posKfs = [] 
        for b in range(blocksTCount):               
                kf2 = rwKeyFrame()
                               
                kf2.time = bs.readFloat()
                #print('kf.time ',kf.time)
                kf2.trans =NoeVec3.fromBytes(bs.readBytes(12))
                #print('kf.trans ',kf.trans)

                posKfs.append(NoeKeyFramedValue(kf2.time, kf2.trans))    

        #print('Lenght rotKfs: ', len(rotKfs))
        #print('Lenght posKfs: ', len(posKfs))
        
        b = bonesDic
        print(b)
        for i in range(boneCount):



                rotKfsRes = []
                posKfsRes = []


                for q in range(offsetsBlocksQ[i],offsetsBlocksQ[i+1]):
                                rotKfsRes.append(rotKfs[q])


                for t in range(offsetsBlocksT[i],offsetsBlocksT[i+1]):
                                posKfsRes.append(posKfs[t])        



                kfBones.append(createKfBone(bonesDic[i], posKfsRes, rotKfsRes))       

                      
                    
        return kfBones    




def createKfBone(boneIndex, posKfs, rotKfs):
        
    kfBone = NoeKeyFramedBone(boneIndex)
    if (rotKfs):
        kfBone.setRotation(rotKfs, noesis.NOEKF_ROTATION_QUATERNION_4,noesis.NOEKF_INTERPOLATE_LINEAR)
    if (posKfs):
        kfBone.setTranslation(posKfs, noesis.NOEKF_TRANSLATION_VECTOR_3,noesis.NOEKF_INTERPOLATE_LINEAR)
    return kfBone

def animGetNumNodes(keyFrames):
    first =  keyFrames[0].currentFrameHdrOfs
    index = 0
    while(keyFrames[index].prevFrameHdrOfs!=first):
        index += 1
    return index




def noepyLoadModel(data, mdlList):
        noesis.logPopup()
        bs = NoeBitStream(data)	
        ctx = rapi.rpgCreateContext()        
        ms = NoeBitStream()
        chunkEndOfs = 0xFFFF0318
        #chunkEndOfs = 0x50
        while (not bs.checkEOF()):
                chunk=rwChunk(bs)

                if chunk.chunkID == 0x16:
                        rtex = rTex(bs.readBytes(chunk.chunkSize))
                        rtex.rTexList()
                        texList = rtex.texList
                elif chunk.chunkID == 0x10:
                        clumpEndOfs = bs.tell()+chunk.chunkSize                      
                        clumpStructHeader = rClumpStruct(bs)
                        
                        framtListHeader = rwChunk(bs)
                        datas = bs.readBytes(framtListHeader.chunkSize)
                        frameList = rFrameList(datas)
                        bones = frameList.readBoneList()
                        skinBones = frameList.getSkinBones()
                        #print('bones /n', bones)
                        #print('skinBones /n', skinBones)
                        geometryListHeader = rwChunk(bs)
                        geometryListStructHeader = rwChunk(bs)
                        geometryCount = bs.readUInt()
                        if geometryCount:
                                datas = bs.readBytes(geometryListHeader.chunkSize-16)
                        vertMatList=[0]*clumpStructHeader.numAtomics
                        if clumpStructHeader.numAtomics:
                                atomicData = bytes()
                                for i in range(clumpStructHeader.numAtomics):
                                        atomicHeader = rwChunk(bs)
                                        atomicData += bs.readBytes(atomicHeader.chunkSize)
                                atomicList = rAtomicList(atomicData,clumpStructHeader.numAtomics).rAtomicStuct()
                                for j in range(clumpStructHeader.numAtomics):
                                        #self.boneIDList
                                        #vertMatList[atomicList[j].geometryIndex]= bones[frameList.boneIDList[atomicList[j].frameIndex]].getMatrix()
                                        vertMatList[atomicList[j].geometryIndex]= bones[atomicList[j].frameIndex].getMatrix()
                        if geometryCount:
                                geometryList = rGeometryList(datas,geometryCount,vertMatList,frameList.bonesDic)
                                geometryList.readGeometry()                                
                                mdl = rapi.rpgConstructModel()
                                matList = []
                                for tex in texList:
                                        matName = tex.name
                                        material = NoeMaterial(matName, tex.name)
                                        material.setDefaultBlend(0)
                                        matList.append(material)
                                mdl.setModelMaterials(NoeModelMaterials(texList,matList))
                                mdl.setBones(bones)
                                
                                anims = []      
                                LoadAnimation = True    
                                       
                                if LoadAnimation:
                                        path = os.path.dirname(rapi.getInputName())
                                        #path +='\sanm\lo'
                                        #print(path)
                                        anmFiles = get_ext_file(path,"sanm")
                                        #print(anmFiles)
                                        for anmFile in anmFiles:
                                                #print(anmFile)
                                                anmName = os.path.basename(anmFile)[:-5] # Filename without extension
                                                animData = rapi.loadIntoByteArray(anmFile)                   
                                                if animData:                        
                                                        anims.append(LoadAnims(animData, anmName, bones, frameList.bonesDic))
                                                       
                                        if anims:
                                                mdl.setAnims(anims)    

                                
                                mdlList.append(mdl)
                                rapi.rpgReset()

                                
                                
                        bs.seek(clumpEndOfs)
                else:
                        bs.seek(chunk.chunkSize,1)
        ##
 
        return 1



class rwChunk(object):   
        def __init__(self,bs):
                self.chunkID,self.chunkSize,self.chunkVersion = struct.unpack("3I", bs.readBytes(12))
class rTexNative(object):
        def __init__(self,datas):
                self.bs = NoeBitStream(datas)
        def rTexture(self):                
                texNativeStructHeader = rwChunk(self.bs)
                
                platformId = self.bs.readInt()
                textureFormat = self.bs.readInt()
                nameEndOfs = self.bs.tell()+32
                texName = self.bs.readString()
                self.bs.seek(nameEndOfs)
                self.bs.seek(32,1)

                rasterFormat = self.bs.readUInt()
                d3dFormat = self.bs.readUInt()
                width = self.bs.readUShort()
                height = self.bs.readUShort()
                depth = self.bs.readUByte()
                numLevels = self.bs.readUByte()
                rasterType = self.bs.readUByte()
                bitFlag = self.bs.readUByte()
                alpha = bitFlag & 0x1
                cubTeture = (bitFlag & 0x2) >> 1
                autoMipMaps = (bitFlag & 0x4) >> 2
                compressed = (bitFlag & 0x8) >> 3
                texFormatExt = rasterFormat & 0xf000
                texFormat = rasterFormat & 0xf00
                pixelBuffSize = self.bs.readUInt()
                if compressed == 0:
                    palette = self.bs.readBytes(1024) #256 colors         
                #pixelBuff = reader.readBytes(pixelBuffSize)
                pixelBuff = self.bs.readBytes(pixelBuffSize)

                if depth == 32:
                        if compressed == 1:
                                texData = rapi.imageDecodeDXT(pixelBuff, width, height, noesis.NOESISTEX_DXT1)
                        elif compressed == 0:
                                pixelBuff = rapi.imageFromMortonOrder(pixelBuff,width,height)
                                texData = rapi.imageDecodeRaw(pixelBuff, width, height, "r8g8b8a8")
                elif depth == 8:
                        pixelBuff = rapi.imageFromMortonOrder(pixelBuff,width,height)
                        texData = rapi.imageDecodeRawPal(pixelBuff, palette, width, height, 8, "b8g8r8a8")
                        
                elif depth == 4:
                        texData = rapi.imageDecodeRawPal(pixelBuff, palette, width, height, 4, "r8g8b8a8")
                
                
                dirName = rapi.getDirForFilePath(rapi.getInputName())
                outName = dirName + texName + ".png"
                texture = NoeTexture(texName, width, height, texData, noesis.NOESISTEX_RGBA32)
                if not rapi.checkFileExists(outName):
                    noesis.saveImageRGBA(outName,texture)
                    #self.texList.append(texture)
                #noesis.saveImageRGBA(outName,texture)
                return texture
class rTex(object):
        def __init__(self,datas):
                self.bs = NoeBitStream(datas)
                self.texList = []
                self.texCount = 0
        def rTexList(self):
                texStruct = rwChunk(self.bs)
                texCount = self.bs.readUShort()
                self.texCount = texCount
                deviceId = self.bs.readUShort()
                for i in range(texCount):
                        texNativeHeader = rwChunk(self.bs)
                        datas = self.bs.readBytes(texNativeHeader.chunkSize)
                        texNative = rTexNative(datas)
                        texture = texNative.rTexture()
                        self.texList.append(texture)
       
class rClumpStruct(object):
        def __init__(self,bs):
                self.chunkID,self.chunkSize,self.chunkVersion = struct.unpack("3I", bs.readBytes(12))                
                self.numAtomics = bs.readUInt()
                self.numLights = bs.readUInt()
                self.numCameras = bs.readUInt()
class rFrameList(object):
        def __init__(self,datas):
                self.bs = NoeBitStream(datas)                
                self.frameCount = 0
                self.boneMatList=[]
                self.bonePrtIdList=[]
                self.boneIndexList=[]
                self.boneIDList=[]
                self.boneNameList=[]                
                self.hAnimBoneIDList =[]
                self.hAnimBoneIndexList=[]                
                self.bones = []
                self.skinBones=[]
                self.hasAnim = 0
                self.kickDummy = 0
                self.bonesDic = {}
        def rFrameListStruct(self):
                header = rwChunk(self.bs)
                frameCount = self.bs.readUInt()
                #print('frameCount ', frameCount)
                self.frameCount = frameCount
                if frameCount:
                        for i in range(frameCount):
                                boneMat = NoeMat43.fromBytes(self.bs.readBytes(48)).transpose()
                                bonePrtId = self.bs.readInt()
                                self.bs.readInt()
                                self.boneMatList.append(boneMat)
                                self.bonePrtIdList.append(bonePrtId)
                                self.boneIndexList.append(i)

        def rHAnimPLG(self):
                hAnimVersion = self.bs.readInt()
                self.boneIDList.append(self.bs.readInt())
                boneCount = self.bs.readUInt()
                if boneCount:
                        self.hasAnim = 1
                        flags = self.bs.readInt()
                        keyFrameSize = self.bs.readInt()
                        for i in range(boneCount):
                                self.hAnimBoneIDList.append(self.bs.readInt())
                                self.hAnimBoneIndexList.append(self.bs.readInt())
                                boneType = self.bs.readInt()
        def rUserDataPLG(self,index):
                numSet = self.bs.readInt()
                boneName = "Dummy"+str(index)
                #print('YYYYYYYY')
                for i in range(numSet):
                        typeNameLen = self.bs.readInt()
                        self.bs.seek(typeNameLen,1)
                        u2 = self.bs.readInt()
                        u3 = self.bs.readInt()
                        boneNameLen = self.bs.readInt()
                        if boneNameLen>1:
                                boneName = self.bs.readString()
                                #print('boneName ',boneName) 
                        #if (i == 0): self.boneNameList.append(boneName)
                self.boneNameList.append(boneName)
        def rFrameExt(self,index):
                header = rwChunk(self.bs)
                endOfs = self.bs.tell() + header.chunkSize
                hasName = 0
                if header.chunkSize:
                        while (self.bs.tell()<endOfs):
                                chunk = rwChunk(self.bs)                                
                                if chunk.chunkID == 0x11e:
                                        self.rHAnimPLG()
                                elif chunk.chunkID == 0x11f:
                                        hasName = 1
                                        self.rUserDataPLG(index)
                                else:
                                        self.bs.seek(chunk.chunkSize,1)
                if(hasName==0):
                        #self.boneNameList.append("Dummy "+str(index))
                        if index==0:
                                self.boneNameList.append("Root")
                        else:
                                self.boneNameList.append("Dummy "+str(index))
        def rFrameExtList(self):
                #self.boneNameList.append("Root")
                for i in range(self.frameCount):
                        self.rFrameExt(i)
                #print(self.boneNameList)

        def loadBoneNames(self, data):
                # Разделяем данные по байту 32 (пробел), убирая пустые части
                chunks = [chunk for chunk in data.split(b' ') if chunk]
                # Преобразуем каждую часть в строку
                boneNames = [chunk.decode('utf-8', errors='replace').strip() for chunk in chunks]    
                return boneNames

        
        def readBoneList(self):
                self.rFrameListStruct()
                self.rFrameExtList()

                path = os.path.dirname(rapi.getInputName())
                #print(path)
                bnFilesExt = get_ext_file(path,"jlist")
                #print(bnFilesExt)
                for bnFile in bnFilesExt:
                        bnFileName = os.path.basename(bnFile)[:-6] # Filename without extension
                        bnData = rapi.loadIntoByteArray(bnFile)  
                
                if bnData: 
                        self.boneNames = self.loadBoneNames(bnData)
                #print('END ', self.boneNames)
                                
                
                
                bones=[]
                for i in range(self.frameCount):
                        boneIndex = self.boneIndexList[i]
                        #print('boneIndex ',boneIndex)
                        #boneName = self.boneNameList[i]
                        if i==0: boneName = 'Root'
                                
                        else: boneName = self.boneNames[self.boneIDList[i-1]]


                        #print(i, ' ', self.boneNames[i])
                        #print('boneName',boneName)
                        boneMat = self.boneMatList[i]
                        bonePIndex = self.bonePrtIdList[i]
                        bone = NoeBone(boneIndex, boneName, boneMat, None, bonePIndex)
                        
                        bones.append(bone)
                        
                for i in range(self.frameCount):
                        bonePIndex = self.bonePrtIdList[i]
                        if(bonePIndex>-1):
                                prtMat=bones[bonePIndex].getMatrix()
                                boneMat = bones[i].getMatrix()                             
                                bones[i].setMatrix(boneMat * prtMat)
                self.bones = bones
                #print(bones)
                return bones
        
        def getSkinBones(self):               
                bones=[]
                oldBoneIndexList = [0]*(self.frameCount-1)
                oldBonePrtIDlist =[0]*(self.frameCount-1)
                newBonePrtIdList = [0]*(self.frameCount-1)
                #print('self.boneIDList ', self.boneIDList)
                for i in range(self.frameCount-1):
                        oldBoneIndexList[self.boneIDList[i]] = i+1
                        oldBonePrtIDlist[self.boneIDList[i]] = self.bonePrtIdList[i+1]
                for i in range(self.frameCount-1):                        
                        oldPrtBoneIndex = oldBonePrtIDlist[self.boneIDList[i]] 
                        for j in range(self.frameCount-1):                                
                                if oldPrtBoneIndex == oldBoneIndexList[j]:                                
                                        newBonePrtIdList[self.boneIDList[i]] = j
                                        break
                                elif oldPrtBoneIndex == 0:
                                        newBonePrtIdList[self.boneIDList[i]] = -1
                                        break                    
                        
                for j in range(self.frameCount-1):                
                        boneIndex = j
                        #boneName =  self.boneNameList[oldBoneIndexList[j]]
                        boneName = self.boneNames[j]
                        boneMat = self.boneMatList[oldBoneIndexList[j]]
                        bonePIndex = newBonePrtIdList[j]
                        #print('AAAboneIndex ',boneIndex,' boneName',boneName)
                        bone = NoeBone(boneIndex, boneName, boneMat, None, bonePIndex)
                        bones.append(bone)
                for j in range(self.frameCount-1):
                        bonePIndex = newBonePrtIdList[j]
                        if(bonePIndex>-1):
                                prtMat=bones[bonePIndex].getMatrix()
                                boneMat = bones[j].getMatrix()                             
                                bones[j].setMatrix(boneMat * prtMat)
                        else:
                                prtMat=self.bones[0].getMatrix()
                                boneMat = bones[j].getMatrix()                             
                                bones[j].setMatrix(boneMat * prtMat)
                #bones.insert(0,self.bones[0])
                self.skinBones = bones
                #print(bones)
                
                self.bonesDic = {}
                print('self.skinBones ', self.skinBones)
                print('self.bones ', self.bones)
                for skinBone in self.skinBones:
                        # skinBone.index
                        # skinBone.name   
                        for i in range(len(self.bones)):
                                if self.bones[i].name == skinBone.name:
                                     self.bonesDic[skinBone.index] = self.bones[i].index
                print(self.bonesDic)
                                
                return bones
class Atomic(object):
        def __init__(self):
               self.frameIndex = 0
               self.geometryIndex = 0
class rAtomicList(object):
        def __init__(self,datas,numAtomics):
               self.bs = NoeBitStream(datas)
               self.numAtomics = numAtomics
        def rAtomicStuct(self):
                atomicList=[]
                for i in range(self.numAtomics):
                        header = rwChunk(self.bs)
                        atomic = Atomic()
                        atomic.frameIndex = self.bs.readUInt()
                        atomic.geometryIndex = self.bs.readUInt()
                        flags = self.bs.readUInt()
                        unused = self.bs.readUInt()
                        extHeader = rwChunk(self.bs)
                        self.bs.seek(extHeader.chunkSize,1)
                        atomicList.append(atomic)
                return atomicList
class rMatrial(object):
        def __init__(self,datas):
                self.bs = NoeBitStream(datas)                
        def rMaterialStruct(self):
                header = rwChunk(self.bs)
                unused = self.bs.readInt()
                rgba = self.bs.readInt()
                unused2 = self.bs.readInt()
                hasTexture = self.bs.readInt()
                ambient = self.bs.readFloat()
                specular = self.bs.readFloat()
                diffuse = self.bs.readFloat()
                texName = ""
                if hasTexture:
                        texHeader = rwChunk(self.bs)
                        texStructHeader = rwChunk(self.bs)
                        textureFilter = self.bs.readByte()
                        UVAddressing = self.bs.readByte()
                        useMipLevelFlag = self.bs.readShort()
                        texName = noeStrFromBytes(self.bs.readBytes(rwChunk(self.bs).chunkSize))
                        alphaTexName = noeStrFromBytes(self.bs.readBytes(rwChunk(self.bs).chunkSize))
                        texExtHeader = rwChunk(self.bs)
                        self.bs.seek(texExtHeader.chunkSize,1)
                matExtHeader = rwChunk(self.bs)
                self.bs.seek(matExtHeader.chunkSize,1)
                return texName
                        
class rMaterialList(object):
        def __init__(self,datas):
                self.bs = NoeBitStream(datas)            
                self.matCount = 0
                self.matList = []
                self.texList = []
        def rMaterialListStruct(self):
                header = rwChunk(self.bs)
                self.matCount = self.bs.readUInt()
                self.bs.seek(self.matCount*4,1)
        def getMaterial(self):
                self.rMaterialListStruct()
                for i in range(self.matCount):
                        matData = self.bs.readBytes(rwChunk(self.bs).chunkSize)
                        texName = rMatrial(matData).rMaterialStruct()
                        self.texList.append(texName)
                        #matName = "material[%d]" %len(self.matList)
                        matName = texName
                        material = NoeMaterial(matName, texName)
                        material.setDefaultBlend(0)
                        self.matList.append(material)
                        #texture = NoeTexture()
                        self.texList.append(texName)                        
                #return self.matList
class rGeometryList(object):
        def __init__(self,datas,geometryCount,vertMatList,skinBones):
                self.bs = NoeBitStream(datas)            
                self.geometryCount = geometryCount
                self.vertMatList = vertMatList
                self.matList =[]
                self.skinBones = skinBones
        def readGeometry(self):
                
                for i in range(self.geometryCount):
                        vertMat = self.vertMatList[i]
                        geometryHeader = rwChunk(self.bs)
                        datas = self.bs.readBytes(geometryHeader.chunkSize)
                        geo = rGeomtry(datas,vertMat,self.skinBones)
                        
                        geo.rGeometryStruct()
                        for m in range(len(geo.matList)):
                                self.matList.append(geo.matList[m])
                        
                             
class rSkin(object):
        def __init__(self,datas,numVert,nativeFlag,skinBones):
                self.bs = NoeBitStream(datas)
                self.numVert = numVert
                self.nativeFlag = nativeFlag
                self.boneIndexs = bytes()
                self.boneWeights = bytes()
                self.skinBones = skinBones
        def readSkin(self):
                if self.nativeFlag != 1:
                        self.bs.seek(4,1)
                        boneCount = self.bs.readByte()
                        usedBoneIDCount=self.bs.readByte()
                        maxNumWeights = self.bs.readByte()
                        unk2 = self.bs.readByte()
                        self.bs.seek(usedBoneIDCount,1)
                        self.boneIndexs = self.bs.readBytes(self.numVert*4)
                        self.boneWeights= self.bs.readBytes(self.numVert*16)
                        rapi.rpgBindBoneIndexBuffer(self.boneIndexs, noesis.RPGEODATA_UBYTE, 4 , 4)
                        rapi.rpgBindBoneWeightBuffer(self.boneWeights, noesis.RPGEODATA_FLOAT, 16, 4)
                        

                else:
                        skinStruct = rwChunk(self.bs)
                        unk_5 = self.bs.readInt()
                        boneCount = self.bs.readInt()
                        #print('boneCount ', boneCount)
                        boneIndexList1=[]
                        boneIndexList2=[]
                        usedBoneCount = 0
                        #boneIndexList1.append(0)
                        for i in range(256):
                                boneIndex = self.bs.readInt()
                                
                                if (boneIndex >= 0):
                                        #print(boneIndex)
                                        #boneIndexList1.append(boneIndex)
                                        boneIndexList1.append(self.skinBones[boneIndex])
                                        usedBoneCount += 1
                        #print('boneIndexList1 SKINAAA ',boneIndex)                                     
                        #print(boneIndexList1)
                        for i in range(boneCount):
                                boneIndex = self.bs.readInt()
                                #print('AAA')
                                #print(boneIndex)
                                boneIndexList2.append(self.skinBones[boneIndex])
                        #print(boneIndexList2)        
                        self.bs.seek((256-boneCount)*4,NOESEEK_REL)                        
                        unknown_type = self.bs.readInt() #20
                        
                        maxWeightsPerVertex = self.bs.readInt() #3
                        #print(maxWeightsPerVertex)
                        unk1 = self.bs.readInt()
                        perVertDataSize = self.bs.readInt()
                        skinBoneIndexs=bytes()
                        skinBoneWeights=bytes()
                        #print(self.skinBones)
                        for i in range(self.numVert):
                                for j in range(maxWeightsPerVertex):
                                        weight = self.bs.readUByte()/255.0
                                        wbytes = struct.pack('f',weight)
                                        skinBoneWeights += wbytes
                                for j in range(maxWeightsPerVertex):
                                        temp= (self.bs.readUShort() // 3)
                                        #print('temp ',temp)
                                        #print('max(boneIndexList1)',max(boneIndexList1))
                                        #print(boneIndexList1[temp])
                                        #if (temp in boneIndexList1): 
                                        #boneIDttt = boneIndexList1[temp]
                                        #bone = NoeBone(boneIndex, boneName, boneMat, None, bonePIndex)
                                        #frameList.boneIDList
                                        #boneName = .boneNames[self.boneIDList[i-1]]
                                        boneID = boneIndexList1[temp]
                                        #print(temp, ' boneTMP ',boneTMP)
                                        # bonestr= boneTMP.name.replace('Dummy ','')
                                        # boneID = int(bonestr)
                                        
                                        skinBoneIndexs += struct.pack('i',boneID)  
                                                  
                        rapi.rpgBindBoneIndexBuffer(skinBoneIndexs, noesis.RPGEODATA_INT, maxWeightsPerVertex*4 , maxWeightsPerVertex)
                        rapi.rpgBindBoneWeightBuffer(skinBoneWeights, noesis.RPGEODATA_FLOAT, maxWeightsPerVertex*4, maxWeightsPerVertex)
                                
                #inverseBoneMats=[]
                #for i in range(boneCount):
                #         inverseBoneMats.append(NoeMat44.fromBytes(self.bs.readBytes(64)))                        
                self.bs.read('3f')
class rBinMeshPLG(object):
        def __init__(self,datas,matList,nativeFlag):
                self.bs = NoeBitStream(datas)
                self.matList = matList
                self.nativeFlag = nativeFlag
                self.matIdList = []
        def readFace(self):
                faceType = self.bs.readInt() # 1 = triangle strip
                numSplitMatID = self.bs.readUInt()
                indicesCount = self.bs.readUInt()
                for i in range(numSplitMatID):
                        faceIndices = self.bs.readUInt()                        
                        matID = self.bs.readUInt()
                        self.matIdList.append(matID)
                        if self.nativeFlag != 1:
                                matName = self.matList[matID].name
                                rapi.rpgSetMaterial(matName)
                                tristrips = self.bs.readBytes(faceIndices*4)
                                rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_UINT, faceIndices, noesis.RPGEO_TRIANGLE_STRIP, 1)
class materialTristripsInfo(object):
        def __init__(self,vertexCountStart,vertexCountEnd,tristripsCount,unknownCount):
                self.vertexCountStart = vertexCountStart
                self.vertexCountEnd = vertexCountEnd
                self.tristripsCount = tristripsCount
                self.unknownCount = unknownCount
class rNativeDataPLG(object):
        def __init__(self,datas,matList,matIdList,vertMat,FormatFlags):
                self.bs = NoeBitStream(datas)
                self.matList = matList
                self.matIdList = matIdList
                self.vertMat = vertMat
                self.FormatFlags = FormatFlags
        def readMesh(self):
                natvieStruct = rwChunk(self.bs)
                unk_5 = self.bs.readInt()
                
                vertexOffset = self.bs.tell() + self.bs.readInt()
                vertexUnk = self.bs.readShort()                
                materialCount = self.bs.readShort()
                unk_6 = self.bs.readInt()
                vertexCount = self.bs.readInt()
                perVertElementDataSize = self.bs.readInt()
                unk_flag = self.bs.readInt()
                
                matHeader_0 = self.bs.readInt()
                matHeader_unk1 = self.bs.readInt()
                matHeader_unk2 = self.bs.readInt()
                matTristripsInfo = []
                for i in range(materialCount):
                        vertexCountStart = self.bs.readInt()
                        vertexCountEnd = self.bs.readInt()
                        tristripsCount = self.bs.readInt()
                        unknownCount = self.bs.readInt()
                        self.bs.seek(8,1)
                        info = materialTristripsInfo(vertexCountStart,vertexCountEnd,tristripsCount,unknownCount)
                        matTristripsInfo.append(info)
                padLen = 16-((12+materialCount*24)%16)
                self.bs.seek(padLen,1)
                faceOffset = self.bs.tell()
                #print('faceOffset ',faceOffset)
                self.bs.seek(vertexOffset)
                #print('vertexOffset ',vertexOffset)
                vertBuff = bytes()
                uvBuff = bytes()
                colorBuff = bytes()
                #print('padLen ',padLen )
                
                for i in range(vertexCount):
                        #vertBuff+=self.bs.readBytes(12)
                        tempVert = self.bs.readBytes(12)
                        vert = NoeVec3.fromBytes(tempVert)
                        vert *= self.vertMat
                        if (self.FormatFlags==63):
                        #if (self.FormatFlags==55):
                                vertBuff+=vert.toBytes()                        
                                colorBuff+=self.bs.readBytes(4)
                                self.bs.seek(perVertElementDataSize-24,1)
                                #self.bs.seek(4,1)
                                #self.bs.seek(padLen-4,1)
                                tempUV = self.bs.readBytes(8)
                                #self.bs.seek(8,1)
                                uvBuff += tempUV
                        #elif (self.FormatFlags==187):
                        elif (self.FormatFlags==119):  
                                vertBuff+=vert.toBytes()                        
                                colorBuff+=self.bs.readBytes(4)
                                #self.bs.seek(perVertElementDataSize-24,1)
                                #self.bs.seek(4,1)
                                #self.bs.seek(padLen-4,1)
                                tempUV = self.bs.readBytes(8)
                                #self.bs.seek(8,1)
                                uvBuff += tempUV
                        elif (self.FormatFlags==55):  
                                vertBuff+=vert.toBytes()                        
                                colorBuff+=self.bs.readBytes(4)
                                #self.bs.seek(perVertElementDataSize-24,1)
                                #self.bs.seek(4,1)
                                #self.bs.seek(padLen-4,1)
                                tempUV = self.bs.readBytes(8)
                                #self.bs.seek(8,1)
                                uvBuff += tempUV                                
                        else:
                                vertBuff+=vert.toBytes()                        
                                colorBuff+=self.bs.readBytes(4)
                                self.bs.seek(perVertElementDataSize-24,1)
                                #self.bs.seek(4,1)
                                #self.bs.seek(padLen-4,1)
                                tempUV = self.bs.readBytes(8)
                                #self.bs.seek(8,1)
                                uvBuff += tempUV                                                                
                        
                rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT,12)
                rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
                #rapi.rpgBindColorBuffer(colorBuff, noesis.RPGEODATA_UBYTE, 4, 4)
                self.bs.seek(faceOffset)
                #print('materialCount ', materialCount)
                for i in range(materialCount):
                        info = matTristripsInfo[i]
                        #print('info', info)
                        matID = self.matIdList[i]
                        #print('matID',matID)
                        matName = self.matList[matID].name
                        #print('matName',matName)
                        rapi.rpgSetMaterial(matName)
                        tristrips = self.bs.readBytes(info.tristripsCount * 2)
                        #print('tristrips ',tristrips)
                        #if (matName=='ViperCape_B_Clr'):
                        #        rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_USHORT, info.tristripsCount, noesis.RPGEO_TRIANGLE, 1)
                        #        print('YYY')
                        #else: 
                        #if (self.FormatFlags==119):rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_USHORT, info.tristripsCount, noesis.RPGEO_TRIANGLE, 1)
                        #else: rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_USHORT, info.tristripsCount, noesis.RPGEO_TRIANGLE_STRIP, 1)
                        #rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_USHORT, info.tristripsCount, noesis.RPGEO_TRIANGLE, 1)
                        rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_USHORT, info.tristripsCount, noesis.RPGEO_TRIANGLE_STRIP, 1)
                        if ((info.tristripsCount * 2) % 16):
                                padLen = 16 - ((info.tristripsCount * 2) % 16)
                                self.bs.seek(padLen,1)

class rGeomtry(object):
        def __init__(self,datas,vertMat,skinBones):
                self.bs = NoeBitStream(datas)
                self.vertMat = vertMat
                self.matList = []
                self.skinBones = skinBones
        def rGeometryStruct(self):
                geoStruct = rwChunk(self.bs)
                FormatFlags = self.bs.readUShort()
                #print('FormatFlags ',FormatFlags)
                numUV = self.bs.readByte()
                nativeFlags = self.bs.readByte()
                numFace = self.bs.readUInt()
                numVert = self.bs.readUInt()
                numMorphTargets = self.bs.readUInt()
                Tristrip = FormatFlags % 2
                Meshes = (FormatFlags & 3) >> 1
                Textured = (FormatFlags & 7) >> 2
                Prelit = (FormatFlags & 0xF) >> 3
                Normals = (FormatFlags & 0x1F) >> 4
                Light = (FormatFlags & 0x3F) >> 5
                ModulateMaterialColor = (FormatFlags & 0x7F) >> 6
                Textured_2 = (FormatFlags & 0xFF) >> 7;
                
                MtlIDList = []
                faceBuff = bytes()
                vertBuff = bytes()
                normBuff = bytes()
                uvs = None
                if nativeFlags != 1:
                        if (Prelit==1):
                                self.bs.seek(numVert*4,1)
                        if (Textured == 1):
                                uvs = self.bs.readBytes(numVert * 8)
                                rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 8)
                        if (Textured_2==1):
                                uvs = self.bs.readBytes(numVert * 8)              
                                self.bs.seek(numVert*8,1)
                                rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 8)
                        if (Meshes==1):                        
                                for i in range(numFace):
                                        f2 = self.bs.readBytes(2)
                                        f1 = self.bs.readBytes(2)
                                        MtlIDList.append(self.bs.readUShort())
                                        f3 = self.bs.readBytes(2)
                                        faceBuff+=f1
                                        faceBuff+=f2
                                        faceBuff+=f3                                
                sphereXYZ = NoeVec3.fromBytes(self.bs.readBytes(12))
                sphereRadius = self.bs.readFloat()
                positionFlag = self.bs.readUInt()
                normalFlag = self.bs.readUInt()
                if nativeFlags != 1:
                        if (Meshes==1):
                                #vertBuff = self.bs.readBytes(numVert * 12)
                                for i in range(numVert):
                                        vert = NoeVec3.fromBytes(self.bs.readBytes(12))
                                        vert *= self.vertMat
                                        vertBuff+=vert.toBytes()
                                        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
                        if (Normals==1):
                                #normBuff = self.bs.readBytes(numVert * 12)
                                for i in range(numVert):
                                        normal = NoeVec3.fromBytes(self.bs.readBytes(12))
                                        normal *= self.vertMat
                                        normBuff+=normal.toBytes()        
                                        rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
                                                
                

                matrialListHeader = rwChunk(self.bs)
                matDatas = self.bs.readBytes(matrialListHeader.chunkSize)
                rMatList = rMaterialList(matDatas)
                rMatList.getMaterial()
                matList = rMatList.matList
                texList = rMatList.texList
                for m in range(len(matList)):
                        self.matList.append(matList[m])
                geoExtHeader = rwChunk(self.bs)
                #geoExtDatas = self.bs.readBytes(geoExtHeader.chunkSize)
                geoExtEndOfs = self.bs.tell()+geoExtHeader.chunkSize

                haveSkin = 0
                haveBinMesh = 0
                haveNavtiveMesh = 0
                while self.bs.tell()<geoExtEndOfs:
                        header = rwChunk(self.bs)
                        if header.chunkID == 0x50e:
                                haveBinMesh = 1
                                binMeshDatas = self.bs.readBytes(header.chunkSize)                    
                        elif header.chunkID == 0x116:
                                haveSkin = 1
                                skinDatas = self.bs.readBytes(header.chunkSize)
                        elif header.chunkID == 0x510:
                                haveNavtiveMesh = 1
                                nativeDatas = self.bs.readBytes(header.chunkSize)                                
                        else:
                             self.bs.seek(header.chunkSize,1)
                #if nativeFlags==1:
                #        print("found native mesh")
                if haveSkin:
                        skin = rSkin(skinDatas,numVert,nativeFlags,self.skinBones)
                        skin.readSkin()
                if haveBinMesh:
                        binMeshPLG = rBinMeshPLG(binMeshDatas,matList,nativeFlags)
                        binMeshPLG.readFace()
                if haveNavtiveMesh:
                        nativeDataPLG = rNativeDataPLG(nativeDatas,matList,binMeshPLG.matIdList,self.vertMat,FormatFlags)
                        nativeDataPLG.readMesh()
                #rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, (numFace * 3), noesis.RPGEO_TRIANGLE, 1)
                rapi.rpgClearBufferBinds()                

