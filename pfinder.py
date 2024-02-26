#!/usr/bin/python3
import sys
from argparse import ArgumentParser
from queue import PriorityQueue
from random import choice, random, randint
from time import sleep, time
from typing import List

import pygame
from colour import Color, rgb2hex


A_STAR = "A*"
DJIKSTRA = "Djikstra"
GREEDY = "Greedy BFS"

# Parameters
WIDTH = 1300
HEIGHT = 700
ROWS = 350
CELL_SIZE = HEIGHT/ROWS
COLUMNS = WIDTH/CELL_SIZE
FPS = 120
ALG = A_STAR
START = None
END = None
nodes = []


# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (84, 119, 232)  # Start Node
CYAN = (62, 234, 250)  # End Node
RED = (235, 87, 84)  # Visited Node
GREEN = (84, 232, 124)  # Open Node
GREY = (112, 109, 103)  # Obstacle Node

# Important variables
SCREEN = None
CLOCK = None
SHOW_MAZE_ANIM = False
PAUSED = False
QUICK_MODE = False


class Node:
    def __init__(self, row, column) -> None:
        self.row = row
        self.column = column
        self.color = WHITE
        self.needs_refresh = True
        self.g_score = float("inf")
        self.h_score = 0
        self.parent_node = None

    def get_neighbours(self, n: int) -> List:
        neighbours = []

        if self.row > n-1:
            neighbours.append(nodes[self.row-n][self.column])
        if self.column > n-1:
            neighbours.append(nodes[self.row][self.column-n])
        if self.row < ROWS-n:
            neighbours.append(nodes[self.row+n][self.column])
        if self.column < COLUMNS-n:
            neighbours.append(nodes[self.row][self.column+n])

        return neighbours

    def update_h_score(self) -> None:
        self.h_score = abs(END.row-self.row) +\
            abs(END.column - self.column)  # Manhattan heuristic

    @property
    def f_score(self) -> int:
        return self.g_score+self.h_score

    @property
    def score(self) -> int:
        if ALG == A_STAR:
            return self.f_score
        elif ALG == DJIKSTRA:
            return self.g_score
        else:
            return self.h_score

    def draw(self) -> None:
        if self.needs_refresh:
            pygame.draw.rect(SCREEN, self.color,
                             (self.column*CELL_SIZE, self.row*CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.line(SCREEN, BLACK, (self.column*CELL_SIZE, self.row*CELL_SIZE),
                             (self.column*CELL_SIZE, self.row*CELL_SIZE+CELL_SIZE))
            pygame.draw.line(SCREEN, BLACK, (self.column*CELL_SIZE, self.row*CELL_SIZE),
                             (self.column*CELL_SIZE+CELL_SIZE, self.row*CELL_SIZE))
            self.needs_refresh = False

    def make_start(self) -> None:
        global START
        if not self.is_end():
            self.color = BLUE
            START = self
            self.needs_refresh = True

    def make_end(self) -> None:
        global END
        if not self.is_start():
            self.color = CYAN
            END = self
            self.needs_refresh = True

    def make_obstacle(self) -> None:
        if not self.is_end() and not self.is_start():
            self.color = GREY
            self.needs_refresh = True

    def make_active(self) -> None:
        self.color = GREEN
        self.needs_refresh = True

    def make_visited(self) -> None:
        if not self.is_start():
            self.color = RED
            self.needs_refresh = True

    def make_path(self, color) -> None:
        self.color = color
        self.needs_refresh = True

    def reset(self) -> None:
        if self.is_start():
            global START
            START = None
        elif self.is_end():
            global END
            END = None
        self.color = WHITE
        self.parent_node = None
        self.g_score = float("inf")
        self.needs_refresh = True

    def is_start(self) -> bool:
        return self == START

    def is_end(self) -> bool:
        return self == END

    def is_obstacle(self) -> bool:
        return self.color == GREY

    def is_active(self) -> bool:
        return self.color == GREEN

    def is_visited(self) -> bool:
        return self.color == RED or self.is_start()

    def is_normal(self) -> bool:
        return self.color == WHITE


def draw_screen():
    for row in nodes:
        for node in row:
            node.draw()
    pygame.display.update()
    CLOCK.tick(FPS)


def reset_grid(mode: int) -> None:
    if mode == 0:
        for row in nodes:
            for node in row:
                node.reset()
    elif mode == 1:
        for row in nodes:
            for node in row:
                if not node.is_start() and not node.is_end() and not node.is_obstacle():
                    node.reset()
        END.g_score = float("inf")
        END.parent_node = None


def generate_maze() -> None:
    reset_grid(0)
    for row in nodes:
        for node in row:
            node.make_obstacle()
    nodes[0][0].reset()
    active = [nodes[0][0]]

    while active:
        if SHOW_MAZE_ANIM:
            handle_input_running()
            draw_screen()

        current = active.pop()
        current.make_active()

        current.reset()
        neighbours = [neighbour for neighbour in current.get_neighbours(2)
                      if not neighbour.is_normal()]

        if not neighbours:
            continue

        active.append(current)
        next_cell = choice(neighbours)

        dividing_wall = nodes[(current.row+next_cell.row) //
                              2][(current.column+next_cell.column)//2]

        dividing_wall.reset()
        next_cell.reset()
        active.append(next_cell)

    nodes[0][0].make_start()
    nodes[ROWS-1][COLUMNS-2].make_end()


def random_grid() -> None:
    reset_grid(0)
    for row in nodes:
        for node in row:
            if random() < 0.3:
                node.make_obstacle()

    nodes[randint(
        0, ROWS-1)][randint(0, COLUMNS-1)].make_start()
    end = nodes[randint(
        0, ROWS-1)][randint(0, COLUMNS-1)]

    while end == START:
        end = nodes[randint(0, ROWS-1)][randint(0, COLUMNS-1)]
    end.make_end()


def draw_path() -> None:
    path = []
    node = END

    for _ in range(END.g_score):
        path.insert(0, node)
        node = node.parent_node

    start = Color(rgb2hex(tuple(i/255 for i in BLUE)))
    end = Color(rgb2hex(tuple(i/255 for i in CYAN)))
    colors = list(start.range_to(end, END.g_score))
    index = 0

    while index < len(path):
        handle_input_running()
        if not PAUSED:
            color = tuple(255*i for i in colors[index].get_rgb())
            path[index].make_path(color)
            if not QUICK_MODE:
                draw_screen()
            index += 1


def find_path() -> int:
    start_time = time()
    for row in nodes:
        for node in row:
            node.update_h_score()
            node.parent_node = None

    active = PriorityQueue()
    START.g_score = 0
    index = 0

    active.put((START.score, index, START))
    found_path = False

    while not active.empty():
        if handle_input_running():
            print("Pathfinding was cancelled.")
            reset_grid(1)
            return

        if PAUSED:
            continue

        if not QUICK_MODE:
            draw_screen()

        current = active.get()[2]
        if current == END:
            found_path = True
            break
        current.make_visited()

        for neighbour in current.get_neighbours(1):
            if not neighbour.is_obstacle():
                if current.g_score + 1 < neighbour.g_score:
                    neighbour.g_score = current.g_score + 1
                    neighbour.parent_node = current
                    if not neighbour.is_active() and not neighbour.is_visited():
                        neighbour.make_active()
                        active.put((neighbour.score, index, neighbour))
                        index += 1

    if not found_path:
        print("No Path Found.")
    else:
        print(
            f"A path of length {END.g_score} is found in {time()-start_time} seconds.")
        draw_path()

    draw_screen()
    sleep(2)
    reset_grid(1)


def handle_mouse_press() -> None:
    if pygame.mouse.get_pressed()[0]:
        pos = pygame.mouse.get_pos()
        row = pos[1]//CELL_SIZE
        column = pos[0]//CELL_SIZE
        if row < ROWS and column < COLUMNS:
            if START and END:
                nodes[row][column].make_obstacle()
            elif START and not END:
                nodes[row][column].make_end()
            else:
                nodes[row][column].make_start()

    if pygame.mouse.get_pressed()[2]:
        pos = pygame.mouse.get_pos()
        row = pos[1]//CELL_SIZE
        column = pos[0]//CELL_SIZE
        if row < ROWS and column < COLUMNS:
            nodes[row][column].reset()


def handle_input_running() -> bool:
    global PAUSED, QUICK_MODE, SHOW_MAZE_ANIM
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                QUICK_MODE = not QUICK_MODE
            elif event.key == pygame.K_s:
                SHOW_MAZE_ANIM = not SHOW_MAZE_ANIM
            elif event.key == pygame.K_SPACE:
                PAUSED = not PAUSED
            elif event.key == pygame.K_BACKSPACE:
                return True
    return False


def handle_input_normal() -> None:
    global ALG,  QUICK_MODE, SHOW_MAZE_ANIM, PAUSED
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and START and END:
                find_path()
                PAUSED = False

            elif event.key == pygame.K_s:
                SHOW_MAZE_ANIM = not SHOW_MAZE_ANIM
            elif event.key == pygame.K_q:
                QUICK_MODE = not QUICK_MODE

            elif event.key == pygame.K_BACKSPACE:
                reset_grid(0)
            elif event.key == pygame.K_r:
                random_grid()
            elif event.key == pygame.K_m:
                generate_maze()
                PAUSED = False

            elif event.key == pygame.K_d:
                ALG = DJIKSTRA
                print("Set algorithm to Djikstra's.")
            elif event.key == pygame.K_a:
                ALG = A_STAR
                print("Set algorithm to A*.")
            elif event.key == pygame.K_g:
                ALG = GREEDY
                print("Set algorithm to Greedy Best-first Search.")

    handle_mouse_press()


def parse_args() -> None:
    global WIDTH, HEIGHT, ROWS, COLUMNS, CELL_SIZE, FPS
    parser = ArgumentParser("A* Visualiser",
                            usage="""\n\n
    1. Select start node by clicking on it(Blue).\n
    2. Select end node(Cyan).\n
    3. Draw obstacles by clicking on cells.(Grey)(or)\n
    4. Press 'm' to generate a maze.\n
    5. Press 'r' to randomly assign start,end and obstacles.\n
    5. Right click on a node to erase it.\n
    6. Press Space to run or pause the algorithm.\n
    7. Press BACKSPACE to cancel algorithm if it is running, if not the whole grid is cleared.\n
    8. Blue, Cyan, Grey, Red, Green, Purple indicate Start, End, Obstacle, Visited, Open, Path nodes respectively\n
    9. Press 'd' to switch algorithm to Djikstra's.\n
    10. Press 'a' to switch algorithm to A-star.\n
    11. Press 'g' to set algorithm to Greedy Best-first Search.\n
    12. Press 'q' to toggle Quick Mode( Only shows the final path found and not the process).\n""",
                            description="A program to visualise Pathfinding Algorithms.")

    parser.add_argument(
        "--width", "-w", help="Choose width of the screen.", type=int, default=WIDTH)
    parser.add_argument(
        "--height", "-ht", help="Choose height of the screen.", type=int, default=HEIGHT)
    parser.add_argument(
        "--ROWS", "-r", help="Enter the number of rows.", type=int, default=ROWS)
    parser.add_argument(
        "--fps", "-f", help="Enter FPS", type=int, default=FPS)
    args = parser.parse_args()

    WIDTH = args.width
    HEIGHT = args.height
    ROWS = args.ROWS
    CELL_SIZE = HEIGHT//ROWS
    COLUMNS = WIDTH//CELL_SIZE
    FPS = args.fps


def init_pygame() -> None:
    global SCREEN, CLOCK
    pygame.init()
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pathfinding Visualiser")
    CLOCK = pygame.time.Clock()


def create_nodes() -> None:
    global nodes
    nodes = [[Node(row, column) for column in range(COLUMNS)]
             for row in range(ROWS)]


def main() -> None:
    parse_args()
    init_pygame()
    create_nodes()
    while True:
        handle_input_normal()
        draw_screen()


if __name__ == "__main__":
    main()
