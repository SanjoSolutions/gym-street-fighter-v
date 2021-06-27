import math
import time
from enum import IntEnum

import gym
from gym import error, spaces, utils
from gym.utils import seeding
from ctypes import *
import pymem
from win32process import CreateProcess, STARTUPINFO
import numpy as np

from gym_street_fighter_v.ActionSpaceRyu import ActionSpaceRyu, Input
from gym_street_fighter_v.KeyPressing import KeyPressing, VirtualKeyCode
from gym_street_fighter_v.MoveEmbedding import move_to_embedding
from gym_street_fighter_v.StandingCrouchingJumpingEmbedding import standing_crouching_jumping_to_embedding
from gym_street_fighter_v.read_pointer import read_pointer

RYU_TOTAL_HP = 500.0
MIN_X = -750
MAX_X = 750
MIN_Y = 0
MAX_Y = 215
MAX_X_DISTANCE = MAX_X - MIN_X
MAX_Y_DISTANCE = MAX_Y - MIN_Y
MAX_DISTANCE = math.sqrt((MAX_X_DISTANCE) ** 2 + (MAX_Y_DISTANCE) ** 2)

program_path = r'D:\SteamLibrary\steamapps\common\StreetFighterV\StreetFighterV.exe'


class WindowsAppEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        pass

    def step(self, action):
        pass

    def reset(self):
        pass

    def render(self, mode='human'):
        pass

    def close(self):
        pass


FRAMES_PER_SECOND = 60
DURATION_BETWEEN_FRAMES = 1.0 / FRAMES_PER_SECOND

actions = list(ActionSpaceRyu)


