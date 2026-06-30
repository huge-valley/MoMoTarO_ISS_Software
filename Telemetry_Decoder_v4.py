import os
import pandas as pd
import uproot

#super class
class TD_SUPER:
    def __init__(self):
        self.PACKET_SIZE = 3600 #1800 word
        self.hk_data = None
        self.event_data = None
        self.shape_data = None
        self.event_only_data = None
   
    def to_root(self, output_filename):
        with uproot.recreate(output_filename) as root_file:
            if self.hk_data is not None and not self.hk_data.empty:
                root_file["HK"] = self.hk_data
                print(f"Wrote HK tree -> {len(self.hk_data)} entries")
                
            if self.event_data is not None and not self.event_data.empty:
                root_file["EVENT"] = self.event_data
                print(f"Wrote EVENT tree -> {len(self.event_data)} entries")
                
            if self.shape_data is not None and not self.shape_data.empty:
                root_file["SHAPE"] = self.shape_data
                print(f"Wrote SHAPE tree -> {len(self.shape_data)} entries")

            if self.event_only_data is not None and not self.event_only_data.empty:
                root_file["EVENT_ONLY"] = self.event_only_data
                print(f"Wrote EVENT_ONLY tree -> {len(self.event_only_data)} entries")    
            
        print(f"saved to {output_filename}")

    

     

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
        gps_stat = (others >> 14) & 0x03
        flag_daq = (others >> 13) & 0x01
        flag_spre = (others >> 12) & 0x01
        flag_sensor = f"{(others >> 4) & 0xFF:08b}"
        pi_mode = (others >> 2) & 0x03
        reserved = f"{others & 0x03:02b}"
        row['Others_DEC'] = int(f"{gps_stat}{flag_daq}{flag_spre}{flag_sensor}{pi_mode}{reserved}")

        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')
        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 wordVoltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big') 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')
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
                row[f'SiPM{i}_Voltage_Reference'] = int.from_bytes(chunk[832+i*2:834+i*2], byteorder='big') * 100

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
        gps_stat = (others >> 14) & 0x03
        flag_daq = (others >> 13) & 0x01
        flag_spre = (others >> 12) & 0x01
        flag_sensor = f"{(others >> 4) & 0xFF:08b}"
        pi_mode = (others >> 2) & 0x03
        reserved = f"{others & 0x03:02b}"
        row['Others_DEC'] = int(f"{gps_stat}{flag_daq}{flag_spre}{flag_sensor}{pi_mode}{reserved}")

        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')
        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 wordVoltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big') 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')
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


    def read_EVENT(self, filename):
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
        gps_stat = (others >> 14) & 0x03
        flag_daq = (others >> 13) & 0x01
        flag_spre = (others >> 12) & 0x01
        flag_sensor = f"{(others >> 4) & 0xFF:08b}"
        pi_mode = (others >> 2) & 0x03
        reserved = f"{others & 0x03:02b}"
        row['Others_DEC'] = int(f"{gps_stat}{flag_daq}{flag_spre}{flag_sensor}{pi_mode}{reserved}")

        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')
        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 wordVoltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big') 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')
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
    def read_SHAPE(self, filename):
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
        gps_stat = (others >> 14) & 0x03
        flag_daq = (others >> 13) & 0x01
        flag_spre = (others >> 12) & 0x01
        flag_sensor = f"{(others >> 4) & 0xFF:08b}"
        pi_mode = (others >> 2) & 0x03
        reserved = f"{others & 0x03:02b}"
        row['Others_DEC'] = int(f"{gps_stat}{flag_daq}{flag_spre}{flag_sensor}{pi_mode}{reserved}")

        #22 word DSizeSD
        # print(chunk[42:44].hex())
        row['DSizeSD'] = int.from_bytes(chunk[42:44], byteorder='big')
        # print(row['DSizeSD'])

        #23 word Voltage_MoMoTarO
        # print(chunk[44:46].hex())
        row['Voltage_MoMoTarO'] = int.from_bytes(chunk[44:46], byteorder='big')
        # print(row['Voltage_MoMoTarO'])

        #24 word Current_MoMoTarO
        # print(chunk[46:48].hex())
        row['Current_MoMoTarO'] = int.from_bytes(chunk[46:48], byteorder='big')
        # print(row['Current_MoMoTarO'])

        #25 word Voltage_InterfaceMCU
        row['Voltage_InterfaceMCU'] = int.from_bytes(chunk[48:50], byteorder='big')

        #26 word Temp_InterfaceMCU 
        #hex cd48
        #bin 5215.2 ここからしたがおかしい？
        # print(chunk[50:52].hex())
        row['Temp_InterfaceMCU'] = int.from_bytes(chunk[50:52], byteorder='big')
        # print((row['Temp_InterfaceMCU']-400)/10)

        #27 wordVoltage_DAQFEC
        # print(chunk[52:54].hex())
        row['Voltage_DAQFEC'] = int.from_bytes(chunk[52:54], byteorder='big')
        # print(row['Voltage_DAQFEC'])
        
        #28 wordCurrent_DAQFEC
        # print(chunk[54:56].hex())
        row['Current_DAQFEC'] = int.from_bytes(chunk[54:56], byteorder='big')
        # print(row['Current_DAQFEC'])

        #29 word Voltage_DAQMCU 
        # print(chunk[56:58].hex())
        row['Voltage_DAQMCU'] = int.from_bytes(chunk[56:58], byteorder='big')
        # print(row['Voltage_DAQMCU'])

        #30 word Temp_DAQMCU
        row['Temp_DAQMCU'] = int.from_bytes(chunk[58:60], byteorder='big')
        
        #31-38 word Voltage_SiPM
        for i in range(8):
            # print(chunk[60+i*2:62+i*2].hex())
            row[f'Voltage_SiPM{i}'] = int.from_bytes(chunk[60+i*2:62+i*2], byteorder='big')
            # print(row[f'Voltage_SiPM{i}'])

        #39-46 word Current_SiPM
        for i in range(8):
            row[f'Current_SiPM{i}'] = int.from_bytes(chunk[76+i*2:78+i*2], byteorder='big') 
            # print(row[f'Current_SiPM{i}'])

        #47-54 word Temp_SiPM
        for i in range(8):
            row[f'Temp_SiPM{i}'] = int.from_bytes(chunk[92+i*2:94+i*2], byteorder='big')
            # print(row[f'Temp_SiPM{i}'])

        #55-62 word Temp_Ch
        #ここはch8-15でいいのか？
        for i in range(8):
            row[f'Temp_Ch{i+8}'] = int.from_bytes(chunk[108+  i*2:110+i*2], byteorder='big')
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


    def read_EVENT(self, filename):
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

    
     

if __name__ == "__main__":
    d = TD_CONFIG()
    # d = TD_EVENT()
    input_path = '../data/'
    # filename = '20251112130402_MoMoTarO.hex'
    filename = '20260619_132027.dat'
    # filename = '20260619_161107.dat'

    
    df = d.read_HK(input_path + filename)
    pd.set_option("display.max_columns", None)  
    print(df)

    # df_EVT = d.read_EVENT(input_path + filename)
    # print(df_EVT)