# -*- coding: utf-8 -*-
from pygame import *
from pygame.sprite import *
from Gfunctions import *
# Needed to "compile" the exe with pygame2exe
#import pygame._view

# Initializing the engine (graphical and sound)
pygame.init()
pygame.mixer.init(44100, -16, 2, 65536)
# Miscellaneous Variables related to the game, quite self-explanatory
windowSize = (800, 480)
screen = display.set_mode(windowSize)
display.set_caption("Flappy Bird")
os.environ['SDL_VIDEO_CENTERED'] = '1'
settings_file = "settings.ini"
scores_file = "scores.txt"
# Pipe scaled at
pipescale = 0.6
#load images (related to performance issues, we should load the images only once)
background = pygame.image.load(loadimage("background.png")).convert_alpha()
pipeimage = image.load(loadimage("pipe.png")).convert_alpha()
pipeimage = pygame.transform.rotozoom(pipeimage, 0, pipescale)
pipe_pair_image = pygame.transform.flip(pipeimage, False, True)


# Function that starts new game calling the functions required in order
def startnewgame():
    # start menu
    startmenu(screen, background)
    # ready screen
    birdpos = readyinstance(screen, background, windowSize)
    # main loop for the game
    game(birdpos)


# Function responsible for drawing the end game menu
def endgame(screen, background):
    screen.blit(background, (0, 0))
    pygame.display.flip()

    #Create Menus
    menu0 = cMenu(50, 50, 20, 5, 'vertical', 100, screen,
                  [('Yes', 1, None),
                   ('No', 2, None)])

    # Color for unselected text
    menu0.u_color = unselected_item_color
    # Color for selected text
    menu0.s_color = selected_item_color
    # Center the menu on the draw_surface (the entire screen here)
    menu0.set_center(True, True)
    # Center the menu on the draw_surface (the entire screen here)
    menu0.set_alignment('center', 'center')
    state = 0
    prev_state = 1
    rect_list = []
    # Banner asking if the user wants to start a new game
    continue_banner = Banner("Start New Game?", 50)
    continue_banner.center(windowSize, True, False)
    continue_banner.set_color((0, 25, 107))
    continue_banner.rect.y = 40
    banners = Group(continue_banner)

    # The main while loop
    while 1:
        # Check if the state has changed, if it has, then post a user event to
        # the queue to force the menu to be shown at least once
        if prev_state != state:
            pygame.event.post(pygame.event.Event(EVENT_CHANGE_STATE, key=0))
            prev_state = state

        # Get the next event
        e = pygame.event.wait()
        # Update the menu, based on which "state" we are in
        if e.type == pygame.KEYDOWN or e.type == EVENT_CHANGE_STATE:
            if state == 0:
                screen.blit(background, (0, 0))
                rect_list, state = menu0.update(e, state)
                banners.draw(screen)
                if state is not 0:
                    pygame.display.flip()
            elif state == 1:
                startnewgame()
            elif state == 2:
                pygame.quit()
                sys.exit()
            else:
                print 'Exit!'
                pygame.quit()
                sys.exit()
        #makes the selection based on mouse input
        menu0.update_mouse()

        # Quit if the user presses the exit button
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Update the screen
        if rect_list[0] is not None:
            pygame.display.update(screen.get_rect())
        else:
            pygame.display.update(rect_list)


