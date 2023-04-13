import random
from os import system
from os import name as os_name
from time import sleep

# константы - символы точек на поле
_DOT_MISS = '\u25AA'
_DOT_HIT = '\033[9;33m\u25EA\033[0m'
_DOT_KILL = '\033[9;31m\u25CF\033[0m'

MAX_SHIP_LENGTH = 3
MAX_COORD = 6


# определение пользовательских исключений
class Error(Exception):
    """Базовый класс для других исключений"""
    pass


class BoardOutError(Error):
    """Вызывается, когда точка попадает вне поля"""
    pass


class TooLargeShipError(Error):
    """Вызывается, когда длина корабля превышает максимальную"""
    pass


class ShipDirectionError(Error):
    """Вызывается, когда направление корабля неверное"""
    pass


class ShipContourError(Error):
    """Вызывается, когда нет зазора в 1 клетку между соседними кораблями"""
    pass


class RandomAttemptsError(Error):
    """Вызывается, когда превышено количество попыток поставить корабль на доску"""
    pass


class Dot:
    """Определяет базовую точку на поле"""

    def __init__(self, x, y):
        self._x = x
        self._y = y

    def __str__(self):
        return f"{chr(ord('a') + self._x - 1)}{self._y}"

    def __repr__(self):
        return f"{chr(ord('a') + self._x - 1)}{self._y}"

    @staticmethod
    def get_dot_coord(coord):
        x = ord(coord[0]) - ord('a') + 1
        y = int(coord[1])
        return Dot(x, y)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def __eq__(self, other):
        return self._x == other.x and self._y == other.y


class Ship:
    """Описывает параметры корабля на поле"""

    def __init__(self, length, position, direction):
        self._length = length
        self._life = length
        self._position = Dot(position.x, position.y)
        self._direction = direction

    def dots(self):
        """возвращает список с координатами точек корабля"""
        li = []
        for i in range(self._length):
            if self._direction:
                # горизонтальное расположение
                li.append(Dot(self._position.x + i, self._position.y))
            else:
                # вертикальное расположение
                li.append(Dot(self._position.x, self._position.y + i))
        return li

    @property
    def length(self):
        return self._length

    @property
    def direction(self):
        return self._direction

    @property
    def position(self):
        return self._position

    @property
    def life(self):
        return self._life

    def dec_life(self):
        if self._life > 0:
            self._life -= 1
        else:
            raise ValueError("Корабль уже убит.")


class Board:
    """Класс доска, содержит двумерный массив клеток доски, список кораблей
       а также методы для расстановки кораблей, вывода доски на экран,
       методы для выстрела и для проверки не выходит ли координата за доску
       если доска открытая (своя) то поле hidden = False"""
    _live_ship_counter = 0

    def __init__(self, hidden):
        self.board_array = [list('O' * MAX_COORD) for _ in range(MAX_COORD)]
        self.fleet = []
        self.hid = hidden

    @property
    def live_ship_counter(self):
        return self._live_ship_counter

    @staticmethod
    def out(dot):
        if dot.x > MAX_COORD or dot.y > MAX_COORD \
                or dot.x < 1 or dot.y < 1:
            return True
        else:
            return False

    @staticmethod
    def contour(ship):
        """Проверяем все точки вокруг корабля, если они на поле, возвращаем их список"""
        _contour = []
        for dot in ship.dots():
            for x in range(dot.x-1, dot.x+2):
                for y in range(dot.y-1, dot.y+2):
                    _dot = Dot(x, y)
                    if Board.out(_dot) or (_dot in ship.dots()) or (_dot in _contour):
                        continue
                    else:
                        _contour.append(_dot)
        return _contour

    def check_ship_collision(self, ship):
        """Проверяем, можно ли разместить очередной корабль среди остальных, если нельзя, возвращаем True"""
        obstacle = []  # список точек корабля и области вокруг него
        obstacle += ship.dots() + self.contour(ship)
        # перебираем точки всех кораблей и проверяем, не попадают ли они в эту область
        for ship in self.fleet:
            for shipdot in ship.dots():
                if shipdot in obstacle:
                    return True
        return False

    def add_ship(self, ship):
        #  проверки при выставлении корабля
        if Board.out(ship.position):
            raise BoardOutError("Координата точки выходит за пределы поля!")

        elif ship.length > MAX_SHIP_LENGTH:
            raise TooLargeShipError("Длина корабля слишком большая. Максимум: " + str(MAX_SHIP_LENGTH))

        elif ship.direction and (ship.position.x + ship.length - 1 > MAX_COORD) \
                or (not ship.direction and (ship.position.y + ship.length - 1 > MAX_COORD)):
            raise BoardOutError("Корабль выходит за пределы поля.")

        elif self.check_ship_collision(ship):
            raise ShipContourError("Корабль нельзя разместить рядом с уже стоящим кораблем.")

        else:
            self.fleet.append(ship)
            self.insert_ship_into_board(ship)
            self._live_ship_counter += 1
            return True

    def clean_board(self):
        self.fleet.clear()
        self._live_ship_counter = 0
        self.board_array = [list('O' * MAX_COORD) for _ in range(MAX_COORD)]

    def insert_ship_into_board(self, ship):
        if self.hid:
            return
        for shipdot in ship.dots():
            self.board_array[shipdot.y-1][shipdot.x-1] = '\u25A0'
        for shipdot in self.contour(ship):
            self.board_array[shipdot.y - 1][shipdot.x - 1] = '\u25A1'

    def print_board(self):
        for s in self.get_board():
            print(s)

    def print_boards(self, enemy_board):
        for index, value in enumerate(self.get_board()):
            print(value, '\t', enemy_board.get_board()[index])

    def get_board(self):
        string_array = ["  a b c d e f"]
        for index, value in enumerate(self.board_array):
            string_array.append(f"{index + 1} " + " ".join(map(str, value)))
        return string_array

    def get_dot(self, dot):
        if Board.out(dot):
            raise BoardOutError("Задана точка вне поля")
        return self.board_array[dot.y-1][dot.x-1]

    def set_dot(self, dot, state_char):
        if Board.out(dot):
            raise BoardOutError("Задана точка вне поля")
        self.board_array[dot.y-1][dot.x-1] = state_char
        return True

    def shot(self, dot):

        forbidden_dots = [_DOT_MISS, _DOT_HIT]
        if self.get_dot(dot) in forbidden_dots:
            raise BoardOutError("Стрелять в одну точку запрещается")

        for ship in self.fleet:
            if dot in ship.dots():
                # Hit the ship!
                ship.dec_life()
                self.set_dot(dot, _DOT_HIT)
                if ship.life == 0:
                    self._live_ship_counter -= 1
                    for d in ship.dots():
                        self.set_dot(d, _DOT_KILL)
                    for d in Board.contour(ship):
                        self.set_dot(d, _DOT_MISS)
                return True

        self.set_dot(dot, _DOT_MISS)
        return False


