# -*- coding: utf-8 -*-

import datetime
import os
from pygame import *
from pygame.sprite import *
import re
import sys
import random
import pyganim
from menu import *
from operator import attrgetter


# Bird's Size
birdsize = (70, 70)
# Size of Running Window
windowSize = (800, 480)
# How hard the bird falls
gravity = 0.1
# Distance between pipes
pipedistance = 100
# Margin(+ x position) before pipes appears on screen
margin = 71
# Pipe scaled at
pipescale = 0.6
# Pipe scroll speed (should be equal to skip, for smoother animation)
pipespeed = 3
# Number of pairs of pipes pre-loaded
numbersetpipes = 3
# How hard should the bird jump (- y position)
birdjump = 40
#Max degrees of animation jumping
updegree = 40
#Max degrees of animation falling
downdegree = 90
#Size of score's text
textscoresize = 72
# frames per second setting
fps = 60
#velocity of background scrolling
skip = 3
#Animation speeds
wingsanimationspeed = 0.2
upanimationspeed = 0.002
downanimationspeed = 0.002
# We define how many scores should appear in the screen, in this case is best 5 scores
topscores = 5
# Best scores Y margin
bscores_margin_y = 30
# Colors for the menus
selected_item_color = (0, 25, 107)
unselected_item_color = (70, 130, 180)
# Files for scores and settings
scores_file = "scores.txt"
settings_file = "settings.ini"

#from http://www.pygame.org/wiki/RotateCenter?parent=CookBook
def rot_center(image, angle, scale):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotozoom(image, angle, scale)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

## ---[ createanimationlist ]-------------------------------------------------------
    #  @param   imglist       List containing the frames to be animated
    #  @param   seconds       Number of seconds between each frame
    #  @return                A list to be used by the module pyganim
    #                         List of tuples. Each tuple is either of
    #                         the format (str_image_filename, float/int_duration)
    #                         or (pygame.Surface, float/int_duration).
    #  #Creates a list for animObj(see references for module pyganim).
    #


def createanimationlist(imglist, seconds):
    newlist = []
    for i in range(0, len(imglist)):
        newlist.append((imglist[i], seconds))
    return newlist

    ## ---[ loadsound ]-------------------------------------------------------
    #  @param   sounds_str    List containing the sounds to be loaded
    #  @return                A dictionary containing all the sounds
    #  Creates a dictionary containing every sound needed for the game(They are located at projectfolder\sounds.)
    #  After loading, the usage is sounds['nameofthesounds'].play() for example
    #

#Gets the filepath of the sounds located at projectfolder\sounds. Returns the files paths on a dictionary.
def loadsound(sounds_str):
    sounds = {}
    for elem in sounds_str:
        file_path = os.getcwd() + "\sounds" + "\\" + elem
        decoded_str = file_path.decode("windows-1252")
        final_path = decoded_str.encode("utf8")
        matchobj = re.match(r'(.*)_(.*).ogg', elem)
        sounds[matchobj.group(2)] = pygame.mixer.Sound(final_path)
    return sounds


#Gets the filepath of an image located at projectfolder\images. Returns the file path of the image.
def loadimage(image):
    file_path = os.getcwd() + "\\images" + "\\" + image
    decoded_str = file_path.decode("windows-1252")
    final_path = decoded_str.encode("utf8")
    return final_path


#Loads the frames needed to initialize the bird and his animation. They are stored at the attribute frames.
def loadbird(bird):
    arraybirdframes = []
    for i in range(1, 8):
        file_path = os.getcwd() + "\\animatedsprites" + "\\" + "bird" + str(i) + ".png"
        decoded_str = file_path.decode("windows-1252")
        final_path = decoded_str.encode("utf8")
        arraybirdframes.append(pygame.transform.scale(image.load(final_path).convert_alpha(), birdsize))
    bird.frames = arraybirdframes


#Resets the first 4 arguments, and clears the queue event also
def reset(bird, birds, pipes, hitboxesg):
    bird.rect.x = bird.startposition[0]
    bird.rect.y = bird.startposition[1]
    bird.velocity = 0
    pygame.event.clear()
    birds.update()
    pipes.empty()
    hitboxesg.empty()
    pipes.update()
    hitboxesg.update()


