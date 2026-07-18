
#system
import os
import sys

#Decoder
import pandas as pd
import uproot
from datetime import datetime

#VISUALIZER
import ROOT
import matplotlib.pyplot as plt #matplot
import matplotlib.cm as cm      #to draw colormap
import copy                     #to copy the colorbar

#EXAMPLE
import glob




#super class
class TD_SUPER:
    def __init__(self):
        self.PACKET_SIZE = 3600 #1800 word
        self.hk_data = None
        self.event_data = None
        self.shape_data = None
        self.event_only_data = None
    

    def init(self,filename):
        with open(filename, 'rb') as file:
            chunk = file.read(self.PACKET_SIZE)
            # if not chunk or len(chunk) < self.PACKET_SIZE:
            #     break

         #21 word Others_DEC
        others = int.from_bytes(chunk[40:42], byteorder='big')
        # SiPM3 = (others >> 14) & 0x01
        # SiPM2 = (others >> 13) & 0x01
        # SiPM1 = (others >> 12) & 0x01
        # SiPM0 = (others >> 11) & 0x01
        # daq = (others >> 9) & 0x01
        PImode = (others >> 4) & 0x03
        # SiPM7 = (others >> 3) & 0x01
        # SiPM6 = (others >> 2) & 0x01
        # SiPM5 = (others >> 1) & 0x01
        # SiPM4 = others & 0x01
        # print(int(f"{SiPM3}{SiPM2}{SiPM1}{SiPM0}{daq}{PImode}{SiPM7}{SiPM6}{SiPM5}{SiPM4}"))
        return PImode
        # row['Others_DEC'] = int(f"{gps_stat}{flag_daq}{flag_spre}{flag_sensor}{pi_mode}{reserved}")
        
   
    def to_root(self, df_dict ,output_filename):
        with uproot.recreate(output_filename) as root_file:
            for tree_name, df in df_dict.items():
                if df is not None and not df.empty:
                    branch_types = {col: df[col].dtype for col in df.columns}
                    root_file.mktree(tree_name, branch_types)
                    
                    data_dict = {col: df[col].values for col in df.columns}
                    root_file[tree_name].extend(data_dict)
                    
                    print(f"Wrote {tree_name} tree  {len(df)} entries") 
                    
        print(f"saved to {output_filename}")

    def time(self, DIR):

        base = os.path.basename(DIR)
        filename, _ = os.path.splitext(base)
        date_format = '%Y%m%d_%H%M%S'

        time = datetime.strptime(filename, date_format)
        # print(int(time.timestamp())) #unix_time
        return time
     

