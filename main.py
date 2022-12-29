import perlin

from Shapes import QuadTree, TerrainTile

import pygame
from Plates import get_voronoi, Plate, polygons_to_rects, get_points, smooth_edges

# Constants
DRAW_VORONOI_POLYGONS = False
PIXEL_WIDTH = 5
NUM_PLATES = 15


def main():
    # Set up Pygame window and canvas
    width, height = 720, 720
    window = pygame.display.set_mode((width, height))
    canvas = pygame.Surface((width, height))
    p = perlin.Perlin(100)

    # Set up initial conditions
    plate_centers = get_points(NUM_PLATES, width)
    voronoi_polys = get_voronoi(plate_centers)  # Replace with function to generate Voronoi polygons
    plates = []

    # Define the x and y coordinates of the center of the plate

    for i in range(NUM_PLATES):
        # Generate the perlin noise value at the center of the plate
        center = plate_centers[i]

        plate_center_noise = p.two(center[0], center[1])

        # Set the value of plate_is_water based on the perlin noise value at the center of the plate
        if plate_center_noise > 0.5:
            plate_is_water = True
        else:
            plate_is_water = False
        plate = Plate(i, center=center, water=plate_is_water)  # Replace with function to create Plate objects
        plates.append(plate)
    rects = polygons_to_rects(voronoi_polys, plates, width, height,
                              PIXEL_WIDTH)  # Replace with function to convert polygons to rectangles
    rects = smooth_edges(rects, 20)
    print("Created rects with {} rectangles: ".format(len(rects)))

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Do logic

        # Clear canvas
        canvas.fill((255, 255, 255))

        # Draw rectangles
        for x, strip in enumerate(rects):
            for y, rect in enumerate(strip):
                color_option = plates[rect.plate_index].color
                color = color_option  # Plate's color if not overlapped
                pygame.draw.rect(canvas, color,
                                 (rect.x, rect.y, rect.width, rect.height))  # Replace with function to draw rectangle

        # Update window
        window.blit(canvas, (0, 0))
        pygame.display.update()


if __name__ == "__main__":
    main()
