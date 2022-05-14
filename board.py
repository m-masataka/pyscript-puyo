from enum import Enum, auto
import copy
import asyncio
import random
from pyodide import create_proxy

ROW = 13
COL = 6

grid_container = Element("grid-container")
next_puyo_container = Element("next-puyo")
puyo_template = Element("puyo-template").select(".view-cell", from_content=True)


class Puyo(Enum):
    Red  = ("red", "img/puyo_red.png")
    Blue = ("blue", "img/puyo_blue.png")
    Green = ("green", "img/puyo_green.png")
    Purple = ("purple", "img/puyo_purple.png")
    Yellow = ("yellow", "img/puyo_yellow.png")
    Empty = ("empty", "")

    def __init__(self, text, img):
        self.text = text
        self.img = img

class Status(Enum):
    Start = auto()
    New = auto()
    Normal = auto()
    Vanish = auto()
    Fall = auto()
    End = auto()

def move_check(b, c, n):
    cp = list(map(lambda x: (x['position']['row'], x['position']['col']), c))
    np = list(map(lambda x: (x['position']['row'], x['position']['col']), n))
    for p in np:
        if 0 <= p[0] < ROW and 0 <= p[1] < COL:
            if not p in cp:
                if b[p[0]][p[1]] != Puyo.Empty:
                    return False
        else:
            return False
    return True

def fall(b, r):
    if r == 0:
        return b
    for c in range(6):
        if b[r][c] is Puyo.Empty:
            cell = None
            for _r in reversed(range(r)):
                if b[_r][c] is not Puyo.Empty:
                    cell = copy.deepcopy(b[_r][c])
                    b[_r][c] = Puyo.Empty
            if cell is not None:
                b[r][c] = cell
    return fall(b, r-1)

class Board():
    def __init__(self):
        self.board = [[Puyo.Empty for i in range(COL)] for i in range(ROW)]
        self.gripped_puyo = [
            { 'position': {'row': 0, 'col': 1}, 'color': Puyo.Blue},
            { 'position': {'row': 1, 'col': 1}, 'color': Puyo.Red}
        ]
        for p in self.gripped_puyo:
            self.board[p['position']['row']][p['position']['col']] = p['color']
        self.next_puyo = [
            [Puyo.Blue, Puyo.Red],
            [Puyo.Blue, Puyo.Red],
        ]
        self._status = Status.Normal
        self.init_view()

    def init_view(self):
        pos = [0,0]
        count = 0
        for r in self.board:
            if pos[0] == 0:
                pos[0] = pos[0] + 1
                continue
            pos[1] = 0
            for c in r:
                puyo_html = puyo_template.clone('puyo-'+str(count), to=grid_container)
                puyo_html.element.style = "position: absolute; top: " + str(25 * (pos[0]-1)) + "px; left: " + str(25 * (pos[1]+1)) + "px;"
                puyo_html_img =  puyo_html.select("img")
                puyo_html_img.element.src = c.img
                grid_container.element.appendChild(puyo_html.element)
                pos[1] = pos[1] + 1
                count += 1
            pos[0] = pos[0] + 1
        self.update_next_view()

    @property
    def status(self):
        return self._status

    def update_view(self):
        count = 0
        for r in self.board[1:]:
            for c in r:
                puyo_html = Element("puyo-" + str(count))
                puyo_html_img =  puyo_html.select("img")
                puyo_html_img.element.src = c.img
                count += 1

    def update_next_view(self):
        count = 0
        for pair in self.next_puyo:
            for c in pair:
                puyo_html = Element('next-puyo-'+str(count))
                puyo_html_img =  puyo_html.select("img")
                puyo_html_img.element.src = c.img
                count += 1

    def move_griped_puyo(self, direction):
        org_pos = self.gripped_puyo
        def right(x):
            r = copy.deepcopy(x)
            r['position']['col'] += 1
            return r
        def down(x):
            r = copy.deepcopy(x)
            r['position']['row'] += 1
            return r
        def left(x):
            r = copy.deepcopy(x)
            r['position']['col'] -= 1
            return r
        def spin(x):
            r = copy.deepcopy(x)
            ax = [r[0]['position']['row'], r[0]['position']['col']]
            if ax[0] == r[1]['position']['row']:
                if ax[1] + 1 == r[1]['position']['col']: # right
                    r[1]['position']['row'] = ax[0] + 1
                    r[1]['position']['col'] = ax[1]
                else: # left
                    r[1]['position']['row'] = ax[0] - 1
                    r[1]['position']['col'] = ax[1]
            else:
                if ax[0] + 1 == r[1]['position']['row']: # buttom
                    r[1]['position']['row'] = ax[0]
                    r[1]['position']['col'] = ax[1] - 1
                else: # top
                    r[1]['position']['row'] = ax[0]
                    r[1]['position']['col'] = ax[1] + 1
            return r
        if direction == 'ArrowRight':
            next_pos = list(map(right, org_pos))
        elif direction == 'ArrowLeft':
            next_pos = list(map(left, org_pos))
        elif direction == 'ArrowDown':
            next_pos = list(map(down, org_pos))
        elif direction in ['ArrowUp', ' ']:
            next_pos = spin(org_pos)
        else:
            return False

        if not move_check(self.board, org_pos, next_pos):
            return False
        for p in org_pos:
            self.board[p['position']['row']][p['position']['col']] = Puyo.Empty
        for p in next_pos:
            self.board[p['position']['row']][p['position']['col']] = p['color']
        self.gripped_puyo = next_pos
        self.update_view()
        return True
 
    def key_event(self, event):
        self.move_griped_puyo(event.key)

    def update_board(self):
        if not self.move_griped_puyo('ArrowDown'):
            self._status = Status.Fall

    def update_view(self):
        count = 0
        for r in self.board[1:]:
            for c in r:
                puyo_html = Element("puyo-" + str(count))
                puyo_html_img =  puyo_html.select("img")
                puyo_html_img.element.src = c.img
                count += 1

    def add_next_puyo(self):
        self.gripped_puyo = [
            { 'position': {'row': 0, 'col': 1}, 'color': self.next_puyo[0][0]},
            { 'position': {'row': 1, 'col': 1}, 'color': self.next_puyo[0][1]}
        ]
        for p in self.gripped_puyo:
            self.board[p['position']['row']][p['position']['col']] = p['color']
        self.update_view()
        l = (Puyo.Red, Puyo.Blue, Puyo.Green, Puyo.Yellow, Puyo.Purple)
        self.next_puyo = [
            self.next_puyo[1],
            [random.choice(l), random.choice(l)], 
        ]
        self.update_next_view()


    def status_check(self):
        if self._status == Status.Normal:
            pass
        elif self._status == Status.Fall:
            fall(self.board, 12)
            self._status = Status.Vanish
            self.status_check()
        elif self._status == Status.Vanish:
            ## Vanish chefk
            self._status = Status.New
            self.status_check()
        elif self._status == Status.New:
            self.add_next_puyo()
            self._status = Status.Normal
            ## end_check


board = Board()
async def tick():
  while True:
    try:
        if board.status is not Status.Normal:
            board.status_check()
        await asyncio.sleep(1)
        board.update_board()
        board.update_view()
    except Exception as e:
        print(str(e))
        break


async def key_down(event):
    board.key_event(event)

game_panel = document.querySelector("body")
game_panel.addEventListener("keyup", create_proxy(key_down))

pyscript.run_until_complete(tick())