class TD_CONFIG(TD_SUPER):
    def read_HK(self, filename):
        parsed_data = []
        #read 1800 words onece
        with open(filename, 'rb') as file:
            chunk = file.read(self.PACKET_SIZE)
            # if not chunk or len(chunk) < self.PACKET_SIZE:
            #     break
            
        row = {}

        '''HK'''
        #1-2 word PacketNum_MoMoTarO + Status
        pc_num_st = int.from_bytes(chunk[0:4], byteorder='big')
        row['PcNum'] = (pc_num_st >> 6) & 0x3FFFFFF
        row['Status'] = hex(pc_num_st & 0x3F) #to hex

        #3-4 word Packet 
        row['TimeCounter_Packet'] = int.from_bytes(chunk[4:8], byteorder='big')
        #5-6  TimeCounters
        row['TimeCounter_GPS'] = int.from_bytes(chunk[8:12], byteorder='big')

        #7-9 word GPS_UnixTime_DEC
        y, m, d, h, mn, s = chunk[12:18]
        # print(y)  
        row['GPS_UnixTime_DEC'] = int(f"{y}{m}{d}{h}{mn}{s}")

        #10-12 word GPS_UnixTimeSbs_HEX
        row['GPS_UnixTimeSbs_HEX'] = chunk[18:24].hex()

        #13-20 word GPS_Longitude, Lattitude
        row['longitude'] = int.from_bytes(chunk[24:32], byteorder='big')
        row['lattitude'] = int.from_bytes(chunk[32:40], byteorder='big')

        #21 word Others_DEC
        others = int.from_bytes(chunk[40:42], byteorder='big')
        SiPM3 = (others >> 14) & 0x01
        SiPM2 = (others >> 13) & 0x01
        SiPM1 = (others >> 12) & 0x01
        SiPM0 = (others >> 11) & 0x01
        daq = (others >> 9) & 0x01
        PImode = (others >> 4) & 0x03
        SiPM7 = (others >> 3) & 0x01
        SiPM6 = (others >> 2) & 0x01
        SiPM5 = (others >> 1) & 0x01
        SiPM4 = others & 0x01
        row['Others_DEC'] = int(f"{SiPM3}{SiPM2}{SiPM1}{SiPM0}{daq}{PImode}{SiPM7}{SiPM6}{SiPM5}{SiPM4}")


        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')/100
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')/10
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')/100

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')/10 -300
        # row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52])

        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 wordVoltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')/100
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')/10
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')/100
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')/10 -300
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')/100
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big')/10 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_Ch{i}'])

        #63-70 word Pedestal_Ch
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Pedestal_Ch{i+8}'] = int.from_bytes(chunk[124+i*2:126+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #71 word TrigEnable_Event, TrigEnable_Shape
        row['TrigEnable_Event'] = int.from_bytes(chunk[140:141], byteorder='big')
        row['TrigEnable_Shape'] = int.from_bytes(chunk[141:142], byteorder='big')

        #72 word AnticoNum, DeltaTCut  
        row['AnticoNum'] = int.from_bytes(chunk[142:143], byteorder='big') & 0xE0 # 0xE0 = 11100000
        row['DeltaTCut'] = int.from_bytes(chunk[143:144], byteorder='big') 
        
        #73 word AntiHitPattern, DownlinkHitPattern
        row['AntiHitPattern'] = int.from_bytes(chunk[144:145], byteorder='big') 
        row['DownlinkHitPattern'] = int.from_bytes(chunk[145:146], byteorder='big') 

        #74 word RawCount_Total
        row['RawCount_Total'] = int.from_bytes(chunk[146:148], byteorder='big')

        #75-82 word RawCount_Ch
        for i in range(8):
            row[f'RawCount_Ch{i}'] = int.from_bytes(chunk[148+i*2:150+i*2], byteorder='big')

        #83-90 word Rejected_Anti_Ch
        for i in range(8):
            row[f'Rejected_Anti_Ch{i}'] = int.from_bytes(chunk[164+i*2:166+i*2], byteorder='big')

        #91-98 word Rejected_Shape_Ch
        for i in range(8):
            row[f'Rejected_Shape_Ch{i}'] = int.from_bytes(chunk[180+i*2:182+i*2], byteorder='big')

        #99-226 word Count_Ch0_ADC
        for i in range(8):
            #99-114 word Count_Ch0_ADC{j}
            #115-130 word Count_Ch1_ADC{j}
            #...
            #211-226 word Count_Ch7_ADC{j}
            # j = 0
            for j in range(16):
                row[f'Count_Ch{i}_ADC{j}'] = int.from_bytes(chunk[196+i*32+j*2:198+i*32+j*2], byteorder='big')

        #227-338 word Count_Ch_PSD / not for ch0=GAGG
        for i in range(7):
            #227-242 word Count_Ch1_ADC{j}
            #243-258 word Count_Ch2_ADC{j}
            #...
            #323-338 word Count_Ch7_ADC{j}
            # j = 0
            for j in range(16):
                row[f'Count_Ch{i+1}_PSD{j}'] = int.from_bytes(chunk[452+i*32+j*2:454+i*32+j*2], byteorder='big')
        
        #339-363 word Ch0 LC bin
        for i in range(25):
                row[f'Count_Ch0_LC_T{i}'] = int.from_bytes(chunk[676+i*2:678+i*2], byteorder='big')
        
        #364-370 word Ch0 LC bin
        for i in range(7):                     
                row[f'Count_Ch0_LC_T{i+25}'] = int.from_bytes(chunk[726+i*2:728+i*2], byteorder='big')

        #371-374 word Reserved
        # row['Reserved'] = int.from_bytes(chunk[740:748], byteorder='big')

        '''config'''
        #375-382 word Ch{i}_DACoffset masked Upper 12bit
        for i in range(8):                     
                row[f'Ch{i}_DACoffset'] = int.from_bytes(chunk[748+i*2:750+i*2], byteorder='big') & 0xFFF0
        
        #383-390 word Ch{i}_Trig_Threshold masked Upper 12bit
        for i in range(8):                     
                row[f'Ch{i}_Trig_Threshold'] = int.from_bytes(chunk[764+i*2:766+i*2], byteorder='big') & 0xFFF0

        #391-398 word Ch{i}_Ready_Threshold masked Upper 12bit
        for i in range(8):                     
                row[f'Ch{i}_Ready_Threshold'] = int.from_bytes(chunk[780+i*2:782+i*2], byteorder='big') & 0xFFF0

        #399 word SampleNum_{Front,Back}
        row[f'SampleNum_Front'] = int.from_bytes(chunk[796:797], byteorder='big')
        row[f'SampleNum_Back'] = int.from_bytes(chunk[797:798], byteorder='big')
        
        #400-407 word Ch{i}_SampleNum_StartTotal/StartTail (check)
        for i in range(8):
            row[f'Ch{i}_SampleNum_StartTotal'] = int.from_bytes(chunk[798+i*2:799+i*2], byteorder='big')
            row[f'Ch{i}_SampleNum_StartTail'] = int.from_bytes(chunk[799+i*2:800+i*2], byteorder='big')
        
        #408-415 word Ch{i}_SampleNum_Stop/Hold (check)
        for i in range(8):
            row[f'Ch{i}_SampleNum_Stop'] = int.from_bytes(chunk[814+i*2:815+i*2], byteorder='big')
            row[f'Ch{i}_SampleNum_Hold'] = int.from_bytes(chunk[815+i*2:816+i*2], byteorder='big')

        #416 word SiPM?_Voltage_OnOff , only upper 8bit
        row[f'SiPM_Voltage_OnOff'] = int.from_bytes(chunk[830:832], byteorder='big') >> 8 
        # row['Reserved'] = int.from_bytes(chunk[831:832], byteorder='big')

        #417-424 word SiPM{i}_Voltage_Reference /V
        for i in range(8):                     
                row[f'SiPM{i}_Voltage_Reference'] = int.from_bytes(chunk[832+i*2:834+i*2], byteorder='big') /100

        #425-432 word SiPM{i}_TempCorr_Slope/ mV
        for i in range(8):                     
                row[f'SiPM{i}_TempCorr_Slope'] = int.from_bytes(chunk[848+i*2:850+i*2], byteorder='big')

        #433-436 word SiPM{i}_AMPGain
        for i in range(8):
                row[f'SiPM{i}_AMPGain'] = int.from_bytes(chunk[864+i:865+i], byteorder='big')
                
        #437-444 word Ch{i}_Antico_ADCthreshold
        for i in range(8):
                row[f'Ch{i}_Antico_ADCthreshold'] = int.from_bytes(chunk[872+i*2:874+i*2], byteorder='big') >> 4
        
        #445-572 word Ch{i}_Threshold_ADC{j} , Null
        for i in range(8):
                for j in range(16):
                    row[f'Ch{i}_Threshold_ADC{j}'] = int.from_bytes(chunk[888+i*32+j*2:890+i*32+j*2], byteorder='big') >> 4
        
        #573-588 word Ch{i}_PSDhist_Min/Max 
        for i in range(8):
                #ch0 : 573-574 word
                #ch1 : 575-576 word
                #...
                #ch1 : 586-588 word
                row[f'Ch{i}_PSDhist_Min'] = int.from_bytes(chunk[1144+i*4:1146+i*4], byteorder='big') >> 4
                row[f'Ch{i}_PSDhist_Max'] = int.from_bytes(chunk[1146+i*4:1148+i*4], byteorder='big') >> 4
                
        #589-716 word Ch{i}_Threshold_ADC{j} , Null
        for i in range(8):
            #589-604 word Ch0_Threshold_ADC{j}
            #...
            #589-604 word Ch0_Threshold_ADC{j}
                for j in range(16):
                    row[f'Ch{i}_Threshold_ADC{j}'] = int.from_bytes(chunk[1176+i*32+j*2:1178+i*32+j*2], byteorder='big') >> 6
            
            # break

        parsed_data.append(row)

        self.hk_data = pd.DataFrame(parsed_data)
        return self.hk_data
    


