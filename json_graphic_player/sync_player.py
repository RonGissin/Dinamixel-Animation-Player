import time
import json
import math
import sys

from dynamixel_sdk import *

GOALPOS = 30
CURRPOS = 36
MOVINGSP = 32
GOAL_ACC = 73
TORQUE_E = 24
ENGINE_DICT = {"base": 1, "dome": 2}
packetHandler = PacketHandler(1.0)
# portHandler = PortHandler('/dev/ttyACM0')
portHandler = PortHandler('COM7')


def init():
    portHandler.openPort()
    portHandler.setBaudRate(1000000)
    # torque enable both engines
    packetHandler.write1ByteTxRx(portHandler, 1, 24, 0)
    packetHandler.write1ByteTxRx(portHandler, 2, 24, 0)
    # move both motors to starting pos
    packetHandler.write2ByteTxRx(portHandler, ENGINE_DICT["base"], GOALPOS, 0)
    packetHandler.write2ByteTxRx(portHandler, ENGINE_DICT["dome"], GOALPOS, 0)
    time.sleep(5)
    # slow down engines to 10 MV
    packetHandler.write2ByteTxRx(portHandler, ENGINE_DICT["base"], MOVINGSP, 30)
    packetHandler.write2ByteTxRx(portHandler, ENGINE_DICT["dome"], MOVINGSP, 30)


def read_write():
    # get json file name from user
    # print("please enter the name of the json file you wish to run !")
    json_file = str(sys.argv[1])

    # get dict from json graphic file
    dict_file = get_dict_from_json(json_file)

    action = dict_file["action"]
    if not action:
        print("The json isn't formatted correctly !\n"
              "please make sure the ACTION attribute is valid")
        exit()
    if action.lower() == "gtp":
        run_gtp(dict_file["args"])
    elif action.lower() == "animate":
        interval = dict_file["args"]["interval"]
        if not interval:
            print("couldn't read interval from json.")
            exit()
        frame_list = dict_file["args"]["frame_list"]
        if not frame_list:
            print("couldn't read frame list from json.")
            exit()
        run_graphic(interval, frame_list)
    else:
        print("ACTION attribute is not valid in json file")
        exit()


def convert_radians_to_dynamixel_pos(radians):
    return int(math.degrees(float(radians)) / 0.088)


def run_graphic(interval, frame_list):
    pos_packets = []
    base_positions = []
    dome_positions = []
    for frame in frame_list:
        base_item = next(item for item in frame["positions"] if item["dof"] == "base")
        dome_item = next(item for item in frame["positions"] if item["dof"] == "dome")
        goal_base_pos_radians = base_item["pos"]
        goal_dome_pos_radians = dome_item["pos"]
        # convert the positions to degrees and normalize to dynamixels 0.088x0 format
        goal_base_pos_dynamixel = convert_radians_to_dynamixel_pos(goal_base_pos_radians)
        goal_dome_pos_dynamixel = convert_radians_to_dynamixel_pos(goal_dome_pos_radians)
        curr_packet = GroupSyncWrite(portHandler, packetHandler, GOALPOS, 2)
        param_goal_position_base = [DXL_LOBYTE(DXL_LOWORD(goal_base_pos_dynamixel)),
                                    DXL_HIBYTE(DXL_LOWORD(goal_base_pos_dynamixel))]
        param_goal_position_dome = [DXL_LOBYTE(DXL_LOWORD(goal_dome_pos_dynamixel)),
                                    DXL_HIBYTE(DXL_LOWORD(goal_dome_pos_dynamixel))]
        curr_packet.addParam(ENGINE_DICT["base"], param_goal_position_base)
        curr_packet.addParam(ENGINE_DICT["dome"], param_goal_position_dome)
        # base_positions.append(goal_base_pos_dynamixel)
        # dome_positions.append(goal_dome_pos_dynamixel)
        pos_packets.append(curr_packet)
        print(curr_packet)

    # print("base positions\n\n\n")
    # print(*base_positions)
    # print("dome positions\n\n\n")
    # print(*dome_positions)

    for packet in pos_packets:
        packet.txPacket()
        time.sleep(interval / 1000)
        # print("moving 1")
        # move_engine_to_position(ENGINE_DICT["base"], base_positions[i])
        # packetHandler.write2ByteTxRx(portHandler, ENGINE_DICT["base"], GOALPOS, base_positions[i])
        # print("moving 2")
        # move_engine_to_position(ENGINE_DICT["dome"], dome_positions[i])
        # packetHandler.write2ByteTxRx(portHandler, ENGINE_DICT["dome"], GOALPOS, dome_positions[i])


def run_gtp(positions_dict):
    packet = GroupSyncWrite(portHandler, packetHandler, GOALPOS, 2)
    for engine_id, position in positions_dict.items():
        goal_pos = convert_radians_to_dynamixel_pos(position)
        print(goal_pos)
        goal_pos_param = [DXL_LOBYTE(DXL_LOWORD(goal_pos)),
                          DXL_HIBYTE(DXL_LOWORD(goal_pos))]
        add_result = packet.addParam(engine_id, goal_pos_param)
        print(add_result)
        print(f"moving engine number {engine_id}")
    packet.txPacket()

        # move_engine_to_position(int(engine_id), goal_pos)
        # packetHandler.write2ByteTxRx(portHandler, int(engine_id), GOALPOS, position)



def get_dict_from_json(json_file):
    with open(json_file, "r") as read_file:
        if not read_file:
            return None
        return json.load(read_file)


def move_engine_to_position(engine_id, position):
    packetHandler.write2ByteTxRx(portHandler, engine_id, GOALPOS, position)


# def move_engines_to_json_positions():
#     with open("engine_positions.json", "r") as read_file:
#         pos_list = list(json.load(read_file))
#     pos_list.reverse()
#     print(pos_list)
#
#     for pos in pos_list:
#         print("moving 1")
#         packetHandler.write2ByteTxRx(portHandler, 1, GOALPOS, pos["1"])
#         print("moving 2")
#         packetHandler.write2ByteTxRx(portHandler, 2, GOALPOS, pos["2"])
#         time.sleep(1)
#     print(packetHandler.read2ByteTxRx(portHandler, 1, 36))
#     print(packetHandler.read2ByteTxRx(portHandler, 2, 36))


def main():
    init()
    read_write()


main()
