import os
import sys
import glob
import time
from os import system, name
import platform

comPorts = []
pathSeparator = ""
platformSlash = ""
if platform.uname()[0] == "Windows":
    # Set ComPort framework
    comPorts = ['COM%s' % (i + 1) for i in range(256)]
    # Set path separator
    pathSeparator = ";"
    # Set platform slash
    platformSlash = "\\"
elif platform.uname()[0] == "Linux":
    # Set ComPort framework
    comPorts = glob.glob('/dev/tty[A-Za-z]*')
    # Set path separator
    pathSeparator = ":"
    # Set platform slash
    platformSlash = "/"
else:
    print("\tUnsupported platform !!!")
    sys.exit()

# Define relative path to wrapper directory: "..\..\..\..\Middleware\wrapper\python"
PATHTOWRAPPER = ".." + platformSlash + "Big-Scanner-Stuff/Middleware" + platformSlash + "wrapper" + platformSlash + "python"
print(PATHTOWRAPPER)
# Check Python wrapper and related DLL can be reached
if not os.path.isdir(os.getcwd() + platformSlash + PATHTOWRAPPER):
    sys.exit()
os.environ['PATH'] += pathSeparator + os.getcwd() + platformSlash + PATHTOWRAPPER
sys.path.append(PATHTOWRAPPER)

for path in os.environ["PATH"].split(";"):
    print("path: {}".format(path))

import STUHFL


libVersion = STUHFL.STUHFL_T_VersionLib()
libVersion.fetch()

tags = []

# Connect to board
currentPort = ""
for port in comPorts:
    try:
        ret = STUHFL.Connect(port)
        if ret == 0:
            # runs boardVersion.fetch() to ensure communication with FW is established
            boardVersion = STUHFL.STUHFL_T_VersionBoard()
            if boardVersion.fetch() == STUHFL.STUHFL_ERR_NONE:
                currentPort = port
                break
            else:
                STUHFL.Disconnect()
    except (OSError):
        pass


def demo_SetupGen2Config(singleTag, freqHopping, antenna, tuningAlgo):
    txRxCfg = STUHFL.STUHFL_T_ST25RU3993_TxRxCfg()
    txRxCfg.fetch();
    txRxCfg.rxSensitivity = 3;
    txRxCfg.txOutputLevel = -2;
    txRxCfg.usedAntenna = antenna;
    txRxCfg.alternateAntennaInterval = 1;
    txRxCfg.commit();

    invGen2Cfg = STUHFL.STUHFL_T_ST25RU3993_Gen2_InventoryCfg()
    invGen2Cfg.fetch();
    invGen2Cfg.inventoryOption.fast = True;
    invGen2Cfg.inventoryOption.autoAck = False;
    invGen2Cfg.antiCollision.startQ = 0 if singleTag else 4
    invGen2Cfg.antiCollision.adaptiveQ = False if singleTag else True
    invGen2Cfg.adaptiveSensitivity.enable = True;
    invGen2Cfg.queryParams.toggleTarget = True;
    invGen2Cfg.queryParams.targetDepletionMode = True;
    invGen2Cfg.commit();

    gen2ProtocolCfg = STUHFL.STUHFL_T_ST25RU3993_Gen2_ProtocolCfg()
    gen2ProtocolCfg.fetch();
    gen2ProtocolCfg.tari = STUHFL.STUHFL_D_GEN2_TARI_25_00;
    gen2ProtocolCfg.blf = STUHFL.STUHFL_D_GEN2_BLF_256;
    gen2ProtocolCfg.coding = STUHFL.STUHFL_D_GEN2_CODING_MILLER8;
    gen2ProtocolCfg.trext = STUHFL.STUHFL_D_TREXT_ON;
    gen2ProtocolCfg.commit();

    freqLBT = STUHFL.STUHFL_T_ST25RU3993_FreqLBT()
    freqLBT.fetch();
    freqLBT.listeningTime = 0;
    freqLBT.idleTime = 0;
    freqLBT.rssiLogThreshold = 38;
    freqLBT.skipLBTcheck = True;
    freqLBT.commit();

    if (freqHopping):
        channelList = STUHFL.STUHFL_T_ST25RU3993_ChannelList(STUHFL.STUHFL_D_PROFILE_EUROPE)
    else:
        channelList = STUHFL.STUHFL_T_ST25RU3993_ChannelList()
        channelList.numFrequencies = 1;
        channelList.itemList[0].frequency = STUHFL.STUHFL_D_DEFAULT_FREQUENCY;
    channelList.antenna = antenna;
    channelList.persistent = False;
    channelList.channelListIdx = 0;
    channelList.commit()

    freqHop = STUHFL.STUHFL_T_ST25RU3993_FreqHop()
    freqHop.maxSendingTime = 400;
    freqHop.minSendingTime = 400;
    freqHop.mode = STUHFL.STUHFL_D_FREQUENCY_HOP_MODE_IGNORE_MIN;
    freqHop.commit();

    gen2Select = STUHFL.STUHFL_T_Gen2_Select()
    gen2Select.mode = STUHFL.STUHFL_D_GEN2_SELECT_MODE_CLEAR_LIST
    gen2Select.execute()

    # Eventually Tune the channel lists
    demo_TuneChannelList(tuningAlgo);

    return


def demo_TuneChannelList(tuningAlgo):
    if (tuningAlgo == STUHFL.STUHFL_D_TUNING_ALGO_NONE):
        return

    txRxCfg = STUHFL.STUHFL_T_ST25RU3993_TxRxCfg()
    txRxCfg.fetch()

    channelList = STUHFL.STUHFL_T_ST25RU3993_ChannelList()
    channelList.persistent = False
    channelList.antenna = txRxCfg.usedAntenna
    channelList.fetch()       # Retrieve ChannelLists already configured in FW

    channelList.falsePositiveDetection = True
    channelList.persistent = False
    channelList.algorithm = tuningAlgo
    channelList.tune()      # Tune all Channels

    # Prints all ChannelList
    channelList.fetch()
    return


class CycleData(STUHFL.ICycleData):
    def cycleCallback(self, data):
        global tags

        # print EPC list
        for i, tag in enumerate(data.tagList):
            tagepc = ''
            for j, val in enumerate(tag.epc):
                tagepc += "{:02x}".format(val)

            if tagepc not in tags:
                tags.append(tagepc)

        return STUHFL.STUHFL_ERR_NONE

    def finishedCallback(self, data):
        #clear()
        # print statistics summary
        global tags
        return STUHFL.STUHFL_ERR_NONE


def detect(rounds):
    singleTag = False
    demo_SetupGen2Config(singleTag, True, STUHFL.STUHFL_D_ANTENNA_1, STUHFL.STUHFL_D_TUNING_ALGO_MEDIUM)

    cycleData = CycleData(1024)  # Define callbacks + set max 1024 tags inventoried at once
    inventory = STUHFL.STUHFL_T_Gen2_Inventory(cycleData)
    inventory.options = STUHFL.STUHFL_D_INVENTORYREPORT_OPTION_HEARTBEAT
    inventory.start(rounds)
    return tags


if __name__ == '__main__':
    detect(500)
    print(tags)
    print('did this for some reason')