class TD_EVENT(TD_SUPER):
    def read_HK(self, filename):
        parsed_data = []
        
        with open(filename, 'rb') as file:
            # while True:
            chunk = file.read(self.PACKET_SIZE)
            # if not chunk or len(chunk) < self.PACKET_SIZE:
            #     break
        
        row = {}

        '''HK'''
        #1-2 word PacketNum_MoMoTarO + Status
        pc_num_st = int.from_bytes(chunk[0:4], byteorder='big')
        row['PcNum'] = (pc_num_st >> 6) & 0x3FFFFFF
        row['Status'] = hex(pc_num_st & 0x3F) #to hex

        #3-4 word Packet 
        row['TimeCounter_Packet'] = int.from_bytes(chunk[4:8], byteorder='big')
        #5-6  TimeCounters
        row['TimeCounter_GPS'] = int.from_bytes(chunk[8:12], byteorder='big')

        #7-9 word GPS_UnixTime_DEC
        y, m, d, h, mn, s = chunk[12:18]
        # print(y)
        row['GPS_UnixTime_DEC'] = int(f"{y}{m}{d}{h}{mn}{s}")

        #10-12 word GPS_UnixTimeSbs_HEX
        row['GPS_UnixTimeSbs_HEX'] = chunk[18:24].hex()

        #13-20 word GPS_Longitude, Lattitude
        row['longitude'] = int.from_bytes(chunk[24:32], byteorder='big')
        row['lattitude'] = int.from_bytes(chunk[32:40], byteorder='big')

        #21 word Others_DEC
        others = int.from_bytes(chunk[40:42], byteorder='big')
        SiPM3 = (others >> 14) & 0x01
        SiPM2 = (others >> 13) & 0x01
        SiPM1 = (others >> 12) & 0x01
        SiPM0 = (others >> 11) & 0x01
        daq = (others >> 9) & 0x01
        PImode = (others >> 4) & 0x03
        SiPM7 = (others >> 3) & 0x01
        SiPM6 = (others >> 2) & 0x01
        SiPM5 = (others >> 1) & 0x01
        SiPM4 = others & 0x01
        row['Others_DEC'] = int(f"{SiPM3}{SiPM2}{SiPM1}{SiPM0}{daq}{PImode}{SiPM7}{SiPM6}{SiPM5}{SiPM4}")

        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')/100
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')/10
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')/100

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')/10 - 300   
        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 word Voltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')/100
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')/10
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')/100
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')/10 -300
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')/100
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big')/10 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_Ch{i}'])

        #63-70 word Pedestal_Ch
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Pedestal_Ch{i+8}'] = int.from_bytes(chunk[124+i*2:126+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #71 word TrigEnable_Event, TrigEnable_Shape
        row['TrigEnable_Event'] = int.from_bytes(chunk[140:141], byteorder='big')
        row['TrigEnable_Shape'] = int.from_bytes(chunk[141:142], byteorder='big')

        #72 word AnticoNum, DeltaTCut  
        row['AnticoNum'] = int.from_bytes(chunk[142:143], byteorder='big') & 0xE0 # 0xE0 = 11100000
        row['DeltaTCut'] = int.from_bytes(chunk[143:144], byteorder='big') 
        
        #73 word AntiHitPattern, DownlinkHitPattern
        row['AntiHitPattern'] = int.from_bytes(chunk[144:145], byteorder='big') 
        row['DownlinkHitPattern'] = int.from_bytes(chunk[145:146], byteorder='big') 

        #74 word RawCount_Total
        row['RawCount_Total'] = int.from_bytes(chunk[146:148], byteorder='big')

        #75-82 word RawCount_Ch
        for i in range(8):
            row[f'RawCount_Ch{i}'] = int.from_bytes(chunk[148+i*2:150+i*2], byteorder='big')

        #83-90 word Rejected_Anti_Ch
        for i in range(8):
            row[f'Rejected_Anti_Ch{i}'] = int.from_bytes(chunk[164+i*2:166+i*2], byteorder='big')

        #91-98 word Rejected_Shape_Ch
        for i in range(8):
            row[f'Rejected_Shape_Ch{i}'] = int.from_bytes(chunk[180+i*2:182+i*2], byteorder='big')

        #99-226 word Count_Ch0_ADC
        for i in range(8):
            #99-114 word Count_Ch0_ADC{j}
            #115-130 word Count_Ch1_ADC{j}
            #...
            #211-226 word Count_Ch7_ADC{j}
            # j = 0
            for j in range(16):
                row[f'Count_Ch{i}_ADC{j}'] = int.from_bytes(chunk[196+i*32+j*2:198+i*32+j*2], byteorder='big')

        #227-338 word Count_Ch_PSD / not for ch0=GAGG
        for i in range(7):
            #227-242 word Count_Ch1_ADC{j}
            #243-258 word Count_Ch2_ADC{j}
            #...
            #323-338 word Count_Ch7_ADC{j}
            # j = 0
            for j in range(16):
                row[f'Count_Ch{i+1}_PSD{j}'] = int.from_bytes(chunk[452+i*32+j*2:454+i*32+j*2], byteorder='big')
        
        #339-363 word Ch0 LC bin
        for i in range(25):
                row[f'Count_Ch0_LC_T{i}'] = int.from_bytes(chunk[676+i*2:678+i*2], byteorder='big')
        
        #364-370 word Ch0 LC bin
        for i in range(7):                     
                row[f'Count_Ch0_LC_T{i+25}'] = int.from_bytes(chunk[726+i*2:728+i*2], byteorder='big')

        #371-374 word Reserved
        # row['Reserved'] = int.from_bytes(chunk[740:748], byteorder='big')
        parsed_data.append(row)
        self.hk_data = pd.DataFrame(parsed_data)
        return self.hk_data


    def read_PI(self, filename):
        parsed_data = []
        
        with open(filename, 'rb') as file:
            # read 1 packet -> chunk
            chunk = file.read(self.PACKET_SIZE)
            
        #375-377 word entry0 -> 
        #378-380 word entry1
        #...
        offset = 748
        
        # 3 word/event = 6 byte/event
        EVENT_BYTE_SIZE = 6
        
        #entry[event_id]
        event_id = 0  
        
        #check if there is one more event : 6 bytes
        while offset + EVENT_BYTE_SIZE <= len(chunk):
            
            #create row event by event
            row = {
                'event_id': event_id
            }
            
            
            event_bytes = chunk[offset : offset + EVENT_BYTE_SIZE]
            tmp = int.from_bytes(event_bytes, byteorder='big')
            if tmp == 0:
                 break
            #get 6 bytes
            #event[0] -> tmp = int.from_bytes(chunk[748:754], byteorder='big')
            #event[1] -> tmp = int.from_bytes(chunk[754:760], byteorder='big')
            #...

            
            row['TrigCh'] = (tmp >> 45) & 0x07        # Upper 3 bit masked
            row['ADC'] = (tmp >> 33) & 0x0FFF         # Upper 15 bit masked Lower 12 bit
            row['PSD'] = (tmp >> 23) & 0x03FF         # Upper 26 bit masked Lower 10 bit
            row['TimeCounter'] = tmp & 0x7FFFFF       # Full bit masked Lower 23 bit
            
            parsed_data.append(row)
            
            #for next entry
            event_id += 1
            offset += EVENT_BYTE_SIZE

        self.event_data = pd.DataFrame(parsed_data)
        return self.event_data
    