#Scrolls the background in the area of the screen
def scroll(background, screen, x, x1):
    x -= skip
    x1 -= skip
    screen.blit(background, (x, 0))
    screen.blit(background, (x1, 0))
    if x < -windowSize[0]:
        x = windowSize[0]
    if x1 < -windowSize[0]:
        x1 = windowSize[0]
    return x, x1


#Creates a "life" depending on the position wanted.
class BirdLife(Sprite):
    def __init__(self, pos):
        Sprite.__init__(self)
        self.image = pygame.transform.scale(image.load(loadimage("bird.png")).convert_alpha(), (25, 25))
        # the lifes are 30 pixels away from each other(on X), example: life 1 = 30, life2 = 60, etc
        self.position = (pos * 30, 5)
        self.rect = self.image.get_rect().move(self.position)


#Generates a list with all the lifes(life1 in pos1, life2 in pos2, etc), depending on the number of lifes
def generatelifes(numberlifes):
    startlifes = []
    for i in range(0, numberlifes):
        startlifes.append(BirdLife(i))
    return startlifes


#Function used to update the group containing the array of lifes. Useful when the player loses a life, returns the group
def updatelifes(numberlifes, lifes):
    temp = generatelifes(numberlifes)
    lifes.empty()
    lifes.add(temp)
    return lifes


# Pipe class inherits everything from class Sprite. The constructor isn't complex. Attribute inscreen is 1
# if pipe is still visible by a margin in screen and 0 if it's gone (Valuable attribute for starting drawing a
# new set of pipes). Attribute disappear is a safe "spot" for initializing other processes like removing an
# old set of pipes
class Pipe(Sprite):
    def __init__(self, pipeimage):
        Sprite.__init__(self)
        self.image = pipeimage
        self.rect = self.image.get_rect()
        self.resize()
        self.inscreen = 1
        self.disappear = 0

    #After loading the pipe, we need to set a random height and scale it for the size we want.
    def resize(self):
        y = random.randint(pipedistance, windowSize[1] - pipedistance)
        self.rect.x = windowSize[0] + margin
        self.rect.y = 0 + y

    #update method for moving the pipe and re-evaluate the attributes like inscreen and disappear
    def update(self):
        self.rect = self.rect.move(-pipespeed, 0)
        if self.rect.right < margin + 15:
            self.inscreen = 0
        if self.rect.right < 0:
            self.disappear = 1


# InvisibleHitbox class inherits everything from class Sprite. The constructor initializes a surface with 1 pixel width
# and height is defined by the distance between a pair of pipes. It's like a flag. Its purpose is to add points to the
# player's score everytime the player crosses this surface. Its position is inherited from the pipe passed on the
# constructor
class InvisibleHitbox(Sprite):
    def __init__(self, pipe):
        Sprite.__init__(self)
        self.image = Surface((1, pipedistance), pygame.SRCALPHA, 32).convert_alpha()
        self.rect = Rect(pipe.rect.right, pipe.rect.y - pipedistance, 1, pipedistance)
        self.disappear = 0
        # This statement puts the hitbox visible
        #self.image.fill((255, 0, 0))

    #update method for moving the hitbox and re-evaluate the attribute disappear
    def update(self):
        self.rect = self.rect.move(-pipespeed, 0)
        if self.rect.x < 0:
            self.disappear = 1


# Function that receives two arrays, and checks if the last pipe/hitbox is gone, therefore is safe to remove
# the set that contains pipes/hitboxes
def checkpipes(arraypipes, hitboxes, group, group2):
    if arraypipes[len(arraypipes) - 1].disappear == 1:
        group.remove(arraypipes)
    if hitboxes[len(hitboxes) - 1].disappear == 1:
        group2.remove(hitboxes)


# Receives a number that dictates how many pipes/hitboxes should be created in each set and the pipe images
# (that way we don't have to load the images again). Does the pair generation and in the end returns two arrays,
# one containing the pipes, the other containing the hitboxes. Each pipe/hitbox are 300 pixels away from the next one.
def generatepipes(numbersetpipes, pipeimage, pipe_pair_image):
    arraypipes = []
    hitboxes = []
    for i in range(0, numbersetpipes):
        pipe1 = Pipe(pipeimage)
        hitbox1 = InvisibleHitbox(pipe1)
        pipe2 = Pipe(pipeimage)
        # pipe2 has the image inverted (top pipe)
        pipe2.image = pipe_pair_image
        temp = pipe1.rect.y
        # adjusts the top pipe position
        pipe2.rect.y = 0 - (windowSize[1] - temp) - pipedistance
        pipe1.rect.x += i * 300
        pipe2.rect.x += i * 300
        hitbox1.rect.x += i * 300
        arraypipes.append(pipe1)
        arraypipes.append(pipe2)
        hitboxes.append(hitbox1)
        # We don't need these pipes anymore in memory
        del pipe1
        del pipe2
    return arraypipes, hitboxes


