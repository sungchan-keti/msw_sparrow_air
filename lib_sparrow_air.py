#!/usr/bin/python3
import json, sys, serial, threading, time
import paho.mqtt.client as mqtt

argv = sys.argv

global lib_topic
global lib_mqtt_client

global missionPort
global airQ

missionPort = None
airQ = dict()
airQ['PM2.5'] = 0.0 # (ug/m3)
airQ['PM10'] = 0.0 # (ug/m3)
airQ['CO'] = 0.0 # (ppb)
airQ['NO2'] = 0.0 # (ppb)
airQ['O3_org'] = 0.0 # (org/ppb)
airQ['O3_comp'] = 0.0 # (comp/ppb)
airQ['SO2_org'] = 0.0 # (org/ppb)
airQ['SO2_comp'] = 0.0 # (comp/ppb)
airQ['T'] = 0.0 # (C)
airQ['H'] = 0.0 # (%)
airQ['NO2_OP1'] = 0 # (mV)
airQ['NO2_OP2'] = 0 # (mV)
airQ['O3_OP1'] = 0 # (mV)
airQ['O3_OP2'] = 0 # (mV)
airQ['CO_OP1'] = 0 # (mV)
airQ['CO_OP2'] = 0 # (mV)
airQ['SO2_OP1'] = 0 # (mV)
airQ['SO2_OP2'] = 0 # (mV)

def on_connect(client,userdata,flags, rc):
    print('[msw_mqtt_connect] connect to ', broker_ip)
    sub_container_name = lib['control'][0]
    control_topic = '/MUV/control/' + lib['name'] + '/' + sub_container_name
    lib_mqtt_client.subscribe(control_topic, 0) 
    print ('[lib]control_topic\n', control_topic)


def on_disconnect(client, userdata, flags, rc=0):
	print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    global missionPort

    message = str(msg.payload.decode("utf-8"))
    if (message == 'G'):
        print ('call on_receive_from_msw function')
        on_receive_from_msw(message)
    

def on_receive_from_msw(str_message):
    global missionPort
    print ('start on_receive_from_msw function')
    if missionPort is not None:
        print ('missionPort is not None')
        if missionPort.is_open:
            print ('missionPort is open')
            setcmd = b'G'
            print('setcmd: ', setcmd)
            missionPort.write(setcmd)


def msw_mqtt_connect(broker_ip, port):
    global lib_topic
    global lib_mqtt_client

    lib_topic = ''

    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_subscribe = on_subscribe
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    lib_mqtt_client.loop_start()
    return lib_mqtt_client


def missionPortOpening(missionPortNum, missionBaudrate):
    global airQ
    global lib
    global missionPort

    if (missionPort == None):
        try:
            missionPort = serial.Serial(missionPortNum, missionBaudrate, timeout = 2)
            print ('missionPort open. ' + missionPortNum + ' Data rate: ' + missionBaudrate)
            mission_thread = threading.Thread(
                target=missionPortData, args=(missionPort, )
            )
            mission_thread.start()

            return missionPort

        except serial.SerialException as e:
            missionPortError(e)
        except TypeError as e:
            missionPortClose()
    else:
        if (missionPort.is_open == False):
            missionPortOpen()

            # airQ.rssi = -Math.random()*100;
            container_name = lib["data"]
            data_topic = '/MUV/data/' + lib["name"] + '/' + container_name
            send_data_to_msw(data_topic, airQ)

def missionPortOpen():
    print('missionPort open!')
    missionPort.open()

def missionPortClose():
    global missionPort
    print('missionPort closed!')
    missionPort.close()


def missionPortError(err):
    print('[missionPort error]: ', err)


def airReqMessage(missionPort):
    if missionPort is not None:
        if missionPort.is_open:
            setcmd = b'I'
            missionPort.write(setcmd)

def send_data_to_msw (data_topic, obj_data):
    global lib_mqtt_client
    
    lib_mqtt_client.publish(data_topic, obj_data)