class StreetFighterVEnv(WindowsAppEnv):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.action_space = spaces.Discrete(len(ActionSpaceRyu))

        self.key_pressing = KeyPressing()

        self.process = pymem.Pymem('StreetFighterV.exe')
        PROCESS_SUSPEND_RESUME = 0x0800
        self.process_handle = cdll.kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, self.process.process_id)

        self.hwnd = cdll.user32.FindWindowW(None, 'StreetFighterV')

        self._set_previous_hp_to_current_hp()

        self.game_over = False

    def _set_previous_hp_to_current_hp(self):
        self.previous_hp_p1 = self._read_character_1_health_points()
        self.previous_hp_p2 = self._read_character_2_health_points()

    def step(self, action):
        # cdll.ntdll.NtResumeProcess(self.process_handle)
        resumption_time = time.time()
        while windll.user32.GetForegroundWindow() != self.hwnd:
            time.sleep(1)

        input_to_keys = {
            Input.Forward: lambda: (VirtualKeyCode.D,) if self.is_character_on_left() else (VirtualKeyCode.A,),
            Input.Backward: lambda: (VirtualKeyCode.A,) if self.is_character_on_left() else (VirtualKeyCode.D,),
            Input.Up: VirtualKeyCode.W,
            Input.Down: VirtualKeyCode.S,
            Input.LP: VirtualKeyCode.G,
            Input.MP: VirtualKeyCode.H,
            Input.HP: VirtualKeyCode.J,
            Input.LMHP: VirtualKeyCode.K,
            Input.LK: VirtualKeyCode.B,
            Input.MK: VirtualKeyCode.N,
            Input.HK: VirtualKeyCode.M,
            Input.LMHK: VirtualKeyCode.OEM_COMMA
        }

        input_to_keys = dict(
            self.convert_input_to_key_mapping_to_lambda_function(input, key) for input, key in input_to_keys.items())

        inputs, conditions = actions[action].value
        for inputs_entry in inputs:
            for input in inputs_entry:
                keys = input_to_keys[input]()
                for key in keys:
                    self.key_pressing.key_down(key)
            time.sleep(0.1)
            for input in inputs_entry:
                keys = input_to_keys[input]()
                for key in keys:
                    self.key_pressing.key_up(key)

        move_time_left = self._read_character_1_move_time_left()
        while move_time_left > 0 and not self._is_done():
            time.sleep(DURATION_BETWEEN_FRAMES)
            move_time_left = self._read_character_1_move_time_left()

        duration_to_sleep = max(0.0, DURATION_BETWEEN_FRAMES - (time.time() - resumption_time))
        if duration_to_sleep > 0.0:
            time.sleep(duration_to_sleep)

        # cdll.ntdll.NtSuspendProcess(self.process_handle)

        hp_p1 = self._read_character_1_health_points()
        hp_p2 = self._read_character_2_health_points()
        state = self._get_state()
        hp_p1_delta = self._calculate_hp_delta(hp_p1, self.previous_hp_p1)
        hp_p2_delta = self._calculate_hp_delta(hp_p2, self.previous_hp_p2)
        reward = self._normalize(hp_p1_delta, 0, RYU_TOTAL_HP) - self._normalize(hp_p2_delta, 0, RYU_TOTAL_HP)
        done = self._is_done()

        self.previous_hp_p1 = hp_p1
        self.previous_hp_p2 = hp_p2

        if done:
            self.game_over = True

        return state, reward, done, {}

    def _calculate_hp_delta(self, hp, previous_hp):
        return hp - previous_hp

    def _is_done(self):
        hp_p1 = self._read_character_1_health_points()
        hp_p2 = self._read_character_2_health_points()
        done = hp_p1 == 0.0 or hp_p2 == 0.0
        return done

    def convert_input_to_key_mapping_to_lambda_function(self, input, key):
        if isinstance(key, VirtualKeyCode):
            return input, lambda: (key,)
        elif isinstance(key, tuple):
            return input, lambda: key
        else:
            return input, key

    def is_character_on_left(self):
        character_1_x = self._read_character_1_x()
        character_2_x = self._read_character_2_x()
        return character_1_x <= character_2_x

    def _read_character_1_x(self):
        character_1_x_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x288,
            0x1F0,
            0x58,
            0x18,
            0x290,
            0x50
        ))
        character_1_x = self.process.read_float(character_1_x_base_address + 0xC0)
        return character_1_x

    def _read_character_1_y(self):
        character_1_y_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x288,
            0x1F0,
            0x58,
            0x18,
            0x290,
            0x50
        ))
        character_1_y = self.process.read_float(character_1_y_base_address + 0xC8)
        return character_1_y

    def _read_character_1_move_time_left(self):
        character_1_move_time_left_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x288,
            0x1F0,
            0x20,
            0x998,
            0x1B8,
            0x18
        ))
        character_1_move_time_left = self.process.read_int(character_1_move_time_left_base_address + 0x914)
        return character_1_move_time_left

    def _read_character_1_move_id(self):
        character_1_move_id_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x288,
            0x1F0,
            0x20,
            0x998,
            0x1B8,
            0x18
        ))
        character_1_move_id = self.process.read_int(character_1_move_id_base_address + 0x9E0)
        return character_1_move_id

    def _read_character_1_standing_crouching_jumping(self):
        character_1_standing_crouching_jumping_base_address = read_pointer(self.process,
                                                                           self.process.base_address + 0x03CFDCD0, (
                                                                               0x288,
                                                                               0x1F0,
                                                                               0x20,
                                                                               0x998,
                                                                               0x1B8,
                                                                               0x18
                                                                           ))
        character_1_standing_crouching_jumping = self.process.read_int(
            character_1_standing_crouching_jumping_base_address + 0xCBC)
        return character_1_standing_crouching_jumping

    def _read_character_1_critical_art_bar(self):
        character_1_critical_art_bar_base_address = read_pointer(self.process,
                                                                 self.process.base_address + 0x03CFDCD0, (
                                                                     0x288,
                                                                     0x1F0,
                                                                     0x20,
                                                                     0x998,
                                                                     0x1B8,
                                                                     0x18
                                                                 )
                                                                 )
        character_1_critical_art_bar = self.process.read_int(character_1_critical_art_bar_base_address + 0xCE4)
        return character_1_critical_art_bar

    def _read_character_1_v_bar(self):
        character_1_v_bar_base_address = read_pointer(self.process,
                                                      self.process.base_address + 0x03CFDCD0, (
                                                          0x288,
                                                          0x1F0,
                                                          0x20,
                                                          0x998,
                                                          0x1B8,
                                                          0x18
                                                      )
                                                      )
        character_1_v_bar = self.process.read_int(character_1_v_bar_base_address + 0xCEC)
        return character_1_v_bar

    def _read_character_1_v_trigger_active_time_left(self):
        character_1_v_trigger_active_time_left_base_address = read_pointer(self.process,
                                                                           self.process.base_address + 0x03CFDCD0, (
                                                                               0x288,
                                                                               0x1F0,
                                                                               0x20,
                                                                               0x998,
                                                                               0x1B8,
                                                                               0x18
                                                                           ))
        character_1_v_trigger_active_time_left = self.process.read_int(
            character_1_v_trigger_active_time_left_base_address + 0xCF0
        )
        return character_1_v_trigger_active_time_left

    def _read_character_1_health_points(self):
        character_1_health_points_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x170,
            0x0,
            0x70,
            0x50,
            0x258,
            0x30
        ))
        character_1_health_points = self.process.read_int(
            character_1_health_points_base_address + 0x47C
        )
        return character_1_health_points

    def _read_character_2_x(self):
        character_2_x_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x288,
            0x200,
            0x58,
            0x18,
            0x3E0,
            0x10
        ))
        character_2_x = self.process.read_float(character_2_x_base_address + 0xC0)
        return character_2_x

    def _read_character_2_y(self):
        character_2_y_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x288,
            0x200,
            0x58,
            0x18,
            0x3E0,
            0x10
        ))
        character_2_y = self.process.read_float(character_2_y_base_address + 0xC8)
        return character_2_y

    def _read_character_2_move_time_left(self):
        character_2_move_time_left_base_address = read_pointer(self.process, self.process.base_address + 0x03A15660, (
            0x8,
            0x48,
            0x28,
            0x10,
            0x98,
            0xF0
        ))
        character_2_move_time_left = self.process.read_int(character_2_move_time_left_base_address + 0x91C)
        return character_2_move_time_left

    def _read_character_2_move_id(self):
        character_2_move_id_base_address = read_pointer(self.process, self.process.base_address + 0x03A15660, (
            0x8,
            0x48,
            0x28,
            0x10,
            0x98,
            0xF0
        ))
        character_2_move_id = self.process.read_int(character_2_move_id_base_address + 0x9E8)
        return character_2_move_id

    def _read_character_2_standing_crouching_jumping(self):
        character_2_standing_crouching_jumping_base_address = read_pointer(
            self.process,
            self.process.base_address + 0x03A15660, (
                0x8,
                0x48,
                0x28,
                0x10,
                0x98,
                0xF0
            )
        )
        character_2_standing_crouching_jumping = self.process.read_int(
            character_2_standing_crouching_jumping_base_address + 0xCC4
        )
        return character_2_standing_crouching_jumping

    def _read_character_2_critical_art_bar(self):
        character_2_critical_art_bar_base_address = read_pointer(self.process,
                                                                 self.process.base_address + 0x03A15660, (
                                                                     0x8,
                                                                     0x48,
                                                                     0x28,
                                                                     0x10,
                                                                     0x98,
                                                                     0xF0
                                                                 )
                                                                 )
        character_2_critical_art_bar = self.process.read_int(character_2_critical_art_bar_base_address + 0xCEC)
        return character_2_critical_art_bar

    def _read_character_2_v_bar(self):
        character_2_v_bar_base_address = read_pointer(self.process,
                                                      self.process.base_address + 0x03A15660, (
                                                          0x8,
                                                          0x48,
                                                          0x28,
                                                          0x10,
                                                          0x98,
                                                          0xF0
                                                      )
                                                      )
        character_2_v_bar = self.process.read_int(character_2_v_bar_base_address + 0xCF4)
        return character_2_v_bar

    def _read_character_2_v_trigger_active_time_left(self):
        character_2_v_trigger_active_time_left_base_address = read_pointer(
            self.process,
            self.process.base_address + 0x03A15660, (
                0x8,
                0x48,
                0x28,
                0x10,
                0x98,
                0xF0
            )
        )
        character_2_v_trigger_active_time_left = self.process.read_int(
            character_2_v_trigger_active_time_left_base_address + 0xCF8
        )
        return character_2_v_trigger_active_time_left

    def _read_character_2_health_points(self):
        character_2_health_points_base_address = read_pointer(self.process, self.process.base_address + 0x03CFDCD0, (
            0x170,
            0x0,
            0x70,
            0x50,
            0x98,
            0xA8
        ))
        character_2_health_points = self.process.read_int(
            character_2_health_points_base_address + 0x11C
        )
        return character_2_health_points

    def _read_state(self):
        return {
            'character_1': {
                'x': self._read_character_1_x(),
                'y': self._read_character_1_y(),
                'move_time_left': self._read_character_1_move_time_left(),
                'move_id': self._read_character_1_move_id(),
                'standing_crouching_jumping': self._read_character_1_standing_crouching_jumping(),
                'critical_art_bar': self._read_character_1_critical_art_bar(),
                'v_bar': self._read_character_1_v_bar(),
                'v_trigger_active_time_left': self._read_character_1_v_trigger_active_time_left(),
                'health_points': self._read_character_1_health_points()
            },
            'character_2': {
                'x': self._read_character_2_x(),
                'y': self._read_character_2_y(),
                'move_time_left': self._read_character_2_move_time_left(),
                'move_id': self._read_character_2_move_id(),
                'standing_crouching_jumping': self._read_character_2_standing_crouching_jumping(),
                'critical_art_bar': self._read_character_2_critical_art_bar(),
                'v_bar': self._read_character_2_v_bar(),
                'v_trigger_active_time_left': self._read_character_2_v_trigger_active_time_left(),
                'health_points': self._read_character_2_health_points()
            }
        }

    def _generate_state_for_character(self, character):
        MAX_MOVE_TIME_LEFT = 65536000
        if character['move_time_left'] > MAX_MOVE_TIME_LEFT:
            print('bigger move time left:', character['move_time_left'])
        return (
                self._normalize(character['x'], MIN_X, MAX_X),
                self._normalize(character['y'], MIN_Y, MAX_Y),
                self._normalize(character['move_time_left'], 0, MAX_MOVE_TIME_LEFT)
            ) + \
            move_to_embedding(character['move_id']) + \
            standing_crouching_jumping_to_embedding(character['standing_crouching_jumping']) + \
            (
                self._normalize(character['critical_art_bar'], 0, 900),
                self._normalize(character['v_bar'], 0, 600),
                self._normalize(character['v_trigger_active_time_left'], 0, 1000),
                self._normalize(character['health_points'], 0, 500)
            )

    def _get_state(self):
        state = self._read_state()

        return np.array(
            self._generate_state_for_character(state['character_1']) +
            self._generate_state_for_character(state['character_2']) +
            (
                self._normalize(abs(state['character_2']['x'] - state['character_1']['x']), 0, MAX_X_DISTANCE),
                self._normalize(abs(state['character_2']['y'] - state['character_1']['y']), 0, MAX_Y_DISTANCE),
                self._normalize(
                    math.sqrt(
                        (state['character_2']['x'] - state['character_1']['x']) ** 2 +
                        (state['character_2']['y'] - state['character_1']['y']) ** 2
                    ),
                    0,
                    MAX_DISTANCE
                )
            )
            # TODO: Time left when using environment with round format where time left has a significance
            #       regarding decision making.
        )

    def _normalize(self, value, min, max):
        return (value - min) / float(max - min)

    def reset(self):
        while windll.user32.GetForegroundWindow() != self.hwnd:
            time.sleep(1)
        # cdll.ntdll.NtResumeProcess(self.process_handle)

        if (
            self._read_character_1_health_points() > 0 and
            self._read_character_2_health_points() > 0
        ):
            self.key_pressing.press(VirtualKeyCode.RETURN)
            time.sleep(1)
            self.key_pressing.press(VirtualKeyCode.B)

        while not (
            self._read_character_1_health_points() == RYU_TOTAL_HP and
            self._read_character_2_health_points() == RYU_TOTAL_HP
        ):
            time.sleep(DURATION_BETWEEN_FRAMES)

        self.game_over = False
        self._set_previous_hp_to_current_hp()

        # cdll.ntdll.NtSuspendProcess(self.process_handle)
        state = self._get_state()
        return state

    def render(self, mode='human'):
        pass

    def close(self):
        pass


env = StreetFighterVEnv()
time.sleep(3)
env.reset()

# suspend and resume
# PROCESS_SUSPEND_RESUME = 0x0800
# process = pymem.Pymem('StreetFighterV.exe')
# print(process)
# process_handle = cdll.kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, process.process_id)
# cdll.ntdll.NtSuspendProcess(process_handle)
# print('')
# cdll.ntdll.NtResumeProcess(process_handle)


# starting process:
# startup_info = STARTUPINFO()
# CreateProcess(
#     None,
#     program_path,
#     None,
#     None,
#     False,
#     0,
#     None,
#     None,
#     startup_info
# )