# Bird class inherits everything from class Sprite. Startposition is where we want the bird to start flying. The bird
# starts with 0 velocity. The method loadbird loads all the frames needed for the animation of him. In this case we are
# using 8 frames, that creates the animation of the bird flapping the wings. Up and down are storing the frames need in
# case the user clicks the mouse button causing the bird to jump (up); in case the bird collides, we are using the
# attribute down that stores the frames for falling in to the ground. For animobj refer to pyganim reference
class Bird(Sprite):
    def __init__(self):
        Sprite.__init__(self)
        self.image = pygame.transform.scale(image.load(loadimage("bird1.png")).convert_alpha(), birdsize)
        self.copy = pygame.transform.scale(image.load(loadimage("bird1.png")).convert_alpha(), birdsize)
        self.startposition = (windowSize[0] / 2 - (windowSize[0] / 4), windowSize[1] / 2)
        self.rect = self.image.get_rect().move(self.startposition)
        self.velocity = 0
        loadbird(self)
        self.up = self.generateframes(self.frames, updegree, 'up', 4)
        self.down = self.generateframes(self.frames, downdegree, 'down', 1)
        self.animatelist = createanimationlist(self.frames, wingsanimationspeed)
        self.animobj = pyganim.PygAnimation(self.animatelist, loop=False)

    # Method that generates all the frames for the animations up and down. It's based on the angle provided(the
    # max angle that we want the bird to reach with its head.
    def generateframes(self, images, nframes, direction, step):
        save = []
        for i in range(0, nframes, step):
            if direction == 'up':
                for elem in images:
                    save.append(rot_center(elem, i, 1.0))
            elif direction == 'down':
                for elem in images:
                    save.append(rot_center(elem, - i, 1.0))
        return save

    #Check pyganim reference
    def animate(self, frames, speed):
        self.animatelist = createanimationlist(frames, speed)
        self.animobj = pyganim.PygAnimation(self.animatelist, loop=False)
        self.animobj.play()

    # Update method. Bird is always falling unless the user inputs a mouse click. The bird falls harder relying on
    # time passed. It's a linear function. Each call of the method we add the constant gravity to the velocity. After
    # calculating the velocity it updates the bird's coordinates. X is always the same. After the random start position
    # on the ready instance, we re-alocate him on the start position (fixed X).
    def update(self):
        self.velocity += gravity
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y + self.velocity)
        if self.rect.x > self.startposition[0]:
            self.rect.x -= 1
        elif self.rect.x < self.startposition[0]:
            self.rect.x += 1


# Banner class inherits everything from class Sprite. The constructor receives two arguments, the text to be shown and
# the size of the text. This class by default uses the font 'Flappyfont' and the text color is white by default. Its
# position by default is on the center of the screen (the beginning of the text).
class Banner(Sprite):
    def __init__(self, text, size):
        Sprite.__init__(self)
        self.my_font = font.Font("flappyfont.ttf", size)
        self.text = text
        self.color = (255, 255, 255)
        self.image = self.my_font.render(self.text, True, self.color).convert_alpha()
        self.rect = self.image.get_rect().move(windowSize[0] / 2, windowSize[1] / 2)

    # Update Method. If we need to update the text of the banner.
    def update(self, text):
        self.text = text
        self.image = self.my_font.render(self.text, True, self.color).convert_alpha()
        tempx = self.rect.x
        tempy = self.rect.y
        self.rect = self.image.get_rect()
        self.rect.x = tempx
        self.rect.y = tempy

    # This method is just to change the text color.
    def set_color(self, color):
        self.color = color
        self.image = self.my_font.render(self.text, True, color).convert_alpha()

    # This method centers the text based on its size and receives screen size. Receives also two booleans, whether we
    # want to center it on the horizontal or vertical or both.
    def center(self, windowSize, xcenter, ycenter):
        if xcenter:
            self.rect.centerx = windowSize[0]/2
        if ycenter:
            self.rect.centery = windowSize[1]/2


