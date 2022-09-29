from bluesky import plan_stubs as bps
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import Component as Cpt

class IsaraRobotDevice(Device):
  ### Commands

  ## Generic command channels
  # power
  power_on = Cpt(EpicsSignal, 'Pwr:On-Cmd', put_complete=True)
  power_off = Cpt(EpicsSignal, 'Pwr:Off-Cmd', put_complete=True)

  # arm movement speed
  speed_up = Cpt(EpicsSignal, 'Spd:Up-Cmd', put_complete=True)
  speed_down = Cpt(EpicsSignal, 'Spd:Dn-Cmd', put_complete=True)
  # 0 - 100
  speed_setpoint = Cpt(EpicsSignal, 'Speed-SP', put_complete=True)

  # heater
  heater_on = Cpt(EpicsSignal, 'Htr:On-Cmd', put_complete=True)
  heater_off = Cpt(EpicsSignal, 'Htr:Off-Cmd', put_complete=True)

  # dewar lid
  dewar_lid_open = Cpt(EpicsSignal, 'Lid:Opn-Cmd', put_complete=True)
  dewar_lid_close = Cpt(EpicsSignal, 'Lid:Cls-Cmd', put_complete=True)

  # gripper a
  gripper_a_open = Cpt(EpicsSignal, 'OpnA-Cmd', put_complete=True)
  gripper_a_close = Cpt(EpicsSignal, 'ClsA-Cmd', put_complete=True)
  
  # gripper b
  gripper_b_open = Cpt(EpicsSignal, 'OpnB-Cmd', put_complete=True)
  gripper_b_close = Cpt(EpicsSignal, 'ClsB-Cmd', put_complete=True)

  ## Trajectories
  # write 1 to start move
  home_traj = Cpt(EpicsSignal,'Move:Home-Cmd', put_complete=True)
  recover_traj = Cpt(EpicsSignal,'Move:Rcvr-Cmd', put_complete=True)
  get_traj = Cpt(EpicsSignal,'Move:GetHt-Cmd', put_complete=True)
  put_traj = Cpt(EpicsSignal,'Move:PutHt-Cmd', put_complete=True)
  getput_traj = Cpt(EpicsSignal,'Move:GetPutHt-Cmd', put_complete=True)
  back_traj = Cpt(EpicsSignal,'Move:BckHt-Cmd', put_complete=True)
  dry_traj = Cpt(EpicsSignal, 'Move:Dry-Cmd', put_complete=True)
  soak_traj = Cpt(EpicsSignal, 'Move:Sk-Cmd', put_complete=True)

  ## Trajectory Arguments
  # 0 = "ToolChanger"
  # 1 = "Cryotong"
  # 2 = "SingleGripper"
  # 3 = "DoubleGripper"
  # 4 = "MiniSpineGripper"
  # 5 = "RotatingGripper"
  # 6 = "PlateGripper"
  # 7 = "Spare"
  # 8 = "LaserTool"
  tool_selected = Cpt(EpicsSignal,'Tl-Sel')

  # limits 0-29 
  plate_selected = Cpt(EpicsSignal, 'Plt-SP', put_complete=True)
  plate_n_selected = Cpt(EpicsSignal, 'Plt:N-SP', put_complete=True)

  # limits 0-16
  sample_selected = Cpt(EpicsSignal, 'Samp-SP', put_complete=True)
  samp_n_selected = Cpt(EpicsSignal, 'Samp:N-SP', put_complete=True)

  # 0 = "Skip"
  # 1 = "Scan"
  dm_selected = Cpt(EpicsSignal, 'DM-Sel', put_complete=True)

  ### Statuses
  # interface from denso, try to maintain types
  #int
  #status

  #bool
  #busy_sts

  #bool
  #mount_ready_sts

  #is mounting bool
  #mounting_sts

  #is dismounting bool
  #dismounting_sts

  # is drying bool
  # 0 = "Idle"
  # 1 = "Drying"
  drying_sts = Cpt(EpicsSignalRO, 'GripDry-Sts')
  # new 
  drying_permitted_sts = Cpt(EpicsSignalRO,'DryPmt-I')

  # spindle occupied bool
  spindle_occupied_sts = Cpt(EpicsSignalRO, 'Samp:Dif-Sts')

  # New statuses for ISARA

  # Occupied statuses
  # 0 = "Empty"
  # 1 = "Present"
  samp_a_occ_sts = Cpt(EpicsSignalRO, 'Samp:A-Sts')
  samp_b_occ_sts  = Cpt(EpicsSignalRO, 'Samp:B-Sts')
  samp_dif_occ_sts = Cpt(EpicsSignalRO, 'Samp:Dif-Sts')

  # Gripper Statuses
  # 0 = "Open"
  # 1 = "Closed"
  grip_a_sts = Cpt(EpicsSignalRO, 'Grp:A-Sts')
  grip_b_sts = Cpt(EpicsSignalRO, 'Grp:B-Sts')
  
  # Samples occupying gripper/spindle
  # returns 0-29
  # returns -1 if empty
  puck_a_read = Cpt(EpicsSignalRO, 'Pck:A-I')
  puck_b_read = Cpt(EpicsSignalRO, 'Pck:B-I')
  puck_dif_read = Cpt(EpicsSignalRO, 'Pck:Dif-I')
  
  # returns 0-16
  # returns -1 if empty
  samp_a_read = Cpt(EpicsSignalRO, 'Samp:A-I')
  samp_b_read = Cpt(EpicsSignalRO, 'Samp:B-I')
  samp_dif_read = Cpt(EpicsSignalRO, 'Samp:Dif-I')

  # deprecated possibly by doublegripper functions

  def selectSample(sample_no):
    yield from bps.abs_set(self.sample_selected, sample_no, wait=True)

  def selectPlate(plate_no):
    yield from bps.abs_set(self.plate_selected, plate_no, wait=True)

  def openGripper():
    pass   

  def closeGripper():
    pass

  def openGripperA():
    self.gripper_a_open.put(1)

  def openGripperB():
    self.gripper_b_open.put(1)

  def closeGripperA():
    self.gripper_a_close.put(1)

  def closeGripperB():
    self.gripper_b_close.put(1)

  def warmupGripper():
    pass

  def DewarHeaterOff():
    yield from bps.abs_set(self.heater_off.put, 1, wait=True)

  def DewarHeaterOn():
    yield from bps.abs_set(self.heater_on, 1, wait=True)

  def parkGripper():
    pass

  def testRobot():
    pass

  def openPort(PortNo):
    pass

  def closePorts():
    pass

  def dryGripper():
    yield from bps.abs_set(self.dry_traj.put, 1, wait=True)

  def recoverRobot():
    yield from bps.abs_set(self.recover_traj, 1, wait=True)

  def finish():
    pass

  def mountRobotSample():
    yield from bps.abs_set(self.put_traj, 1, wait=True)

  def unmountRobotSample():
    yield from bps.abs_set(self.back_traj, 1, wait=True)

  def homeRobot():
    yield from bps.abs_set(self.home_traj, 1, wait=True)

  def soakGripper():
    yield from bps.abs_set(self.soak_traj, 1, wait=True)

