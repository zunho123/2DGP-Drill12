from pico2d import *

import random
import math
import game_framework
import game_world
import common
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector


PIXEL_PER_METER = (10.0 / 0.3)
RUN_SPEED_KMPH = 10.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0


        self.tx, self.ty = 0, 0
        self.build_behavior_tree()

        self.patrol_locations = [(43, 274), (1118,274), (1050, 494), (575, 804), (235, 991), (575, 804), (1050, 494), (1118, 274)]
        self.loc_no = 0


    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        self.bt.run()

    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        Zombie.marker_image.draw(self.tx+25, self.ty-25)
        draw_circle(self.x, self.y, int(7.0 * PIXEL_PER_METER), 255, 255, 255)
        draw_rectangle(*self.get_bb())

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1


    def set_target_location(self, x=None, y=None):
        if x is None or y is None:
            raise ValueError('목표위치가 설정되어야 합니다.')
        self.tx, self.ty = x, y
        return BehaviorTree.SUCCESS


    def distance_less_than(self, x1, y1, x2, y2, r):
        distance2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
        return distance2 < (PIXEL_PER_METER * r) ** 2




    def move_little_to(self, tx, ty):
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.dir = math.atan2(ty - self.y, tx - self.x)
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)




    def move_to(self, r=0.5):
        self.state = 'Walk'
        self.move_little_to(self.tx, self.ty)
        if self.distance_less_than(self.tx, self.ty, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING



    def set_random_location(self):
        self.tx = random.randint(100, 1180)
        self.ty = random.randint(100, 924)
        return BehaviorTree.SUCCESS


    def if_boy_nearby(self, distance):
        if self.distance_less_than(common.boy.x, common.boy.y, self.x, self.y, distance):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL


    def move_to_boy(self, r=0.5):
      self.state = 'Walk'
      self.move_little_to(common.boy.x, common.boy.y)
      if self.distance_less_than(common.boy.x, common.boy.y, self.x, self.y, r):
          return BehaviorTree.SUCCESS
      else:
          return BehaviorTree.RUNNING


    def get_patrol_location(self):
        self.tx, self.ty = self.patrol_locations[self.loc_no]
        self.loc_no = (self.loc_no+1) % len(self.patrol_locations)
        return BehaviorTree.SUCCESS

    def if_zombie_has_more_balls_than_boy(self):
        if self.ball_count > common.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def build_behavior_tree(self):
        a1 = Action('Set target location', self.set_target_location, 1000, 1000)
        a2 = Action('Move to', self.move_to, 0.5)
        root = move_to_target_location = Sequence('Move to target location', a1, a2)

        a3 = Action('Set random location', self.set_random_location)

        root = wander = Sequence('Wander', a3, a2)

        c1 = Condition('소년이 근처에 있는가?', self.if_boy_nearby, 7)
        c2 = Condition('좀비 공이 더 많은가?', self.if_zombie_has_more_balls_than_boy)
        a4 = Action('소년한테 접근', self.move_to_boy)
        root = chase_boy = Sequence('조건 만족 시 추적', c1, c2, a4)
        root = chase_or_wander = Selector('조건 만족 시 추적 아니면 방황', chase_boy, wander)
        self.bt = BehaviorTree(root)