# Function that updates specific stuff and draws it after
def draw_update_elements(pipes, hitboxesg, scorebanner, lifes, bird, textscore, screen):
    bird.update()
    pipes.update()
    hitboxesg.update()
    scorebanner.update(textscore.text)
    pipes.draw(screen)
    hitboxesg.draw(screen)
    scorebanner.draw(screen)
    lifes.draw(screen)
    bird.animobj.blit(screen, (bird.rect.x, bird.rect.y))


# Load settings from file
def loadsettings(settings_file):
    export_settings = []
    # Checks if the file already exists, if it's true then loads the settings
    if os.path.exists(settings_file):
        scores = open(settings_file)
        load_settings = scores.readlines()
        matchobj = re.match(r'Sounds:\W(.*)\n', load_settings[0])
        export_settings.append(bool(int(matchobj.group(1))))
        matchobj1 = re.match(r'FPS:\W(.*)', load_settings[1])
        export_settings.append(bool(int(matchobj1.group(1))))
        scores.close()
    # If there are no settings file, then it creates a new file with default values (1 for sounds 0 for showing FPS).
    else:
        scores = open('settings.ini', 'w')
        scores.write('Sounds: 1\nFPS: 0')
        scores.close()
        export_settings = [True, False]
    return export_settings


# Save settings to file
def savesettings(settings_file, music_state, show_FPS):
    scores = open(settings_file, 'w')
    scores.write("Sounds: %d\nFPS: %d" % (music_state, show_FPS))
    scores.close()


# Save scores to file and can erase if we want to
def savescore(score, scores_file, erase):
    #if we don't want to erase, we save the score
    if not erase:
        scores = open(scores_file, 'a')
        day = datetime.datetime.today().strftime('%d')
        month = datetime.datetime.today().strftime('%m')
        year = datetime.datetime.today().year
        data_score = "%s/%s/%s  -  Score: %d" % (day, month, year, score)
        scores.write(data_score + "\n")
    #else we erase
    else:
        scores = open(scores_file, 'w')
    scores.close()


# Very basic class. Stores the text that will be written to the file, and the value of the score.
class Score():
    def __init__(self, points, text):
        self.score = points
        self.text = text


# Load best scores from file. In this case we are using the best 5 scores. Could be changed by the variable topscores.
def loadbestscores(scores_file):
    scores_to_print = []
    # Check the existence of the scores file
    # If it exists, loads the best scores.
    if os.path.exists(scores_file):
        #checkfile is True if the file is empty
        checkfile = os.stat(scores_file)[6] == 0
        scores = open(scores_file)
        highscores = scores.readlines()
        save_scores = []
        best_scores = []

        for i in range(0, len(highscores)):
            matchobj = re.match(r'(.*)Score:\W(.*)\n', highscores[i])
            save_scores.append(Score(int(matchobj.group(2)), matchobj.group(1) + "Score: "))
            sorted_by_score = sorted(save_scores, key=lambda x: x.score, reverse=True)

        # If the file is not empty, we do:
        if not checkfile:
            if len(highscores) >= topscores:
                for j in range(0, topscores):
                    best_scores.append(sorted_by_score[j])
            else:
                for j in range(0, len(highscores)):
                    best_scores.append(sorted_by_score[j])
            for i in range(0, len(best_scores)):
                if best_scores[i].score > 9:
                    scores_to_print.append(Banner(str(i+1) + ".    " + best_scores[i].text +
                                                  str(best_scores[i].score), 26))
                else:
                    scores_to_print.append(Banner(str(i+1) + ".    " + best_scores[i].text + "0" +
                                                  str(best_scores[i].score), 26))
                scores_to_print[i].my_font = pygame.font.Font(None, 26)
                # Changing font, we have to update everything, including new size
                scores_to_print[i].image = scores_to_print[i].my_font.render(scores_to_print[i].text,
                                            True, scores_to_print[i].color).convert_alpha()
                scores_to_print[i].rect = scores_to_print[i].image.get_rect()
        scores.close()
    # Then we return a list of banners containing the best scores. One banner for each score.
    return scores_to_print


