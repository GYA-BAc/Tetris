from pynput import keyboard
import os
import sys
import time
import random
from copy import deepcopy
from abc import ABC, abstractmethod

from tables import (
    WALL_KICK_TABLE_NORMAL, 
    I_KICK_TABLE, 
    FOUR_CORNERS_RULE, 
    SCORE_CHART
)
from pieces import (
    L_PIECES_LEFT, 
    L_PIECES_RIGHT, 
    S_PIECES_LEFT, 
    S_PIECES_RIGHT, 
    T_PIECES, 
    I_PIECES, 
    O_PIECES
)


SPACER = "  "
EMPTY_TILE = "· "
LEFT_BORDER = " |"
RIGHT_BORDER = "| "
BOTTOM_BORDER = "‾‾"
BLOCK = "██"
PREVIEW = "//" #Alternatives: "[]", "▒▒"

TOP_BOUNDS = 4 # represents # of lines above where the piece spawns



def generate_piece_set() -> list:
    return random.sample([L_PIECES_LEFT, L_PIECES_RIGHT, S_PIECES_LEFT, S_PIECES_RIGHT, T_PIECES, I_PIECES, O_PIECES], 7)


class Process(ABC):
    @abstractmethod
    def stop():
        ...

    @abstractmethod
    def run():
        ...

    @abstractmethod
    def get_next_state():
        ...


class Menu(Process):

    def __init__(self):
            #controller variables
        self.running = True
        self.buffering = False
        
        self.MENU_CONTROLS = {
            'w'                : self._menu_up  ,
            's'                : self._menu_down,

            keyboard.Key.up    : self._menu_up  ,
            keyboard.Key.down  : self._menu_down,

            keyboard.Key.space : self._select   ,
            keyboard.Key.enter : self._select   ,

        }       
        self.controller = keyboard.Listener(
            on_press = self._check_key_press,
        )

        self.menu_options = {
            0 : "game",
            1 : "about",
            2 : None
        }

        self.display = f"""
{'='*45}
████████╗███████╗████████╗██████╗ ██╗███████╗
╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗██║╚══███╔╝
   ██║   █████╗     ██║   ██████╔╝██║  ███╔╝ 
   ██║   ██╔══╝     ██║   ██╔══██╗██║ ███╔╝  
   ██║   ███████╗   ██║   ██║  ██║██║███████╗
   ╚═╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝
                An unofficial, fan-made game
{'='*45}"""

        self.cursor_position = 0
        self.cursor = "> "

        self.next_state = self.menu_options[self.cursor_position]
    
    def run(self):
        self.controller.start()
        os.system('mode con: cols=45 lines=30 ')
        self._render()
        while self.running:
            if os.get_terminal_size().columns != 45 or os.get_terminal_size().lines != 30:
                pass
                os.system('mode con: cols=45 lines=30 ')
            time.sleep(.5)

    def stop(self):
        self.controller.stop()

    def get_next_state(self) -> dict:
        return {"state" : self.next_state}


    def _check_key_press(self, key):
        while self.buffering:
            time.sleep(.001)
        try:
            self.MENU_CONTROLS[key.char]()
        except AttributeError:
            try:
                self.MENU_CONTROLS[key]()
            except KeyError:
                pass
        except KeyError:
            pass

    def _menu_up(self):
        if self.cursor_position > 0:#TODO add variable later
            self.cursor_position -= 1
            self._render()

    def _menu_down(self):
        if self.cursor_position < 2: #TODO: add variable
            self.cursor_position += 1
            self._render()

    def _select(self):
        self.next_state = self.menu_options[self.cursor_position]
        self.running = False

    def _render(self):
        if not self.buffering:
            self.buffering = True
            final = self.display
            final += "\n"*3
            final += f"{' '*15}{self.cursor if self.cursor_position == 0 else ''}  Play\n"
            final += "\n"*2
            final += f"{' '*15}{self.cursor if self.cursor_position == 1 else ''}  About\n"
            final += "\n"*2
            final += f"{' '*15}{self.cursor if self.cursor_position == 2 else ''}  Exit\n"
            final += '\n'*9
            final += "       Use keyboard to navigate menu"
            os.system("cls")
            sys.stdout.write(final)
            self.buffering = False