class TD_SHAPE(TD_SUPER):
    def read_HK(self, filename):
        parsed_data = []
        
        with open(filename, 'rb') as file:
            # while True:
            chunk = file.read(self.PACKET_SIZE)
            # if not chunk or len(chunk) < self.PACKET_SIZE:
            #     break
            
        row = {}

        '''HK'''
        #1-2 word PacketNum_MoMoTarO + Status
        pc_num_st = int.from_bytes(chunk[0:4], byteorder='big')
        row['PcNum'] = (pc_num_st >> 6) & 0x3FFFFFF
        row['Status'] = hex(pc_num_st & 0x3F) #to hex

        #3-4 word Packet 
        row['TimeCounter_Packet'] = int.from_bytes(chunk[4:8], byteorder='big')
        #5-6  TimeCounters
        row['TimeCounter_GPS'] = int.from_bytes(chunk[8:12], byteorder='big')

        #7-9 word GPS_UnixTime_DEC
        y, m, d, h, mn, s = chunk[12:18]
        # print(y)
        row['GPS_UnixTime_DEC'] = int(f"{y}{m}{d}{h}{mn}{s}")

        #10-12 word GPS_UnixTimeSbs_HEX
        row['GPS_UnixTimeSbs_HEX'] = chunk[18:24].hex()

        #13-20 word GPS_Longitude, Lattitude
        row['longitude'] = int.from_bytes(chunk[24:32], byteorder='big')
        row['lattitude'] = int.from_bytes(chunk[32:40], byteorder='big')

        #21 word Others_DEC
        others = int.from_bytes(chunk[40:42], byteorder='big')
        SiPM3 = (others >> 14) & 0x01
        SiPM2 = (others >> 13) & 0x01
        SiPM1 = (others >> 12) & 0x01
        SiPM0 = (others >> 11) & 0x01
        daq = (others >> 9) & 0x01
        PImode = (others >> 4) & 0x03
        SiPM7 = (others >> 3) & 0x01
        SiPM6 = (others >> 2) & 0x01
        SiPM5 = (others >> 1) & 0x01
        SiPM4 = others & 0x01
        row['Others_DEC'] = int(f"{SiPM3}{SiPM2}{SiPM1}{SiPM0}{daq}{PImode}{SiPM7}{SiPM6}{SiPM5}{SiPM4}")

        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')/100
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')/10
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')/100

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')/10 -300   
        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 wordVoltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')/100
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')/10
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')/100
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')/10 -300
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')/100
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big')/10 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_Ch{i}'])

        #63-70 word Pedestal_Ch
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Pedestal_Ch{i+8}'] = int.from_bytes(chunk[124+i*2:126+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #71 word TrigEnable_Event, TrigEnable_Shape
        row['TrigEnable_Event'] = int.from_bytes(chunk[140:141], byteorder='big')
        row['TrigEnable_Shape'] = int.from_bytes(chunk[141:142], byteorder='big')

        #72 word AnticoNum, DeltaTCut  
        row['AnticoNum'] = int.from_bytes(chunk[142:143], byteorder='big') & 0xE0 # 0xE0 = 11100000
        row['DeltaTCut'] = int.from_bytes(chunk[143:144], byteorder='big') 
        
        #73 word AntiHitPattern, DownlinkHitPattern
        row['AntiHitPattern'] = int.from_bytes(chunk[144:145], byteorder='big') 
        row['DownlinkHitPattern'] = int.from_bytes(chunk[145:146], byteorder='big') 

        #74 word RawCount_Total
        row['RawCount_Total'] = int.from_bytes(chunk[146:148], byteorder='big')

        #75-82 word RawCount_Ch
        for i in range(8):
            row[f'RawCount_Ch{i}'] = int.from_bytes(chunk[148+i*2:150+i*2], byteorder='big')

        #83-90 word Rejected_Anti_Ch
        for i in range(8):
            row[f'Rejected_Anti_Ch{i}'] = int.from_bytes(chunk[164+i*2:166+i*2], byteorder='big')

        #91-98 word Rejected_Shape_Ch
        for i in range(8):
            row[f'Rejected_Shape_Ch{i}'] = int.from_bytes(chunk[180+i*2:182+i*2], byteorder='big')

        
        #99 word Reserved
        row['Reserved'] = int.from_bytes(chunk[196:198], byteorder='big')
        parsed_data.append(row)
        self.hk_data = pd.DataFrame(parsed_data)
        return self.hk_data

    '''SHAPE'''
    def read_PI(self, filename):
            parsed_data = []
            
            #100 sample/ch/event x 8 ch = 800 sample/event = 800 word/event
            
            with open(filename, 'rb') as file:
                chunk = file.read(self.PACKET_SIZE)  

            event_id = 0  # entry
            offset = 0    # readed bytes
            EVENT_BYTE_SIZE = 1600 # bytes

            #entry[event_id][sample]
            
            #check if there is one more event : 1600 bytes
            while offset + EVENT_BYTE_SIZE <= len(chunk):
                
                #data starts at 100 word = 198 bytes for entry0
                #data starts at 900 word = 1600 + 198 bytes  bytes for entry1
                data_start_offset = offset + 198
                
                #100 samples/event
                for sample in range(100):
                    row = {
                        'entry_id': event_id,
                        'sample_id': sample
                    }
                    
                    # ADCs for 8 ch
                    for ch in range(8):
                        #sample starts at byte_pos
                        #read 16 bytes/sample, 2 bytes/ch
                        byte_pos = data_start_offset + (sample * 8 + ch) * 2
                        word_bytes = chunk[byte_pos : byte_pos + 2]
                        tmp = int.from_bytes(word_bytes, byteorder='big') >> 1
                        if tmp == 0:
                            break

                        row['Trigger Ch'] = (tmp >> 12) & 0x07 
                        row[f'ADC'] = tmp & 0x0FFF
                        
                        #example:
                        #100-899 word entry0
                        # entry[0][0]['ch0'] -> tmp = int.from_bytes(chunk[198:200], byteorder='big') >> 1
                        #   entry[0][0]['ch1'] -> tmp = int.from_bytes(chunk[200:202], byteorder='big') >> 1
                        #       entry[0][0]['ch2'] -> tmp = int.from_bytes(chunk[202:204], byteorder='big') >> 1
                        #       ...
                        #       entry[0][0]['ch7'] -> tmp = int.from_bytes(chunk[214:216], byteorder='big') >> 1
                        # entry[0][1]['ch0'] -> tmp = int.from_bytes(chunk[216:218], byteorder='big') >> 1
                        #   entry[0][1]['ch1'] -> tmp = int.from_bytes(chunk[218:220], byteorder='big') >> 1
                        #       entry[0][1]['ch2'] -> tmp = int.from_bytes(chunk[220:222], byteorder='big') >> 1
                        #       ...
                        #       entry[0][1]['ch7'] -> tmp = int.from_bytes(chunk[228:230], byteorder='big') >> 1
                        # ...
                        #       entry[0][99]['ch7'] -> tmp = int.from_bytes(chunk[1796:1798], byteorder='big') >> 1
                        #900-1699 word entry1
                        # entry[1][0]['ch0'] -> tmp = int.from_bytes(chunk[1798:1800], byteorder='big') >> 1
                        # ...
                        # entry[1][100]['ch7'] -> tmp = int.from_bytes(chunk[3396:3398], byteorder='big') >> 1
                    
                    parsed_data.append(row)
                
                #next entry
                event_id += 1
                offset += EVENT_BYTE_SIZE
                            
            self.shape_data = pd.DataFrame(parsed_data)
            return self.shape_data
    