#based on http://www.pygame.org/project-MenuClass-1260-.html
def startmenu(screen, background):
    #blit static background
    screen.blit(background, (0, 0))
    pygame.display.flip()

    #Create Menus
    menu0 = cMenu(50, 50, 20, 5, 'vertical', 100, screen,
                  [('Start Game', 1, None),
                   ('Highscores', 2, None),
                   ('Options', 3, None),
                   ('Exit', 4, None)])

    menu1 = cMenu(50, 50, 20, 5, 'vertical', 100, screen,
                  [('Go Back', 0, None),
                   ('Reset Highscores', 7, None)])

    menu2 = cMenu(50, 50, 20, 5, 'vertical', 100, screen,
                  [('Go Back', 0, None),
                   ('Sounds: ', 5, None),
                   ('Show FPS: ', 6, None)])
    menus = [menu0, menu1, menu2]

    for elem in menus:
        # Color for unselected text
        elem.u_color = unselected_item_color
        # Color for selected text
        elem.s_color = selected_item_color
        # Center the menu on the draw_surface (the entire screen here)
        elem.set_center(True, True)
        # Center the menu on the draw_surface (the entire screen here)
        elem.set_alignment('center', 'center')
    # Create the state variables
    state = 0
    prev_state = 1
    reset = False
    # Load settings from file
    settings = loadsettings(settings_file)
    music_state = settings[0]
    show_FPS = settings[1]
    # Color constants
    ON_COLOR = (0, 100, 0)
    OFF_COLOR = (255, 0, 0)
    # Creation of banners for settings
    # Flappyfont
    banner_music = Banner("ON", 32)
    banner_fps = Banner("OFF", 32)
    # Banners default colors
    banner_music.set_color(ON_COLOR)
    banner_fps.set_color(OFF_COLOR)
    banners = Group(banner_music, banner_fps)
    banner_scores = loadbestscores(scores_file)
    # Alocation and set color of each line of bestscores (starts at 10 px, vertical padding of 30)
    for i in range(0, len(banner_scores)):
        banner_scores[i].rect.y = bscores_margin_y * i + 10
        banner_scores[i].set_color((0, 25, 107))
        if i is 0:
            banner_scores[i].center(windowSize, True, False)
        else:
            banner_scores[i].rect.x = banner_scores[0].rect.x
    highscores = Group(banner_scores)
    # rect_list is the list of pygame.Rect's that will tell pygame where to
    # update the screen (there is no point in updating the entire screen if only
    # a small portion of it changed!)
    rect_list = []

    # Ignore mouse motion (greatly reduces resources when not needed)
    pygame.event.set_blocked(pygame.MOUSEMOTION)

    # The main while loop
    while 1:
        # Check if the state has changed, if it has, then post a user event to
        # the queue to force the menu to be shown at least once
        if prev_state != state:
            pygame.event.post(pygame.event.Event(EVENT_CHANGE_STATE, key=0))
            prev_state = state

        # Get the next event
        e = pygame.event.wait()

        # Update the menu, based on which "state" we are in (input is keyboard based in this case)
        if e.type == pygame.KEYDOWN or e.type == EVENT_CHANGE_STATE:
            if state == 0:
                screen.blit(background, (0, 0))
                rect_list, state = menu0.update(e, state)
                if state is not 0:
                    pygame.display.flip()
            elif state == 1:
                savesettings(settings_file, music_state, show_FPS)
                break
            elif state == 2:
                screen.blit(background, (0, 0))
                rect_list, state = menu1.update(e, state)
                if not reset and len(highscores) is not 0:
                    # get the max size of the bestscores, the line with most text, to adjust the borders to it
                    savemax = max(banner_scores, key=attrgetter('rect.width'))
                    # draw borders, 10 margin left, right, top and bottom; size + 20; border thickness: 3
                    draw.rect(screen, selected_item_color, (banner_scores[0].rect.x - 10, 0,
                            savemax.rect.width + 20, bscores_margin_y * len(banner_scores) + 10), 3)
                highscores.draw(screen)
                if reset:
                    highscores.empty()
            elif state == 3:
                screen.blit(background, (0, 0))
                rect_list, state = menu2.update(e, state)
                # Defaultfont
                banner_music.my_font = font.Font(None, menu2.menu_items[0]['u_image'].get_bitsize())
                banner_fps.my_font = font.Font(None, menu2.menu_items[0]['u_image'].get_bitsize())
                if music_state is True:
                    banner_music.update("ON")
                    banner_music.set_color(ON_COLOR)
                if music_state is False:
                    banner_music.update("OFF")
                    banner_music.set_color(OFF_COLOR)
                if show_FPS is True:
                    banner_fps.update("ON")
                    banner_fps.set_color(ON_COLOR)
                if show_FPS is False:
                    banner_fps.update("OFF")
                    banner_fps.set_color(OFF_COLOR)
                banner_music.rect.x = menu2.menu_items[1]['offset'][0] + menu2.menu_items[1]['rect'].width
                banner_music.rect.top = menu2.menu_items[1]['offset'][1]
                banner_fps.rect.x = menu2.menu_items[2]['offset'][0] + menu2.menu_items[2]['rect'].width
                banner_fps.rect.top = menu2.menu_items[2]['offset'][1]
                banners.draw(screen)
            elif state == 5:
                music_state = not music_state
                screen.blit(background, (0, 0))
                rect_list, state = menu2.update(e, state)
                state = 3
            elif state == 6:
                show_FPS = not show_FPS
                screen.blit(background, (0, 0))
                rect_list, state = menu2.update(e, state)
                state = 3
            elif state == 7:
                screen.blit(background, (0, 0))
                rect_list, state = menu1.update(e, state)
                savescore(0, scores_file, True)
                print("Scores Reseted!")
                tempbanner = Banner("Scores Reseted!", 50)
                tempbanner.center(windowSize, True, False)
                tempbanner.rect.y = 20
                highscores.empty()
                highscores.add(tempbanner)
                reset = True
                state = 2
            else:
                print 'Exit!'
                savesettings(settings_file, music_state, show_FPS)
                pygame.quit()
                sys.exit()
        # Update the menu, based on which "state" we are in (input is mouse based in this case)
        if e.type == pygame.MOUSEBUTTONDOWN:
            if state == 0:
                screen.blit(background, (0, 0))
                rect_list = menu0.update_mouse()
            if state == 2:
                screen.blit(background, (0, 0))
                rect_list = menu1.update_mouse()
                highscores.draw(screen)
                if reset:
                    highscores.empty()
            if state == 3:
                screen.blit(background, (0, 0))
                rect_list = menu2.update_mouse()
                # Defaultfont
                banner_music.my_font = font.Font(None, menu2.menu_items[0]['u_image'].get_bitsize())
                banner_fps.my_font = font.Font(None, menu2.menu_items[0]['u_image'].get_bitsize())
                if music_state is True:
                    banner_music.update("ON")
                    banner_music.set_color(ON_COLOR)
                if music_state is False:
                    banner_music.update("OFF")
                    banner_music.set_color(OFF_COLOR)
                if show_FPS is True:
                    banner_fps.update("ON")
                    banner_fps.set_color(ON_COLOR)
                if show_FPS is False:
                    banner_fps.update("OFF")
                    banner_fps.set_color(OFF_COLOR)
                banner_music.rect.x = menu2.menu_items[1]['offset'][0] + menu2.menu_items[1]['rect'].width
                banner_music.rect.y = menu2.menu_items[1]['offset'][1]
                banner_fps.rect.x = menu2.menu_items[2]['offset'][0] + menu2.menu_items[2]['rect'].width
                banner_fps.rect.y = menu2.menu_items[2]['offset'][1]
                banners.draw(screen)

        # Quits if the user presses the exit button
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Updates the screen
        if rect_list[0] is not None:
            pygame.display.update(screen.get_rect())
        else:
            pygame.display.update(rect_list)


