import numpy as np
import pygame
from Plates import get_voronoi, polygons_to_rects, get_points, gaussian_blur, highlight_edges, WIDTH, HEIGHT, \
    NUM_PLATES, get_plates, disturb_rectangles_with_perlin_noise, disturb_tiles, highlight_tiles

# Constants

DRAW_VORONOI_POLYGONS = False


def main():
    # Set up Pygame window and canvas
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    canvas = pygame.Surface((WIDTH, HEIGHT))
    pygame.init()

    toggle_highlight = True

    canvas.fill((255, 255, 255))

    rect_map, plates = generate_map(canvas, toggle_highlight)

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            # Check if the mouse is clicked:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the mouse is clicked, toggle the highlight
                toggle_highlight = not toggle_highlight
                draw(canvas, rect_map, toggle_highlight, plates)
            if event.type == pygame.QUIT:
                quit()
            elif event.type == pygame.QUIT:
                running = False
            # If space is pressed, generate a new map
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    canvas.fill((255, 255, 255))

                    rect_map, plates = generate_map(canvas, toggle_highlight)

        # Do logic

        # Clear canvas

        # Update window
        window.blit(canvas, (0, 0))
        pygame.display.update()


def draw_arrow_on_plate_center(plate, canvas):
    # Draw an arrow on the center of the plate
    x, y = plate.center
    direction = plate.direction
    # draw a line pointing towards the direction of the plate at its center
    pygame.draw.line(canvas, (0, 0, 0), (x, y), (x + 30 * direction[0], y + 30 * direction[1]), 2)
    # Add a circle at the beginning of the arrow
    pygame.draw.circle(canvas, (0, 0, 0), (x, y), 5)


def draw_plate_number(plate, canvas):
    # Draw the number of the plate on the center of the plate
    x, y = plate.center
    font = pygame.font.SysFont('Sans-Serif', 20)
    text = font.render(str(plate.id), True, (0, 0, 0))
    canvas.blit(text, (x, y + 15))


def draw(canvas, rects, toggle_highlight, plates):
    for x, strip in enumerate(rects):
        for y, rect in enumerate(strip):
            if rect.highlight and toggle_highlight:
                color = (255, 0, 0, 255)
            else:
                color = rect.color
            pygame.draw.rect(canvas, color,
                             (rect.x, rect.y, rect.width, rect.height))
    draw_ui(canvas, plates)


def generate_map(canvas, toggle_highlight):
    # Set up initial conditions
    plates = get_plates()
    rects = polygons_to_rects(plates)
    rects = gaussian_blur(rects, 3)
    # rects = smooth_edges(rects, 1)
    # rects = disturb_rectangles_with_perlin_noise(rects, 0.5)
    rects = disturb_tiles(rects, plates)
    # highlight_edges(plates, rects)
    print("Created rects with {} rectangles: ".format(len(rects) * len(rects[0])))
    draw(canvas, rects, toggle_highlight, plates)

    return rects, plates


def draw_ui(canvas, plates):
    # Draw arrows on the centers of the plates
    for plate in plates:
        draw_arrow_on_plate_center(plate, canvas)
        draw_plate_number(plate, canvas)


if __name__ == "__main__":
    main()