class TD_EVENT_ONLY(TD_SUPER):
    def read_HK(self, filename):
        parsed_data = []
        
        with open(filename, 'rb') as file:
            # while True:
            chunk = file.read(self.PACKET_SIZE)
            # if not chunk or len(chunk) < self.PACKET_SIZE:
            #     break
            
        row = {}

        '''HK'''
        #1-2 word PacketNum_MoMoTarO + Status
        pc_num_st = int.from_bytes(chunk[0:4], byteorder='big')
        row['PcNum'] = (pc_num_st >> 6) & 0x3FFFFFF
        row['Status'] = hex(pc_num_st & 0x3F) #to hex

        #3-4 word Packet 
        row['TimeCounter_Packet'] = int.from_bytes(chunk[4:8], byteorder='big')
        #5-6  TimeCounters
        row['TimeCounter_GPS'] = int.from_bytes(chunk[8:12], byteorder='big')

        #7-9 word GPS_UnixTime_DEC
        y, m, d, h, mn, s = chunk[12:18]
        # print(y)
        row['GPS_UnixTime_DEC'] = int(f"{y}{m}{d}{h}{mn}{s}")

        #10-12 word GPS_UnixTimeSbs_HEX
        row['GPS_UnixTimeSbs_HEX'] = chunk[18:24].hex()

        #13-20 word GPS_Longitude, Lattitude
        row['longitude'] = int.from_bytes(chunk[24:32], byteorder='big')
        row['lattitude'] = int.from_bytes(chunk[32:40], byteorder='big')

        #21 word Others_DEC
        others = int.from_bytes(chunk[40:42], byteorder='big')
        SiPM3 = (others >> 14) & 0x01
        SiPM2 = (others >> 13) & 0x01
        SiPM1 = (others >> 12) & 0x01
        SiPM0 = (others >> 11) & 0x01
        daq = (others >> 9) & 0x01
        PImode = (others >> 4) & 0x03
        SiPM7 = (others >> 3) & 0x01
        SiPM6 = (others >> 2) & 0x01
        SiPM5 = (others >> 1) & 0x01
        SiPM4 = others & 0x01
        row['Others_DEC'] = int(f"{SiPM3}{SiPM2}{SiPM1}{SiPM0}{daq}{PImode}{SiPM7}{SiPM6}{SiPM5}{SiPM4}")

        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')/100
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')/10
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')/100

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')/10 -300   
        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 wordVoltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')/100
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')/10
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')/100
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')/10 -300
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')/100
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big')/10 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')/10 -300
            # print(row[f'Temp_Ch{i}'])

        #63-70 word Pedestal_Ch
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Pedestal_Ch{i+8}'] = int.from_bytes(chunk[124+i*2:126+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #71 word TrigEnable_Event, TrigEnable_Shape
        row['TrigEnable_Event'] = int.from_bytes(chunk[140:141], byteorder='big')
        row['TrigEnable_Shape'] = int.from_bytes(chunk[141:142], byteorder='big')

        #72 word AnticoNum, DeltaTCut  
        row['AnticoNum'] = int.from_bytes(chunk[142:143], byteorder='big') & 0xE0 # 0xE0 = 11100000
        row['DeltaTCut'] = int.from_bytes(chunk[143:144], byteorder='big') 
        
        #73 word AntiHitPattern, DownlinkHitPattern
        row['AntiHitPattern'] = int.from_bytes(chunk[144:145], byteorder='big') 
        row['DownlinkHitPattern'] = int.from_bytes(chunk[145:146], byteorder='big') 

        #74 word RawCount_Total
        row['RawCount_Total'] = int.from_bytes(chunk[146:148], byteorder='big')

        #75-82 word RawCount_Ch
        for i in range(8):
            row[f'RawCount_Ch{i}'] = int.from_bytes(chunk[148+i*2:150+i*2], byteorder='big')

        #83-90 word Rejected_Anti_Ch
        for i in range(8):
            row[f'Rejected_Anti_Ch{i}'] = int.from_bytes(chunk[164+i*2:166+i*2], byteorder='big')

        #91-98 word Rejected_Shape_Ch
        for i in range(8):
            row[f'Rejected_Shape_Ch{i}'] = int.from_bytes(chunk[180+i*2:182+i*2], byteorder='big')

        
        #99 word Reserved
        row['Reserved'] = int.from_bytes(chunk[196:198], byteorder='big')
        parsed_data.append(row)
        self.hk_data = pd.DataFrame(parsed_data)
        return self.hk_data


    def read_PI(self, filename):
        parsed_data = []
        
        with open(filename, 'rb') as file:
            # read 1 packet -> chunk
            chunk = file.read(self.PACKET_SIZE)
            
        #100-101 word entry0 
        #102-103 word entry1
        #...
        offset = 198
        
        # 3 word/event = 6 byte/event
        EVENT_BYTE_SIZE = 2
        
        #entry[event_id]
        event_id = 0  
        
        #check if there is one more event : 6 bytes
        while offset + EVENT_BYTE_SIZE <= len(chunk):
            
            #create row event by event
            row = {
                'event_id': event_id
            }
            
            
            event_bytes = chunk[offset : offset + EVENT_BYTE_SIZE]
            tmp = int.from_bytes(event_bytes, byteorder='big')
            if tmp == 0:
                    break
            #get 6 bytes
            #event[0] -> tmp = int.from_bytes(chunk[198:200], byteorder='big')
            #event[1] -> tmp = int.from_bytes(chunk[202:204], byteorder='big')
            #...
            
            row['TrigCh'] = (tmp >> 29) & 0x07        # Upper 3 bit masked
            row['ADC'] = (tmp >> 17) & 0x0FFF         # Upper 15 bit masked Lower 12 bit
            row['PSD'] = (tmp >> 7) & 0x03FF         # Upper 25 bit masked Lower 10 bit
            row['TimeCounter'] = tmp & 0x7F       # Full bit masked Lower 7 bit
            
            parsed_data.append(row)
            
            #for next entry
            event_id += 1
            offset += EVENT_BYTE_SIZE

        self.event_only_data = pd.DataFrame(parsed_data)
        return self.event_only_data