# Function responsible for the ready screen
def readyinstance(screen, background, windowSize):
    arrayready = []
    # Load settings and sounds
    settings = loadsettings(settings_file)
    sounds = loadsound(["sfx_countdown.ogg"])
    if settings[0]:
        sounds['countdown'].play()
    # Creation of banner GO! with the characteristics we want
    banner_go = Banner("GO!", 72)
    banner_go.set_color(selected_item_color)
    banner_go.center(windowSize, True, False)
    # Creation of 3 banners for the countdown (3,2,1)
    for i in range(3, 0, -1):
        temp = Banner(str(i) + "!", 72)
        temp.set_color(selected_item_color)
        temp.center(windowSize, True, False)
        arrayready.append(temp.image)
    # Animate the banners
    arrayready.append(banner_go.image)
    animatelist = createanimationlist(arrayready, 1.3)
    animobj = pyganim.PygAnimation(animatelist, loop=False)
    animobj.play()
    # Bird's start position
    temp = [0, 0]
    # Creation of the bird
    bird1 = Bird()
    loadbird(bird1)
    # Random position that the bird has to reach to make his path
    randompos = [random.randint(0+bird1.rect.width, windowSize[0]/4),
                 random.randint(0+bird1.rect.height, windowSize[1]-bird1.rect.height*2)]
    # Bird animation
    animatelist1 = createanimationlist(bird1.frames, wingsanimationspeed)
    animobj1 = pyganim.PygAnimation(animatelist1, loop=True)
    animobj1.play()

    while 1:
        # Until he reaches the random position this flow corrects bird's position
        if temp != randompos:
            if temp[0] < randompos[0]:
                temp[0] += 0.5
            if temp[0] > randompos[0]:
                temp[0] -= 0.5
            if temp[1] < randompos[1]:
                temp[1] += 0.5
            if temp[1] > randompos[1]:
                temp[1] -= 0.5
        else:
            # If the bird arrived at the random position, we generate another (this process only ends when the countdown
            # reaches GO!)
            randompos = [random.randint(0+bird1.rect.width, windowSize[0]/4),
                         random.randint(0+bird1.rect.height, windowSize[1]-bird1.rect.height*2)]

        ev = event.poll()
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        screen.blit(background, (0, 0))
        animobj.blit(screen,
                     (windowSize[0] / 2 - animobj.getCurrentFrame().get_rect().width / 2, windowSize[1] / 2 -
                      animobj.getCurrentFrame().get_rect().height / 2))
        animobj1.blit(screen, temp)
        pygame.display.flip()
        # We start the game when the banners' animation is finished
        if animobj.isFinished() is True or animobj.state == 'stopped':
            return temp


