import time
from enum import Enum

import bluesky.plan_stubs as bps
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

# TIMEOUT in seconds, should be declared elsewhere
ISARA_TIMEOUT = 100


class IsaraRobotDevice(Device):
    class Tool(int, Enum):  # int enum is necessary in python 3.11+?
        TOOLCHANGER = 0
        CRYOTONG = 1
        SINGLEGRIPPER = 2
        DOUBLEGRIPPER = 3
        MINISPINEGRIPPER = 4
        ROTATINGGRIPPER = 5
        PLATEGRIPPER = 6
        SPARE = 7
        LASERTOOL = 8

    # Commands
    # Generic command channels
    # power
    power_on = Cpt(EpicsSignal, "Pwr:On-Cmd")
    power_off = Cpt(EpicsSignal, "Pwr:Off-Cmd")

    # arm movement speed
    speed_up = Cpt(EpicsSignal, "Spd:Up-Cmd")
    speed_down = Cpt(EpicsSignal, "Spd:Dn-Cmd")
    # 0 - 100
    speed_setpoint = Cpt(EpicsSignal, "Speed-SP")

    # heater
    heater_on = Cpt(EpicsSignal, "Htr:On-Cmd")
    heater_off = Cpt(EpicsSignal, "Htr:Off-Cmd")

    # dewar lid
    dewar_lid_open = Cpt(EpicsSignal, "Lid:Opn-Cmd")
    dewar_lid_close = Cpt(EpicsSignal, "Lid:Cls-Cmd")

    # gripper a
    gripper_a_open = Cpt(EpicsSignal, "OpnA-Cmd")
    gripper_a_close = Cpt(EpicsSignal, "ClsA-Cmd")

    # gripper b
    gripper_b_open = Cpt(EpicsSignal, "OpnB-Cmd")
    gripper_b_close = Cpt(EpicsSignal, "ClsB-Cmd")

    # Trajectories
    # write 1 to start move
    # trajectory arguments are defined by the robot software
    # we provide all arguments by setting a corresponding argument PV before issuing the move

    # Home Trajectory
    #  required arguments
    #     tool_selected
    home_traj = Cpt(EpicsSignal, "Move:Home-Cmd", put_complete=True)

    # Recover Trajectory
    #  required arguments
    #     tool_selected
    recover_traj = Cpt(EpicsSignal, "Move:Rcvr-Cmd", put_complete=True)

    # Get Trajectory
    #   required arguments
    #     tool_selected
    get_traj = Cpt(EpicsSignal, "Move:Get-Cmd", put_complete=True)

    # Put Trajectory
    #   required arguments:
    #     tool_selected
    #     puck_num_sel
    #     sample_num_sel
    #   optional arguments:
    #     puck_next_num_sel
    #     sample_next_num_sel
    put_traj = Cpt(EpicsSignal, "Move:Put-Cmd", put_complete=True)

    # GetPut Trajectory
    #   required arguments:
    #     tool_selected
    #     puck_num_sel
    #     sample_num_sel
    #   optional arguments:
    #     puck_next_num_sel
    #     sample_next_num_sel
    getput_traj = Cpt(EpicsSignal, "Move:GetPut-Cmd", put_complete=True)

    # Back Trajectory
    #   required arguments
    #     tool_selected
    back_traj = Cpt(EpicsSignal, "Move:Bck-Cmd", put_complete=True)

    # Dry Trajectory
    #   required arguments
    #     tool_selected
    dry_traj = Cpt(EpicsSignal, "Move:Dry-Cmd", put_complete=True)

    # Soak Trajectory
    #   required arguments
    #     tool_selected
    soak_traj = Cpt(EpicsSignal, "Move:Sk-Cmd", put_complete=True)

    # Pick Trajectory
    #   required arguments
    #     tool_selected
    #     puck_num_sel
    #     sample_num_sel
    pick_traj = Cpt(EpicsSignal, "Move:Pck-Cmd", put_complete=True)

    # Uses the Tool Enum to define the intended tool for a trajectory
    # NYX currently only has DoubleGripper
    tool_selected = Cpt(EpicsSignal, "Tl-Sel")

    # limits 1-29
    # argument is interchangeable for puck/plate selection field
    # "next" is used for the queueing function of the doublegripper
    puck_num_sel = Cpt(EpicsSignal, "Plt-SP", put_complete=True)
    puck_next_num_sel = Cpt(EpicsSignal, "Plt:N-SP", put_complete=True)

    # limits 1-16
    # "next" is used for the queueing function of the doublegripper
    sample_num_sel = Cpt(EpicsSignal, "Samp-SP", put_complete=True)
    samp_next_num_sel = Cpt(EpicsSignal, "Samp:N-SP", put_complete=True)

    # 0 = "Skip"
    # 1 = "Scan"
    dm_selected = Cpt(EpicsSignal, "DM-Sel", put_complete=True)

    # Statuses

    # interface from denso, try to maintain types
    # int
    # status

    # bool
    # busy_sts

    # bool
    # mount_ready_sts

    # is mounting bool
    # mounting_sts

    # is dismounting bool
    # dismounting_sts

    # is drying bool
    # 0 = "Idle"
    # 1 = "Drying"
    drying_sts = Cpt(EpicsSignalRO, "GripDry-Sts")

    # new
    # 0 = "Hold off"
    # 1 = "Permit"
    drying_permitted_sts = Cpt(EpicsSignalRO, "DryPmt-I")

    # spindle occupied bool
    spindle_occupied_sts = Cpt(EpicsSignalRO, "Samp:Dif-Sts")

    # New statuses for ISARA

    # Last Message
    last_message = Cpt(EpicsSignalRO, "LastMsg-I")

    # Fault Status
    # 0 = "Ok"
    # 1 = "Fault"
    fault_sts = Cpt(EpicsSignalRO, "Flt-Sts")

    # Alarm Status
    # TODO: What does this return?
    alarm_sts = Cpt(EpicsSignalRO, "Alarm-I")

    # Current Position
    # SOAK
    # HOME
    position_sts = Cpt(EpicsSignalRO, "Pos:Name-I")

    # Moving Status
    # 0 = "Stopped"
    # 1 = "Moving"
    moving_sts = Cpt(EpicsSignalRO, "Seq:Run-Sts")

    # Paused Status
    # 0 = "Normal"
    # 1 = "Paused"
    paused_sts = Cpt(EpicsSignalRO, "Seq:Paus-Sts")

    # Speed Status
    speed_sts = Cpt(EpicsSignalRO, "Speed-I")

    current_tool = Cpt(EpicsSignal, "Tl-I")

    # Power status
    # 0 = "Off"
    # 1 = "On"
    power_sts = Cpt(EpicsSignalRO, "Pwr-Sts")

    # Occupied statuses
    # 0 = "Empty"
    # 1 = "Present"
    samp_a_occ_sts = Cpt(EpicsSignalRO, "Samp:A-Sts")
    samp_b_occ_sts = Cpt(EpicsSignalRO, "Samp:B-Sts")
    samp_dif_occ_sts = Cpt(EpicsSignalRO, "Samp:Dif-Sts")

    # Gripper Statuses
    # 0 = "Open"
    # 1 = "Closed"
    grip_a_sts = Cpt(EpicsSignalRO, "Grp:A-Sts")
    grip_b_sts = Cpt(EpicsSignalRO, "Grp:B-Sts")

    # Samples occupying gripper/spindle
    # returns 1-29
    # returns -1 if empty
    puck_a_read = Cpt(EpicsSignalRO, "Pck:A-I")
    puck_b_read = Cpt(EpicsSignalRO, "Pck:B-I")
    puck_dif_read = Cpt(EpicsSignalRO, "Pck:Dif-I")

    # returns 1-16
    # returns -1 if empty
    samp_a_read = Cpt(EpicsSignalRO, "Samp:A-I")
    samp_b_read = Cpt(EpicsSignalRO, "Samp:B-I")
    samp_dif_read = Cpt(EpicsSignalRO, "Samp:Dif-I")

    def dryGripper(self):
        self.dry_traj.set(1)

    def movement_ready(self):
        if not self.power_sts.get():
            return [False, "Power is off"]
        if self.moving_sts.get():
            return [False, "Moving"]
        if self.paused_sts.get():
            return [False, "Paused"]
        return [True, "movement ready"]

    def parkRobot(self):
        # Robot powers on before movement
        print("Parking Robot, in ophyd")
        if not self.power_sts.get():
            self.power_on.put(1)  # , settle_time=1)
            time.sleep(3)
            if not self.power_sts.get():
                raise RuntimeError(f"Failed to power robot on before move: {self.power_sts.get()}")

        if self.current_tool.get() != self.tool_selected.get():
            raise ValueError(f"Bad tool argument:  {self.current_tool.get()}, {self.tool_selected.get()}")

        # Check spindle occupied, then dismount sample
        if self.spindle_occupied_sts.get():
            print("spindle occupied")
            get_traj_status = self.get_traj.set(1)
            get_traj_status.wait(ISARA_TIMEOUT)
            if not get_traj_status.success:
                raise RuntimeError("get trajectory failed during park robot")
            else:
                print(f"get traj status: {get_traj_status}")
        else:
            print("spindle not occupied")

        # Check if gripper is occupied, then return samples to dewar
        if self.samp_a_occ_sts.get() == 1 or self.samp_b_occ_sts.get() == 1:
            print("gripper occupied")
            back_traj_status = self.back_traj.set(1)
            back_traj_status.wait(ISARA_TIMEOUT)
            if not back_traj_status.success:
                raise RuntimeError("back trajectory failed during park robot")
            else:
                print(f"back traj status: {back_traj_status}")

        # Check if gripper drying is allowed, then dry
        if self.drying_permitted_sts.get():
            print("drying permitted")
            if self.position_sts.get() != "SOAK":
                soak_traj_status = self.soak_traj.set(1)
                soak_traj_status.wait()
            dry_traj_status = self.dry_traj.set(1)
            time.sleep(120.0)
            print(f"dry traj status: {dry_traj_status}")
            # dry_traj_status.wait(ISARA_TIMEOUT*2)
            # if not dry_traj_status.success:
            #    raise RuntimeError("drying trajectory failed during park robot")
        else:
            print("dry not permitted, skipping")
            self.homeRobot()
            print("robot homed")
            # robot goes home after dry is finished, we go home when skipping

        # Close Dewar Lid
        print("closing dewar lid")
        dewar_lid_close_sts = self.dewar_lid_close.set(1)
        dewar_lid_close_sts.wait(ISARA_TIMEOUT)
        if not dewar_lid_close_sts.success:
            raise RuntimeError("dewar lid failed to close during park robot")
        else:
            print(f"dewar lid close status: {dewar_lid_close_sts}")

        # Robot power off
        print("powering off")
        self.power_off.put(1)  # , settle_time=1)
        time.sleep(3)
        if self.power_sts.get():
            raise RuntimeError("Robot failed to power off during park robot")
        else:
            return True

    def recoverRobot(self):
        if self.current_tool.get() != self.tool_selected.get():
            raise ValueError(f"Bad tool argument:  {self.current_tool.get()}, {self.tool_selected.get()}")
        traj_status = self.recover_traj.set(1)
        traj_status.wait(ISARA_TIMEOUT)
        return traj_status.success

    def finish():
        pass

    def homeRobot(self):
        if self.current_tool.get() != self.tool_selected.get():
            raise ValueError(f"Bad tool argument:  {self.current_tool.get()}, {self.tool_selected.get()}")
        traj_status = self.home_traj.set(1)
        traj_status.wait(ISARA_TIMEOUT)
        return traj_status.success

    def soakGripper(self):
        if self.current_tool.get() != self.tool_selected.get():
            raise ValueError(f"Bad tool argument:  {self.current_tool.get()}, {self.tool_selected.get()}")
        traj_status = self.soak_traj.set(1)
        traj_status.wait(ISARA_TIMEOUT)
        return traj_status.success

    def set_sample(self, puck: str, sample: str):
        sample_str = f"sample {sample}:puck {puck}"

        # TODO: switch status.wait to callbacks

        sample_sel_status = yield from bps.abs_set(self.sample_num_sel, sample)
        sample_sel_status.wait()
        puck_sel_status = yield from bps.abs_set(self.puck_num_sel, puck)
        puck_sel_status.wait()
        if not sample_sel_status.success:
            raise RuntimeError(f"Failed to set sample_select: {puck}, {sample}")
        if not puck_sel_status.success:
            raise RuntimeError(f"Failed to set puck_select: {puck}, {sample}")

        return sample_str

    def mount(self, puck: str, sample: str):
        sample_str = f"{sample}{puck}"
        # Cancel mount if robot is mid-movement
        if self.moving_sts.get():
            raise RuntimeError(f"Can't mount {sample_str}: robot is moving")

        # Robot powers on before movement
        if not self.power_sts.get():
            yield from bps.abs_set(self.power_on, 1, wait=True, settle_time=1)
        if not self.power_sts.get():
            raise RuntimeError(f"Failed to power robot on before move: {self.power_sts.get()}")

        # Ensure that the robot is using DoubleGripper
        if int(self.current_tool.get()) != int(IsaraRobotDevice.Tool.DOUBLEGRIPPER.value):
            raise RuntimeError("Wrong tool equipped! Aborting mount")
        # Trajectory tool_selected argument must be DoubleGripper
        if int(self.tool_selected.get()) != int(IsaraRobotDevice.Tool.DOUBLEGRIPPER.value):
            tool_set_status = yield from bps.abs_set(
                self.tool_selected, self.current_tool.get(), wait=True, settle_time=0.05
            )
            if not tool_set_status.success:
                raise RuntimeError(
                    f"""Failed to fix bad tool argument:  {self.tool_selected.get()}
                      != {IsaraRobotDevice.Tool.DOUBLEGRIPPER}"""
                )

        # Robot must be in soak position before mounting
        if self.position_sts.get() != "SOAK":
            print("moving to soak before mounting, 45 seconds...")
            soak_traj_status = yield from bps.abs_set(self.soak_traj, 1, wait=True, settle_time=5)
            if not soak_traj_status.success:
                raise RuntimeError("mount error: failed to reach soak position before mount")
            else:
                print("soaking...")
                yield from bps.sleep(45.0)
                print("soak complete")

        sample_str = yield from self.set_sample(puck, sample)
        print(f"mounting sample str:  {sample_str}")
        mount_status = yield from bps.abs_set(self.getput_traj, 1, wait=True)
        if not mount_status.success:
            raise RuntimeError(f"Can't mount {sample_str}: {self.last_message.get()}")
        else:
            print("mount successful")
        return mount_status

    def dismount(self, puck: str, sample: str):
        sample_str = f"{sample}{puck}"
        # Cancel mount if robot is mid-movement
        if self.moving_sts.get():
            raise RuntimeError("Can't dismount: robot is moving")

        # check spindle is actually occupied
        if not self.spindle_occupied_sts.get():
            raise RuntimeError("Can't dismount: spindle not occupied")

        # Robot powers on before movement
        if not self.power_sts.get():
            yield from bps.abs_set(self.power_on, 1, wait=True, settle_time=1)
            if not self.power_sts.get():
                raise RuntimeError(f"Failed to power robot on before move: {self.power_sts.get()}")

        # Ensure that the robot is using DoubleGripper
        if int(self.current_tool.get()) != int(IsaraRobotDevice.Tool.DOUBLEGRIPPER.value):
            raise RuntimeError("Wrong tool equipped! Aborting dismount")
        # Trajectory tool_selected argument must be DoubleGripper
        if int(self.tool_selected.get()) != int(IsaraRobotDevice.Tool.DOUBLEGRIPPER.value):
            tool_set_status = yield from bps.abs_set(
                self.tool_selected, self.current_tool.get(), wait=True, settle_time=0.05
            )
            if not tool_set_status.success:
                raise RuntimeError(
                    f"""Failed to fix bad tool argument:  {self.tool_selected.get()}
                     != {IsaraRobotDevice.Tool.DOUBLEGRIPPER}"""
                )

        print("dismounting")
        dismount_status = yield from bps.abs_set(self.get_traj, 1, wait=True)

        if not dismount_status.success:
            raise RuntimeError(f"Can't dismount {sample_str}: failed to dismount {self.last_message.get()}")
        else:
            print("dismount successful")
        return dismount_status
