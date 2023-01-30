import random
from collections import defaultdict
from typing import List
import numpy as np
import logging
from perlin_noise import PerlinNoise

from numpy import sign
from scipy.spatial import Voronoi

from Shapes import TerrainTile

NUM_PLATES = 15
WIDTH, HEIGHT = 720, 720
PLATE_MELTED_DISTANCE = 2
PLATE_MELTED_THICKNESS = 2
WATER_DENSITY_THRESHOLD = 0.5
# random.seed(20)
PIXEL_WIDTH = 5
noise = PerlinNoise(octaves=6)

logger = logging.getLogger(__name__)


def polygons_to_rects(plates):
    max_x = WIDTH // PIXEL_WIDTH
    max_y = HEIGHT // PIXEL_WIDTH
    rectangles = np.empty((max_y, max_x), dtype=object)

    for y in range(max_y):
        for x in range(max_x):
            #  Loop through rects and determine what polygon it lies in
            poly_idx = next(
                (i for i, plate in enumerate(plates)
                 if plate.polygon is not None and point_in_polygon((x * PIXEL_WIDTH, y * PIXEL_WIDTH), plate.polygon)), 0) - 1
            rect_x = x * PIXEL_WIDTH - PIXEL_WIDTH // 2
            rect_y = y * PIXEL_WIDTH - PIXEL_WIDTH // 2

            if plates[poly_idx].density > WATER_DENSITY_THRESHOLD:
                terrain = "WATER"
            else:
                terrain = "GRASS"

            tile = TerrainTile(
                rect_x,
                rect_y,
                PIXEL_WIDTH,
                PIXEL_WIDTH,
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


def highlight_tiles(tiles, p1, p2):
    hightlight_width = 4
    # Get the number of rows and columns in the tiles array
    # The line has a slope, so we need to iterate over each point on the line
    # and check the tiles around it
    if p1[0] == p2[0] and p1[1] == p2[1]:
        print("p1 and p2 are the same")
        return tiles
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    match abs(dx) > abs(dy):
        case True:
            steps = abs(dx)
            along_x = True
        case False:
            steps = abs(dy)
            along_x = False
        case _:
            print("dx and dy are fucked")
            along_x = None
            steps = 1

    # set direction to true if the lines moves down and it is along the x axis
    moving_down = dy > 0
    moving_right = dx > 0
    for i in range(steps + 2):
        x = p1[0] + i * dx // steps
        y = p1[1] + i * dy // steps

        upper = (not along_x and not moving_down) or (along_x and moving_right)

        if upper:
            rang = range(5, hightlight_width + 1 + 5)
        else:
            rang = range(-hightlight_width - 5, 1 - 5)

        for d in rang:
            if (along_x and 0 <= y + d < len(tiles) and 0 <= x < len(tiles[0])) or \
                    (not along_x and 0 <= x + d < len(tiles[0]) and 0 <= y < len(tiles)):

                match along_x:
                    case False:
                        tiles[y][x + d].highlight = True
                    case True:
                        tiles[y + d][x].highlight = True
                    case _:
                        print("along_x is fucked")

    return tiles


# TODO: Optimize so uses borders calculated before
def disturb_tiles(tiles, plates, scale=10.0, octaves=2):
    new_tiles = tiles.copy()
    # Get the number of rows and columns in the tiles array

    # Iterate over the plates
    for plate in plates:
        if plate.polygon is None:
            continue
        # Get the polygon defining the borders of the plate
        polygon = plate.polygon
        num_points = len(polygon)

        # Iterate over the points in the polygon
        for i in range(num_points):
            # Get the current point and the next point in the polygon
            p1 = polygon[i]
            p2 = polygon[(i + 1) % num_points]

            t1 = get_tile_at_point(p1)
            t2 = get_tile_at_point(p2)

            # Find the tiles that are along the border between the two points
            tiles_on_border = get_tiles_on_line(new_tiles, t1, t2)
            highlight_tiles(new_tiles, t1, t2)
            continue

            # Iterate over the tiles on the border
            for tile in tiles_on_border:
                # Get the tile index and position
                x, y = (tile.x, tile.y)
                tiles_plate = plates[tile.plate_index]

                # Use Perlin noise to determine if the tile should be disturbed
                # noise = p.two_octave(x / scale, y / scale, octaves=octaves)
                # print("noise", noise)
                # if noise > 0.5:
                print("highlighted tile at", x, y)
                # Modify the tile to be disturbed
                tile.highlight = True
                # Modify the corresponding plate to be disturbed
                match tiles_plate.type:
                    case "CONTINENTAL":
                        new_color = (0, 0, 255, 255)
                    case "OCEANIC":
                        new_color = (0, 255, 0, 255)
                    case _:
                        logger.error("Unknown plate type: %s", tiles_plate.type)
                        new_color = tiles_plate.color
                tile.color = new_color
    return new_tiles


def get_tile_at_point(point):
    x, y = point
    # Find what tile lies over the point, given that a tile has a width and height of 5
    tile_x = int(x // PIXEL_WIDTH)
    tile_y = int(y // PIXEL_WIDTH)
    return tile_x, tile_y


def get_tiles_on_line(tiles, t1, t2):
    # Initialize an empty list to store the tiles on the line
    tiles_on_line = []

    # Get the number of rows and columns in the tiles array
    num_rows = len(tiles)
    num_cols = len(tiles[0])

    # Get the x and y coordinates of the first and second tiles
    x1, y1 = t1
    x2, y2 = t2

    # Find the difference between the x and y coordinates of the two tiles
    dx = x2 - x1
    dy = y2 - y1

    # Find the absolute value of the difference between the x and y coordinates of the two tiles
    adx = abs(dx)
    ady = abs(dy)

    # Find the sign of the difference between the x and y coordinates of the two tiles
    sx = sign(dx)
    sy = sign(dy)

    # Find the error between the x and y coordinates of the two tiles
    err = adx - ady

    # Iterate over the tiles on the line
    while True:
        if 0 <= y1 < num_rows and 0 <= x1 < num_cols:
            tiles_on_line.append(tiles[y1][x1])

        # Check if the current tile is the second tile
        if x1 == x2 and y1 == y2:
            break

        # Find the error between the x and y coordinates of the two tiles
        e2 = 2 * err

        # Check if the error is greater than or equal to the absolute value of the difference between the y coordinates
        if e2 >= -ady:
            err -= ady
            x1 += sx

        # Check if the error is less than or equal to the absolute value of the difference between the x coordinates
        if e2 <= adx:
            err += adx
            y1 += sy

    return tiles_on_line


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
            x = rect.x
            y = rect.y
            noise_value = noise.noise([x / WIDTH, y / HEIGHT])

            # Change the type of the rectangle based on the noise value and the strength
            if noise_value > 1 - strength:
                match rect.surface:
                    case "WATER":
                        rect.change_surface("GRASS")
                        rect.highlight = True
                    case "GRASS":
                        rect.change_surface("WATER")
                        rect.highlight = True
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
            #     new_tile.highlight = True

            # Set the surface of the current tile to the average surface
            new_tile.color = avg_color
            new_tile.plate_index = avg_plate
            new_row.append(new_tile)

        new_grid.append(new_row)

    # Return the new grid
    return gaussian_blur(new_grid, iterations - 1)


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
    points = [[random.randrange(width), random.randrange(height)]
              for _ in range(num)]
    # Copy the points to, and move them the screen width's to the left
    points2 = [[x - width, y] for x, y in points]
    # Copy the points to, and move them the screen width's to the right
    points3 = [[x + width, y] for x, y in points]
    # Append to the points list
    points.extend(points2)
    points.extend(points3)

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


def get_plates():
    plate_centers = get_points(NUM_PLATES, WIDTH, HEIGHT)
    voronoi_polys = get_voronoi(plate_centers)
    # Create a list of plates
    plates = []
    # Define the x and y coordinates of the center of the plate
    for i in range(NUM_PLATES):
        # Generate the perlin noise value at the center of the plate
        plate_middle = make_plate(i, plate_centers[i], voronoi_polys[i])
        plate_left = make_plate(i, plate_centers[i], voronoi_polys[i + NUM_PLATES])
        plate_right = make_plate(i, plate_centers[i], voronoi_polys[i + NUM_PLATES * 2])
        plates.append(plate_middle)
        plates.append(plate_left)
        plates.append(plate_right)

    return plates

def make_plate(index, center, polygon):
    plate_center_noise = noise.noise(np.divide(center, [WIDTH / PIXEL_WIDTH, HEIGHT / PIXEL_WIDTH]))
    # Set the value of plate_is_water based on the perlin noise value at the center of the plate

    return Plate(index, center=center, density=plate_center_noise, polygon=polygon)

class Plate:
    def __init__(self, plate_id, center, density, polygon):
        self.type = None
        self.color = None
        self.id = plate_id
        self.center = center
        self.density = density
        angle = random.random() * 360
        self.direction = np.array([np.cos(angle), np.sin(angle)])
        norm = np.linalg.norm(self.direction)
        self.direction = self.direction / norm
        self.set_type_and_color()
        self.polygon = polygon

    def set_type_and_color(self):
        if self.density > 0:
            self.type = "OCEANIC"
            self.color = (random.randint(0, 20), random.randint(0, 20), random.randint(200, 255), 255)
        else:
            self.type = "CONTINENTAL"
            self.color = (random.randint(0, 20), random.randint(200, 255), random.randint(0, 20), 255)

    def __str__(self):
        return f"Plate {self.id} at {self.center} with direction {self.direction}"