def get_ship(length):
    """создаем корабль на поле на основе ввода пользователя"""
    try:
        coord = input(f"Введите координату {length}-палубника (например а1): ")
        x = ord(coord[0]) - ord('a') + 1
        y = int(coord[1])
        # y = int(input("Введите координату y: "))
        # length = int(input("Введите длину корабля: "))
        if length > 1:
            _direction = input("Введите ориентацию (Г(H) - горизонтальная, В(V) - вертикальная): ").upper()
            if _direction == 'H' or _direction == 'Г':
                direction = True
            elif _direction == "V" or _direction == "В":
                direction = False
            else:
                raise ShipDirectionError("Неверное направление корабля")
        else:
            direction = True

        my_ship = Ship(length, Dot(x, y), direction)
        print(my_ship.dots())
        return my_ship
    except Exception as e:
        print(e)  # Выводим информацию об ошибке


class Player:
    """Класс описывает игрока, его доску, доску противника, методы реализации хода"""
    def __init__(self, board_self, board_enemy, name='Player'):
        self.name = name
        self.my_board = board_self
        self.enemy_board = board_enemy
        self.silent = False
        self.last_dot = None
        self.wounded_array = []

    def ask(self):
        """метод реализует выбор точки, в которую игрок стреляет"""
        pass

    def move(self, silent=False):
        while True:
            try:
                dot_to_shoot = self.ask()
                result = self.enemy_board.shot(dot_to_shoot)
                self.last_dot = dot_to_shoot
                if result:
                    # если выстрел результативный, можно повторить стрельбу
                    return True
                else:
                    # иначе - ход противника
                    return False
            except Exception as e:
                if not silent:
                    print(e)


class User(Player):
    """Класс описывает поведение игрока с вводом данных с клавиатуры"""
    def __init__(self, board_self, board_enemy, name='Player'):
        super().__init__(board_self, board_enemy, name)
        self.silent = False

    def ask(self):
        """получаем точку поля из ввода пользователя"""
        coord = input("Введите координату (например а1): ")
        x = ord(coord[0]) - ord('a') + 1
        y = int(coord[1])
        dot = Dot(x, y)
        return dot