def missionPortData(missionPort):
    global airQ
    # airQ = dict()
    airReqMessage(missionPort)
    flag = 0
    while True:
        missionStr = missionPort.readlines()
        print('missionStr\n', missionStr)
        # try:
        #     if (flag == 0):
        #         data = missionStr[3].split(',')
        #         print('data:', data)
        #         flag = 1
        # except ValueError:
        #     airReqMessage(missionPort)

        try:
            if ((not missionStr) or (missionStr[0] == b'\x00\n') or (len(missionStr) < 3)):
                # airReqMessage(missionPort)
                flag = 0
            else:
                if (flag == 0):
                    flag = 1
                    arrAIRQ = missionStr[3].decode("utf-8").split(", ")
                    print('arrAIRQ1: ', arrAIRQ)
                    arrQValue = arrAIRQ[0].split(',')
                    print('arrQValue1: ', arrQValue)
                    airQ['PM2.5'] = float(arrQValue[0]) # (ug/m3)
                    airQ['PM10'] = float(arrQValue[1]) # (ug/m3)
                    airQ['CO'] = float(arrQValue[2]) # (ppb)
                    airQ['NO2'] = float(arrQValue[3]) # (ppb)
                    airQ['O3_org'] = float(arrQValue[4]) # (org/ppb)
                    airQ['O3_comp'] = float(arrQValue[5]) # (comp/ppb)
                    airQ['SO2_org'] = float(arrQValue[6]) # (org/ppb)
                    airQ['SO2_comp'] = float(arrQValue[7]) # (comp/ppb)
                    airQ['T'] = float(arrQValue[8]) # (C)
                    airQ['H'] = float(arrQValue[9]) # (%)
                    airQ['NO2_OP1'] = int(arrAIRQ[1]) # (mV)
                    airQ['NO2_OP2'] = int(arrAIRQ[2]) # (mV)
                    airQ['O3_OP1'] = int(arrAIRQ[3]) # (mV)
                    airQ['O3_OP2'] = int(arrAIRQ[4]) # (mV)
                    airQ['CO_OP1'] = int(arrAIRQ[5]) # (mV)
                    airQ['CO_OP2'] = int(arrAIRQ[6]) # (mV)
                    airQ['SO2_OP1'] = int(arrAIRQ[7]) # (mV)
                    airQ['SO2_OP2'] = int(arrAIRQ[8]) # (mV)
                    container_name = lib["data"][0]
                    data_topic = '/MUV/data/' + lib["name"] + '/' + container_name
                    airQ = json.dumps(airQ)
                    send_data_to_msw(data_topic, airQ)
                else:
                    if (len(missionStr) > 1):
                        arrAIRQ = missionStr[0].decode("utf-8").split(", ")
                        print('arrAIRQ2: ', arrAIRQ)
                        arrQValue = arrAIRQ[0].split(',')
                        print('arrQValue2: ', arrQValue)
                        airQ['PM2.5'] = float(arrQValue[0]) # (ug/m3)
                        airQ['PM10'] = float(arrQValue[1]) # (ug/m3)
                        airQ['CO'] = float(arrQValue[2]) # (ppb)
                        airQ['NO2'] = float(arrQValue[3]) # (ppb)
                        airQ['O3_org'] = float(arrQValue[4]) # (org/ppb)
                        airQ['O3_comp'] = float(arrQValue[5]) # (comp/ppb)
                        airQ['SO2_org'] = float(arrQValue[6]) # (org/ppb)
                        airQ['SO2_comp'] = float(arrQValue[7]) # (comp/ppb)
                        airQ['T'] = float(arrQValue[8]) # (C)
                        airQ['H'] = float(arrQValue[9]) # (%)
                        airQ['NO2_OP1'] = int(arrAIRQ[1]) # (mV)
                        airQ['NO2_OP2'] = int(arrAIRQ[2]) # (mV)
                        airQ['O3_OP1'] = int(arrAIRQ[3]) # (mV)
                        airQ['O3_OP2'] = int(arrAIRQ[4]) # (mV)
                        airQ['CO_OP1'] = int(arrAIRQ[5]) # (mV)
                        airQ['CO_OP2'] = int(arrAIRQ[6]) # (mV)
                        airQ['SO2_OP1'] = int(arrAIRQ[7]) # (mV)
                        airQ['SO2_OP2'] = int(arrAIRQ[8]) # (mV)
                        container_name = lib["data"][0]
                        data_topic = '/MUV/data/' + lib["name"] + '/' + container_name
                        airQ = json.dumps(airQ)
                        send_data_to_msw(data_topic, airQ)
                        
                        airQ = dict()
                        arrAIRQ = missionStr[1].decode("utf-8").split(", ")
                        print('arrAIRQ3: ', arrAIRQ)
                        arrQValue = arrAIRQ[0].split(',')
                        print('arrQValue3: ', arrQValue)
                        airQ['PM2.5'] = float(arrQValue[0]) # (ug/m3)
                        airQ['PM10'] = float(arrQValue[1]) # (ug/m3)
                        airQ['CO'] = float(arrQValue[2]) # (ppb)
                        airQ['NO2'] = float(arrQValue[3]) # (ppb)
                        airQ['O3_org'] = float(arrQValue[4]) # (org/ppb)
                        airQ['O3_comp'] = float(arrQValue[5]) # (comp/ppb)
                        airQ['SO2_org'] = float(arrQValue[6]) # (org/ppb)
                        airQ['SO2_comp'] = float(arrQValue[7]) # (comp/ppb)
                        airQ['T'] = float(arrQValue[8]) # (C)
                        airQ['H'] = float(arrQValue[9]) # (%)
                        airQ['NO2_OP1'] = int(arrAIRQ[1]) # (mV)
                        airQ['NO2_OP2'] = int(arrAIRQ[2]) # (mV)
                        airQ['O3_OP1'] = int(arrAIRQ[3]) # (mV)
                        airQ['O3_OP2'] = int(arrAIRQ[4]) # (mV)
                        airQ['CO_OP1'] = int(arrAIRQ[5]) # (mV)
                        airQ['CO_OP2'] = int(arrAIRQ[6]) # (mV)
                        airQ['SO2_OP1'] = int(arrAIRQ[7]) # (mV)
                        airQ['SO2_OP2'] = int(arrAIRQ[8]) # (mV)
                        container_name = lib["data"][0]
                        data_topic = '/MUV/data/' + lib["name"] + '/' + container_name
                        airQ = json.dumps(airQ)
                        send_data_to_msw(data_topic, airQ)
                    else:
                        arrAIRQ = missionStr[0].decode("utf-8").split(", ")
                        print('arrAIRQ4: ', arrAIRQ)
                        arrQValue = arrAIRQ[0].split(',')
                        print('arrQValue4: ', arrQValue)
                        airQ['PM2.5'] = float(arrQValue[0]) # (ug/m3)
                        airQ['PM10'] = float(arrQValue[1]) # (ug/m3)
                        airQ['CO'] = float(arrQValue[2]) # (ppb)
                        airQ['NO2'] = float(arrQValue[3]) # (ppb)
                        airQ['O3_org'] = float(arrQValue[4]) # (org/ppb)
                        airQ['O3_comp'] = float(arrQValue[5]) # (comp/ppb)
                        airQ['SO2_org'] = float(arrQValue[6]) # (org/ppb)
                        airQ['SO2_comp'] = float(arrQValue[7]) # (comp/ppb)
                        airQ['T'] = float(arrQValue[8]) # (C)
                        airQ['H'] = float(arrQValue[9]) # (%)
                        airQ['NO2_OP1'] = int(arrAIRQ[1]) # (mV)
                        airQ['NO2_OP2'] = int(arrAIRQ[2]) # (mV)
                        airQ['O3_OP1'] = int(arrAIRQ[3]) # (mV)
                        airQ['O3_OP2'] = int(arrAIRQ[4]) # (mV)
                        airQ['CO_OP1'] = int(arrAIRQ[5]) # (mV)
                        airQ['CO_OP2'] = int(arrAIRQ[6]) # (mV)
                        airQ['SO2_OP1'] = int(arrAIRQ[7]) # (mV)
                        airQ['SO2_OP2'] = int(arrAIRQ[8]) # (mV)
                        container_name = lib["data"][0]
                        data_topic = '/MUV/data/' + lib["name"] + '/' + container_name
                        airQ = json.dumps(airQ)
                        send_data_to_msw(data_topic, airQ)
                        
        except ValueError:
            airReqMessage(missionPort)
            pass

        # airQ = dict()
        # time.sleep(10)


if __name__ == '__main__':
    my_lib_name = 'lib_sparrow_air'

    try:
        lib = dict()
        with open(my_lib_name + '.json', 'r') as f:
            lib = json.load(f)
            lib = json.loads(lib)

    except:
        lib = dict()
        lib["name"] = my_lib_name
        lib["target"] = 'armv6'
        lib["description"] = "[name] [portnum] [baudrate]"
        lib["scripts"] = './' + my_lib_name + ' /dev/ttyUSB4 115200'
        lib["data"] = ['AIR']
        lib["control"] = ['Control_AIR']
        lib = json.dumps(lib, indent=4)
        lib = json.loads(lib)

        with open('./' + my_lib_name + '.json', 'w', encoding='utf-8') as json_file:
            json.dump(lib, json_file, indent=4)


    lib['serialPortNum'] = argv[1]
    lib['serialBaudrate'] = argv[2]

    broker_ip = 'localhost'
    port = 1883

    msw_mqtt_connect(broker_ip, port)

    missionPortNum = lib["serialPortNum"]
    missionBaudrate = lib["serialBaudrate"]
    missionPortOpening(missionPortNum, missionBaudrate)
