import math
import random
from collections import defaultdict
from typing import List

from scipy.spatial import Voronoi

from Shapes import TerrainTile

NUM_PLATES = 15

random.seed(20)


def polygons_to_rects(polygons, plates, width, height, pixel_size):
    max_x = width // pixel_size
    max_y = height // pixel_size
    rectangles = []
    for y in range(max_y):
        x_strip = []
        for x in range(max_x):
            #  Loop through rects and determine what polygon it lies in
            poly_idx = next(
                (i for i, poly in enumerate(polygons)
                 if point_in_polygon((x * pixel_size, y * pixel_size), poly)), 0) - 1
            rect_x = x * pixel_size - pixel_size // 2
            rect_y = y * pixel_size - pixel_size // 2

            if plates[poly_idx].water:
                terrain = "WATER"
            else:
                terrain = "GRASS"

            x_strip.append(TerrainTile(
                rect_x,
                rect_y,
                pixel_size,
                pixel_size,
                terrain,
                poly_idx
            )
            )
        rectangles.append(x_strip)

    return rectangles


def smooth_edges(tile_grid: List[List[TerrainTile]], iterations) -> List[List[TerrainTile]]:
    if iterations == 0:
        return tile_grid
    # Create a copy of the input tile grid
    new_grid = [row[:] for row in tile_grid]

    # Iterate through each tile in the grid
    for y, row in enumerate(tile_grid):
        for x, tile in enumerate(row):
            # Get the surrounding tiles
            surrounding_tiles = []
            count = defaultdict(int)
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    if 0 <= y + dy < len(tile_grid) and 0 <= x + dx < len(row):
                        t = tile_grid[y + dy][x + dx]
                        surrounding_tiles.append(t)
                        count[t.surface] += 1

            # Calculate the average surface of the surrounding tiles
            max_surface = max(count)
            if max_surface != tile.surface:
                x = random.random()
                print("Maybe")

            new_grid[y][x].surface = max_surface

    return smooth_edges(new_grid, iterations - 1)


def smooth_edges_newer(rectangles: List[List[TerrainTile]], iterations) -> List[List[TerrainTile]]:
    # List to store the smooth rectangles
    smooth_rectangles = []

    if iterations == 0:
        return rectangles

    # Iterate over the rows and columns of the rectangles
    for y, row in enumerate(rectangles):
        smooth_row = []
        for x, rectangle in enumerate(row):
            # Add the current rectangle to the smooth rectangles list
            smooth_row.append(rectangle)

            # Check if the current rectangle has a different surface type than its left neighbor
            if x > 0 and rectangle.surface != rectangles[y][x - 1].surface:
                # Calculate the x, y, width, and height of the transition rectangle
                width = rectangle.width
                height = rectangle.height

                # Create a transition rectangle with the calculated values and the surface type of the current rectangle
                transition_rectangle = TerrainTile(x, y, width, height, rectangle.surface, rectangle.plate_index)

                # Add the transition rectangle to the smooth rectangles list
                smooth_row.append(transition_rectangle)

            # Check if the current rectangle has a different surface type than its top neighbor
            if y > 0 and rectangle.surface != rectangles[y - 1][x].surface:
                # Calculate the x, y, width, and height of the transition rectangle
                width = rectangle.width
                height = 1

                # Create a transition rectangle with the calculated values and the surface type of the current rectangle
                transition_rectangle = TerrainTile(x, y, width, height, rectangle.surface, rectangle.plate_index)

                # Add the transition rectangle to the smooth rectangles list
                smooth_row.append(transition_rectangle)
        smooth_rectangles.append(smooth_row)

    # Return the list of smooth rectangles
    return smooth_edges(smooth_rectangles, iterations - 1)


def smooth_edges_old(rectangles: List[TerrainTile], iterations) -> List[TerrainTile]:
    # List to store the smooth rectangles
    smooth_rectangles = []
    # Iterate over the rectangles and smooth the edges between plates with different surface types
    for i, rectangle in enumerate(rectangles):
        # Add the current rectangle to the smooth rectangles list
        smooth_rectangles.append(rectangle)

        # Check if the current rectangle has a different surface type than its left neighbor
        if i > 0 and rectangle.surface != rectangles[i - 1].surface:
            # Calculate the x, y, width, and height of the transition rectangle
            x = rectangle.x - 1
            y = rectangle.y
            width = 1
            height = rectangle.height

            # Create a transition rectangle with the calculated values and the surface type of the current rectangle
            transition_rectangle = TerrainTile(x, y, width, height, rectangle.surface, rectangle.plate_index)

            # Add the transition rectangle to the smooth rectangles list
            smooth_rectangles.append(transition_rectangle)

        # Check if the current rectangle has a different surface type than its top neighbor
        if i > 0 and rectangle.surface != rectangles[i - 1].surface:
            # Calculate the x, y, width, and height of the transition rectangle
            x = rectangle.x
            y = rectangle.y - rectangle.width
            width = rectangle.width
            height = 1

            # Create a transition rectangle with the calculated values and the surface type of the current rectangle
            transition_rectangle = TerrainTile(x, y, width, height, rectangle.surface, rectangle.plate_index)

            # Add the transition rectangle to the smooth rectangles list
            smooth_rectangles.append(transition_rectangle)

        # Return the list of smooth rectangles
    if iterations > 0:
        return smooth_edges(smooth_rectangles, iterations - 1)
    return smooth_rectangles


def point_in_polygon(point, polygon):
    x, y = point
    winding_number = 0
    for i in range(len(polygon)):
        j = (i + 1) % len(polygon)
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]
        if yi <= y:
            if yj > y and (xj - xi) * (y - yi) > (x - xi) * (yj - yi):
                winding_number += 1
        else:
            if yj <= y and (xj - xi) * (y - yi) < (x - xi) * (yj - yi):
                winding_number -= 1
    return winding_number != 0


def get_points(num, bounds):
    random.seed(10)
    points = [[random.randrange(bounds), random.randrange(bounds)]
              for _ in range(num)]
    points.append([-bounds * 3, -bounds * 3])
    points.append([-bounds * 3, bounds * 4])
    points.append([bounds * 4, -bounds * 3])
    points.append([bounds * 4, bounds * 4])
    return points


def get_voronoi(points):
    voronoi = Voronoi(points)

    voronoi_vertices = voronoi.vertices

    polygons = []
    for region in voronoi.regions:
        if -1 not in region:
            polygons.append([voronoi_vertices[p] for p in region])

    return polygons


class Plate:
    def __init__(self, plate_id, center, water):
        self.id = plate_id
        self.center = center
        self.depth = random.randint(0, 255)
        angle = random.random() * math.pi * 2
        self.direction = (math.sin(angle) / 10, math.cos(angle) / 10)
        self.water = water
        if water:
            self.color = (0, 0, random.randint(200, 255), 255)
        else:
            self.color = (0, random.randint(200, 255), 0, 255)