# Main game function, only receives one argument, the position where the bird starts, depending on the position
# generated on the readyscreen
def game(birdpos):
    # pre-load sfx effects
    sounds_str = ["sfx_die.ogg", "sfx_hit.ogg", "sfx_point.ogg", "sfx_wing.ogg"]
    sounds = loadsound(sounds_str)
    settings = loadsettings(settings_file)
    # initializing the variable to start drawing pipes on the screen
    initpipes = 1
    # initializing score
    score = 0
    # set number of lifes
    numberlifes = 2
    # starting the internal clock to 'lock' the number of frames per second
    fpsclock = pygame.time.Clock()
    # variable to check if the user clicked on MOUSEBUTTON
    clicked = 0
    # temporary variable to store collisions, useful later on
    temp1 = []
    # starting x coordinates to scroll the background
    x = windowSize[0]
    x1 = 0
    # FPS banner (it's always created, it only is displayed if the user selected that option)
    fps_banner = Banner(str(fpsclock.get_fps()), 20)
    fps_banner.set_color((255, 255, 0))
    fps_banner.rect.y = 0
    fps_banner.rect.right = windowSize[0]-fps_banner.rect.width
    fps_bannerg = Group(fps_banner)
    # create sprites for lifes
    startlifes = generatelifes(numberlifes)
    # creating the bird
    bird1 = Bird()
    # bird starts at the random position generated on the ready screen
    bird1.rect.x = birdpos[0]
    bird1.rect.y = birdpos[1]
    # loading frames
    loadbird(bird1)
    birds = Group(bird1)
    # Creating the banner in case the user lost a life
    banner1 = Banner("YOU LOST A LIFE!", 80)
    banner1.set_color((0, 25, 107))
    banner1.center(windowSize, True, False)
    banners = Group(banner1)
    # Groups for pipe sprites and hitbox sprites
    pipes = Group()
    hitboxesg = Group()
    # Banner for the score
    textscore = Banner(str(score), textscoresize)
    textscore.rect.y = 30
    textscore.center(windowSize, True, False)
    # Groups for score and lifes
    scorebanner = Group(textscore)
    lifes = Group(startlifes)
    while True:
        ev = event.poll()
        # Event if the user closes the game window
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Starts creating and drawing the first set of pipes, variable initpipes takes value 0 after (this cycle is
        # only run one time, when the game is starting).
        if initpipes:
            (arraypipes, hitboxes) = generatepipes(numbersetpipes, pipeimage, pipe_pair_image)
            initpipes = 0
            pipes.add(arraypipes)
            hitboxesg.add(hitboxes)
            temporaryarray = arraypipes
            temporaryarray2 = hitboxes
        # This is the cycle that is always called during the game (after the first set is created). The next set of
        # pipes is created and drawn after the 1st pipe of the previous set is out of the screen
        if arraypipes[0].inscreen == 0:
            temporaryarray = arraypipes
            temporaryarray2 = hitboxes
            (arraypipes, hitboxes) = generatepipes(numbersetpipes, pipeimage, pipe_pair_image)
            pipes.add(arraypipes)
            hitboxesg.add(hitboxes)
        # Calling the function to check if it's safe to remove the old pipes and hitboxes
        checkpipes(temporaryarray, temporaryarray2, pipes, hitboxesg)
        # Scrolls the background
        (x, x1) = scroll(background, screen, x, x1)
        # Bird's default animation of clapping wings, is called whenever the bird isn't jumping
        if bird1.animobj.isFinished() or bird1.animobj.state == 'stopped':
            bird1.animate(bird1.frames, wingsanimationspeed)
        # If the user clicks the mouse:
        if ev.type == MOUSEBUTTONDOWN:
            # Plays the sound of wings clapping (if the user have chosen that option in the settings menu)
            if settings[0]:
                sounds['wing'].play()
            # Animates the bird to jump a little
            bird1.animate(bird1.up + bird1.up[::-1], upanimationspeed)
            # Puts the bird Y units above, simple jump, doesn't smooth anything
            bird1.velocity = - birdjump
            # States that the user clicked the mouse
            clicked = 1
        else:
            # Reset the velocity, bird shouldn't fall as hard after clicking
            if clicked == 1:
                bird1.velocity = 0
                clicked = 0
        # Update all the elements in the screen
        draw_update_elements(pipes, hitboxesg, scorebanner, lifes, bird1, textscore, screen)
        # Stores the collision between the bird and the pipes
        birdhit = pygame.sprite.spritecollideany(bird1, pipes, collide_mask)
        # Stores the collision between the bird and the "flag" for points (end of the pair of pipes)
        birdscore = pygame.sprite.groupcollide(birds, hitboxesg, False, False)
        # Checks if the bird hits a pipe or top/bottom of the screen and the user has still lifes left
        if birdhit is not None and numberlifes > 1 or (bird1.rect.top > windowSize[1] - bird1.rect.height / 2
            and numberlifes > 1) or (bird1.rect.centery < 0 and numberlifes > 1):
            # Plays the sound of hitting (if the user have chosen that option in the settings menu)
            if settings[0]:
                sounds['hit'].play(loops=0, maxtime=0, fade_ms=100)
            # Decreases the lifes number by 1
            numberlifes -= 1
            # Draws the banner "You Lost a Life!"
            banners.draw(screen)
            pygame.display.flip()
            # Wait 3 seconds before starting again
            pygame.time.wait(3000)
            # Resets everything
            reset(bird1, birds, pipes, hitboxesg)
            # Update lifes
            lifes = updatelifes(numberlifes, lifes)
            lifes.draw(screen)
            # Resets the list of "hits"
            birdscore = []
            # Initializes the first set of pipes again
            initpipes = 1
            # Resets the temporary list
            temp1 = []
        # Checks if the bird hits a pipe or top/bottom of the screen and the user has no lifes left
        elif birdhit is not None and numberlifes == 1 or (bird1.rect.top > windowSize[1] - bird1.rect.height / 2
            and numberlifes == 1) or (bird1.rect.centery < 0 and numberlifes == 1):
            # Saves the score
            savescore(score, scores_file, False)
            # Calls the function killscreen
            killscreen(bird1, sounds, screen, background, banner1, pipes, textscore,
                       settings, fps_banner, fpsclock, x, x1)
            # Show the endgame menu
            endgame(screen, background)
        # Checks if the user scored a point (since the bird and the hitbox generates multiple collisions when the bird
        # is traveling through the hitbox, we have to make a check, just to count the score on the first collision)
        if len(birdscore) != 0:
            # temp1 stores the collisions
            temp1.append(birdscore[birdscore.keys()[0]])
            # this prints are useful to understand the mechanism
            ## print("temp1 hitbox: " + str(temp1[len(temp1)-1][0].rect.right - 3))
            ## print("bird x :" + str(bird1.rect.x))

            # if it's the first collision we can add a point to the score
            if len(temp1) == 1:
                # Plays the score point sound (if the user have chosen that option in the settings menu)
                if settings[0]:
                    sounds['point'].play(loops=0, maxtime=0, fade_ms=0)
                score += 1
                # updates the score
                textscore.update(str(score))
            # if the X coordinates of the hitbox is less than the X coordinates of the bird then it's safe to reset the
            # temporary list (so we can score a point in the hitbox) (-3 pixels is a safe number, it's a "sweet spot")
            if temp1[len(temp1)-1][0].rect.right-3 < bird1.rect.x:
                temp1 = []
        # Lock the FPS
        fpsclock.tick(fps)
        # Displays FPS banner (if the user have chosen that option in the settings menu)
        if settings[1]:
            fps_banner.update(str(round(fpsclock.get_fps(), 2)))
            fps_bannerg.draw(screen)
        display.flip()

    pygame.quit()

startnewgame()