class About(Process):

    def __init__(self):
        self.running = True
        self.controller = keyboard.Listener(
            on_press=self._check_key_press,
        )

    def run(self):
        os.system('mode con: cols=45 lines=30 ')
        self.controller.start()
        os.system("cls")
        print("""
THIS IS A REPRODUCTION OF THE GAME TETRIS,
 IMPLEMENTED IN PYTHON. IT IS CREATED FOR 
NON-PROFIT, EDUCATIONAL PURPOSES. 
 THIS CREATION IS NOT INTENDED TO BE SOLD.

V. 1.1.2, by Alan

Controls:
    WASD / Arrow Keys  move
    Space              drop
    Z / X / up         rotate
    C                  hold

+ Hotfixes:
      - fixed issue where starting set was
        repeated between games

""")
        while self.running:
            if os.get_terminal_size().columns != 45 or os.get_terminal_size().lines != 30:
                pass
                os.system('mode con: cols=45 lines=30 ')
            time.sleep(.6)

    def stop(self):
        self.controller.stop()
    
    def get_next_state(self) -> dict:
        return {"state" : "menu"}


    def _check_key_press(self, key):
        if key != None:
            self.running = False



class GameRunner(Process):
    
    def __init__(self, debug = False):


            #controller variables
        self.GAME_CONTROLS = {
            'w' : self._rotate_cw,
            'a' : self._move_left,
            'd' : self._move_right,
            's' : self._soft_drop,

            keyboard.Key.up    : self._rotate_cw,
            keyboard.Key.left  : self._move_left,
            keyboard.Key.right : self._move_right,
            keyboard.Key.down  : self._soft_drop,

            keyboard.Key.space : self._hard_drop,

            'z' : self._rotate_counter_cw,
            'x' : self._rotate_cw,
            'c' : self._hold_piece,

            keyboard.Key.esc   : self._quit,
        }       
        self.controller = keyboard.Listener(
            on_press = self._check_key_press,
            on_release = self._re_enable_key,
        )
        self.next_state = None
        
        self.held_space = False    #} These variables meant to prevent rapid hard drops
        self.held_cw_rotate = False   #}             and rapid rotations
        self.held_ccw_rotate = False  #}             

            #meta variables
        self.running = True 
        self.debug = debug
        self.buffering = False

            #game variables
        self.score = 0

        self.current_piece_set = generate_piece_set()
        self.next_piece_set = None

        self.last_move_rotation = False
        self.held_piece = None
        self.can_hold = True


        self.board = [[EMPTY_TILE if j > 1 else SPACER for j in range(12)] for i in range(21+TOP_BOUNDS)] #This board is the OG
        for i in range(2):                                                                #Used for calculations, 
            self.board.append([SPACER for j in range(12)])                                  #only placed pieces counted
        self.temp_board = deepcopy(self.board) #This board is the displayed one, with the current piece drawn

        self.PREVIEW_NUMBER = 3
        self.piece_set_index = 0
        self.current_piece_orientation = 0
        self.position = [5,TOP_BOUNDS] #position is not technically at the top, but at the visible top (not at the top bounds)
        self.stopped = False
        self.PIECE_DROP_LENIENCY = 3
        self.piece_drop_counter = 0

    def run(self):
        self.controller.start()
        os.system('mode con: cols=45 lines=30 ')
        while self.running:
            if not self.buffering and not self.piece_drop_counter and not self.stopped:
                pass
                self._soft_drop()
                self.last_move_rotation = False
            if self.stopped:
                self.piece_drop_counter += 1  
            self._render()

            if os.get_terminal_size().columns != 45 or os.get_terminal_size().lines != 30:
                pass
                os.system('mode con: cols=45 lines=30 ')
            time.sleep(.6) # .6 is a good starting speed

    def stop(self):
        self.controller.stop()

    def get_next_state(self) -> dict:
        return {
            "state" : self.next_state,
            "score" : self.score,
        }

    def _check_key_press(self, key):
        while self.buffering:
            time.sleep(.001)
        try:
            self.GAME_CONTROLS[key.char]()
        except AttributeError:
            try:
                self.GAME_CONTROLS[key]()
            except KeyError:
                pass
        except KeyError:
            pass

    def _re_enable_key(self, key):
        if key == keyboard.Key.space:
            self.held_space = False
        try:
            if key.char == 'z':
                self.held_ccw_rotate = False
        except AttributeError:
            pass
        try:
            if key == keyboard.Key.up or key.char in ['x','w']:
                self.held_cw_rotate = False
        except AttributeError:
            pass

    def _quit(self):
        self.running = False
        self.next_state = "menu"

    def _rotate_cw(self):
        if not self.held_cw_rotate:
            future_orientation = self.current_piece_orientation + 1 if self.current_piece_orientation < len(self.current_piece_set[self.piece_set_index])-1 else 0
            table = WALL_KICK_TABLE_NORMAL if self.current_piece_set[self.piece_set_index] != I_PIECES else I_KICK_TABLE

            for test in table[f"{self.current_piece_orientation}{future_orientation}"]:
                allowed = True
                try: # check if current test case is allowed
                    for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][future_orientation]):
                        for tile_index, tile in enumerate(row):
                            if tile == BLOCK:
                                if (self.board[self.position[1]+row_index-test[1]][self.position[0]+tile_index+test[0]] == BLOCK or 
                                    self.board[self.position[1]+row_index-test[1]][self.position[0]+tile_index+test[0]] == SPACER):
                                    allowed = False
                except IndexError:
                    allowed = False
                if allowed:
                    self.last_move_rotation = True
                    self.position[0] += test[0]
                    self.position[1] -= test[1]
                    self.current_piece_orientation += 1
                    if self.current_piece_orientation > len(self.current_piece_set[self.piece_set_index])-1:
                        self.current_piece_orientation = 0
                    self._render()
                    self.held_cw_rotate = True
                    break

    def _rotate_counter_cw(self):
        if not self.held_ccw_rotate:
            future_orientation = self.current_piece_orientation - 1 if self.current_piece_orientation > 0 else len(self.current_piece_set[self.piece_set_index])-1
            table = WALL_KICK_TABLE_NORMAL if self.current_piece_set[self.piece_set_index] != I_PIECES else I_KICK_TABLE

            for test in table[f"{self.current_piece_orientation}{future_orientation}"]:
                allowed = True
                try: # check if current test case if allowed
                    for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][future_orientation]):
                        for tile_index, tile in enumerate(row):
                            if tile == BLOCK:
                                if (self.board[self.position[1]+row_index-test[1]][self.position[0]+tile_index+test[0]] == BLOCK or 
                                    self.board[self.position[1]+row_index-test[1]][self.position[0]+tile_index+test[0]] == SPACER):
                                    allowed = False
                except IndexError:
                    allowed = False
                if allowed:
                    self.last_move_rotation = True
                    self.position[0] += test[0]
                    self.position[1] -= test[1]
                    self.current_piece_orientation -= 1
                    if self.current_piece_orientation < 0:
                        self.current_piece_orientation = len(self.current_piece_set[self.piece_set_index])-1
                    self._render()
                    self.held_ccw_rotate = True
                    break

    def _move_left(self):
        allowed = True
        for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][self.current_piece_orientation]):
            for tile_index, tile in enumerate(row):
                if tile == BLOCK:
                    if self.position[0] + tile_index == 2:
                        allowed = False
                    elif self.board[self.position[1]+row_index][self.position[0]+tile_index-1] == BLOCK:
                        allowed = False
        if allowed:
            self.last_move_rotation = False
            self.position[0] -= 1
            self._render()

    def _move_right(self):
        allowed = True
        for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][self.current_piece_orientation]):
            for tile_index, tile in enumerate(row):
                if tile == BLOCK:
                    if self.position[0] + tile_index + 1 == len(self.board[row_index]):
                        allowed = False
                    elif self.board[self.position[1]+row_index][self.position[0]+tile_index+1] == BLOCK:
                        allowed = False
        if allowed:
            self.last_move_rotation = False
            self.position[0] += 1
            self._render()

    def _soft_drop(self):
        allowed = True
        
        for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][self.current_piece_orientation]):
            for tile_index, tile in enumerate(row):
                if tile == BLOCK:
                    if (self.board[self.position[1]+row_index+1][self.position[0]+tile_index] == BLOCK or
                        self.board[self.position[1]+row_index+1][self.position[0]+tile_index] == SPACER):
                        allowed = False
        if allowed:
            self.last_move_rotation = False
            self.position[1] += 1
            self._render()

    def _hard_drop(self):
        if not self.held_space:
            droppable = True
            down_shift_num = 0
            while droppable:
                for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][self.current_piece_orientation]):
                    for tile_index, tile in enumerate(row):
                        if tile == BLOCK:
                            if (self.board[self.position[1]+row_index+down_shift_num+1][self.position[0]+tile_index] == BLOCK or
                                self.board[self.position[1]+row_index+down_shift_num+1][self.position[0]+tile_index] == SPACER):
                                droppable = False
                if droppable:
                    down_shift_num += 1
            self.position[1] += down_shift_num
            self.piece_drop_counter = self.PIECE_DROP_LENIENCY
            self.held_space = True
            self.last_move_rotation = False
            self._render()
            
    def _change_piece(self): 
        self.piece_set_index += 1
        if self.piece_set_index > len(self.current_piece_set)-1 and self.next_piece_set:
            self.current_piece_set = self.next_piece_set
            self.piece_set_index = 0
            self.next_piece_set = None
        elif self.piece_set_index > len(self.current_piece_set)-1-self.PREVIEW_NUMBER and not self.next_piece_set:
            self.next_piece_set = generate_piece_set()
        self.current_piece_orientation = 0

        self.position = [5,TOP_BOUNDS]   #check if starting location needs shifting
        shiftable = True
        while shiftable:
            shiftable = False
            for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][self.current_piece_orientation]):
                for tile_index, tile in enumerate(row):
                    if tile == BLOCK:
                        if self.board[row_index+self.position[1]][tile_index+self.position[0]] == BLOCK:
                            self.position[1] -= 1
                            shiftable = True
                            break
                if shiftable:
                    break

        self.can_hold = True
        self._render()

    def _hold_piece(self):
        # might need to access buffering variable
        if self.can_hold:
            temp = self.held_piece
            self.held_piece = self.current_piece_set[self.piece_set_index]
            if temp != None:
                self.current_piece_set[self.piece_set_index] = temp
                self.piece_set_index -= 1
            self._change_piece()
            self.can_hold = False

    def _draw_to_board(self):
        outline_shiftable = True
        outline_shift = 0

        while outline_shiftable:
            for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][self.current_piece_orientation]):
                for tile_index, tile in enumerate(row):
                    if tile == BLOCK:
                        if (self.board[self.position[1]+row_index+outline_shift][self.position[0]+tile_index] == BLOCK or
                            self.board[self.position[1]+row_index+outline_shift][self.position[0]+tile_index] == SPACER or
                            outline_shift >= len(self.board)-6):
                            outline_shiftable = False
            if outline_shiftable:
                outline_shift += 1

        self.stopped = False
        for row_index, row in enumerate(self.current_piece_set[self.piece_set_index][self.current_piece_orientation]):
            for tile_index, tile in enumerate(row):
                if tile == BLOCK:
                    if self.temp_board[row_index+self.position[1]+outline_shift-1][tile_index+self.position[0]] != BLOCK:
                        self.temp_board[row_index+self.position[1]+outline_shift-1][tile_index+self.position[0]] = PREVIEW
                    self.temp_board[row_index+self.position[1]][tile_index+self.position[0]] = BLOCK
                    if (self.board[row_index+self.position[1]+1][tile_index+self.position[0]] == SPACER or
                        self.board[row_index+self.position[1]+1][tile_index+self.position[0]] == BLOCK):
                        self.stopped = True
        if not self.stopped:
            self.piece_drop_counter = 0

    def _compute_state(self): #where line clears etc are calculated

        lines_cleared = 0
        is_T_spin = False
        four_corners = 0
        
        if self.piece_drop_counter >= self.PIECE_DROP_LENIENCY:
            self.stopped = False
            self.piece_drop_counter = 0

            # check if it is a T spin
            if self.current_piece_set[self.piece_set_index] == T_PIECES:
                for i in FOUR_CORNERS_RULE:
                    try:
                        if (self.board[self.position[1]+i[1]][self.position[0]+i[0]] in [BLOCK, SPACER]
                            and self.position[0]+i[0] > 1):
                           four_corners += 1

                    except IndexError:
                        pass
                if four_corners >= 3 and self.last_move_rotation:
                    is_T_spin = True

            self.board = deepcopy(self.temp_board)
            
            for i in self.board[0:TOP_BOUNDS+1]: #check for loss
                if BLOCK in i:
                    self.running = False
                    self.next_state = "over"
                    break
            self._change_piece()
            

            #check board clear
            for row_index, row in enumerate(self.board): #actually clear board
                if row[2:14] == [BLOCK for i in row[2:14]]:
                    lines_cleared += 1
                    row = [EMPTY_TILE if j > 1 else SPACER for j in range(12)]
                    self.board.insert(0, row)
                    self.board.pop(row_index+1)
            if is_T_spin:
                self.score += 400*lines_cleared
            else:
                self.score += SCORE_CHART[lines_cleared]

    def _render(self):
        final = ""
    
        if not self.buffering:
            self.buffering = True
    
            os.system("cls")
            self._draw_to_board()
    
            hold = [[SPACER for j in range(4)] for i in range(4)]
            if self.held_piece:
                try:
                    for row_index, row in enumerate(self.held_piece[1]):
                        for tile_index, tile in enumerate(row):
                            if self.held_piece == O_PIECES:
                                hold[row_index][tile_index+1] = tile
                            else:
                                hold[row_index][tile_index] = tile
                except IndexError:
                    pass
                
            display = []
            for i in range(1, len(self.temp_board)-2-TOP_BOUNDS):
                if i == 17:
                    display.append([SPACER for j in range(4)] + [LEFT_BORDER] + self.temp_board[i+TOP_BOUNDS][2:] + [RIGHT_BORDER] + [str(self.score)])
                elif i == 1:
                    display.append(["  Held: "] + [LEFT_BORDER] + self.temp_board[i+TOP_BOUNDS][2:] + [RIGHT_BORDER] + ["Preview:"])
                elif i > 1 and i < 6:
                    display.append(hold[i-2] + [LEFT_BORDER] + self.temp_board[i+TOP_BOUNDS][2:] + [RIGHT_BORDER])
                else:
                    display.append([SPACER for j in range(4)] + [LEFT_BORDER] + self.temp_board[i+TOP_BOUNDS][2:] + [RIGHT_BORDER])
            display.append([SPACER for i in range(5)] + [BOTTOM_BORDER for j in range(10)])
            
            allowed = False
            preview_gap = 0
            for i in range(4*self.PREVIEW_NUMBER):
                try:
                    if self.current_piece_set[self.piece_set_index+self.PREVIEW_NUMBER-((11-i)//4)] == O_PIECES:
                        display[i+1+preview_gap] += SPACER
                    display[i+1+preview_gap] += [k for k in self.current_piece_set[self.piece_set_index+self.PREVIEW_NUMBER-((11-i)//4)][1][i%4]]
                except IndexError:
                    allowed = True if i%4 == 0 else allowed
                    if self.piece_set_index+self.PREVIEW_NUMBER>len(self.current_piece_set)-1 and allowed:
                        try:
                            if self.next_piece_set[self.piece_set_index-len(self.current_piece_set)+self.PREVIEW_NUMBER-((11-i)//4)] == O_PIECES:
                                display[i+1+preview_gap] += SPACER
                            display[i+1+preview_gap] += [k for k in self.next_piece_set[self.piece_set_index-len(self.current_piece_set)+self.PREVIEW_NUMBER-((11-i)//4)][1][i%4]]
                        except IndexError:
                            pass
                    allowed = False if i%4 == 3 else allowed
                preview_gap += 1 if i%4 == 3 else 0
    
            for i in range(3):
                sys.stdout.write('\n')
            for i in display:
                final = f"{final}{''.join(i)}\n"
            final += "Controls: WASD/Arrows, Z, X, C; Esc to quit"
            sys.stdout.write(final)
            if self.debug:
                print(f"""
    Debug Mode:
    piece_drop_counter: {self.piece_drop_counter}
    is stopped        : {self.stopped}
    current piece pos : {self.position}
    piece set index   : {self.piece_set_index}
    last move rotation: {self.last_move_rotation}
    """)
            self._compute_state()
            self.temp_board = deepcopy(self.board)
            self.buffering = False

        
class GameOver(Process):

    def __init__(self, score):
        self.score = score

        self.running = True

        self.buffering = False
        self.GAME_OVER_CONTROLS = {
            'w'                : self._menu_up  ,
            's'                : self._menu_down,

            keyboard.Key.up    : self._menu_up  ,
            keyboard.Key.down  : self._menu_down,

            keyboard.Key.space : self._select   ,
            keyboard.Key.enter : self._select   ,

        }       
        self.controller = keyboard.Listener(
            on_press = self._check_key_press,
        )

        self.selection_choices = {
            0 : "game",
            1 : "menu",
        }

        self.cursor_position = 0
        self.cursor = " >"

    def stop(self):
        self.controller.stop()

    def get_next_state(self):
        return {"state" : self.next_state}

    def run(self):
        self.controller.start()
        os.system('mode con: cols=45 lines=30 ')
        self._render()
        while self.running:
            if os.get_terminal_size().columns != 45 or os.get_terminal_size().lines != 30:
                pass
                os.system('mode con: cols=45 lines=30 ')
            time.sleep(.5) # .6 is a good starting speed
            
    def _check_key_press(self, key):
        while self.buffering:
            time.sleep(.001)
        try:
            self.GAME_OVER_CONTROLS[key.char]()
        except AttributeError:
            try:
                self.GAME_OVER_CONTROLS[key]()
            except KeyError:
                pass
        except KeyError:
            pass

    def _menu_up(self):
        if self.cursor_position > 0:
            self.cursor_position -= 1
            self._render()

    def _menu_down(self):
        if self.cursor_position < 1: #TODO: add variable
            self.cursor_position += 1
            self._render()

    def _select(self):
        self.next_state = self.selection_choices[self.cursor_position]
        self.running = False

    def _render(self):
        if not self.buffering:
            final = ""
            self.buffering = True
            os.system("cls")
            final += '\n'*5
            final +=  "                Game Over\n"
            final += f"            Your score was: {self.score}\n\n"
            final += f"               Play again?"
            final +=  '\n'*6
            final += f"{' '*18}{self.cursor if self.cursor_position == 0 else ''} Retry"
            final +=  '\n'*2
            final += f"{' '*18}{self.cursor if self.cursor_position == 1 else ''} Exit"
            final += '\n'*5
            sys.stdout.write(final)
            self.buffering = False




processes = {
    "menu" : Menu,
    "about": About,
    "game" : GameRunner,
    "over" : GameOver,
}
process_args = {
    "menu" : [[],       {"ctx" : False}],  
    "about": [[],       {"ctx" : False}],  
    "game" : [[False],  {"ctx" : False}],  #first arg is debug arg 
    "over" : [[],       {"ctx" : True }],
}

class Application:
    def __init__(self, processes : dict, process_args : dict, starting_state : dict ):

        self.running = True

        self.processes = processes
        self.process_args = process_args
        self.state = starting_state

        self.current_process = None
    
    def run(self):
        while self.running: 
            self.current_process = self.processes[self.state["state"]](
                *self.process_args[self.state["state"]][0], 
                *[self.state[i] for i in self.state 
                    if i != "state" and self.process_args[self.state["state"]][1]["ctx"]
                 ]
            )
            self.current_process.run()
            self.state = self.current_process.get_next_state()
            if self.state["state"] == None: 
                self.running = False
            self.current_process.stop()        


app = Application(processes, process_args, starting_state={"state" : "menu"})


if __name__ == "__main__":
    app.run()
