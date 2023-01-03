import math
import random
from collections import defaultdict
from typing import List
import numpy as np
import perlin
from scipy.spatial import Voronoi

from Shapes import TerrainTile

NUM_PLATES = 15
WIDTH, HEIGHT = 720, 720
PLATE_MELTED_DISTANCE = 2
PLATE_MELTED_THICKNESS = 2
p = perlin.Perlin(203)
random.seed(20)


def polygons_to_rects(polygons, plates, pixel_size):
    max_x = WIDTH // pixel_size
    max_y = HEIGHT // pixel_size
    rectangles = np.empty((max_y, max_x), dtype=object)
    for y in range(max_y):
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

            tile = TerrainTile(
                rect_x,
                rect_y,
                pixel_size,
                pixel_size,
                terrain,
                plates[poly_idx].color,
                poly_idx
            )
            rectangles[y][x] = tile

    return rectangles


# Write a function called highlight edges that takes a list of plates and a list of rectangles, and returns a list of
# rectangles where if a rectangle is next to another rectangle whose corresponding plate is pointing in a different
# direction, it is highlighted
def highlight_edges(plates, rectangles):
    for y, row in enumerate(rectangles):
        for x, rect in enumerate(row):
            if rect.plate_index == -1:
                continue
            rectangles[y][x] = hightlight_single_tile_edge(plates, rectangles, x, y)

    return rectangles


def hightlight_single_tile_edge(plates, rectangles, x, y):
    rect = rectangles[y][x]
    row = rectangles[y]
    # ensure this rect only borders other rects that are part of the same plate
    is_border_plate = False
    for dy in range(-PLATE_MELTED_DISTANCE, PLATE_MELTED_DISTANCE + 1):
        for dx in range(-PLATE_MELTED_DISTANCE, PLATE_MELTED_DISTANCE + 1):
            if dx == 0 and dy == 0:
                continue
            if 0 <= y + dy < len(rectangles) and 0 <= x + dx < len(row):
                is_border_plate = is_border_plate or rectangles[y + dy][x + dx].plate_index != rect.plate_index
    if is_border_plate:
        return rect

    for dy in [-PLATE_MELTED_DISTANCE - PLATE_MELTED_THICKNESS, 0,
               PLATE_MELTED_DISTANCE + PLATE_MELTED_THICKNESS]:
        for dx in [-PLATE_MELTED_DISTANCE - PLATE_MELTED_THICKNESS, 0,
                   PLATE_MELTED_DISTANCE + PLATE_MELTED_THICKNESS]:
            if dx == 0 and dy == 0:
                continue
            if 0 <= y + dy < len(rectangles) and 0 <= x + dx < len(rectangles[0]):
                t = rectangles[y + dy][x + dx]
                if t.plate_index != -1 and t.plate_index != rect.plate_index:
                    approach = tiles_moving_toward_each_other(plates, rect, t)
                    if approach > 0:
                        # rect.highlight = True
                        # Map the value of approach to between 0 and 1
                        red_color = min(1, approach / 1)
                        # Map the value of approach to between 70 and 255
                        red_color = int(red_color * 175 + 80 + rect.color[0])
                        red_color = min(255, red_color)
                        rect.color = (red_color, rect.color[1], rect.color[2], rect.color[3])
    return rect


def tiles_moving_toward_each_other(plates, tile1, tile2):
    plate1 = plates[tile1.plate_index]
    plate2 = plates[tile2.plate_index]
    direction1 = plate1.direction
    direction2 = plate2.direction
    center1 = np.array([tile1.x / float(WIDTH), tile1.y / float(HEIGHT)])
    center2 = np.array([tile2.x / float(WIDTH), tile2.y / float(HEIGHT)])
    # compare if two points are moving towards each other by moving to the frame of reference of the first point
    # and then checking if the second point is moving towards the origin

    # move the second point to the frame of reference of the first point
    new_center2 = center2 - center1
    new_direction2 = direction2 - direction1
    return np.dot(new_direction2, new_center2)


def disturb_rectangles_with_perlin_noise(rectangles, strength):
    """Modifies a list of TerrainTile objects by changing their type based on the value of Perlin noise at their location.

    Args:
    - rectangles: a list of TerrainTile objects
    - scale: the scale of the Perlin noise
    - strength: the strength of the disturbance, between 0 and 1
    """
    for row in rectangles:
        for rect in row:
            # Calculate the noise value at the location of the rectangle
            x = rect.x / WIDTH
            y = rect.y / HEIGHT
            noise_value = p.two(x, y)

            # Change the type of the rectangle based on the noise value and the strength
            if noise_value > 0.1:
                match rect.terrain:
                    case "WATER":
                        rect.terrain = "GRASS"
                    case "GRASS":
                        rect.terrain = "MOUNTAIN"
    return rectangles


# A function that takes a list of tiles and applies gaussian blur to it
def gaussian_blur(tiles: List[List[TerrainTile]], iterations: int) -> List[List[TerrainTile]]:
    if iterations == 0:
        return tiles
    # Create a copy of the input tile grid
    # new_grid = [row[:] for row in tiles]
    new_grid = []

    # Iterate through each tile in the grid
    for y, row in enumerate(tiles):
        new_row = []
        for x, tile in enumerate(row):
            # Get the surrounding tiles
            color_count = defaultdict(int)
            plate_count = defaultdict(int)
            new_tile = tile.__copy__()
            smoothing_radius = 3
            for dy in range(-smoothing_radius, smoothing_radius + 1):
                for dx in range(-smoothing_radius, smoothing_radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    if 0 <= y + dy < len(tiles) and 0 <= x + dx < len(row):
                        t = tiles[y + dy][x + dx]
                        color_count[t.color] += 1
                        plate_count[t.plate_index] += 1

            # Calculate the average surface of the surrounding tiles
            avg_color = max(color_count, key=color_count.get)
            avg_plate = max(plate_count, key=plate_count.get)

            # if avg_color != tile.color:
            # new_tile.highlight = True

            # Set the surface of the current tile to the average surface
            new_tile.color = avg_color
            new_tile.plate_index = avg_plate
            new_row.append(new_tile)

        new_grid.append(new_row)

    # Return the new grid
    return gaussian_blur(new_grid, iterations - 1)


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
                        count[t.color] += 1

            # Calculate the average surface of the surrounding tiles
            avg_color = max(count, key=count.get)

            if avg_color != tile.color:
                print(f"({x}, {y}) {tile.color} -> {avg_color}")
                tile.highlight = True
                # tile.color = (255, 0, 0)
            new_grid[y][x].color = avg_color

    return smooth_edges(new_grid, iterations - 1)


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


def get_points(num, width, height):
    random.seed(10)
    points = [[random.randrange(width), random.randrange(height)]
              for _ in range(num)]
    points.append([-width * 3, -height * 3])
    points.append([-width * 3, height * 4])
    points.append([width * 4, -height * 3])
    points.append([width * 4, height * 4])
    return np.array(points)


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
        angle = random.random() * 360
        self.direction = np.array([np.cos(angle), np.sin(angle)])
        norm = np.linalg.norm(self.direction)
        self.direction = self.direction / norm
        self.water = water
        if water:
            self.color = (0, 0, random.randint(200, 255), 255)
        else:
            self.color = (0, random.randint(200, 255), 0, 255)

    def __str__(self):
        return f"Plate {self.id} at {self.center} with direction {self.direction}"


def get_plates():
    plate_centers = get_points(NUM_PLATES, WIDTH, HEIGHT)
    # Create a list of plates
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
        plate = Plate(i, center=center, water=plate_is_water)
        plates.append(plate)
    return plates