#additional
class VISUALIZER:
     def __init__(self):
        pass
     
     def PSD(self, phas, psds, each_binx, each_biny):
        cmap = copy.copy(cm.viridis)
        cmap.set_under('w',1) 
        binx = int(4096/each_binx)                                     
        biny = int((max(psds)-min(psds))/each_biny)             

        fig = plt.figure()
        ax = fig.add_subplot(111)
        Hist = ax.hist2d(phas, psds,bins=(binx,biny),cmap=cmap) 
        ax.set_xlim(0,4095)
        ax.set_ylim(500,700)
        ax.minorticks_on()
        ax.tick_params(axis="both", which='major', direction='in', length=5) 
        ax.tick_params(axis="both", which='minor', direction='in', length=3) 
        ax.set_title('PSD vs ADC')
        ax.set_xlabel('ADC (channel)')
        ax.set_ylabel('PSD')
        c_bar=fig.colorbar(Hist[3],ax=ax)
        Hist[3].set_clim(1,200)                                             
        # ax.legend()
        # plt.xticks(rotation=45)

        return ax

class EXAMPLE:
    def __init__(self):
         pass
    
    #example1 -> 
    def ex1(self, DIR):
        if sp.init(DIR) == 0:
            print('config')
            d = TD_CONFIG()

        elif sp.init(DIR) == 1:
            print('event')
            d = TD_EVENT()
            df_pi = d.read_PI(DIR)

        elif sp.init(DIR) == 2:
            print('shape')
            d = TD_SHAPE()
            df_pi = d.read_PI(DIR)

        elif sp.init(DIR) == 3:
            print('event_only_mode')
            d = TD_EVENT_ONLY()
            df_pi = d.read_PI(DIR)

        else:
            print('exit status 1')
            sys.exit()


        df_HK = d.read_HK(DIR)
        df_HK['Unix_Time'] = d.time(DIR).timestamp() #Unix_Time
        pd.set_option("display.max_rows", None)  
        pd.set_option("display.max_columns", None)  
        print(df_HK)

        if not __debug__:
            print(df_pi)

    #example2 -> make 1 h file
    def ex2(self, ipath, opath, yyyy, mm, dd, hh):
        files = glob.glob(f'{ipath}/{yyyy}{mm:02}{dd:02}_{hh:02}*.dat')
        # print(files)
        
        df_EVENT = pd.DataFrame()
        df_SHAPE = pd.DataFrame()
        df_EVENT_ONLY = pd.DataFrame()

        for filename in files:
            DIR = filename
            
            if sp.init(DIR) == 0:
                print('config')
                d = TD_CONFIG()

            elif sp.init(DIR) == 1:
                print('event')
                d = TD_EVENT()
                df_pi = d.read_PI(DIR)
                df_pi['Unix_Time'] = d.time(DIR).timestamp() #Unix_Time
                df_EVENT = pd.concat([df_EVENT, df_pi], ignore_index=True)


            elif sp.init(DIR) == 2:
                print('shape')
                d = TD_SHAPE()
                df_pi = d.read_PI(DIR)
                df_pi['Unix_Time'] = d.time(DIR).timestamp() #Unix_Time
                df_SHAPE = pd.concat([df_SHAPE, df_pi], ignore_index=True)


            elif sp.init(DIR) == 3:
                print('event_only_mode')
                d = TD_EVENT_ONLY()
                df_pi = d.read_PI(DIR)
                df_pi['Unix_Time'] = d.time(DIR).timestamp() #Unix_Time
                df_EVENT_ONLY = pd.concat([df_EVENT_ONLY, df_pi], ignore_index=True)

            else:
                print('exit status 1')
                sys.exit()

        data_to_save = {
            "EVENT": df_EVENT,
            "SHAPE": df_SHAPE,
            "EVENT_ONLY": df_EVENT_ONLY
        }

        os.makedirs(opath,exist_ok=True)
        output_file = f"{opath}/{yyyy}{mm:02}{dd:02}_{hh:02}.root"
        sp.to_root(data_to_save, output_file)
    
    #make 1 hour hk csv file 
    def ex3(self, ipath, opath, yyyy, mm, dd, hh):
        files = glob.glob(f'{ipath}/{yyyy}{mm:02}{dd:02}_{hh:02}*.dat')
        # print(files)
        
        df_HK = pd.DataFrame()

        for filename in files:
            DIR = filename
            
            if sp.init(DIR) == 0:
                print('config')
                d = TD_CONFIG()
                df_hk = d.read_HK(DIR)
                df_hk['time'] = d.time(DIR)

            elif sp.init(DIR) == 1:
                print('event')
                d = TD_EVENT()
                df_hk = d.read_HK(DIR)
                df_hk['time'] = d.time(DIR) 

            elif sp.init(DIR) == 2:
                print('shape')
                d = TD_SHAPE()
                df_hk = d.read_HK(DIR)
                df_hk['time'] = d.time(DIR)

            elif sp.init(DIR) == 3:
                print('event_only_mode')
                d = TD_EVENT_ONLY()
                df_hk = d.read_HK(DIR)
                df_hk['time'] = d.time(DIR)

            else:
                print('exit status 1')
                sys.exit()
            df_HK = pd.concat([df_HK, df_hk], ignore_index=True)

        df_HK = df_HK.set_index('PcNum')
        df_HK = df_HK.sort_index()
        # print('hello')

        os.makedirs(opath,exist_ok=True)
        output_file = f"{yyyy}{mm:02}{dd:02}_{hh:02}.csv"
        df_HK.to_csv(f'{opath}/{output_file}')
    

if __name__ == "__main__":
    sp = TD_SUPER()
    e = EXAMPLE()
    input_path = '../data/Telemetry_test'
    root_output_path = '../data/root'
    hk_output_path = '../data/HK'


    # filename = '20260703_150746.dat' #config
    # filename = '20260703_150830.dat' #event
    filename = '20260703_150959.dat' #shape
    # filename = '20260703_151012.dat' #event_only


    DIR = input_path + '/' + filename
    e.ex1(DIR)
    e.ex2(input_path, root_output_path, 2026, 7,3, 15)
    e.ex3(input_path, hk_output_path ,2026, 7,3, 15)
    
    

   


    