class AI(Player):
    """Класс описывает поведение компьютерного игрока со случайным вводом"""
    def __init__(self, board_self, board_enemy, name='AI'):
        super().__init__(board_self, board_enemy, name)
        self.silent = True

    def ask(self):
        if self.wounded_array:
            # если есть раненые точки, то стреляем вокруг них!
            if len(self.wounded_array) > 1:
                # выбираем случайную точку из массива
                dot = self.wounded_array[random.randint(0, 1)]
                if self.wounded_array[0].y == self.wounded_array[1].y:
                    # две точки на горизонтали, значит фиксируем x и берем случайный y
                    rand_x = random.randint(dot.x - 1, dot.x + 1)
                    rand_y = dot.y
                else:
                    rand_x = dot.x
                    rand_y = random.randint(dot.y - 1, dot.y + 1)
            else:
                # или берем одну единственную
                dot = self.wounded_array[0]
                # выбираем случайно горизонталь или вертикаль
                if random.randint(0, 1):
                    rand_x = random.randint(dot.x - 1, dot.x + 1)
                    rand_y = dot.y
                else:
                    rand_x = dot.x
                    rand_y = random.randint(dot.y - 1, dot.y + 1)
        else:
            rand_x = random.randint(1, MAX_COORD)
            rand_y = random.randint(1, MAX_COORD)
        return Dot(rand_x, rand_y)


class Game:
    """Главный класс, который инициализирует игровое поле и содержит цикл
     с последовательными ходами игрока и компьютера"""
    _PRINT_LOG_LINES = 10

    def __init__(self):
        self.user_board = Board(hidden=False)
        self.ai_board = Board(hidden=True)
        self.Gamer = User(self.user_board, self.ai_board)
        self.AI = AI(self.ai_board, self.user_board, name='Враг')
        self.log = ["", "", "", "", "", "", "", "", "", ""]

    @staticmethod
    def add_random_ship(board, ship_length):
        attempts = 1000
        while attempts > 0:
            rand_x = random.randint(1, MAX_COORD)
            rand_y = random.randint(1, MAX_COORD)
            position = Dot(rand_x, rand_y)
            direction = random.randint(0, 1)
            try:
                my_ship = Ship(ship_length, position, direction)
                board.add_ship(my_ship)
                return
            except Exception as e:
                attempts -= 1

        raise RandomAttemptsError("превышено количество попыток поставить корабль")

    @staticmethod
    def random_board(board):
        while True:
            try:
                Game.add_random_ship(board, 3)
                Game.add_random_ship(board, 2)
                Game.add_random_ship(board, 2)
                Game.add_random_ship(board, 1)
                Game.add_random_ship(board, 1)
                Game.add_random_ship(board, 1)
            except RandomAttemptsError:
                board.clean_board()
                continue
            else:
                break
        return board

    @staticmethod
    def clear_screen():
        # for windows
        if os_name == 'nt':
            system('cls')
        # for mac and linux
        else:
            system('clear')

    def print_boards(self):
        Game.clear_screen()
        # Печать полей игрока и противника
        print(f'\033[1m{self.Gamer.name:>10}     {self.AI.name:>12}\033[0m')
        for index, value in enumerate(self.user_board.get_board()):
            print(value, '   ', self.ai_board.get_board()[index])

        # Печать лога действий игрока и компьютера
        print('\nИстория действий игроков:')
        for i in range(len(self.log)-self._PRINT_LOG_LINES-1, len(self.log)):
            if i >= 0:
                print(self.log[i])
        print('\n')

    def greet(self):
        self.clear_screen()
        self.Gamer.name = input("Введите Ваше имя:")
        self.log.append(f"Приветствуем Вас, {self.Gamer.name}")
        self.log.append("Генерируем поле игрока")
        self.print_boards()
        sleep(1)
        Game.random_board(self.user_board)
        self.log.append("Генерируем поле компьютера")
        self.print_boards()
        sleep(1)
        Game.random_board(self.ai_board)

    def result_check(self, player):
        # вытаскиваем с доски последнюю точку, в которую выстрелили
        last_dot = player.enemy_board.get_dot(player.last_dot)
        if last_dot == _DOT_HIT:
            shot_result = 'Ранен!'
            player.wounded_array.append(player.last_dot)
        elif last_dot == _DOT_KILL:
            shot_result = 'Убит!'
            player.wounded_array.clear()
        else:
            shot_result = ''
        if shot_result:
            self.log.append(f"[{player.name}]: {player.last_dot} -> Попадание! {shot_result}")
        else:
            self.log.append(f"[{player.name}]: {player.last_dot} -> Промах!")

    def loop(self):
        while True:
            result = True
            while result:
                result = self.Gamer.move()
                self.result_check(self.Gamer)
                self.print_boards()
                if not self.ai_board.live_ship_counter:
                    self.log.append("\033[5;31mПобеда! Господин Адмирал, примите поздравления,"
                                    " флот противника разгромлен!\033[0m")
                    self.print_boards()
                    return

            result = True
            while result:
                result = self.AI.move()
                self.result_check(self.AI)
                self.print_boards()
                if not self.user_board.live_ship_counter:
                    self.log.append("\033[5;34mК сожалению, в этот раз вы потерпели поражение!"
                                    " В другой раз повезет!\033[0m")
                    self.print_boards()
                    return

    def start(self):
        self.greet()
        self.print_boards()
        self.loop()


if __name__ == '__main__':
    new_game = Game()
    new_game.start()