#  def set_sample(self, puck: str, sample: str):
#    sample_str = f"{sample}{puck}"
#    yield from bps.abs_set(self.puck_num_sel, puck, wait=True)
#    yield from bps.abs_set(self.sample_num_sel, sample, wait=True)
#
#    if self.sample_sts.get(use_monitor=False) != sample_str:
#      raise RuntimeError(f"Failed to set sample '{sample_str}'")
#
#    return sample_str

  def mount(self, puck: str, sample: str):
    if self.busy_sts.get() or not self.mount_ready_sts.get():
      raise RuntimeError("Can't mount: busy or occupied")

    sample_str = yield from self.set_sample(puck, sample)

    yield from bps.abs_set(self.mount_cmd, 1, wait=True)

    if not self.spindle_occupied_sts.get(use_monitor=False):
      raise RuntimeError(f"Can't mount {sample_str}: failed to mount")

  def dismount(self, puck: str, sample: str):
    if self.busy_sts.get() or not self.spindle_occupied_sts.get():
      raise RuntimeError(f"Can't dismount {sample_str}: busy or empty")

    yield from bps.abs_set(self.dismount_cmd, 1, wait=True)


    if self.spindle_occupied_sts.get(use_monitor=False):
      raise RuntimeError(f"Can't dismount {sample_str}: failed to dismount")
