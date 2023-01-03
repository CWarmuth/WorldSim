import numpy as np
import pygame
from Plates import get_voronoi, polygons_to_rects, get_points, gaussian_blur, highlight_edges, WIDTH, HEIGHT, \
    NUM_PLATES, get_plates, disturb_rectangles_with_perlin_noise

# Constants

DRAW_VORONOI_POLYGONS = False
PIXEL_WIDTH = 5


def main():
    # Set up Pygame window and canvas
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    canvas = pygame.Surface((WIDTH, HEIGHT))
    pygame.init()

    # Set up initial conditions
    plates = get_plates()

    toggle_highlight = True

    canvas.fill((255, 255, 255))

    generate_map(canvas, plates, toggle_highlight)

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            # Check if the mouse is clicked:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the mouse is clicked, toggle the highlight
                toggle_highlight = not toggle_highlight
                canvas.fill((255, 255, 255))
                generate_map(canvas, plates, toggle_highlight)

            if event.type == pygame.QUIT:
                running = False
            # If space is pressed, generate a new map
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    canvas.fill((255, 255, 255))
                    plates = get_plates()
                    generate_map(canvas, plates, toggle_highlight)

        # Do logic

        # Clear canvas

        # Draw arrows on the centers of the plates
        for plate in plates:
            draw_arrow_on_plate_center(plate, canvas)
            draw_plate_number(plate, canvas)

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

def generate_map(canvas, plates, toggle_highlight):
    plate_centers = get_points(NUM_PLATES, WIDTH, HEIGHT)
    voronoi_polys = get_voronoi(plate_centers)
    rects = polygons_to_rects(voronoi_polys, plates, PIXEL_WIDTH)
    rects = gaussian_blur(rects, 5)
    rects = disturb_rectangles_with_perlin_noise(rects, 0.5)
    highlight_edges(plates, rects)
    print("Created rects with {} rectangles: ".format(len(rects)))
    for x, strip in enumerate(rects):
        for y, rect in enumerate(strip):
            if rect.highlight and toggle_highlight:
                color = (255, 0, 0)
            else:
                color = rect.color
            pygame.draw.rect(canvas, color,
                             (rect.x, rect.y, rect.width, rect.height))


if __name__ == "__main__":
    main()
