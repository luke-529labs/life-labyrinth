import pygame
import constants
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    pygame.display.set_caption("Life Labyrinth MVP")
    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # --- Pass relevant input events to the game object --- #
            elif event.type == pygame.MOUSEBUTTONDOWN:
                 game.handle_input(event) # Let game handle clicks based on phase
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game.phase == constants.SETUP_PHASE:
                    game.start_simulation()
                # Add optional R key for reset during setup/sim if desired
                # elif event.key == pygame.K_r and (game.phase == constants.SETUP_PHASE or game.phase == constants.SIMULATION_PHASE):
                #     game.reset_level()


        # --- Update game logic based on phase ---
        # Update only runs during simulation phase
        if game.phase == constants.SIMULATION_PHASE:
             game.update() # Run one simulation step per frame

        # Drawing (always happens)
        screen.fill(constants.BLACK)
        game.draw(screen)
        pygame.display.flip()

        clock.tick(100) # Target 100 frames per second (100 simulation steps/sec)

    pygame.quit()

if __name__ == '__main__':
    main() 