# Function responsible for sounds, drawing, etc, when the user is out of lifes
def killscreen(bird, sounds, screen, background, banner, pipes, textscore, settings, fps_banner, fpsclock, x, x1):
        # Plays the die sound (if the user have chosen that option in the settings menu)
        if settings[0]:
            sounds['die'].play(loops=True, maxtime=0, fade_ms=0)
        animatelist = createanimationlist(bird.down, downanimationspeed)
        animobj = pyganim.PygAnimation(animatelist, loop=False)
        animobj.play()
        # The position where the bird hits the pipe or the top/bottom of the screen
        temp = [bird.rect.x, bird.rect.y]
        fps_bannerg = Group(fps_banner)
        # Creates the animation required for the bird's fall
        animatelist1 = createanimationlist(bird.down[-8:], wingsanimationspeed)
        animobj1 = pyganim.PygAnimation(animatelist1, loop=True)
        # Plays the animation
        animobj1.play()
        # Does these animations and stops the background scroll while the bird hasn't reached the bottom of the screen
        while temp[1] < windowSize[1] - bird.rect.height / 2:
            # How hard the bird falls (0.2). This is incremented in the Y coordinates of the bird.
            temp[1] += 0.2
            # Fixes the background
            screen.blit(background, (x, 0))
            screen.blit(background, (x1, 0))
            # Updates the banner for "YOU LOST" instead of "YOU LOST A LIFE!"
            banner.update("YOU LOST!")
            banner.center(windowSize, True, False)
            # Draws the pipes
            pipes.draw(screen)
            animobj.blit(screen, temp)
            # Blitting of the elements needed
            screen.blit(banner.image, (banner.rect.x, banner.rect.y))
            screen.blit(textscore.image, (textscore.rect.x, textscore.rect.y))
            if animobj.isFinished() is True or animobj.state == 'stopped':
                animobj1.blit(screen, temp)
            # Displays FPS banner (if the user have chosen that option in the settings menu)
            if settings[1]:
                fps_banner.update(str(round(fpsclock.get_fps(), 2)))
                fps_bannerg.draw(screen)
            pygame.display.flip()

            ev = event.poll()
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
